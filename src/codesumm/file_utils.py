import os
import pathspec
from codesumm.logger import get_logger

log = get_logger(__name__)


def _build_spec(exclude_patterns: list[str]) -> pathspec.PathSpec:
    return pathspec.PathSpec.from_lines("gitwildmatch", exclude_patterns)


def _is_excluded(path: str, base_dir: str, spec: pathspec.PathSpec) -> bool:
    """
    Returns True if the path matches any exclude pattern.
    pathspec.match_file expects a relative POSIX path.
    Directories get a trailing '/' appended so that directory-only
    patterns (e.g. '.git/') match correctly.
    """
    rel = os.path.relpath(path, base_dir).replace(os.sep, "/")
    if os.path.isdir(path):
        rel += "/"
    return spec.match_file(rel)


def list_contents(
    directory: str, repo_root: str, exclude_patterns: list[str]
) -> tuple[list[str], list[str]]:
    """
    Lists immediate children of directory, split into (files, folders).
    Applies gitignore-style exclusion relative to repo_root so that
    path-based patterns like 'src/generated/' work correctly.
    Returns full absolute paths.
    """
    spec = _build_spec(exclude_patterns)
    files: list[str] = []
    folders: list[str] = []

    try:
        entries = sorted(os.listdir(directory))
    except PermissionError as e:
        log.error("Cannot list directory %s: %s", directory, e)
        return [], []

    for name in entries:
        full_path = os.path.join(directory, name)

        if _is_excluded(full_path, repo_root, spec):
            if os.path.isdir(full_path):
                log.warning("Folder excluded: %s", full_path)
            else:
                log.warning("File excluded: %s", full_path)
            continue

        if os.path.isdir(full_path):
            folders.append(full_path)
            log.info("Found folder: %s", full_path)
        elif os.path.isfile(full_path):
            files.append(full_path)
            log.info("Found file: %s", full_path)

    return files, folders


def filter_supported_files(
    files: list[str], supported_extensions: list[str]
) -> tuple[list[str], list[str]]:
    """
    Splits files into (code_files, doc_files).

    doc_files:  any .md file — either a known doc filename or any other .md.
                .md is never treated as code regardless of filename.
    code_files: files whose extension is in supported_extensions (excluding .md).

    Files with unsupported extensions are skipped with a WARNING.
    """
    code_files: list[str] = []
    doc_files: list[str] = []

    ext_set = {e.lower() for e in supported_extensions}

    for path in files:
        name = os.path.basename(path).lower()
        _, ext = os.path.splitext(name)

        if ext == ".md":
            doc_files.append(path)
            log.info("Doc file: %s", path)
            continue

        if ext in ext_set:
            code_files.append(path)
        else:
            log.warning("Skipping unsupported file type: %s", path)

    return code_files, doc_files


def read_file(path: str) -> str | None:
    """
    Reads a file as UTF-8 text.
    Returns None on binary content, encoding errors, or permission issues.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        log.info("Read file: %s (%d chars)", path, len(content))
        return content
    except (UnicodeDecodeError, PermissionError, OSError) as e:
        log.warning("Skipping file %s: %s", path, e)
        return None


def read_all_files(files: list[str]) -> list[dict]:
    """
    Reads all files, skipping any that fail.
    Returns [{"path": str, "content": str}, ...].
    """
    results = []
    for path in files:
        content = read_file(path)
        if content is not None:
            results.append({"path": path, "content": content})
    return results


def generate_tree(root: str, depth: int, exclude_patterns: list[str]) -> str:
    """
    Generates a simple indented file tree string up to the given depth.
    Used in main.py to include project structure in root_context.
    """
    spec = _build_spec(exclude_patterns)
    lines: list[str] = [os.path.basename(root) + "/"]
    _tree_recurse(root, root, depth, 0, spec, lines)
    return "\n".join(lines)


def _tree_recurse(
    current_dir: str,
    base_dir: str,
    max_depth: int,
    current_depth: int,
    spec: pathspec.PathSpec,
    lines: list[str],
) -> None:
    if current_depth >= max_depth:
        return

    try:
        entries = sorted(os.listdir(current_dir))
    except PermissionError:
        return

    indent = "  " * (current_depth + 1)

    for name in entries:
        full_path = os.path.join(current_dir, name)

        if _is_excluded(full_path, base_dir, spec):
            continue

        if os.path.isdir(full_path):
            lines.append(f"{indent}{name}/")
            _tree_recurse(full_path, base_dir, max_depth, current_depth + 1, spec, lines)
        elif os.path.isfile(full_path):
            lines.append(f"{indent}{name}")
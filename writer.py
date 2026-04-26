import os
from logger import get_logger

log = get_logger(__name__)


def write_summary(repo_root: str, directory: str, output_dir: str, content: str) -> None:
    """
    Writes content to a summary.md file mirroring the directory structure
    under output_dir.

    Example:
      repo_root  = /project
      directory  = /project/src/auth
      output_dir = .summaries
      writes to  = /project/.summaries/src/auth/summary.md
    """
    rel = os.path.relpath(directory, repo_root)
    output_path = os.path.join(repo_root, output_dir, rel, "summary.md")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    content = content.strip()
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    log.info("Summary written: %s", output_path)

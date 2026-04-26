import os
import time
import openai
from dotenv import load_dotenv
from codesumm.config import RateLimitConfig
from codesumm.logger import get_logger

log = get_logger(__name__)

_DEFAULT_CONTEXT_WINDOW = 8192  # conservative fallback if model info can't be fetched

class FatalLLMError(Exception):
    pass


class LLMClient:
    def __init__(self, rate_limit: RateLimitConfig) -> None:
        load_dotenv()

        api_key = os.environ.get("LLM_API_KEY", "")
        base_url = os.environ.get("LLM_BASE_URL", "")
        model = os.environ.get("LLM_MODEL", "")

        if not api_key:
            raise ValueError("LLM_API_KEY is not set in environment")
        if not base_url:
            raise ValueError("LLM_BASE_URL is not set in environment")
        if not model:
            raise ValueError("LLM_MODEL is not set in environment")

        self.model = model
        self.rate_limit = rate_limit
        self._client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.max_context_tokens = self._fetch_context_window()

        log.info("Model: %s", self.model)
        log.info("Context window: %d tokens", self.max_context_tokens)

    def _fetch_context_window(self) -> int:
        """
        Fetches the model's context window size from the /models endpoint.
        Falls back to _DEFAULT_CONTEXT_WINDOW if the model is not found or the
        endpoint fails.
        """
        try:
            # openai SDK exposes the raw models list
            models = self._client.models.list()
            for m in models.data:
                if m.id == self.model:
                    # OpenRouter surfaces context_length in the extra fields
                    ctx = getattr(m, "context_length", None)
                    if ctx and isinstance(ctx, int):
                        log.info("Context window fetched from API: %d tokens", ctx)
                        return ctx
            log.warning(
                "Model '%s' not found in /models response — using default context window of %d",
                self.model,
                _DEFAULT_CONTEXT_WINDOW,
            )
        except Exception as e:
            log.warning(
                "Could not fetch model context window (%s) — using default of %d tokens",
                e,
                _DEFAULT_CONTEXT_WINDOW,
            )
        return _DEFAULT_CONTEXT_WINDOW

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """
        Sends a chat completion request and returns the response text.

        Retry behaviour:
          429  → exponential backoff up to rate_limit.max_retries, then raise
          404  → log CRITICAL, raise FatalLLMError immediately
          other → log ERROR, raise
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        estimated = self.estimate_tokens(system_prompt) + self.estimate_tokens(user_prompt)
        log.info("LLM call — model: %s, estimated input tokens: ~%d", self.model, estimated)

        for attempt in range(self.rate_limit.max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                )
                return response.choices[0].message.content

            except openai.RateLimitError:
                if attempt == self.rate_limit.max_retries:
                    log.error("Rate limit exceeded after %d retries — giving up", attempt)
                    raise
                wait = self.rate_limit.base_delay_seconds * (2 ** attempt)
                log.warning("Rate limited (429). Retry %d/%d in %.1fs", attempt + 1, self.rate_limit.max_retries, wait)
                time.sleep(wait)

            except openai.NotFoundError as e:
                log.critical("404 from LLM — model or endpoint not found: %s", e)
                raise FatalLLMError(str(e)) from e

            except openai.OpenAIError as e:
                log.error("LLM request failed: %s", e)
                raise

        # Unreachable, but satisfies type checkers
        raise RuntimeError("chat() exited retry loop without returning or raising")

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    def fits_in_context(self, texts: list[str], reserve_ratio: float) -> bool:
        total = sum(self.estimate_tokens(t) for t in texts)
        limit = int(self.max_context_tokens * (1 - reserve_ratio))
        log.info("Context check: %d estimated tokens vs %d limit", total, limit)
        return total <= limit

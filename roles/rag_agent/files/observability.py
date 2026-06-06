import logging
import os
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


def _is_enabled() -> bool:
    value = os.getenv("LANGFUSE_TRACING_ENABLED", "false").lower().strip()
    return value in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_langfuse_handler():
    """
    Создаёт Langfuse CallbackHandler для LangChain/LangGraph.

    Важно:
    - если Langfuse выключен через LANGFUSE_TRACING_ENABLED=false,
      возвращаем None;
    - если SDK не установлен или Langfuse недоступен,
      агент НЕ падает, а просто работает без трейсинга.
    """
    if not _is_enabled():
        logger.info("Langfuse tracing is disabled")
        return None

    try:
        from langfuse import get_client
        from langfuse.langchain import CallbackHandler

        langfuse = get_client()

        try:
            if not langfuse.auth_check():
                logger.warning("Langfuse auth_check returned False")
                return None
        except Exception as exc:
            logger.warning("Langfuse auth_check failed: %s", exc)
            return None

        logger.info("Langfuse tracing is enabled")
        return CallbackHandler()

    except Exception as exc:
        logger.warning("Langfuse callback initialization failed: %s", exc)
        return None


def langchain_config(
    *,
    session_id: str = "default",
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Возвращает config для LangGraph/LangChain .ainvoke().

    session_id прокидываем через langfuse_session_id, чтобы в UI Langfuse
    запросы группировались в Sessions.
    """
    handler = get_langfuse_handler()
    if handler is None:
        return {}

    tags = tags or []
    metadata = metadata or {}

    langfuse_metadata = {
        **metadata,
        "langfuse_session_id": session_id,
        "langfuse_tags": tags,
    }

    return {
        "callbacks": [handler],
        "metadata": langfuse_metadata,
        "tags": tags,
        "run_name": "rag-agent-chat",
    }
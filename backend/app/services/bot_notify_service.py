import logging
from typing import Iterable, Sequence

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class BotNotifyError(RuntimeError):
    """Raised when bot notification HTTP call fails."""


def _base_url() -> str:
    base = settings.bot_notify_base_url.strip()
    if not base:
        raise BotNotifyError("bot notify base URL is not configured")
    if base.endswith("/"):
        base = base[:-1]
    return base


def _headers() -> dict[str, str]:
    token = settings.bot_notify_token.strip()
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def notify_user(max_user_id: int, text: str) -> None:
    """Send a single notification to user."""
    _post(f"/notify/{int(max_user_id)}", {"text": text.strip()})


def notify_bulk(sender_max_id: int, user_ids: Sequence[int], text: str) -> int:
    """Send message to multiple users via bot bulk endpoint."""
    ids = _normalize_ids(user_ids)
    if not ids:
        raise BotNotifyError("recipients list is empty")

    payload = {
        "text": text.strip(),
        "sender_id": int(sender_max_id),
        "user_ids": ids,
    }
    _post("/notify/bulk", payload)
    return len(ids)


def notify_tuition_reminder(user_max_id: int) -> None:
    """Trigger tuition reminder notification in bot."""
    _post(f"/notify/payment/tuition/{int(user_max_id)}", None)


def notify_document_ready(user_max_id: int) -> None:
    """Trigger ready-document flow in bot."""
    _post(f"/notify/ready/{int(user_max_id)}", None)


def _normalize_ids(values: Iterable[int]) -> list[int]:
    unique: list[int] = []
    seen: set[int] = set()
    for value in values:
        num = int(value)
        if num <= 0 or num in seen:
            continue
        seen.add(num)
        unique.append(num)
    return unique


def _post(path: str, payload: dict | None) -> None:
    url = f"{_base_url()}{path}"
    try:
        response = httpx.post(url, json=payload, headers=_headers(), timeout=5.0)
        response.raise_for_status()
    except httpx.RequestError as exc:
        logger.error("bot notify request error: %s", exc)
        raise BotNotifyError("бот недоступен") from exc
    except httpx.HTTPStatusError as exc:
        body = exc.response.text
        logger.warning("bot notify rejected request: %s", body)
        raise BotNotifyError(f"бот вернул ошибку: {body}") from exc

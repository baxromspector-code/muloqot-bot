"""Bot faolligini jurnalga yozuvchi middleware (admin sayti grafiklari uchun).

Shaxsiy ma'lumot saqlanmaydi: erkin matn o'rniga faqat «text» turi yoziladi,
menyu tugmalari va buyruqlar esa nomi bilan (m_events, /start, evreg ...).
"""
import asyncio
import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

import db
from texts import T, variants

log = logging.getLogger("activity")
_BUTTONS: dict[str, str] = {}


def _button_key(text: str) -> str | None:
    if not _BUTTONS:
        for key in T:
            if key.startswith(("m_", "btn_")) or key in ("cancel", "skip", "send_phone"):
                for v in variants(key):
                    _BUTTONS.setdefault(v.strip(), key)
    return _BUTTONS.get(text.strip())


def classify(update: Update) -> tuple[int, str, str | None] | None:
    if update.message and update.message.from_user and update.message.chat.type == "private":
        m = update.message
        uid = m.from_user.id
        if m.text:
            if m.text.startswith("/"):
                return uid, "command", m.text.split()[0][:40]
            key = _button_key(m.text)
            return (uid, "button", key) if key else (uid, "text", None)
        for kind in ("photo", "contact", "document", "voice", "video", "sticker"):
            if getattr(m, kind, None):
                return uid, kind, None
        return uid, "other", None
    if update.callback_query and update.callback_query.from_user:
        data = update.callback_query.data or ""
        return update.callback_query.from_user.id, "callback", data.split(":")[0][:40] or None
    return None


async def _save(uid: int, kind: str, action: str | None) -> None:
    try:
        await db.log_activity(uid, kind, action)
    except Exception:  # jurnal yozilmasa bot ishlashda davom etadi
        log.debug("faollik yozilmadi", exc_info=True)


class ActivityLogger(BaseMiddleware):
    def __init__(self) -> None:
        self._tasks: set[asyncio.Task] = set()

    async def __call__(self, handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: dict[str, Any]) -> Any:
        if isinstance(event, Update):
            info = classify(event)
            if info:
                task = asyncio.create_task(_save(*info))  # javobni kechiktirmaydi
                self._tasks.add(task)
                task.add_done_callback(self._tasks.discard)
        return await handler(event, data)

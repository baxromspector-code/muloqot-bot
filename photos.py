"""Talaba suratini olish: Telegram'dan, bo'lmasa bazadagi nusxadan.

Telegram file_id faqat uni olgan botda ishlaydi. Bot tokeni almashsa, eski file_id ochilmaydi —
shuning uchun surat birinchi marta olinganda bazaga (user_photos) nusxa saqlanadi va keyin zaxira sifatida ishlatiladi.
"""
from collections.abc import Awaitable, Callable

import db

Fetch = Callable[[str], Awaitable[bytes | None]]


async def user_photo(user_id: int, file_id: str | None, fetch: Fetch) -> bytes | None:
    saved = await db.get_user_photo(user_id)
    if saved and file_id and saved["file_id"] == file_id:
        return bytes(saved["data"])
    data = None
    if file_id:
        try:
            data = await fetch(file_id)
        except Exception:  # noqa: BLE001 — tarmoq yoki boshqa bot fayli
            data = None
    if data:
        await db.save_user_photo(user_id, file_id, data)
        return data
    return bytes(saved["data"]) if saved else None

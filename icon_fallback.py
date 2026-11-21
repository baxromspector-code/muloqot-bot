"""Tugmalardagi custom emoji belgilari uchun xavfsizlik to'ri.

Belgilar faqat bot egasida Telegram Premium bo'lsa (yoki Fragment username bo'lsa) ishlaydi. Telegram so'rovni
rad etsa, belgilar olib tashlanib (asl matn qaytariladi) so'rov qayta yuboriladi va keyingi barcha
tugmalar belgisiz chiziladi — foydalanuvchi hech qanday xatoni ko'rmaydi.
"""
import logging

from aiogram.client.session.middlewares.base import BaseRequestMiddleware
from aiogram.exceptions import TelegramBadRequest

import keyboards

log = logging.getLogger("icons")


class IconFallback(BaseRequestMiddleware):
    async def __call__(self, make_request, bot, method):
        try:
            return await make_request(bot, method)
        except TelegramBadRequest:
            markup = getattr(method, "reply_markup", None)
            if markup is None or not keyboards.strip_icons(markup):
                raise
            if keyboards.ICONS_ENABLED:
                keyboards.disable_icons()
                log.warning("Telegram tugma belgilarini qabul qilmadi (bot egasida Premium yo'qmi?) — "
                            "belgilar o'chirildi, ranglar qoldi.")
            return await make_request(bot, method)

"""MULOQOT klubi Telegram boti — ishga tushirish nuqtasi.

    python bot.py
"""
import asyncio
import contextlib
import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import BaseStorage
from aiogram.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonDefault, MenuButtonWebApp, Message, WebAppInfo

import db
import keyboards as kb
import scheduler
from activity import ActivityLogger
from config import BOT_TOKEN, REDIS_URL, site_url
from fsm_storage import PostgresStorage
from icon_fallback import IconFallback
from handlers import admin, appeals, events, membership, menu, start
from texts import TG_LANGS, t

log = logging.getLogger("bot")
fallback = Router(name="fallback")
miniapp = Router(name="miniapp")
def app_url() -> str:
    return f"{site_url()}/app"


def app_ready() -> bool:
    return site_url().startswith("https://")  # Telegram Mini App faqat https manzilda ochiladi


@miniapp.message(F.chat.type == "private", F.text.in_({"/app", "/ilova"}))
async def open_app(message: Message):
    if not app_ready():
        return await message.answer("📱 Ilova tez orada ishga tushadi (sayt https manzilga chiqarilgach).")
    await message.answer("📱 <b>MULOQOT ilovasi</b>\nTadbirlar, chiptalar, reyting, ariza va murojaatlar — bitta oynada.",
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                             InlineKeyboardButton(text="Ilovani ochish", web_app=WebAppInfo(url=app_url()))]]))


@fallback.message(F.chat.type == "private")
async def unknown(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user or not user["registered"]:
        return await message.answer(t("need_register", user["lang"] if user else "uz"))
    await message.answer(t("unknown", user["lang"]), reply_markup=kb.main_menu(user["lang"]))


def make_storage() -> BaseStorage:
    if REDIS_URL:
        from aiogram.fsm.storage.redis import RedisStorage  # pip install redis
        return RedisStorage.from_url(REDIS_URL)
    return PostgresStorage()  # holatlar PostgreSQL'da: qayta ishga tushganda yo'qolmaydi


async def setup_bot_profile(bot: Bot) -> None:
    """Botni birinchi ochganda ko'rinadigan tavsif va buyruqlar — har bir til uchun."""
    try:
        for lang in TG_LANGS:
            code = None if lang == "uz" else lang  # uz — standart (boshqa barcha tillar uchun ham)
            await bot.set_my_description(t("bot_description", lang), language_code=code)
            await bot.set_my_short_description(t("bot_short_description", lang), language_code=code)
            await bot.set_my_commands([BotCommand(command="start", description=t("cmd_start", lang))],
                                      language_code=code)
    except Exception:  # Telegram limiti yoki tarmoq — bot ishlashiga xalaqit bermasin
        log.warning("Bot tavsifini o'rnatib bo'lmadi", exc_info=True)
    try:  # chat pastidagi «Ilova» tugmasi (faqat https bo'lsa)
        await bot.set_chat_menu_button(menu_button=MenuButtonWebApp(text="Ilova", web_app=WebAppInfo(url=app_url()))
                                       if app_ready() else MenuButtonDefault())
    except Exception:
        log.warning("Ilova tugmasini o'rnatib bo'lmadi", exc_info=True)


def create() -> tuple[Bot, Dispatcher]:
    """Bot va dispetcher (bir jarayonda faqat bir marta: routerlar bitta dispetcherga ulanadi).
    Polling (python bot.py) ham, webhook (admin_site/tg_webhook.py, Render) ham shuni ishlatadi."""
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    bot.session.middleware(IconFallback())  # Premium bo'lmasa tugma belgilarisiz ishlashda davom etadi
    dp = Dispatcher(storage=make_storage())
    dp.update.outer_middleware(ActivityLogger())  # admin sayti uchun faollik jurnali
    # Tartib muhim: menyu tugmalari jarayon routerlaridan oldin (har qanday holatni bekor qiladi).
    dp.include_routers(miniapp, start.router, admin.router, menu.router, events.router,
                       membership.router, appeals.router, fallback)
    return bot, dp


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN topilmadi: .env faylini to'ldiring (.env.example ga qarang).")
    await db.init()
    bot, dp = create()
    await setup_bot_profile(bot)
    jobs = asyncio.create_task(scheduler.run(bot))
    try:
        await bot.delete_webhook(drop_pending_updates=False)  # navbatdagi xabarlar yo'qolmasin
        await dp.start_polling(bot)
    finally:
        jobs.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await jobs
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

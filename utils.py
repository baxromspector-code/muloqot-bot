from html import escape

from aiogram import Bot
from aiogram.types import Message

from texts import t


def h(value) -> str:
    """Foydalanuvchi matnini HTML uchun xavfsiz qiladi."""
    return escape(str(value), quote=False) if value not in (None, "") else "—"


def course_label(course, lang: str) -> str:
    return t("course_master", lang) if course == "M" else h(course)


def profile_text(user, lang: str) -> str:
    return t(
        "profile", lang,
        full_name=h(user["full_name"]), direction=h(user["direction"]), course=course_label(user["course"], lang),
        group=h(user["group_name"]), student_id=h(user["student_id"]), phone=h(user["phone"]),
    )


def appeal_status(status: str, lang: str) -> str:
    return t(f"st_{status}", lang)


def fmt_id(num: int) -> str:
    return f"{num:04d}"


def short_date(ts: str) -> str:
    """'2026-11-17 23:08' -> '17.11'"""
    return f"{ts[8:10]}.{ts[5:7]}" if ts and len(ts) >= 10 else "—"


def extract_file(message: Message) -> tuple[str, str] | None:
    """Xabardan (file_id, turi) ni ajratadi."""
    if message.photo:
        return message.photo[-1].file_id, "photo"
    if message.document:
        return message.document.file_id, "document"
    if message.voice:
        return message.voice.file_id, "voice"
    if message.video:
        return message.video.file_id, "video"
    if message.audio:
        return message.audio.file_id, "audio"
    return None


async def send_file(bot: Bot, chat_id: int, file_id: str, file_type: str, caption: str | None = None) -> None:
    sender = {
        "photo": bot.send_photo, "document": bot.send_document, "voice": bot.send_voice,
        "video": bot.send_video, "audio": bot.send_audio,
    }[file_type]
    await sender(chat_id, file_id, caption=caption)


async def safe_send(bot: Bot, chat_id: int, text: str, **kwargs) -> bool:
    """Foydalanuvchi botni bloklagan bo'lsa ham yiqilmaydi."""
    try:
        await bot.send_message(chat_id, text, **kwargs)
        return True
    except Exception:
        return False

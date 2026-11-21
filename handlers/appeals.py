"""Murojaatlar: savol / taklif / shikoyat. Foydalanuvchi va admin chat tomoni."""
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import db
import keyboards as kb
from config import ADMIN_CHAT_ID, COMPLAINT_CHAT_ID
from states import AdminReply, Appeal, UserReply
from texts import t, variants
from utils import extract_file, fmt_id, h, profile_text, send_file

router = Router(name="appeals")
MAX_FILES = 5
KIND_UZ = {"question": "❓ Savol", "suggestion": "💡 Taklif", "complaint": "⚖️ SHIKOYAT (maxfiy)"}


def target_chat(kind: str) -> int:
    return COMPLAINT_CHAT_ID if kind == "complaint" else ADMIN_CHAT_ID


def is_staff_chat(chat_id: int) -> bool:
    return chat_id != 0 and chat_id in {ADMIN_CHAT_ID, COMPLAINT_CHAT_ID}


# ======================= foydalanuvchi tomoni =======================
@router.message(Appeal.text, F.chat.type == "private")
async def appeal_text(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    text = message.text or message.caption or ""
    if not 10 <= len(text) <= 2000:
        return await message.answer(t("appeal_bad_len", lang, n=len(text)))
    f = extract_file(message)
    files = [f] if f else []
    await state.update_data(text=text, files=files)
    await state.set_state(Appeal.attach)
    await message.answer(t("appeal_text_ok", lang, n=len(files)), reply_markup=kb.send_cancel_kb(lang))


@router.message(Appeal.attach, F.chat.type == "private", F.text.in_(variants("btn_send")))
async def appeal_send(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    kind = data.get("kind", "question")
    appeal_id = await db.create_appeal(message.from_user.id, kind)
    await db.add_appeal_message(appeal_id, "user", data["text"])
    for file_id, file_type in data.get("files", []):
        await db.add_appeal_message(appeal_id, "user", None, file_id, file_type)
    await state.clear()
    await message.answer(t("appeal_sent", lang, id=fmt_id(appeal_id)), reply_markup=kb.main_menu(lang))
    await notify_staff(bot, appeal_id, data["text"], data.get("files", []), new=True)


@router.message(Appeal.attach, F.chat.type == "private")
async def appeal_attach(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    files = data.get("files", [])
    f = extract_file(message)
    if not f:
        return await message.answer(t("appeal_text_ok", lang, n=len(files)))
    if len(files) >= MAX_FILES:
        return await message.answer(t("appeal_file_limit", lang, max=MAX_FILES))
    files.append(f)
    await state.update_data(files=files)
    await message.answer(t("appeal_file_added", lang, n=len(files), max=MAX_FILES))


@router.callback_query(F.data.startswith("ureply:"))
async def user_reply_start(call: CallbackQuery, state: FSMContext):
    lang = await db.get_lang(call.from_user.id)
    appeal = await db.get_appeal(int(call.data.split(":")[1]))
    if not appeal or appeal["user_id"] != call.from_user.id:
        return await call.answer()
    if appeal["status"] == "closed":
        return await call.answer(t("appeal_is_closed", lang), show_alert=True)
    await state.set_state(UserReply.text)
    await state.update_data(appeal_id=appeal["id"], lang=lang)
    await call.message.answer(t("reply_ask", lang, id=fmt_id(appeal["id"])), reply_markup=kb.cancel_inline(lang))
    await call.answer()


@router.message(UserReply.text, F.chat.type == "private")
async def user_reply_text(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    appeal_id = data["appeal_id"]
    text = message.text or message.caption
    f = extract_file(message)
    if not text and not f:
        return await message.answer(t("reply_ask", lang, id=fmt_id(appeal_id)))
    await db.add_appeal_message(appeal_id, "user", text, *(f or (None, None)))
    await db.set_appeal_status(appeal_id, "new")
    await state.clear()
    await message.answer(t("reply_sent", lang), reply_markup=kb.main_menu(lang))
    await notify_staff(bot, appeal_id, text or "", [f] if f else [], new=False)


async def notify_staff(bot: Bot, appeal_id: int, text: str, files: list, new: bool) -> None:
    appeal = await db.get_appeal(appeal_id)
    chat = target_chat(appeal["kind"])
    if not chat:
        return
    user = await db.get_user(appeal["user_id"])
    head = "📨 <b>Yangi murojaat</b>" if new else "↩️ <b>Foydalanuvchi javobi</b>"
    card = (
        f"{head} #{fmt_id(appeal_id)} · {KIND_UZ.get(appeal['kind'], '')}\n\n{profile_text(user, 'uz')}\n"
        f"🆔 <a href=\"tg://user?id={user['user_id']}\">{user['user_id']}</a>\n\n💬 {h(text)}"
    )
    if appeal["kind"] == "complaint" and new:
        card += "\n\n<i>Nizom 8.4: 3 ish kunida qabul qilinganini bildiring, 10 ish kunida yozma qaror bering.</i>"
    await bot.send_message(chat, card[:4000], reply_markup=kb.admin_appeal_kb(appeal_id))
    for file_id, file_type in files:
        await send_file(bot, chat, file_id, file_type, caption=f"#{fmt_id(appeal_id)}")


# ======================= admin chat tomoni =======================
@router.callback_query(F.data.startswith("a_review:"))
async def admin_review(call: CallbackQuery, bot: Bot):
    if not is_staff_chat(call.message.chat.id):
        return await call.answer()
    appeal = await db.get_appeal(int(call.data.split(":")[1]))
    if not appeal:
        return await call.answer()
    await db.set_appeal_status(appeal["id"], "in_review")
    lang = await db.get_lang(appeal["user_id"])
    try:
        await bot.send_message(appeal["user_id"], t("appeal_in_review", lang, id=fmt_id(appeal["id"])))
    except Exception:
        pass
    await call.answer("Foydalanuvchiga xabar berildi")


@router.callback_query(F.data.startswith("a_reply:"))
async def admin_reply_start(call: CallbackQuery, state: FSMContext):
    if not is_staff_chat(call.message.chat.id):
        return await call.answer()
    appeal_id = int(call.data.split(":")[1])
    await state.set_state(AdminReply.text)
    await state.update_data(appeal_id=appeal_id)
    await call.message.answer(f"✍️ {h(call.from_user.full_name)}, #{fmt_id(appeal_id)} murojaatga javobingizni "
                              f"yozing (matn yoki fayl). Bekor qilish: /cancel")
    await call.answer()


@router.message(AdminReply.text, F.text == "/cancel")
async def admin_reply_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.")


@router.message(AdminReply.text)
async def admin_reply_text(message: Message, state: FSMContext, bot: Bot):
    appeal_id = (await state.get_data())["appeal_id"]
    appeal = await db.get_appeal(appeal_id)
    text = message.text or message.caption
    f = extract_file(message)
    if not appeal or (not text and not f):
        return await message.answer("Matn yoki fayl yuboring. Bekor qilish: /cancel")
    await db.add_appeal_message(appeal_id, "admin", text, *(f or (None, None)))
    await db.set_appeal_status(appeal_id, "answered")
    await state.clear()
    uid = appeal["user_id"]
    lang = await db.get_lang(uid)
    try:
        if f:
            await send_file(bot, uid, f[0], f[1], caption=f"#{fmt_id(appeal_id)}")
        await bot.send_message(uid, t("appeal_answer", lang, id=fmt_id(appeal_id), text=h(text or "📎"))[:4000],
                               reply_markup=kb.reply_kb(lang, appeal_id))
        await message.reply(f"✅ #{fmt_id(appeal_id)} javob yuborildi.")
    except Exception as e:  # foydalanuvchi botni bloklagan bo'lishi mumkin
        await message.reply(f"⚠️ Yuborib bo'lmadi: {h(e)}")


@router.callback_query(F.data.startswith("a_close:"))
async def admin_close(call: CallbackQuery, bot: Bot):
    if not is_staff_chat(call.message.chat.id):
        return await call.answer()
    appeal = await db.get_appeal(int(call.data.split(":")[1]))
    if not appeal:
        return await call.answer()
    await db.set_appeal_status(appeal["id"], "closed")
    lang = await db.get_lang(appeal["user_id"])
    try:
        await bot.send_message(appeal["user_id"], t("appeal_closed", lang, id=fmt_id(appeal["id"])))
    except Exception:
        pass
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer("Yopildi")

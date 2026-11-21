"""/start, til tanlash, ro'yxatdan o'tish va profilning bitta maydonini tahrirlash."""
import asyncio
import io
import re

from aiogram import Bot, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import CallbackQuery, FSInputFile, Message, ReplyKeyboardRemove

import db
import keyboards as kb
import qr
from config import ASSETS
from states import Reg
from texts import DIRECTIONS, LANGS, t
from utils import course_label, h, profile_text

router = Router(name="start")
router.message.filter(F.chat.type == "private")

STUDENT_ID_RE = re.compile(r"^[A-Za-z0-9\-/]{3,30}$")


async def send_banner(message: Message, caption: str, reply_markup=None) -> None:
    """Klub banneri bilan salomlashish (file_id keshlanadi — rasm har safar qayta yuklanmaydi)."""
    path = ASSETS / "banner.png"
    cached = await db.cached_file("banner.png")
    try:
        if cached or path.exists():
            sent = await message.answer_photo(cached or FSInputFile(path), caption=caption, reply_markup=reply_markup)
            if not cached and sent.photo:
                await db.cache_file("banner.png", sent.photo[-1].file_id)
            return
    except Exception:  # rasm yuborilmasa oddiy matn
        pass
    await message.answer(caption, reply_markup=reply_markup)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_user(message.from_user.id)
    if user and user["registered"]:
        lang = user["lang"]
        await send_banner(message, t("welcome_back", lang, name=h(user["full_name"])), kb.main_menu(lang))
        return
    await message.answer(t("choose_lang"), reply_markup=kb.lang_kb())


@router.callback_query(F.data.startswith("lang:"))
async def choose_lang(call: CallbackQuery, state: FSMContext):
    lang = call.data.split(":")[1]
    if lang not in LANGS:
        return await call.answer()
    await db.set_lang(call.from_user.id, lang)
    await call.message.edit_text(t("lang_set", lang))
    await call.answer()
    user = await db.get_user(call.from_user.id)
    if user and user["registered"]:  # sozlamalardan til almashtirildi
        await state.clear()
        await call.message.answer(t("welcome_back", lang, name=h(user["full_name"])), reply_markup=kb.main_menu(lang))
        return
    await send_banner(call.message, t("welcome_new", lang))
    await start_registration(call.message, state, lang)


async def start_registration(message: Message, state: FSMContext, lang: str):
    await state.clear()
    await state.update_data(lang=lang)
    await state.set_state(Reg.name)
    await message.answer(t("ask_name", lang), reply_markup=ReplyKeyboardRemove())


# ---------------- bitta maydonni tahrirlash ----------------
EDIT_STEPS: dict[str, tuple[State, str]] = {
    "full_name": (Reg.name, "ask_name"),
    "direction": (Reg.direction, "ask_direction"),
    "course": (Reg.course, "ask_course"),
    "group_name": (Reg.group, "ask_group"),
    "student_id": (Reg.student_id, "ask_student_id"),
    "phone": (Reg.phone, "ask_phone"),
    "photo_id": (Reg.photo, "ask_photo"),
}


async def edit_single_field(message: Message, state: FSMContext, lang: str, field: str, required: bool = False):
    """Bitta maydonni so'raydi. required=True — bekor qilish tugmasisiz (majburiy surat uchun)."""
    st, prompt = EDIT_STEPS[field]
    await state.clear()
    await state.update_data(lang=lang, edit_one=field)
    await state.set_state(st)
    markup = {"direction": kb.directions_kb(), "course": kb.course_kb(lang), "phone": kb.phone_kb(lang)}.get(field)
    if markup is None:
        markup = ReplyKeyboardRemove() if required else kb.cancel_inline(lang)
    await message.answer(t(prompt, lang), reply_markup=markup)


async def _next(message: Message, state: FSMContext, field: str, value, next_state: State | None, prompt=None,
                markup=None) -> None:
    """Qiymatni saqlaydi: tahrirlash rejimida bazaga yozib tugatadi, aks holda keyingi savolga o'tadi."""
    data = await state.get_data()
    lang = data.get("lang", "uz")
    if data.get("edit_one") == field:
        await db.update_user_field(message.chat.id, field, value)
        await state.clear()
        user = await db.get_user(message.chat.id)
        await message.answer(t("pf_saved", lang), reply_markup=kb.main_menu(lang))
        await message.answer(t("settings", lang, profile=profile_text(user, lang)), reply_markup=kb.settings_kb(lang))
        return
    await state.update_data(**{field: value})
    if next_state:
        await state.set_state(next_state)
        await message.answer(t(prompt, lang), reply_markup=markup)


async def _lang(state: FSMContext) -> str:
    return (await state.get_data()).get("lang", "uz")


# ---------------- ro'yxatdan o'tish qadamlari ----------------
@router.message(Reg.name, F.text)
async def reg_name(message: Message, state: FSMContext):
    lang = await _lang(state)
    name = " ".join(message.text.split())
    if not 3 <= len(name) <= 80 or name.startswith("/"):
        return await message.answer(t("bad_name", lang))
    await _next(message, state, "full_name", name, Reg.direction, "ask_direction", kb.directions_kb())


@router.callback_query(Reg.direction, F.data.startswith("dir:"))
async def reg_direction(call: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    idx = int(call.data.split(":")[1])
    if not 0 <= idx < len(DIRECTIONS):
        return await call.answer()
    await call.message.edit_text(f"{t('ask_direction', lang)}\n<b>{DIRECTIONS[idx]}</b>")
    await call.answer()
    await _next(call.message, state, "direction", DIRECTIONS[idx], Reg.course, "ask_course", kb.course_kb(lang))


@router.callback_query(Reg.course, F.data.startswith("course:"))
async def reg_course(call: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    course = call.data.split(":")[1]
    await call.message.edit_text(f"{t('ask_course', lang)} <b>{course_label(course, lang)}</b>")
    await call.answer()
    await _next(call.message, state, "course", course, Reg.group, "ask_group")


@router.message(Reg.group, F.text)
async def reg_group(message: Message, state: FSMContext):
    lang = await _lang(state)
    group = message.text.strip()
    if not 1 <= len(group) <= 20 or group.startswith("/"):
        return await message.answer(t("bad_group", lang))
    await _next(message, state, "group_name", group, Reg.student_id, "ask_student_id")


@router.message(Reg.student_id, F.text)
async def reg_student_id(message: Message, state: FSMContext):
    lang = await _lang(state)
    sid = message.text.strip()
    if not STUDENT_ID_RE.match(sid):
        return await message.answer(t("bad_student_id", lang))
    await _next(message, state, "student_id", sid, Reg.photo, "ask_photo")


MAX_FACE_TRIES = 2  # yuz aniqlanmasa ikkinchi urinishda qabul qilinadi (admin baribir ko'radi)


@router.message(Reg.photo, F.photo | F.document.mime_type.startswith("image/"))
async def reg_photo(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    file_id = message.photo[-1].file_id if message.photo else message.document.file_id
    buf = io.BytesIO()
    await bot.download(message.photo[-1] if message.photo else message.document, destination=buf)
    tries = data.get("face_tries", 0) + 1
    if not await asyncio.to_thread(qr.has_face, buf.getvalue()) and tries < MAX_FACE_TRIES:
        await state.update_data(face_tries=tries)
        return await message.answer(t("no_face", lang))
    await state.update_data(face_tries=0)
    if data.get("edit_one") == "photo_id":
        return await _next(message, state, "photo_id", file_id, None)
    await message.answer(t("photo_ok", lang))
    await _next(message, state, "photo_id", file_id, Reg.phone, "ask_phone", kb.phone_kb(lang))


@router.message(Reg.photo)
async def reg_photo_bad(message: Message, state: FSMContext):
    await message.answer(t("bad_photo", await _lang(state)))


@router.message(Reg.phone, F.contact)
async def reg_phone(message: Message, state: FSMContext):
    lang = await _lang(state)
    if message.contact.user_id != message.from_user.id:
        return await message.answer(t("bad_phone", lang), reply_markup=kb.phone_kb(lang))
    phone = message.contact.phone_number
    phone = phone if phone.startswith("+") else "+" + phone
    if (await state.get_data()).get("edit_one") == "phone":
        return await _next(message, state, "phone", phone, None)
    await state.update_data(phone=phone)
    await state.set_state(Reg.consent)
    await message.answer(t("phone_ok", lang), reply_markup=ReplyKeyboardRemove())
    await message.answer(t("consent", lang), reply_markup=kb.agree_kb(lang))


@router.message(Reg.phone)
async def reg_phone_bad(message: Message, state: FSMContext):
    lang = await _lang(state)
    await message.answer(t("bad_phone", lang), reply_markup=kb.phone_kb(lang))


@router.callback_query(Reg.consent, F.data == "agree")
async def reg_consent(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    data["username"] = f"@{call.from_user.username}" if call.from_user.username else None
    await db.save_profile(call.from_user.id, data)
    await state.clear()
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()
    await call.message.answer(t("registered", lang), reply_markup=kb.main_menu(lang))

"""Asosiy menyu tugmalari va ma'lumot bo'limlari.

Bu router boshqa jarayon routerlaridan OLDIN ulanadi va holat (FSM) filtrisiz ishlaydi:
menyu tugmasi bosilsa har qanday boshlangan jarayon (murojaat, ariza va h.k.) bekor qilinadi.
Namuna botdagi «menyu tugmasi murojaat matni bo'lib ketishi» xatosi shu bilan tuzatilgan.
"""
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

import db
import keyboards as kb
from config import ADMIN_CHAT_ID, DOCS, INSTAGRAM_URL, TELEGRAM_URL
from handlers.membership import start_join
from handlers.start import edit_single_field, start_registration
from states import Appeal, Reg
from texts import member_level, opt, t, variants
from utils import appeal_status, fmt_id, h, profile_text, short_date

router = Router(name="menu")
router.message.filter(F.chat.type == "private")


async def registered_user(message: Message, state: FSMContext):
    """Ro'yxatdan o'tgan foydalanuvchini qaytaradi va boshlangan jarayonni bekor qiladi."""
    user = await db.get_user(message.from_user.id)
    if not user or not user["registered"]:
        current = await state.get_state()
        if not (current and current.startswith(Reg.__name__)):
            await message.answer(t("need_register", user["lang"] if user else "uz"))
        return None
    if not user["photo_id"]:  # surat majburiy: avval ro'yxatdan o'tganlardan ham so'raladi
        await message.answer(t("need_photo", user["lang"]))
        await edit_single_field(message, state, user["lang"], "photo_id", required=True)
        return None
    await state.clear()
    return user


def menu(key: str):
    return F.text.in_(variants(key))


# ---------------- a'zolik ----------------
@router.message(menu("m_join"))
async def m_join(message: Message, state: FSMContext):
    user = await registered_user(message, state)
    if user:
        await start_join(message, state, user)


@router.message(menu("m_membership"))
async def m_membership(message: Message, state: FSMContext):
    user = await registered_user(message, state)
    if not user:
        return
    lang, uid = user["lang"], user["user_id"]
    points = await db.total_points(uid)
    rank = await db.user_rank(uid)
    went, held = await db.attendance(uid)
    member = await db.get_member(uid)
    if not member or member["status"] != "active":
        await message.answer(t("ms_participant", lang, points=points, rank=rank, went=went, held=held))
        return
    month_start = db.month_start()
    is_active = held > 0 and went * 3 >= held * 2
    expired = member["academic_year"] != db.academic_year()
    text = t(
        "ms_member", lang,
        category=opt("level", member_level(member, went, held), lang), number=member["number"],
        section=opt("section", member["section"], lang), year=member["academic_year"],
        expired=t("expired", lang) if expired else "✅", points=points,
        month_points=await db.total_points(uid, month_start), rank=rank, went=went, held=held,
        active_note=t("active_yes" if is_active else "active_no", lang),
    )
    await message.answer(text, reply_markup=kb.inline([[(t("btn_card", lang), "my_card")]]))


# ---------------- reyting ----------------
@router.message(menu("m_rating"))
async def m_rating(message: Message, state: FSMContext):
    user = await registered_user(message, state)
    if not user:
        return
    lang = user["lang"]
    medals = ["🥇", "🥈", "🥉"]

    def fmt(rows) -> str:
        if not rows:
            return t("rating_empty", lang)
        return "\n".join(f"{medals[i] if i < 3 else f'{i + 1}.'} {h(r['full_name'])} — {r['total']}"
                         for i, r in enumerate(rows))

    month = await db.leaderboard(db.month_start())
    total = await db.leaderboard()
    await message.answer(t("rating", lang, month=fmt(month), total=fmt(total),
                           mine=await db.total_points(user["user_id"]), rank=await db.user_rank(user["user_id"])))


# ---------------- murojaat ----------------
@router.message(menu("m_appeal"))
async def m_appeal(message: Message, state: FSMContext):
    user = await registered_user(message, state)
    if user:
        await message.answer(t("appeal_kind", user["lang"]), reply_markup=kb.appeal_kind_kb(user["lang"]))


@router.callback_query(F.data.startswith("akind:"))
async def appeal_kind(call: CallbackQuery, state: FSMContext):
    kind = call.data.split(":")[1]
    lang = await db.get_lang(call.from_user.id)
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()
    if kind == "complaint":
        await call.message.answer(t("complaint_note", lang))
    await state.set_state(Appeal.text)
    await state.update_data(lang=lang, kind=kind, files=[])
    await call.message.answer(t("appeal_ask_text", lang), reply_markup=kb.cancel_inline(lang))


@router.message(menu("m_my_appeals"))
async def m_my_appeals(message: Message, state: FSMContext):
    user = await registered_user(message, state)
    if not user:
        return
    lang = user["lang"]
    appeals = await db.user_appeals(user["user_id"])
    if not appeals:
        return await message.answer(t("my_appeals_empty", lang))
    rows = [[(f"#{fmt_id(a['id'])} · {appeal_status(a['status'], lang)} · {short_date(a['created_at'])}",
              f"myappeal:{a['id']}")] for a in appeals]
    await message.answer(t("my_appeals_title", lang), reply_markup=kb.inline(rows))


@router.callback_query(F.data.startswith("myappeal:"))
async def show_appeal(call: CallbackQuery):
    lang = await db.get_lang(call.from_user.id)
    appeal = await db.get_appeal(int(call.data.split(":")[1]))
    if not appeal or appeal["user_id"] != call.from_user.id:
        return await call.answer()
    history = []
    for m in await db.appeal_messages(appeal["id"]):
        who = t("you", lang) if m["sender"] == "user" else t("club", lang)
        body = h(m["text"]) if m["text"] else t("attachment", lang)
        history.append(f"<b>{who}</b> ({short_date(m['created_at'])} {m['created_at'][11:]}):\n{body}")
    text = t("appeal_detail", lang, id=fmt_id(appeal["id"]), kind=t(f"kind_{appeal['kind']}", lang),
             status=appeal_status(appeal["status"], lang), date=appeal["created_at"], history="\n\n".join(history))
    markup = None if appeal["status"] == "closed" else kb.reply_kb(lang, appeal["id"])
    await call.message.answer(text[:4000], reply_markup=markup)
    await call.answer()


# ---------------- klub haqida ----------------
@router.message(menu("m_about"))
async def m_about(message: Message, state: FSMContext):
    user = await registered_user(message, state)
    if user:
        await message.answer(t("about_menu", user["lang"]), reply_markup=kb.about_kb(user["lang"]))


@router.callback_query(F.data.startswith("about:"))
async def about_section(call: CallbackQuery):
    key = call.data.split(":")[1]
    lang = await db.get_lang(call.from_user.id)
    await call.answer()
    if key == "ab_links":
        await call.message.answer(
            t("ab_links_text", lang, tg=TELEGRAM_URL, ig=INSTAGRAM_URL),
            reply_markup=kb.url_kb([[("Telegram", TELEGRAM_URL), ("Instagram", INSTAGRAM_URL)]]),
            disable_web_page_preview=True,
        )
        return
    if f"{key}_text" in __import__("texts").T:
        await call.message.answer(t(f"{key}_text", lang))


# ---------------- hujjatlar ----------------
DOC_FILES = {
    "ustav": "MULOQOT-klubi-ustavi.pdf",
    "nizom": "MULOQOT-klubi-nizomi.pdf",
    "blanka": "MULOQOT-azolik-blankasi.docx",
    "taqdimot": "MULOQOT-klubi-taqdimoti.pptx",
}


@router.message(menu("m_docs"))
async def m_docs(message: Message, state: FSMContext):
    user = await registered_user(message, state)
    if user:
        lang = user["lang"]
        await message.answer(f"{t('docs_title', lang)}\n\n{t('docs_note', lang)}", reply_markup=kb.docs_kb(lang))


@router.callback_query(F.data.startswith("doc:"))
async def send_doc(call: CallbackQuery, bot: Bot):
    key = call.data.split(":")[1]
    lang = await db.get_lang(call.from_user.id)
    name = DOC_FILES.get(key)
    await call.answer()
    if not name:
        return
    cached = await db.cached_file(name)
    if cached:
        await bot.send_document(call.from_user.id, cached)
        return
    path = DOCS / name
    if not path.exists():
        return await call.message.answer(t("doc_missing", lang))
    msg = await bot.send_document(call.from_user.id, FSInputFile(path, filename=name))
    if msg.document:
        await db.cache_file(name, msg.document.file_id)


# ---------------- FAQ ----------------
@router.message(menu("m_faq"))
async def m_faq(message: Message, state: FSMContext):
    user = await registered_user(message, state)
    if not user:
        return
    lang = user["lang"]
    items = await db.faq_list(lang) or await db.faq_list("uz")
    if not items:
        return await message.answer(t("faq_empty", lang))
    rows = [[(f["question"][:60], f"faq:{f['id']}")] for f in items]
    await message.answer(t("faq_title", lang), reply_markup=kb.inline(rows))


@router.callback_query(F.data.startswith("faq:"))
async def show_faq(call: CallbackQuery):
    item = await db.faq_get(int(call.data.split(":")[1]))
    if item:
        await call.message.answer(f"❓ <b>{h(item['question'])}</b>\n\n{h(item['answer'])}")
    await call.answer()


# ---------------- sozlamalar ----------------
@router.message(menu("m_settings"))
async def m_settings(message: Message, state: FSMContext):
    user = await registered_user(message, state)
    if user:
        lang = user["lang"]
        text = t("settings", lang, profile=profile_text(user, lang))
        try:
            await message.answer_photo(user["photo_id"], caption=text, reply_markup=kb.settings_kb(lang))
        except Exception:  # surat Telegram'da topilmasa — matn ko'rinishida
            await message.answer(text, reply_markup=kb.settings_kb(lang))


PROFILE_EDIT = ["full_name", "direction", "course", "group_name", "student_id", "phone", "photo_id"]


@router.callback_query(F.data == "edit_profile")
async def edit_profile(call: CallbackQuery):
    lang = await db.get_lang(call.from_user.id)
    buttons = [(t(f"pf_{f}", lang), f"pf:{f}") for f in PROFILE_EDIT]
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)] + [[(t("pf_all", lang), "pf:all")]]
    await call.answer()
    await call.message.answer(t("edit_profile_pick", lang), reply_markup=kb.inline(rows))


@router.callback_query(F.data.startswith("pf:"))
async def edit_profile_field(call: CallbackQuery, state: FSMContext):
    field = call.data.split(":")[1]
    lang = await db.get_lang(call.from_user.id)
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()
    if field == "all":
        return await start_registration(call.message, state, lang)
    if field in PROFILE_EDIT:
        await edit_single_field(call.message, state, lang, field)


@router.callback_query(F.data == "change_lang")
async def change_lang(call: CallbackQuery):
    await call.answer()
    await call.message.answer(t("choose_lang"), reply_markup=kb.lang_kb())


@router.callback_query(F.data == "delete_data")
async def delete_data(call: CallbackQuery):
    lang = await db.get_lang(call.from_user.id)
    await call.answer()
    await call.message.answer(t("delete_confirm", lang), reply_markup=kb.inline([
        [(t("btn_yes", lang), "delete_yes"), (t("btn_no", lang), "delete_no")]]))


@router.callback_query(F.data.in_({"delete_yes", "delete_no"}))
async def delete_answer(call: CallbackQuery, bot: Bot):
    lang = await db.get_lang(call.from_user.id)
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()
    if call.data == "delete_no":
        return await call.message.answer(t("cancelled", lang))
    req_id = await db.add_deletion_request(call.from_user.id)
    await call.message.answer(t("delete_requested", lang))
    if ADMIN_CHAT_ID:
        user = await db.get_user(call.from_user.id)
        await bot.send_message(
            ADMIN_CHAT_ID,
            f"🗑 <b>Ma'lumotlarni o'chirish so'rovi #{req_id}</b>\n{h(user['full_name'] if user else '—')} "
            f"(<a href=\"tg://user?id={call.from_user.id}\">{call.from_user.id}</a>)\n"
            f"Nizom 7.9: 5 ish kuni ichida o'chirilishi kerak.",
            reply_markup=kb.admin_delete_kb(req_id),
        )


# ---------------- umumiy bekor qilish ----------------
@router.callback_query(F.data == "cancel")
async def cancel(call: CallbackQuery, state: FSMContext):
    lang = await db.get_lang(call.from_user.id)
    await state.clear()
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()
    user = await db.get_user(call.from_user.id)
    markup = kb.main_menu(lang) if user and user["registered"] else None
    await call.message.answer(t("cancelled", lang), reply_markup=markup)


@router.message(F.text.in_(variants("btn_cancel")))
async def cancel_text(message: Message, state: FSMContext):
    lang = await db.get_lang(message.from_user.id)
    await state.clear()
    await message.answer(t("cancelled", lang), reply_markup=kb.main_menu(lang))

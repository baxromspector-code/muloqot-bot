"""«📝 A'zo bo'lish» — MULOQOT a'zolik blankasining elektron shakli."""
import io
import json
import re

from aiogram import Bot, F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

import cards
import db
import photos
import keyboards as kb
from config import ADMIN_CHAT_ID
from states import Join
from texts import APP_FIELDS, OPTIONS, opt, t
from utils import course_label, fmt_id, h

router = Router(name="membership")
EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")

# Blanka qadamlari: (holat, maydon, savol kaliti, turi, guruh, ixtiyoriy)
STEPS = [
    (Join.email, "email", "q_email", "email", None, False),
    (Join.social, "social", "q_social", "text", None, True),
    (Join.edu_lang, "edu_lang", "q_edu_lang", "one", "edu_lang", False),
    (Join.section, "section", "q_section", "one", "section", False),
    (Join.directions, "directions", "q_directions", "one", "directions", False),
    (Join.languages, "languages", "q_languages", "text", None, False),
    (Join.mun, "mun", "q_mun", "text", None, True),
    (Join.other_exp, "other_exp", "q_other_exp", "text", None, True),
    (Join.skills, "skills", "q_skills", "many", "skills", True),
    (Join.certs, "certs", "q_certs", "text", None, True),
    (Join.mot1, "mot1", "q_mot1", "motivation", None, False),
    (Join.mot2, "mot2", "q_mot2", "motivation", None, False),
    (Join.mot3, "mot3", "q_mot3", "motivation", None, False),
    (Join.issue, "issue", "q_issue", "text", None, True),
    (Join.hours, "hours", "q_hours", "one", "hours", False),
    (Join.days, "days", "q_days", "many", "days", False),
    (Join.time, "time", "q_time", "many", "time", False),
    (Join.online, "online", "q_online", "yesno", None, False),
    (Join.rules, "rules", "q_rules", "rules", None, False),
    (Join.photo, "photo_consent", "q_photo", "yesno", None, False),
]
STATE_INDEX = {s[0].state: i for i, s in enumerate(STEPS)}

# Foydalanuvchiga ko'rsatiladigan xulosa yorliqlari
LABELS = {
    "app_type": ("Ariza turi", "Тип заявки", "Type", "신청 유형"),
    "email": ("Email", "E-mail", "E-mail", "이메일"),
    "social": ("Instagram/LinkedIn", "Instagram/LinkedIn", "Instagram/LinkedIn", "Instagram/LinkedIn"),
    "edu_lang": ("Ta'lim tili", "Язык обучения", "Language of study", "수업 언어"),
    "section": ("Bo'lim", "Отдел", "Section", "부서"),
    "directions": ("Yo'nalish", "Направление", "Activity", "활동 분야"),
    "languages": ("Tillar", "Языки", "Languages", "언어"),
    "skills": ("Ko'nikmalar", "Навыки", "Skills", "기술"),
    "hours": ("Haftalik vaqt", "Время в неделю", "Hours per week", "주당 시간"),
    "days": ("Qulay kunlar", "Удобные дни", "Days", "가능한 요일"),
    "time": ("Qulay vaqt", "Удобное время", "Time", "가능한 시간"),
    "online": ("Onlayn", "Онлайн", "Online", "온라인"),
    "photo_consent": ("Foto/video", "Фото/видео", "Photo/video", "사진·영상"),
    "motivation": ("Motivatsiya", "Мотивация", "Motivation", "지원 동기"),
    "mun": ("MUN/debat tajribasi", "Опыт MUN/дебатов", "MUN/debate experience", "MUN·토론 경험"),
    "other_exp": ("Boshqa tajriba", "Другой опыт", "Other experience", "기타 경험"),
    "certs": ("Sertifikatlar", "Сертификаты", "Certificates", "자격증"),
    "mot1": ("Nega qo'shilmoqchisiz", "Почему вступаете", "Why join", "가입 이유"),
    "mot2": ("Nimani o'rganmoqchisiz", "Чему хотите научиться", "What to learn", "배우고 싶은 것"),
    "mot3": ("Qanday hissa qo'shasiz", "Ваш вклад", "Your contribution", "기여 방법"),
    "issue": ("Xalqaro masala", "Международная проблема", "International issue", "국제 이슈"),
}
LANG_IDX = {"uz": 0, "ru": 1, "en": 2, "ko": 3}


def _label(key: str, lang: str) -> str:
    if lang == "un":
        from alphabet import to_new
        return to_new(LABELS[key][0])
    return LABELS[key][LANG_IDX.get(lang, 0)]


def _value(field: str, value, lang: str) -> str:
    """Saqlangan qiymatni o'qiladigan matnga aylantiradi."""
    if value in (None, "", []):
        return "—"
    if field == "app_type":
        return t("app_new" if value == "new" else "app_renew", lang)
    if field in ("online", "photo_consent"):
        return t("btn_yes" if value == "yes" else "btn_no", lang)
    if field in OPTIONS:
        if isinstance(value, list):
            return ", ".join(opt(field, v, lang) for v in value)
        return opt(field, value, lang)
    return h(value)


# ---------------- boshlash ----------------
async def start_join(message: Message, state: FSMContext, user) -> None:
    lang = user["lang"]
    last = await db.last_application(user["user_id"])
    if last and last["status"] == "pending":
        await message.answer(t("join_pending", lang, id=fmt_id(last["id"])))
        return
    member = await db.get_member(user["user_id"])
    if member and member["status"] == "active" and member["academic_year"] == db.academic_year():
        await message.answer(t("join_already", lang, year=member["academic_year"]))
        return
    if last and last["status"] == "returned":  # avvalgi javoblar saqlanadi, faqat tahrirlanadi
        answers = json.loads(last["data"] or "{}")
        await state.update_data(lang=lang, answers=answers, edit_one=False)
        await message.answer(t("app_returned_resume", lang, id=fmt_id(last["id"]), reason=h(last["reason"])))
        await ask(message, state, len(STEPS))
        return
    await state.set_state(Join.app_type)
    tg = f"@{message.chat.username}" if message.chat.username else None
    await state.update_data(lang=lang, answers={"telegram": tg})
    default = "renew" if member else "new"
    rows = [[(t("app_new", lang), "atype:new")], [(t("app_renew", lang), "atype:renew")],
            [(t("btn_cancel", lang), "cancel")]]
    if default == "renew":
        rows[0], rows[1] = rows[1], rows[0]
    await message.answer(t("join_intro", lang), reply_markup=kb.inline(rows))


@router.callback_query(Join.app_type, F.data.startswith("atype:"))
async def app_type(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data["answers"]["app_type"] = call.data.split(":")[1]
    await state.update_data(answers=data["answers"])
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()
    await ask(call.message, state, 0)


async def ask(message: Message, state: FSMContext, index: int) -> None:
    """index-raqamli savolni beradi (yoki tugaganda xulosani)."""
    data = await state.get_data()
    lang = data.get("lang", "uz")
    if index >= len(STEPS):
        await state.set_state(Join.confirm)
        await message.answer(t("app_summary", lang, body=_summary(data["answers"], lang)), reply_markup=kb.inline([
            [(t("btn_submit", lang), "app_submit")],
            [(t("btn_edit_answers", lang), "app_edit")],
            [(t("btn_restart", lang), "app_restart"), (t("btn_cancel", lang), "cancel")],
        ]))
        return
    st, field, q, kind, group, optional = STEPS[index]
    await state.set_state(st)
    text = t(q, lang)
    if kind == "one":
        markup = kb.single_choice_kb(group, lang, per_row={"section": 1, "directions": 2}.get(group, 3))
    elif kind == "many":
        selected = data["answers"].get(field) or []
        markup = kb.multi_choice_kb(group, lang, selected, per_row=3 if group == "days" else 2)
    elif kind == "yesno":
        markup = kb.yes_no_kb(lang, f"yn:{field}")
    elif kind == "rules":
        markup = kb.inline([[(t("btn_accept_all", lang), "rules_ok")], [(t("btn_cancel", lang), "cancel")]])
    elif optional:
        markup = kb.skip_kb(lang)
    else:
        markup = kb.cancel_inline(lang)
    await message.answer(text, reply_markup=markup)


async def _save_and_next(message: Message, state: FSMContext, field: str, value) -> None:
    data = await state.get_data()
    answers = data["answers"]
    answers[field] = value
    if data.get("edit_one"):  # bitta javob tahrirlandi — xulosaga qaytamiz
        await state.update_data(answers=answers, edit_one=False)
        return await ask(message, state, len(STEPS))
    await state.update_data(answers=answers)
    current = await state.get_state()
    await ask(message, state, STATE_INDEX[current] + 1)


def _current_step(state_name: str | None):
    if state_name in STATE_INDEX:
        return STEPS[STATE_INDEX[state_name]]
    return None


# ---------------- matnli javoblar ----------------
@router.message(StateFilter(*[s[0] for s in STEPS]), F.chat.type == "private", F.text)
async def join_text(message: Message, state: FSMContext):
    """Blankadagi matnli javoblar."""
    step = _current_step(await state.get_state())
    if not step:
        return
    _, field, q, kind, _, optional = step
    lang = (await state.get_data()).get("lang", "uz")
    text = message.text.strip()
    if kind == "email":
        if not EMAIL_RE.match(text) or len(text) > 100:
            return await message.answer(t("bad_email", lang))
    elif kind == "motivation":
        if not 20 <= len(text) <= 1500:
            return await message.answer(t("bad_motivation", lang))
    elif kind == "text":
        if not 2 <= len(text) <= 1000:
            return await message.answer(t("bad_text", lang))
    else:  # tugma kutilmoqda
        return await message.answer(t(q, lang))
    await _save_and_next(message, state, field, text)


@router.callback_query(StateFilter(Join), F.data == "skip")
async def join_skip(call: CallbackQuery, state: FSMContext):
    step = _current_step(await state.get_state())
    await call.answer()
    if not step or not step[5]:
        return
    await call.message.edit_reply_markup(reply_markup=None)
    await _save_and_next(call.message, state, step[1], None)


# ---------------- tugmali javoblar ----------------
@router.callback_query(StateFilter(Join), F.data.startswith("one:"))
async def join_one(call: CallbackQuery, state: FSMContext):
    step = _current_step(await state.get_state())
    _, group, key = call.data.split(":")
    if not step or step[4] != group or key not in OPTIONS[group]:
        return await call.answer()
    lang = (await state.get_data()).get("lang", "uz")
    await call.message.edit_text(f"{t(step[2], lang)}\n\n<b>{opt(group, key, lang)}</b>")
    await call.answer()
    await _save_and_next(call.message, state, step[1], key)


@router.callback_query(StateFilter(Join), F.data.startswith("many:"))
async def join_many_toggle(call: CallbackQuery, state: FSMContext):
    step = _current_step(await state.get_state())
    _, group, key = call.data.split(":")
    if not step or step[4] != group or key not in OPTIONS[group]:
        return await call.answer()
    data = await state.get_data()
    selected = list(data["answers"].get(step[1]) or [])
    selected.remove(key) if key in selected else selected.append(key)
    data["answers"][step[1]] = selected
    await state.update_data(answers=data["answers"])
    per_row = 3 if group == "days" else 2
    await call.message.edit_reply_markup(reply_markup=kb.multi_choice_kb(group, data.get("lang", "uz"), selected, per_row))
    await call.answer()


@router.callback_query(StateFilter(Join), F.data.startswith("manydone:"))
async def join_many_done(call: CallbackQuery, state: FSMContext):
    step = _current_step(await state.get_state())
    group = call.data.split(":")[1]
    if not step or step[4] != group:
        return await call.answer()
    data = await state.get_data()
    lang = data.get("lang", "uz")
    selected = data["answers"].get(step[1]) or []
    if not selected and not step[5]:
        return await call.answer(t("pick_one", lang), show_alert=True)
    await call.message.edit_text(f"{t(step[2], lang)}\n\n<b>{_value(group, selected, lang)}</b>")
    await call.answer()
    await _save_and_next(call.message, state, step[1], selected)


@router.callback_query(StateFilter(Join), F.data.startswith("yn:"))
async def join_yes_no(call: CallbackQuery, state: FSMContext):
    step = _current_step(await state.get_state())
    _, field, value = call.data.split(":")
    if not step or step[1] != field:
        return await call.answer()
    lang = (await state.get_data()).get("lang", "uz")
    await call.message.edit_text(f"{t(step[2], lang)}\n\n<b>{_value(field, value, lang)}</b>")
    await call.answer()
    await _save_and_next(call.message, state, field, value)


@router.callback_query(Join.rules, F.data == "rules_ok")
async def join_rules(call: CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get("lang", "uz")
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(f"✅ {t('btn_accept_all', lang)[2:]}")
    await call.answer()
    await _save_and_next(call.message, state, "rules", "yes")


# ---------------- xulosa va yuborish ----------------
def _summary(a: dict, lang: str) -> str:
    keys = ["app_type", "email", "social", "edu_lang", "section", "directions", "languages", "skills",
            "hours", "days", "time", "online", "photo_consent"]
    lines = [f"• {_label(k, lang)}: {_value(k, a.get(k), lang)}" for k in keys]
    lines.append(f"• {_label('motivation', lang)}: ✅")
    return "\n".join(lines)


EDITABLE = [i for i, s in enumerate(STEPS) if s[3] != "rules"]


@router.callback_query(Join.confirm, F.data == "app_edit")
async def join_edit_pick(call: CallbackQuery, state: FSMContext):
    lang = (await state.get_data()).get("lang", "uz")
    buttons = [(_label(STEPS[i][1], lang), f"appedit:{i}") for i in EDITABLE]
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)] + [[(t("btn_back", lang), "appedit:back")]]
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()
    await call.message.answer(t("edit_pick", lang), reply_markup=kb.inline(rows))


@router.callback_query(Join.confirm, F.data.startswith("appedit:"))
async def join_edit_field(call: CallbackQuery, state: FSMContext):
    key = call.data.split(":")[1]
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()
    if key == "back" or not key.isdigit() or int(key) not in EDITABLE:
        return await ask(call.message, state, len(STEPS))
    await state.update_data(edit_one=True)
    await ask(call.message, state, int(key))


@router.callback_query(Join.confirm, F.data == "app_restart")
async def join_restart(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    keep = {k: data["answers"].get(k) for k in ("telegram", "app_type")}
    await state.update_data(answers=keep)
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()
    await ask(call.message, state, 0)


@router.callback_query(Join.confirm, F.data == "app_submit")
async def join_submit(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    answers = data["answers"]
    app_id = await db.create_application(call.from_user.id, answers.get("app_type", "new"), answers)
    await state.clear()
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()
    await call.message.answer(t("app_sent", lang, id=fmt_id(app_id)), reply_markup=kb.main_menu(lang))
    await notify_admins_application(bot, app_id)


def application_text(app, user) -> str:
    a = json.loads(app["data"])
    head = (
        f"📝 <b>A'zolik arizasi #{fmt_id(app['id'])}</b> · {_value('app_type', a.get('app_type'), 'uz')}\n\n"
        f"👤 {h(user['full_name'])}\n🎓 {h(user['direction'])}, {course_label(user['course'], 'uz')}-kurs, "
        f"guruh {h(user['group_name'])}\n🪪 Guvohnoma: {h(user['student_id'])}\n📱 {h(user['phone'])}\n"
        f"🆔 <a href=\"tg://user?id={user['user_id']}\">{user['user_id']}</a>\n"
    )
    body = "\n".join(f"<b>{label}:</b> {_value(key, a.get(key), 'uz')}" for key, label in APP_FIELDS
                     if key != "app_type")
    return head + "\n" + body


async def notify_admins_application(bot: Bot, app_id: int) -> None:
    if not ADMIN_CHAT_ID:
        return
    app = await db.get_application(app_id)
    user = await db.get_user(app["user_id"])
    if user["photo_id"]:  # Bosh kotib arizachining suratini ham ko'radi
        try:
            await bot.send_photo(ADMIN_CHAT_ID, user["photo_id"],
                                 caption=f"📸 #{fmt_id(app_id)} · {h(user['full_name'])}")
        except Exception:
            pass
    text = application_text(app, user)
    chunks = [text[i:i + 3900] for i in range(0, len(text), 3900)]
    for i, chunk in enumerate(chunks):
        last = i == len(chunks) - 1
        await bot.send_message(ADMIN_CHAT_ID, chunk, reply_markup=kb.admin_application_kb(app_id) if last else None)


# ---------------- guvohnoma ----------------
async def send_card(bot: Bot, user_id: int) -> bool:
    member = await db.get_member(user_id)
    user = await db.get_user(user_id)
    if not member or not user:
        return False
    async def fetch(file_id: str) -> bytes:
        buf = io.BytesIO()
        await bot.download(file_id, destination=buf)
        return buf.getvalue()

    # Telegram'dan, bo'lmasa bazadagi nusxadan; topilmasa guvohnoma logotip bilan chiqadi
    photo = await photos.user_photo(user_id, user["photo_id"], fetch)
    png = cards.membership_card(
        full_name=user["full_name"] or "—", number=member["number"], section=opt("section", member["section"]),
        group=user["group_name"] or "—", valid_year=member["academic_year"], photo=photo,
    )
    await bot.send_photo(user_id, BufferedInputFile(png, filename=f"{member['number']}.png"),
                         caption=f"🪪 <b>{member['number']}</b> · MULOQOT")
    return True


@router.callback_query(F.data == "my_card")
async def my_card(call: CallbackQuery, bot: Bot):
    await call.answer()
    await send_card(bot, call.from_user.id)

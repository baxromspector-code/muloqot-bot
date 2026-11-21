"""Admin panel: arizalarni ko'rib chiqish, tadbirlar, davomat (QR), ball, FAQ, e'lon, eksport."""
import asyncio
import csv
import io
import json

from aiogram import Bot, F, Router
from aiogram.filters import BaseFilter, Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import (BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message,
                           TelegramObject)

import db
import keyboards as kb
import panel_link
import qr
from config import ADMIN_CHAT_ID, ADMIN_IDS, COMPLAINT_CHAT_ID, PANEL_ADMIN_IDS
from handlers.membership import send_card
from states import AddEvent, AddFaq, AdminReturn, Broadcast
from texts import LANG_NAMES, OPTIONS, TG_LANGS, member_level, opt, t
from utils import fmt_id, h, safe_send

router = Router(name="admin")


class IsAdmin(BaseFilter):
    """ADMIN_IDS dagi foydalanuvchi yoki admin chatdagi istalgan a'zo."""

    async def __call__(self, event: TelegramObject) -> bool:
        user = getattr(event, "from_user", None)
        msg = event.message if isinstance(event, CallbackQuery) else event
        chat_id = msg.chat.id if msg is not None and getattr(msg, "chat", None) else 0
        if user and user.id in ADMIN_IDS:
            return True
        return chat_id != 0 and chat_id in {ADMIN_CHAT_ID, COMPLAINT_CHAT_ID}


router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

HELP = (
    "🛠 <b>MULOQOT admin panel</b>\n\n"
    "/panel — admin saytga kirish havolasi (5 daqiqa, bir martalik)\n"
    "/stats — statistika\n"
    "/addevent — yangi tadbir yoki mashg'ulot\n"
    "/events — tadbirlarni boshqarish (yopish, yakunlash, eslatma, ishtirokchilar)\n"
    "/check KOD — kirishda chiptani tekshirish (EVT-0001 yoki QR matni)\n"
    "/ball ID|MLQ-26-001 SON sabab — ball qo'shish (manfiy son — ayirish)\n"
    "/daraja MLQ-26-001 yetakchi|ekspert|faxriy|avto — a'zolik darajasi\n"
    "/addfaq · /faqlist · /delfaq ID — savol-javoblar\n"
    "/broadcast — barcha foydalanuvchilarga xabar\n"
    "/export — a'zolar va arizalar (CSV)\n"
    "/cancel — joriy amalni bekor qilish\n\n"
    "<i>Ball (Nizom 2.4): mashg'ulot 1 · ko'ngilli yordam 2 · tahliliy matn 3 · debat/MUN 3 · loyihaga mas'ul 5</i>"
)


@router.message(Command("admin", "help"))
async def cmd_admin(message: Message):
    await message.answer(HELP)


@router.message(Command("panel"))
async def cmd_panel(message: Message):
    """Admin sayt uchun bir martalik kirish havolasi — faqat PANEL_ADMIN_IDS va faqat shaxsiy chatda."""
    uid = message.from_user.id if message.from_user else 0
    if uid not in PANEL_ADMIN_IDS:
        return
    if message.chat.type != "private":
        await message.answer("🔒 Havola faqat botning shaxsiy chatida beriladi.")
        return
    link = panel_link.make_link(uid)
    text = ("🔐 <b>Admin panelga kirish</b>\n\nHavola <b>5 daqiqa</b> amal qiladi va faqat <b>bir marta</b> "
            "ishlaydi. Uni hech kimga yubormang.")
    if link.startswith("https://"):
        try:
            await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="Admin panelni ochish", url=link)]]))
            return
        except TelegramBadRequest:
            pass
    try:
        await message.answer(f'{text}\n\n👉 <a href="{h(link)}">Admin panelni ochish</a>', disable_web_page_preview=True)
    except TelegramBadRequest:  # Telegram mahalliy (127.0.0.1) havolani qabul qilmasa — matn ko'rinishida
        await message.answer(f"{text}\n\nBrauzerda oching:\n<code>{h(link)}</code>")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    s = await db.stats()
    await message.answer(
        f"📊 <b>Statistika</b> ({db.academic_year()})\n\n"
        f"👥 Ro'yxatdan o'tganlar: {s['users']}\n🪪 Faol a'zolar: {s['members']}\n"
        f"📝 Kutilayotgan arizalar: {s['apps_pending']}\n✉️ Ochiq murojaatlar: {s['appeals_open']}\n"
        f"📅 Ochiq tadbirlar: {s['events']}\n☑️ Belgilangan davomat: {s['tickets_used']}"
    )


# ======================= a'zolik arizalari =======================
async def _app_and_lang(app_id: int):
    app = await db.get_application(app_id)
    return app, (await db.get_lang(app["user_id"]) if app else "uz")


@router.callback_query(F.data.startswith("ap_ok:"))
async def app_accept(call: CallbackQuery):
    app, _ = await _app_and_lang(int(call.data.split(":")[1]))
    if not app or app["status"] != "pending":
        return await call.answer("Bu ariza allaqachon ko'rib chiqilgan", show_alert=True)
    await call.message.edit_reply_markup(reply_markup=kb.admin_section_kb(app["id"]))
    await call.answer("Bo'limni tanlang")


@router.callback_query(F.data.startswith("ap_sec:"))
async def app_section(call: CallbackQuery, bot: Bot):
    _, app_id, section = call.data.split(":")
    app, lang = await _app_and_lang(int(app_id))
    if not app or app["status"] != "pending" or section not in OPTIONS["section"]:
        return await call.answer()
    number = await db.upsert_member(app["user_id"], section)
    await db.decide_application(app["id"], "accepted", section=section)
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.reply(f"✅ #{fmt_id(app['id'])} qabul qilindi → {number}, {opt('section', section)} "
                             f"({h(call.from_user.full_name)})")
    await call.answer()
    await safe_send(bot, app["user_id"], t("app_accepted", lang, id=fmt_id(app["id"]), number=number,
                                            section=opt("section", section, lang), year=db.academic_year()))
    try:
        await send_card(bot, app["user_id"])
    except Exception:
        pass


@router.callback_query(F.data.startswith("ap_ret:"))
async def app_return(call: CallbackQuery, state: FSMContext):
    app, _ = await _app_and_lang(int(call.data.split(":")[1]))
    if not app or app["status"] != "pending":
        return await call.answer("Bu ariza allaqachon ko'rib chiqilgan", show_alert=True)
    await state.set_state(AdminReturn.reason)
    await state.update_data(app_id=app["id"])
    await call.message.answer(f"↩️ #{fmt_id(app['id'])}: nimani to'ldirish kerakligini yozing. Bekor qilish: /cancel")
    await call.answer()


@router.message(AdminReturn.reason, F.text)
async def app_return_reason(message: Message, state: FSMContext, bot: Bot):
    app_id = (await state.get_data())["app_id"]
    app, lang = await _app_and_lang(app_id)
    await state.clear()
    if not app or app["status"] != "pending":
        return await message.answer("Ariza topilmadi yoki allaqachon ko'rib chiqilgan.")
    await db.decide_application(app_id, "returned", reason=message.text)
    await safe_send(bot, app["user_id"], t("app_returned", lang, id=fmt_id(app_id), reason=h(message.text)))
    await message.reply(f"↩️ #{fmt_id(app_id)} to'ldirish uchun qaytarildi.")


@router.callback_query(F.data.startswith("ap_no:"))
async def app_reject(call: CallbackQuery):
    app, _ = await _app_and_lang(int(call.data.split(":")[1]))
    if not app or app["status"] != "pending":
        return await call.answer("Bu ariza allaqachon ko'rib chiqilgan", show_alert=True)
    await call.message.edit_reply_markup(reply_markup=kb.admin_reject_kb(app["id"]))
    await call.answer("Ustav 4.6: faqat shu 3 sabab")


@router.callback_query(F.data.startswith("ap_rej:"))
async def app_reject_reason(call: CallbackQuery, bot: Bot):
    _, app_id, reason_key = call.data.split(":")
    app, lang = await _app_and_lang(int(app_id))
    if not app or app["status"] != "pending" or not reason_key.startswith("rej_"):
        return await call.answer()
    await db.decide_application(app["id"], "rejected", reason=t(reason_key, "uz"))
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.reply(f"❌ #{fmt_id(app['id'])} rad etildi: {t(reason_key, 'uz')} ({h(call.from_user.full_name)})")
    await call.answer()
    await safe_send(bot, app["user_id"], t("app_rejected", lang, id=fmt_id(app["id"]), reason=t(reason_key, lang)))


# ======================= tadbirlar =======================
@router.message(Command("addevent"))
async def addevent_start(message: Message, state: FSMContext):
    await state.set_state(AddEvent.kind)
    await message.answer("Turini tanlang:", reply_markup=kb.inline([
        [("🗣 Haftalik mashg'ulot (1-daraja)", "aev:session")], [("📅 Tadbir / ochiq uchrashuv", "aev:event")]]))


@router.callback_query(AddEvent.kind, F.data.startswith("aev:"))
async def addevent_kind(call: CallbackQuery, state: FSMContext):
    kind = call.data.split(":")[1]
    await state.update_data(kind=kind)
    await state.set_state(AddEvent.title)
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer("1/7 Nomi (masalan: «Debat: Ko'p qutbli dunyo»):")
    await call.answer()


ADD_EVENT_FLOW = [
    (AddEvent.title, "title", "2/7 Tavsif (mavzu, kimlar uchun, nima qilinadi). O'tkazib yuborish uchun «-»:"),
    (AddEvent.description, "description", "3/7 Sana va vaqt (masalan: 24.11.2026 16:00):"),
    (AddEvent.date_text, "date_text", "4/7 Joy (masalan: B-blok, 9-qavat):"),
    (AddEvent.place, "place", "5/7 Joylar soni (0 — cheklanmagan):"),
    (AddEvent.capacity, "capacity", "6/7 Qatnashgani uchun ball (odatda 1; debat/MUN — 3):"),
    (AddEvent.points, "points", "7/7 Nechta ko'ngilli kerak? (0 — kerak emas):"),
    (AddEvent.volunteers, "volunteers", None),
]
INT_FIELDS = {"capacity", "points", "volunteers"}


@router.message(StateFilter(*[s[0] for s in ADD_EVENT_FLOW]), F.text)
async def addevent_step(message: Message, state: FSMContext):
    current = await state.get_state()
    idx = next(i for i, s in enumerate(ADD_EVENT_FLOW) if s[0].state == current)
    _, field, next_prompt = ADD_EVENT_FLOW[idx]
    value: object = message.text.strip()
    extra = {}
    if field in INT_FIELDS:
        if not str(value).isdigit():
            return await message.answer("❗ Butun son kiriting.")
        value = int(str(value))
    elif field == "description" and value == "-":
        value = ""
    elif field == "date_text":
        starts_at = db.parse_event_date(str(value))
        if not starts_at:
            return await message.answer("❗ Sana formati: 24.11.2026 16:00")
        if starts_at < db.now():
            return await message.answer("❗ Bu sana o'tib ketgan. Kelajakdagi sanani kiriting.")
        value = starts_at.strftime("%d.%m.%Y %H:%M")
        extra["starts_at"] = starts_at.isoformat()
    await state.update_data(**{field: value}, **extra)
    if next_prompt:
        await state.set_state(ADD_EVENT_FLOW[idx + 1][0])
        return await message.answer(next_prompt)
    data = await state.get_data()
    await state.clear()
    event_id = await db.add_event(data)
    await message.answer(
        f"✅ Tadbir #{event_id} yaratildi: <b>{h(data['title'])}</b>\n🗓 {h(data['date_text'])} · 📍 {h(data['place'])}\n"
        f"Joylar: {data['capacity'] or 'cheklanmagan'} · Ball: {data['points']} · Ko'ngillilar: {data['volunteers']}\n\n"
        "🔔 Chipta olganlarga 24 soat oldin eslatma avtomatik ketadi, boshlanganda ro'yxat yopiladi, "
        "6 soatdan keyin tadbir yakunlangan deb davomatga kiritiladi.\n\n"
        "<i>Nizom 6.2: 2-darajali tadbir uchun dekanatga 3 hafta, 3-darajali uchun universitetga 4 hafta oldin ariza.</i>",
        reply_markup=kb.inline([[("📣 Hammaga e'lon qilish", f"ev_announce:{event_id}")]]),
    )


@router.message(Command("events"))
async def cmd_events(message: Message):
    events = await db.recent_events()
    if not events:
        return await message.answer("Tadbirlar yo'q. /addevent")
    for ev in events:
        taken = await db.taken_seats(ev["id"])
        state = "🏁 yakunlangan" if ev["finished"] else ("🟢 ro'yxat ochiq" if ev["active"] else "⏸ ro'yxat yopiq")
        await message.answer(
            f"#{ev['id']} <b>{h(ev['title'])}</b>\n🗓 {h(ev['date_text'])} · 📍 {h(ev['place'])}\n"
            f"🎫 {taken}/{ev['capacity'] or '∞'} · ⭐ {ev['points']} · {state}",
            reply_markup=kb.admin_event_kb(ev),
        )


@router.callback_query(F.data.regexp(r"^ev_(open|close|finish):\d+$"))
async def event_toggle(call: CallbackQuery):
    action, eid = call.data.split(":")
    eid = int(eid)
    if action == "ev_open":
        await db.set_event_active(eid, True)
    elif action == "ev_close":
        await db.set_event_active(eid, False)
    else:
        await db.finish_event(eid)
    ev = await db.get_event(eid)
    await call.message.edit_reply_markup(reply_markup=kb.admin_event_kb(ev))
    await call.answer({"ev_open": "Ochildi", "ev_close": "Yopildi", "ev_finish": "Yakunlandi — davomat hisobiga kirdi"}[action])


@router.callback_query(F.data.startswith("ev_remind:"))
async def event_remind(call: CallbackQuery, bot: Bot):
    ev = await db.get_event(int(call.data.split(":")[1]))
    await call.answer("Yuborilmoqda...")
    sent = 0
    for p in await db.event_participants(ev["id"]):
        if p["status"] != "active":
            continue
        lang = await db.get_lang(p["user_id"])
        if await safe_send(bot, p["user_id"], t("event_reminder", lang, title=h(ev["title"]),
                                                   date=h(ev["date_text"]), place=h(ev["place"]))):
            sent += 1
        await asyncio.sleep(0.05)
    await call.message.reply(f"🔔 Eslatma {sent} kishiga yuborildi.")


@router.callback_query(F.data.startswith("ev_announce:"))
async def event_announce(call: CallbackQuery, bot: Bot):
    ev = await db.get_event(int(call.data.split(":")[1]))
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer("E'lon yuborilmoqda...")
    sent = 0
    for uid in await db.registered_ids():
        lang = await db.get_lang(uid)
        text = t("event_card", lang, title=h(ev["title"]), kind=t(f"kind_{ev['kind']}", lang), date=h(ev["date_text"]),
                 place=h(ev["place"]), seats=str(ev["capacity"] or t("unlimited", lang)), points=ev["points"],
                 description=h(ev["description"]) if ev["description"] else "")
        markup = kb.inline([[(t("btn_register_event", lang), f"evreg:{ev['id']}")]])
        if await safe_send(bot, uid, "📣 " + text[:3990], reply_markup=markup):
            sent += 1
        await asyncio.sleep(0.05)
    await call.message.reply(f"📣 E'lon {sent} kishiga yuborildi.")


def _csv(rows: list[list], header: list[str]) -> bytes:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue().encode("utf-8-sig")


@router.callback_query(F.data.startswith("ev_list:"))
async def event_list(call: CallbackQuery, bot: Bot):
    ev = await db.get_event(int(call.data.split(":")[1]))
    parts = await db.event_participants(ev["id"])
    rows = [[db.ticket_code(p["id"]), p["full_name"], p["phone"], p["group_name"],
             "keldi" if p["status"] == "used" else "", p["used_at"] or ""] for p in parts]
    data = _csv(rows, ["Chipta", "F.I.Sh", "Telefon", "Guruh", "Davomat", "Kelgan vaqti"])
    await call.answer()
    await bot.send_document(call.message.chat.id, BufferedInputFile(data, filename=f"tadbir_{ev['id']}.csv"),
                            caption=f"👥 {h(ev['title'])}: {len(parts)} ta ishtirokchi")


# ======================= davomat (QR) =======================
async def _check_in(message: Message, bot: Bot, raw: str):
    parsed = db.parse_ticket_code(raw)
    if not parsed:
        return await message.answer("❗ Kod noto'g'ri. Misol: /check EVT-0012")
    ticket_id, token = parsed
    tk = await db.get_ticket_by_id(ticket_id)
    if not tk or (token and token != tk["token"]):
        return await message.answer("❌ Chipta topilmadi yoki QR soxta.")
    ev = await db.get_event(tk["event_id"])
    user = await db.get_user(tk["user_id"])
    who = f"{h(user['full_name'])} · {h(user['group_name'])}"
    if tk["status"] == "used":
        return await message.answer(f"⚠️ Bu chipta allaqachon ishlatilgan ({tk['used_at']}).\n{who}")
    if tk["status"] != "active":
        return await message.answer(f"❌ Chipta bekor qilingan.\n{who}")
    if not await db.use_ticket(tk["id"]):  # ikki admin bir vaqtda skanerlasa
        return await message.answer(f"⚠️ Bu chipta hozirgina ishlatildi.\n{who}")
    await db.add_points(tk["user_id"], ev["points"], f"Qatnashish: {ev['title']}")
    lang = await db.get_lang(tk["user_id"])
    await safe_send(bot, tk["user_id"], t("checked_in", lang, title=h(ev["title"])) + "\n" +
                    t("points_added", lang, amount=ev["points"], reason=h(ev["title"]),
                      total=await db.total_points(tk["user_id"])))
    caption = (f"✅ Kirish tasdiqlandi: {who}\n🎟 {db.ticket_code(tk['id'])} · {h(ev['title'])} · +{ev['points']} ball\n"
               f"👀 Suratdagi odam chipta egasi ekanini tekshiring.")
    if user["photo_id"]:  # navbatchi yuzni solishtiradi — chiptani boshqaga berib bo'lmaydi
        try:
            return await bot.send_photo(message.chat.id, user["photo_id"], caption=caption)
        except Exception:
            pass
    await message.answer(caption)


@router.message(Command("check"))
async def cmd_check(message: Message, command: CommandObject, bot: Bot):
    if not command.args:
        return await message.answer("Foydalanish: /check EVT-0012 (yoki QR skanerdan olingan matn)")
    await _check_in(message, bot, command.args)


@router.message(F.text.regexp(r"(?i)^MULOQOT:EVT-\d+:[0-9A-F]+$"))
async def qr_text(message: Message, bot: Bot):
    """QR skaner ilovasidan nusxa olingan matnni to'g'ridan-to'g'ri yuborish ham mumkin."""
    await _check_in(message, bot, message.text)


@router.message(StateFilter(None), F.photo | F.document.mime_type.startswith("image/"))
async def qr_photo(message: Message, bot: Bot):
    """Navbatchi chipta rasmini (yoki telefondagi suratini) yuboradi — bot QR'ni o'zi o'qiydi."""
    buf = io.BytesIO()
    await bot.download(message.photo[-1] if message.photo else message.document, destination=buf)
    text = await asyncio.to_thread(qr.decode, buf.getvalue())
    if text and text.upper().startswith("MULOQOT:EVT-"):
        return await _check_in(message, bot, text)
    if message.chat.type == "private":  # guruhda oddiy rasmlarga javob bermaymiz
        await message.answer("🔍 Rasmda MULOQOT chiptasining QR kodi topilmadi. QR aniq va to'liq ko'rinsin, "
                             "yoki /check EVT-0001 deb yozing.")


# ======================= ball =======================
@router.message(Command("ball"))
async def cmd_ball(message: Message, command: CommandObject, bot: Bot):
    parts = (command.args or "").split(maxsplit=2)
    if len(parts) < 3 or not parts[1].lstrip("-").isdigit():
        return await message.answer("Foydalanish: /ball 123456789 3 Tahliliy matn\nyoki: /ball MLQ-26-001 5 Loyihaga mas'ul")
    target, amount, reason = parts[0], int(parts[1]), parts[2]
    if target.upper().startswith("MLQ-"):
        member = await db.get_member_by_number(target)
        uid = member["user_id"] if member else None
    else:
        uid = int(target) if target.isdigit() else None
    user = await db.get_user(uid) if uid else None
    if not user:
        return await message.answer("❌ Foydalanuvchi topilmadi.")
    await db.add_points(uid, amount, reason)
    total = await db.total_points(uid)
    lang = user["lang"]
    if amount > 0:
        await safe_send(bot, uid, t("points_added", lang, amount=amount, reason=h(reason), total=total))
    await message.answer(f"⭐ {h(user['full_name'])}: {amount:+d} ({h(reason)}). Jami: {total}")


LEVEL_ALIASES = {"yetakchi": "leader", "leader": "leader", "ekspert": "expert", "mentor": "expert",
                 "expert": "expert", "faxriy": "honorary", "honorary": "honorary",
                 "avto": None, "auto": None, "yoq": None, "yo'q": None}


@router.message(Command("daraja"))
async def cmd_level(message: Message, command: CommandObject, bot: Bot):
    """A'zolik darajasi (tashkiliy model, VI bo'lim). Kuzatuvchi/nomzod/faol — davomatdan avtomatik."""
    parts = (command.args or "").split()
    if len(parts) != 2 or parts[1].lower() not in LEVEL_ALIASES:
        return await message.answer(
            "Foydalanish: /daraja MLQ-26-001 yetakchi\n"
            "Darajalar: <b>yetakchi</b> · <b>ekspert</b> (mentor) · <b>faxriy</b> · <b>avto</b> (qo'lda belgilashni olib tashlash)\n"
            "<i>Kuzatuvchi, nomzod va faol a'zo darajalari davomatdan o'zi hisoblanadi (faol — 2/3 qatnashish).</i>")
    target, level = parts[0], LEVEL_ALIASES[parts[1].lower()]
    member = await (db.get_member_by_number(target) if target.upper().startswith("MLQ-")
                    else db.get_member(int(target)) if target.isdigit() else asyncio.sleep(0, None))
    if not member:
        return await message.answer("❌ A'zo topilmadi (guvohnoma raqami yoki Telegram ID).")
    await db.set_member_level(member["user_id"], level)
    member = await db.get_member(member["user_id"])
    went, held = await db.attendance(member["user_id"])
    user = await db.get_user(member["user_id"])
    now = member_level(member, went, held)
    lang = user["lang"] if user else "uz"
    await safe_send(bot, member["user_id"], t("level_changed", lang, level=opt("level", now, lang)))
    await message.answer(f"🎖 {h(user['full_name'] if user else member['number'])} ({member['number']}): "
                         f"<b>{opt('level', now)}</b>" + (" <i>(avtomatik)</i>" if level is None else ""))


# ======================= ko'ngillilar va o'chirish =======================
@router.callback_query(F.data.regexp(r"^v_(ok|no):\d+$"))
async def volunteer_decide(call: CallbackQuery, bot: Bot):
    action, vid = call.data.split(":")
    vol = await db.get_volunteer_by_id(int(vid))
    if not vol or vol["status"] != "pending":
        return await call.answer("Allaqachon ko'rib chiqilgan")
    ev = await db.get_event(vol["event_id"])
    status = "accepted" if action == "v_ok" else "rejected"
    await db.set_volunteer_status(vol["id"], status)
    lang = await db.get_lang(vol["user_id"])
    await safe_send(bot, vol["user_id"], t("vol_accepted" if status == "accepted" else "vol_rejected", lang,
                                           title=h(ev["title"])))
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.reply(("✅ Qabul qilindi" if status == "accepted" else "❌ Rad etildi") +
                             (". Tadbirdan keyin: /ball ID 2 Ko'ngilli yordam" if status == "accepted" else ""))
    await call.answer()


@router.callback_query(F.data.startswith("del_ok:"))
async def delete_user(call: CallbackQuery, bot: Bot):
    req = await db.get_deletion_request(int(call.data.split(":")[1]))
    if not req or req["status"] != "pending":
        return await call.answer("Allaqachon bajarilgan")
    lang = await db.get_lang(req["user_id"])
    await db.delete_user_data(req["user_id"])
    await db.finish_deletion_request(req["id"])
    await safe_send(bot, req["user_id"], t("data_deleted", lang))
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.reply(f"🗑 #{req['id']} — ma'lumotlar o'chirildi ({h(call.from_user.full_name)}).")
    await call.answer()


# ======================= FAQ =======================
@router.message(Command("addfaq"))
async def addfaq_start(message: Message, state: FSMContext):
    await state.set_state(AddFaq.lang)
    await message.answer("Qaysi til uchun?", reply_markup=kb.inline([[(name, f"faqlang:{code}")]
                                                                      for code, name in LANG_NAMES.items()
                                                                      if code in TG_LANGS]))


@router.callback_query(AddFaq.lang, F.data.startswith("faqlang:"))
async def addfaq_lang(call: CallbackQuery, state: FSMContext):
    await state.update_data(lang=call.data.split(":")[1])
    await state.set_state(AddFaq.question)
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer("Savol matni:")
    await call.answer()


@router.message(AddFaq.question, F.text)
async def addfaq_question(message: Message, state: FSMContext):
    await state.update_data(question=message.text.strip())
    await state.set_state(AddFaq.answer)
    await message.answer("Javob matni:")


@router.message(AddFaq.answer, F.text)
async def addfaq_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()
    faq_id = await db.faq_add(data["lang"], data["question"], message.text.strip())
    await message.answer(f"✅ FAQ #{faq_id} qo'shildi ({data['lang']}).")


@router.message(Command("faqlist"))
async def faq_list(message: Message):
    items = await db.faq_all()
    if not items:
        return await message.answer("FAQ bo'sh. /addfaq")
    await message.answer("\n".join(f"#{f['id']} [{f['lang']}] {h(f['question'])}" for f in items)[:4000])


@router.message(Command("delfaq"))
async def faq_delete(message: Message, command: CommandObject):
    if not command.args or not command.args.strip().isdigit():
        return await message.answer("Foydalanish: /delfaq 3")
    await db.faq_delete(int(command.args))
    await message.answer("🗑 O'chirildi.")


# ======================= e'lon =======================
@router.message(Command("broadcast"))
async def broadcast_start(message: Message, state: FSMContext):
    await state.set_state(Broadcast.message)
    await message.answer("📣 Hammaga yuboriladigan xabarni yuboring (matn, rasm, video...). Bekor qilish: /cancel")


@router.message(Broadcast.message)
async def broadcast_send(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    ids = await db.registered_ids()
    await message.answer(f"Yuborilmoqda: {len(ids)} kishi...")
    sent = 0
    for uid in ids:
        try:
            await bot.copy_message(uid, message.chat.id, message.message_id)
            sent += 1
        except Exception:
            pass
        await asyncio.sleep(0.05)  # Telegram limiti: ~20 xabar/soniya
    await message.answer(f"✅ {sent}/{len(ids)} kishiga yetkazildi.")


# ======================= eksport =======================
@router.message(Command("export"))
async def cmd_export(message: Message, bot: Bot):
    members = await db.all_members()
    m_rows = [[m["number"], m["full_name"], opt("section", m["section"]), m["academic_year"], m["status"],
               m["direction"], m["course"], m["group_name"], m["student_id"], m["phone"], m["username"] or "",
               await db.total_points(m["user_id"])] for m in members]
    await bot.send_document(message.chat.id, BufferedInputFile(_csv(m_rows, [
        "Guvohnoma", "F.I.Sh", "Bo'lim", "O'quv yili", "Holat", "Yo'nalish", "Kurs", "Guruh", "Talaba ID",
        "Telefon", "Telegram", "Ball"]), filename="azolar.csv"), caption=f"🪪 A'zolar: {len(members)}")

    apps = await db.all_applications()
    keys = ["email", "edu_lang", "section", "directions", "languages", "skills", "hours", "days", "time",
            "online", "photo_consent", "mot1", "mot2", "mot3"]
    a_rows = []
    for a in apps:
        d = json.loads(a["data"] or "{}")
        a_rows.append([fmt_id(a["id"]), a["user_id"], a["app_type"], a["status"], a["reason"] or "", a["created_at"]] +
                      [", ".join(d[k]) if isinstance(d.get(k), list) else (d.get(k) or "") for k in keys])
    await bot.send_document(message.chat.id, BufferedInputFile(_csv(a_rows, [
        "Ariza", "User ID", "Turi", "Holat", "Sabab", "Sana"] + keys), filename="arizalar.csv"),
        caption=f"📝 Arizalar: {len(apps)}")

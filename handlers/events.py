"""Tadbirlar, QR-chiptalar va ko'ngillilar (foydalanuvchi tomoni). Barcha tadbirlar bepul."""
from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

import cards
import db
import keyboards as kb
from config import ADMIN_CHAT_ID
from handlers.menu import menu, registered_user
from texts import t
from utils import h

router = Router(name="events")
router.message.filter(F.chat.type == "private")


def seats_text(ev, taken: int, lang: str) -> str:
    return f"{taken} / {ev['capacity']}" if ev["capacity"] else f"{taken} ({t('unlimited', lang)})"


async def send_ticket(bot: Bot, ticket_id: int, lang: str) -> None:
    tk = await db.get_ticket_by_id(ticket_id)
    ev = await db.get_event(tk["event_id"])
    user = await db.get_user(tk["user_id"])
    code = db.ticket_code(tk["id"])
    png = cards.ticket(
        event_title=ev["title"], date_text=ev["date_text"] or "—", place=ev["place"] or "—", code=code,
        owner=user["full_name"] or "—", payload=f"MULOQOT:{code}:{tk['token']}",
    )
    markup = None
    if tk["status"] == "active" and not ev["finished"]:
        markup = kb.inline([[(t("btn_cancel_ticket", lang), f"tkcancel:{tk['id']}")]])
    await bot.send_photo(
        tk["user_id"], BufferedInputFile(png, filename=f"{code}.png"),
        caption=t("ticket_caption", lang, title=h(ev["title"]), date=h(ev["date_text"]), place=h(ev["place"]), code=code),
        reply_markup=markup,
    )


# ---------------- tadbirlar ----------------
@router.message(menu("m_events"))
async def m_events(message: Message, state: FSMContext):
    user = await registered_user(message, state)
    if not user:
        return
    lang = user["lang"]
    events = await db.open_events()
    if not events:
        return await message.answer(t("events_empty", lang))
    rows = [[(f"{'🗣' if e['kind'] == 'session' else '📅'} {e['title'][:40]} · {e['date_text'] or ''}"[:64],
              f"ev:{e['id']}")] for e in events]
    await message.answer(t("events_title", lang), reply_markup=kb.inline(rows))


@router.callback_query(F.data.startswith("ev:"))
async def event_card(call: CallbackQuery):
    lang = await db.get_lang(call.from_user.id)
    ev = await db.get_event(int(call.data.split(":")[1]))
    await call.answer()
    if not ev:
        return
    taken = await db.taken_seats(ev["id"])
    text = t("event_card", lang, title=h(ev["title"]), kind=t(f"kind_{ev['kind']}", lang), date=h(ev["date_text"]),
             place=h(ev["place"]), seats=seats_text(ev, taken, lang), points=ev["points"],
             description=h(ev["description"]) if ev["description"] else "")
    tk = await db.get_ticket(ev["id"], call.from_user.id)
    if tk and tk["status"] in ("active", "used"):
        markup = kb.inline([[(f"🎟 {db.ticket_code(tk['id'])}", f"tk:{tk['id']}")]])
    elif ev["active"] and not ev["finished"]:
        markup = kb.inline([[(t("btn_register_event", lang), f"evreg:{ev['id']}")]])
    else:
        markup = None
    await call.message.answer(text[:4000], reply_markup=markup)


@router.callback_query(F.data.startswith("evreg:"))
async def event_register(call: CallbackQuery, bot: Bot):
    lang = await db.get_lang(call.from_user.id)
    user = await db.get_user(call.from_user.id)
    if not user or not user["registered"]:
        return await call.answer(t("need_register", lang), show_alert=True)
    ev = await db.get_event(int(call.data.split(":")[1]))
    if not ev or not ev["active"] or ev["finished"]:
        return await call.answer(t("event_closed", lang), show_alert=True)
    tk = await db.get_ticket(ev["id"], call.from_user.id)
    if tk and tk["status"] in ("active", "used"):
        await call.answer()
        return await send_ticket(bot, tk["id"], lang)
    if ev["capacity"] and await db.taken_seats(ev["id"]) >= ev["capacity"]:
        return await call.answer(t("event_full", lang), show_alert=True)
    ticket_id = await db.create_ticket(ev["id"], call.from_user.id)
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer("✅")
    await send_ticket(bot, ticket_id, lang)


# ---------------- chiptalar ----------------
@router.message(menu("m_tickets"))
async def m_tickets(message: Message, state: FSMContext):
    user = await registered_user(message, state)
    if not user:
        return
    lang = user["lang"]
    tickets = await db.user_tickets(user["user_id"])
    if not tickets:
        return await message.answer(t("tickets_empty", lang))
    rows = [[(f"{'☑️' if tk['status'] == 'used' else '🎟'} {db.ticket_code(tk['id'])} · {tk['title'][:35]}",
              f"tk:{tk['id']}")] for tk in tickets]
    await message.answer(t("tickets_title", lang), reply_markup=kb.inline(rows))


@router.callback_query(F.data.startswith("tk:"))
async def show_ticket(call: CallbackQuery, bot: Bot):
    tk = await db.get_ticket_by_id(int(call.data.split(":")[1]))
    await call.answer()
    if tk and tk["user_id"] == call.from_user.id:
        await send_ticket(bot, tk["id"], await db.get_lang(call.from_user.id))


@router.callback_query(F.data.startswith("tkcancel:"))
async def cancel_ticket(call: CallbackQuery):
    lang = await db.get_lang(call.from_user.id)
    tk = await db.get_ticket_by_id(int(call.data.split(":")[1]))
    if not tk or tk["user_id"] != call.from_user.id or tk["status"] != "active":
        return await call.answer()
    await db.cancel_ticket(tk["id"])
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()
    await call.message.answer(t("ticket_cancelled", lang))


# ---------------- ko'ngillilar ----------------
@router.message(menu("m_volunteer"))
async def m_volunteer(message: Message, state: FSMContext):
    user = await registered_user(message, state)
    if not user:
        return
    lang = user["lang"]
    events = await db.volunteer_events()
    if not events:
        return await message.answer(t("vol_empty", lang))
    lines = [t("vol_title", lang), ""]
    rows = []
    for e in events:
        lines.append(f"• <b>{h(e['title'])}</b> — {h(e['date_text'])}, {h(e['place'])} ({e['volunteers']})")
        rows.append([(f"{t('btn_apply_vol', lang)}: {e['title'][:30]}", f"vol:{e['id']}")])
    await message.answer("\n".join(lines), reply_markup=kb.inline(rows))


@router.callback_query(F.data.startswith("vol:"))
async def volunteer_apply(call: CallbackQuery, bot: Bot):
    lang = await db.get_lang(call.from_user.id)
    ev = await db.get_event(int(call.data.split(":")[1]))
    if not ev or ev["finished"]:
        return await call.answer(t("event_closed", lang), show_alert=True)
    if await db.get_volunteer(ev["id"], call.from_user.id):
        return await call.answer(t("vol_already", lang), show_alert=True)
    vid = await db.add_volunteer(ev["id"], call.from_user.id)
    await call.answer()
    await call.message.answer(t("vol_applied", lang))
    if ADMIN_CHAT_ID:
        user = await db.get_user(call.from_user.id)
        member = await db.get_member(call.from_user.id)
        await bot.send_message(
            ADMIN_CHAT_ID,
            f"🙋 <b>Ko'ngilli arizasi</b> — {h(ev['title'])}\n👤 {h(user['full_name'])} "
            f"({member['number'] if member else 'ishtirokchi'})\n📱 {h(user['phone'])} · {h(user['group_name'])}",
            reply_markup=kb.admin_volunteer_kb(vid),
        )

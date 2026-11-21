"""Fon vazifalari: tadbir eslatmalari, ro'yxatni yopish, avto-yakunlash, muddatlar bo'yicha kunlik hisobot
va bazaning kunlik zaxirasi (tools/backup_db.py).

Har 5 daqiqada ishlaydi. Kunlik hisobot har kuni soat 09:00 dan keyin bir marta yuboriladi.
"""
import asyncio
import logging
from datetime import date, datetime, timedelta

from aiogram import Bot

import db
from config import ADMIN_CHAT_ID, ADMIN_IDS, COMPLAINT_CHAT_ID, DATABASE_URL
from texts import t
from utils import fmt_id, h, safe_send

log = logging.getLogger("scheduler")
INTERVAL = 300            # soniya
REMIND_BEFORE = timedelta(hours=24)
AUTOFINISH_AFTER = timedelta(hours=6)
DIGEST_HOUR = 9

# Ustav va Nizomdagi muddatlar (ish kunlarida)
SECRETARY_CHECK_DAYS = 3   # Nizom 2.2: Bosh kotib ma'lumotni tekshiradi
COUNCIL_DECISION_DAYS = 10  # Ustav 4.6: Kengash qarori
COMPLAINT_ACK_DAYS = 3     # Nizom 8.4: shikoyat qabul qilinganini bildirish
COMPLAINT_DECISION_DAYS = 10
APPEAL_REPLY_DAYS = 3      # oddiy savol/taklifga javob (klub ichki qoidasi)


def working_days_between(start: date, end: date) -> int:
    """start (kirmaydi) va end (kiradi) oralig'idagi dushanba–juma kunlari."""
    days, d = 0, start
    while d < end:
        d += timedelta(days=1)
        if d.weekday() < 5:
            days += 1
    return days


def _age(created_at: str) -> int:
    return working_days_between(datetime.strptime(created_at[:10], "%Y-%m-%d").date(), date.today())


async def remind_events(bot: Bot) -> None:
    for ev in await db.events_to_remind(db.now() + REMIND_BEFORE):
        sent = 0
        for p in await db.event_participants(ev["id"]):
            if p["status"] != "active":
                continue
            lang = await db.get_lang(p["user_id"])
            if await safe_send(bot, p["user_id"], t("event_reminder", lang, title=h(ev["title"]),
                                                       date=h(ev["date_text"]), place=h(ev["place"]))):
                sent += 1
            await asyncio.sleep(0.05)
        await db.mark_reminded(ev["id"])
        log.info("Eslatma: tadbir #%s, %s kishi", ev["id"], sent)


async def close_and_finish(bot: Bot) -> None:
    closed = await db.close_started_events()
    if closed:
        log.info("Boshlangan %s ta tadbirda ro'yxat yopildi", closed)
    for ev in await db.events_to_autofinish(db.now() - AUTOFINISH_AFTER):
        await db.finish_event(ev["id"])
        came = sum(1 for p in await db.event_participants(ev["id"]) if p["status"] == "used")
        if ADMIN_CHAT_ID:
            await safe_send(bot, ADMIN_CHAT_ID, f"🏁 «{h(ev['title'])}» avtomatik yakunlandi va davomat hisobiga "
                                                f"kirdi. Kelganlar: {came}. Ro'yxat: /events")


async def daily_digest(bot: Bot) -> None:
    today = date.today().isoformat()
    if datetime.now().hour < DIGEST_HOUR or await db.get_meta("digest_date") == today:
        return
    await db.set_meta("digest_date", today)

    lines = []
    for a in await db.pending_applications():
        age = _age(a["created_at"])
        if age >= COUNCIL_DECISION_DAYS:
            lines.append(f"🔴 Ariza #{fmt_id(a['id'])} ({h(a['full_name'])}) — {age} ish kuni, Kengash muddati "
                         f"({COUNCIL_DECISION_DAYS}) o'tdi")
        elif age >= SECRETARY_CHECK_DAYS:
            lines.append(f"🟡 Ariza #{fmt_id(a['id'])} ({h(a['full_name'])}) — {age} ish kuni, "
                         f"qaror uchun {COUNCIL_DECISION_DAYS - age} kun qoldi")
    complaints = []
    for ap in await db.open_appeals():
        age = _age(ap["created_at"])
        if ap["kind"] == "complaint":
            if ap["status"] == "new" and age >= COMPLAINT_ACK_DAYS:
                complaints.append(f"🔴 Shikoyat #{fmt_id(ap['id'])} — {age} ish kuni, qabul qilinganini bildirish "
                                  f"muddati ({COMPLAINT_ACK_DAYS}) o'tdi")
            elif age >= COMPLAINT_DECISION_DAYS:
                complaints.append(f"🔴 Shikoyat #{fmt_id(ap['id'])} — {age} ish kuni, yozma qaror muddati o'tdi")
        elif ap["status"] == "new" and age >= APPEAL_REPLY_DAYS:
            lines.append(f"🟡 Murojaat #{fmt_id(ap['id'])} ({h(ap['full_name'])}) — {age} ish kunidan beri javobsiz")

    if lines and ADMIN_CHAT_ID:
        await safe_send(bot, ADMIN_CHAT_ID, "⏰ <b>Muddatlar bo'yicha kunlik eslatma</b>\n\n" + "\n".join(lines)[:3800])
    if complaints and COMPLAINT_CHAT_ID:
        await safe_send(bot, COMPLAINT_CHAT_ID, "⚖️ <b>Shikoyatlar muddati (Nizom 8.4)</b>\n\n" + "\n".join(complaints))


_backup_failed_at = 0.0


async def daily_backup(bot: Bot) -> None:
    """Oxirgi zaxiradan 24 soat o'tgan bo'lsa — yangi zaxira (alohida oqimda, bot to'xtab qolmaydi).
    Xato bo'lsa bot egasiga xabar (ko'pi bilan 6 soatda bir marta)."""
    global _backup_failed_at
    import os
    if os.getenv("LOCAL_BACKUP", "1") == "0":  # bulut serverda (Railway/Docker) zaxirani platforma oladi
        return
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent / "tools"))
    import backup_db
    if not backup_db.due():
        return
    try:
        path = await asyncio.to_thread(backup_db.make_backup, DATABASE_URL)
        log.info("Baza zaxirasi olindi: %s (%d KB)", path, path.stat().st_size // 1024)
    except Exception as e:
        log.exception("Baza zaxirasini olib bo'lmadi")
        now = datetime.now().timestamp()
        if now - _backup_failed_at > 6 * 3600:
            _backup_failed_at = now
            owner = 7089836188 if 7089836188 in ADMIN_IDS else next(iter(ADMIN_IDS), 0)
            if owner:
                await safe_send(bot, owner, "⚠️ <b>Baza zaxirasi olinmadi</b>\n<code>" + h(str(e))[:500] + "</code>")


async def tick(bot: Bot) -> None:
    for job in (remind_events, close_and_finish, daily_digest, daily_backup):
        try:
            await job(bot)
        except Exception:  # bitta vazifadagi xato qolganlarini to'xtatmasin
            log.exception("Rejalashtiruvchi vazifasida xato: %s", job.__name__)


async def run(bot: Bot) -> None:
    while True:
        await tick(bot)
        await asyncio.sleep(INTERVAL)

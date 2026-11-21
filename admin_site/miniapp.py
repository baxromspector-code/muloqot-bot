"""Telegram Mini App (bot ichidagi veb-ilova) uchun API.

Har bir so'rov Telegram imzolagan initData bilan keladi (X-Tg-Init sarlavhasi); server uni bot tokeni
bilan tekshiradi (HMAC-SHA256) va foydalanuvchi ID'sini faqat shundan oladi — boshqa birovning nomidan
so'rov yuborib bo'lmaydi. Biznes qoidalari botdagi bilan bir xil: o'sha db funksiyalari va o'sha
admin xabarnomalari (notify_admins_application, notify_staff) ishlatiladi.
"""
import asyncio
import hashlib
import hmac
import html
import json
import logging
import re
import time
from urllib.parse import parse_qsl

import httpx
from fastapi import APIRouter, Body, Depends, Header, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response

import cards
import db
import photos
from config import ADMIN_CHAT_ID, BOT_TOKEN, DOCS, SITE_DEFAULTS
from texts import member_level, DIRECTIONS, LANG_NAMES, LANGS, OPTIONS, T, opt, strip_emoji, t

log = logging.getLogger("miniapp")
router = APIRouter()
INIT_MAX_AGE = 24 * 3600
DOC_FILES = {"ustav": "MULOQOT-klubi-ustavi.pdf", "nizom": "MULOQOT-klubi-nizomi.pdf",
             "blanka": "MULOQOT-azolik-blankasi.docx", "taqdimot": "MULOQOT-klubi-taqdimoti.pptx"}
DOC_NAMES = {"ustav": "Klub ustavi", "nizom": "Klub nizomi", "blanka": "A'zolik blankasi", "taqdimot": "Klub taqdimoti"}
ABOUT = ["ab_mission", "ab_directions", "ab_modules", "ab_structure", "ab_leaders", "ab_rhythm"]
KINDS = ("question", "suggestion", "complaint")


# ---------------- Telegram imzosini tekshirish ----------------
def check_init_data(raw: str) -> dict:
    if not raw or not BOT_TOKEN:
        raise HTTPException(401, "no init data")
    pairs = dict(parse_qsl(raw, keep_blank_values=True))
    received = pairs.pop("hash", "")
    check = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    calc = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    if not received or not hmac.compare_digest(calc, received):
        raise HTTPException(401, "bad signature")
    if time.time() - int(pairs.get("auth_date") or 0) > INIT_MAX_AGE:
        raise HTTPException(401, "expired")
    user = json.loads(pairs.get("user") or "{}")
    if not isinstance(user.get("id"), int):
        raise HTTPException(401, "no user")
    return user


async def tg_user(x_tg_init: str = Header("", alias="X-Tg-Init")) -> dict:
    return check_init_data(x_tg_init)


async def reg_user(tg: dict = Depends(tg_user)) -> dict:
    user = await db.get_user(tg["id"])
    if not user or not user["registered"]:
        raise HTTPException(403, "Avval botda ro'yxatdan o'ting")
    return {**user, "_tg": tg}


def _err(msg: str, code: int = 400):
    return JSONResponse({"detail": msg}, code)


# ---------------- yordamchilar ----------------
_TAG = re.compile(r"&lt;(/?)(b|i|u|code)&gt;")
_LINK = re.compile(r"&lt;a href=&quot;((?:https?|tg)://[^&\s]+?)&quot;&gt;(.*?)&lt;/a&gt;", re.S)


def tg_html(s: str) -> str:
    """Bot matnidagi Telegram-HTML ni xavfsiz HTML ga aylantiradi (faqat b, i, u, code va havola)."""
    e = html.escape(s or "", quote=True)
    e = _LINK.sub(lambda m: f'<a href="{m.group(1)}" target="_blank" rel="noopener">{m.group(2)}</a>', e)
    return _TAG.sub(lambda m: f"<{m.group(1)}{m.group(2)}>", e).replace("\n", "<br>")


_bot = None


def bot():
    """Admin xabarnomalari uchun aiogram Bot (bot jarayoni bilan bir xil token, faqat xabar yuboradi)."""
    global _bot
    if _bot is None:
        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        _bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    return _bot


async def close() -> None:
    if _bot is not None:
        await _bot.session.close()


def _later(coro, what: str) -> None:
    async def run():
        try:
            await coro
        except Exception:  # xabarnoma o'tmasa ham foydalanuvchi amali saqlangan
            log.warning("Xabarnoma yuborilmadi: %s", what, exc_info=True)
    asyncio.create_task(run())


_files: dict[str, tuple[float, bytes]] = {}


async def tg_file(file_id: str) -> bytes | None:
    if file_id in _files and _files[file_id][0] > time.time():
        return _files[file_id][1]
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile", params={"file_id": file_id})
            path = r.json().get("result", {}).get("file_path") if r.status_code == 200 else None
            if not path:
                return None
            f = await c.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{path}")
        if f.status_code != 200:
            return None
    except httpx.HTTPError:
        return None
    if len(_files) > 200:
        _files.clear()
    _files[file_id] = (time.time() + 3600, f.content)
    return f.content


def _png(data: bytes) -> Response:
    return Response(data, media_type="image/png", headers={"Cache-Control": "private, no-store"})


# ---------------- profil va bosh sahifa ----------------
# Bosh sahifa uchun hamma narsa BITTA SQL so'rovda (avval 9 ta alohida murojaat edi):
# 3000 kishi bir vaqtda kirganda baza va server navbati keskin qisqaradi.
ME_SQL = """
WITH mine AS (SELECT COALESCE(SUM(amount), 0)::int AS pts FROM points WHERE user_id = $1)
SELECT u.*,
       mine.pts AS points,
       (SELECT COALESCE(SUM(amount), 0) FROM points WHERE user_id = $1 AND created_at >= $3)::int AS month_points,
       (SELECT COUNT(*) FROM (SELECT 1 FROM points GROUP BY user_id HAVING SUM(amount) > mine.pts) s)::int + 1 AS rank,
       (SELECT COUNT(*) FROM events WHERE finished AND finished_at >= $2)::int AS held,
       (SELECT COUNT(*) FROM tickets t JOIN events e ON e.id = t.event_id
         WHERE t.user_id = $1 AND t.status = 'used' AND e.finished AND e.finished_at >= $2)::int AS went,
       m.number AS m_number, m.section AS m_section, m.academic_year AS m_year, m.status AS m_status,
       m.level AS m_level,
       la.id AS la_id, la.status AS la_status, la.reason AS la_reason
FROM users u
CROSS JOIN mine
LEFT JOIN members m ON m.user_id = u.user_id
LEFT JOIN LATERAL (SELECT id, status, reason FROM applications a WHERE a.user_id = u.user_id
                   ORDER BY id DESC LIMIT 1) la ON TRUE
WHERE u.user_id = $1"""


@router.get("/me")
async def me(tg: dict = Depends(tg_user)):
    user = await db._one(ME_SQL, tg["id"], db.semester_start(), db.month_start())
    links = {"bot": SITE_DEFAULTS["bot"], "telegram": SITE_DEFAULTS["telegram"], "instagram": SITE_DEFAULTS["instagram"]}
    if not user or not user["registered"]:
        return {"registered": False, "first_name": tg.get("first_name", ""), "links": links,
                "lang": (user or {}).get("lang", "uz")}
    lang = user["lang"]
    went, held, points, month_points, rank = (user["went"], user["held"], user["points"], user["month_points"],
                                              user["rank"])
    member = ({"number": user["m_number"], "section": user["m_section"], "academic_year": user["m_year"],
               "status": user["m_status"], "level": user["m_level"]} if user["m_number"] else None)
    last = {"id": user["la_id"], "status": user["la_status"], "reason": user["la_reason"]} if user["la_id"] else None
    m = None
    if member:
        m = {"number": member["number"], "section": strip_emoji(opt("section", member["section"], lang)) if member["section"] else "—",
             "year": member["academic_year"], "active": member["status"] == "active",
             "expired": member["academic_year"] != db.academic_year(),
             "is_active_member": held > 0 and went * 3 >= held * 2}
    level = member_level(member, went, held)
    return {
        "registered": True, "lang": lang, "langs": [{"key": k, "label": strip_emoji(LANG_NAMES[k])} for k in LANGS],
        "user": {k: user[k] for k in ("full_name", "username", "direction", "course", "group_name", "student_id", "phone")},
        "has_photo": bool(user["photo_id"]),
        "points": points, "month_points": month_points, "rank": rank, "went": went, "held": held, "member": m,
        "level": strip_emoji(opt("level", level, lang)), "level_key": level,
        "application": {"id": last["id"], "status": last["status"], "reason": last["reason"]} if last else None,
        "links": links, "directions": DIRECTIONS,
    }


@router.get("/photo")
async def my_photo(user: dict = Depends(reg_user)):
    data = await photos.user_photo(user["user_id"], user["photo_id"], tg_file)
    if not data:
        raise HTTPException(404)
    return Response(data, media_type="image/jpeg", headers={"Cache-Control": "private, max-age=3600"})


STUDENT_ID_RE = re.compile(r"^[A-Za-z0-9\-/]{3,30}$")


@router.put("/profile")
async def edit_profile(data: dict = Body(...), user: dict = Depends(reg_user)):
    name = " ".join(str(data.get("full_name", "")).split())
    group = str(data.get("group_name", "")).strip()
    sid = str(data.get("student_id", "")).strip()
    direction, course = data.get("direction"), str(data.get("course", ""))
    if not 3 <= len(name) <= 80:
        return _err("Ism-familiya 3–80 belgi bo'lsin")
    if direction not in DIRECTIONS:
        return _err("Yo'nalishni ro'yxatdan tanlang")
    if course not in ("1", "2", "3", "4", "M"):
        return _err("Kursni tanlang")
    if not 1 <= len(group) <= 20:
        return _err("Guruh nomini yozing (20 belgigacha)")
    if not STUDENT_ID_RE.match(sid):
        return _err("Talaba ID: 3–30 ta harf, raqam, - yoki /")
    for field, value in (("full_name", name), ("direction", direction), ("course", course),
                         ("group_name", group), ("student_id", sid)):
        await db.update_user_field(user["user_id"], field, value)
    return {"ok": True}


@router.put("/lang")
async def set_lang(data: dict = Body(...), user: dict = Depends(reg_user)):
    if data.get("lang") not in LANGS:
        return _err("Bunday til yo'q")
    await db.set_lang(user["user_id"], data["lang"])
    return {"ok": True}


@router.post("/delete")
async def delete_request(user: dict = Depends(reg_user)):
    import keyboards as kb
    from utils import h
    req_id = await db.add_deletion_request(user["user_id"])
    if ADMIN_CHAT_ID:
        _later(bot().send_message(
            ADMIN_CHAT_ID,
            f"🗑 <b>Ma'lumotlarni o'chirish so'rovi #{req_id}</b> (ilova orqali)\n{h(user['full_name'])} "
            f"(<a href=\"tg://user?id={user['user_id']}\">{user['user_id']}</a>)\n"
            f"Nizom 7.9: 5 ish kuni ichida o'chirilishi kerak.", reply_markup=kb.admin_delete_kb(req_id)), "delete")
    return {"ok": True, "message": strip_emoji(t("delete_requested", user["lang"]))}


# ---------------- tadbirlar va chiptalar ----------------
def _ticket_out(tk) -> dict:
    return {"id": tk["id"], "status": tk["status"], "code": db.ticket_code(tk["id"])}


EVENTS_SQL = """
    SELECT e.id, e.title, e.kind, e.description, e.date_text, e.place, e.capacity, e.points, e.starts_at, e.active,
           (SELECT COUNT(*) FROM tickets t WHERE t.event_id = e.id AND t.status IN ('active','used'))::int AS taken,
           mt.id AS tk_id, mt.status AS tk_status
    FROM events e
    LEFT JOIN tickets mt ON mt.event_id = e.id AND mt.user_id = $1 AND mt.status IN ('active','used')
    WHERE e.active AND NOT e.finished
    ORDER BY e.starts_at NULLS LAST, e.id"""


@router.get("/events")
async def events(user: dict = Depends(reg_user)):
    """Bitta SQL so'rov (har bir tadbir uchun alohida so'rov emas) — ro'yxat tez chiqadi."""
    out = []
    for e in await db._all(EVENTS_SQL, user["user_id"]):
        tk = {"id": e.pop("tk_id"), "status": e.pop("tk_status")}
        e["ticket"] = _ticket_out(tk) if tk["id"] else None
        out.append(e)
    return out


@router.post("/events/{eid}/register")
async def register(eid: int, user: dict = Depends(reg_user)):
    ev = await db.get_event(eid)
    if not ev or not ev["active"] or ev["finished"]:
        return _err("Ro'yxatga olish yopilgan")
    tk = await db.get_ticket(eid, user["user_id"])
    if tk and tk["status"] in ("active", "used"):
        return _ticket_out(tk)
    if ev["capacity"] and await db.taken_seats(eid) >= ev["capacity"]:
        return _err("Joylar to'lgan")
    tid = await db.create_ticket(eid, user["user_id"])
    return _ticket_out(await db.get_ticket_by_id(tid))


@router.get("/tickets")
async def tickets(user: dict = Depends(reg_user)):
    return [{"id": tk["id"], "status": tk["status"], "code": db.ticket_code(tk["id"]), "title": tk["title"],
             "date_text": tk["date_text"], "place": tk["place"], "finished": tk["finished"]}
            for tk in await db.user_tickets(user["user_id"])]


@router.get("/tickets/{tid}.png")
async def ticket_png(tid: int, user: dict = Depends(reg_user)):
    tk = await db.get_ticket_by_id(tid)
    if not tk or tk["user_id"] != user["user_id"]:
        raise HTTPException(404)
    ev = await db.get_event(tk["event_id"])
    code = db.ticket_code(tk["id"])
    return _png(cards.ticket(event_title=ev["title"], date_text=ev["date_text"] or "—", place=ev["place"] or "—",
                             code=code, owner=user["full_name"] or "—", payload=f"MULOQOT:{code}:{tk['token']}"))


@router.post("/tickets/{tid}/cancel")
async def ticket_cancel(tid: int, user: dict = Depends(reg_user)):
    tk = await db.get_ticket_by_id(tid)
    if not tk or tk["user_id"] != user["user_id"] or tk["status"] != "active":
        return _err("Bu chiptani bekor qilib bo'lmaydi")
    await db.cancel_ticket(tid)
    return {"ok": True}


@router.get("/volunteer")
async def volunteer_list(user: dict = Depends(reg_user)):
    out = []
    for e in await db.volunteer_events():
        out.append({k: e[k] for k in ("id", "title", "date_text", "place", "volunteers")}
                   | {"applied": bool(await db.get_volunteer(e["id"], user["user_id"]))})
    return out


@router.post("/volunteer/{eid}")
async def volunteer_apply(eid: int, user: dict = Depends(reg_user)):
    import keyboards as kb
    from utils import h
    ev = await db.get_event(eid)
    if not ev or ev["finished"]:
        return _err("Tadbir yakunlangan")
    if await db.get_volunteer(eid, user["user_id"]):
        return _err("Siz allaqachon ariza bergansiz")
    vid = await db.add_volunteer(eid, user["user_id"])
    if ADMIN_CHAT_ID:
        member = await db.get_member(user["user_id"])
        _later(bot().send_message(
            ADMIN_CHAT_ID, f"🙋 <b>Ko'ngilli arizasi</b> (ilova) — {h(ev['title'])}\n👤 {h(user['full_name'])} "
            f"({member['number'] if member else 'ishtirokchi'})\n📱 {h(user['phone'])} · {h(user['group_name'])}",
            reply_markup=kb.admin_volunteer_kb(vid)), "volunteer")
    return {"ok": True}


# ---------------- reyting va guvohnoma ----------------
_board_cache: dict[str, tuple[float, list]] = {}


async def _board(kind: str) -> list:
    """Reyting ro'yxati hamma uchun bir xil — 15 soniya keshlanadi (minglab kishi bir vaqtda ochganda baza bo'shaydi)."""
    hit = _board_cache.get(kind)
    if hit and hit[0] > time.time():
        return hit[1]
    rows = await (db.leaderboard(db.month_start()) if kind == "month" else db.leaderboard())
    _board_cache[kind] = (time.time() + 15, rows)
    return rows


@router.get("/rating")
async def rating(user: dict = Depends(reg_user)):
    pick = lambda rows: [{"user_id": r["user_id"], "name": r["full_name"] or "—", "total": r["total"],
                          "me": r["user_id"] == user["user_id"]} for r in rows]
    month, total = await _board("month"), await _board("total")
    mine = await db.total_points(user["user_id"])
    rank = await db._count("SELECT COUNT(*) FROM (SELECT 1 FROM points GROUP BY user_id HAVING SUM(amount) > $1) s",
                           mine) + 1
    return {"month": pick(month), "total": pick(total), "mine": mine, "rank": rank}


@router.get("/card.png")
async def card_png(user: dict = Depends(reg_user)):
    member = await db.get_member(user["user_id"])
    if not member:
        raise HTTPException(404)
    photo = await photos.user_photo(user["user_id"], user["photo_id"], tg_file)
    return _png(cards.membership_card(full_name=user["full_name"] or "—", number=member["number"],
                                      section=opt("section", member["section"]), group=user["group_name"] or "—",
                                      valid_year=member["academic_year"], photo=photo))


# ---------------- murojaatlar ----------------
@router.get("/appeals")
async def appeals(user: dict = Depends(reg_user)):
    out = []
    for a in await db.user_appeals(user["user_id"], 30):
        msgs = await db.appeal_messages(a["id"])
        out.append({"id": a["id"], "kind": a["kind"], "status": a["status"], "created_at": a["created_at"],
                    "messages": [{"from": m["sender"], "text": m["text"], "file": bool(m["file_id"]),
                                  "at": m["created_at"]} for m in msgs]})
    return out


@router.post("/appeals")
async def appeal_create(data: dict = Body(...), user: dict = Depends(reg_user)):
    from handlers.appeals import notify_staff
    kind, text = data.get("kind"), str(data.get("text") or "").strip()
    if kind not in KINDS:
        return _err("Murojaat turini tanlang")
    if not 10 <= len(text) <= 2000:
        return _err("Matn 10–2000 belgi bo'lsin")
    aid = await db.create_appeal(user["user_id"], kind)
    await db.add_appeal_message(aid, "user", text)
    _later(notify_staff(bot(), aid, text, [], new=True), "appeal")
    return {"id": aid}


@router.post("/appeals/{aid}/reply")
async def appeal_reply(aid: int, data: dict = Body(...), user: dict = Depends(reg_user)):
    from handlers.appeals import notify_staff
    a = await db.get_appeal(aid)
    text = str(data.get("text") or "").strip()
    if not a or a["user_id"] != user["user_id"]:
        raise HTTPException(404)
    if a["status"] == "closed":
        return _err("Murojaat yopilgan")
    if not 1 <= len(text) <= 2000:
        return _err("Javob matnini yozing")
    await db.add_appeal_message(aid, "user", text)
    await db.set_appeal_status(aid, "new")
    _later(notify_staff(bot(), aid, text, [], new=False), "appeal reply")
    return {"ok": True}


# ---------------- a'zolik arizasi (blanka) ----------------
def _steps():
    from handlers.membership import STEPS
    return STEPS


@router.get("/form")
async def form(user: dict = Depends(reg_user)):
    lang, uid = user["lang"], user["user_id"]
    last = await db.last_application(uid)
    member = await db.get_member(uid)
    if last and last["status"] == "pending":
        return {"blocked": f"#{last['id']} arizangiz ko'rib chiqilmoqda. Natija botda xabar qilinadi."}
    if member and member["status"] == "active" and member["academic_year"] == db.academic_year():
        return {"blocked": f"Siz {member['academic_year']} o'quv yili uchun klub a'zosisiz."}
    prev, reason = {}, None
    if last and last["status"] == "returned":
        prev, reason = json.loads(last["data"] or "{}"), last["reason"]
    steps = []
    for _, field, q, kind, group, optional in _steps():
        steps.append({"field": field, "kind": kind, "optional": optional, "question": tg_html(t(q, lang)),
                      "options": [{"key": k, "label": strip_emoji(opt(group, k, lang))} for k in OPTIONS[group]]
                      if group else []})
    return {"steps": steps, "answers": prev, "returned_reason": reason, "renew_default": bool(member),
            "types": [{"key": "new", "label": strip_emoji(t("app_new", lang))},
                      {"key": "renew", "label": strip_emoji(t("app_renew", lang))}]}


@router.post("/apply")
async def apply(data: dict = Body(...), user: dict = Depends(reg_user)):
    from handlers.membership import EMAIL_RE, notify_admins_application
    uid = user["user_id"]
    check = await form(user)
    if "blocked" in check:
        return _err(check["blocked"])
    raw = data.get("answers") or {}
    app_type = data.get("app_type") if data.get("app_type") in ("new", "renew") else "new"
    tg = user["_tg"]
    answers = {"telegram": f"@{tg['username']}" if tg.get("username") else None, "app_type": app_type}
    for _, field, _q, kind, group, optional in _steps():
        v = raw.get(field)
        empty = v in (None, "", [])
        if empty and optional:
            answers[field] = None
            continue
        if kind == "email":
            ok = isinstance(v, str) and EMAIL_RE.match(v.strip()) and len(v) <= 100
        elif kind == "motivation":
            ok = isinstance(v, str) and 20 <= len(v.strip()) <= 1500
        elif kind == "text":
            ok = isinstance(v, str) and 2 <= len(v.strip()) <= 1000
        elif kind == "one":
            ok = v in OPTIONS[group]
        elif kind == "many":
            ok = isinstance(v, list) and v and all(x in OPTIONS[group] for x in v)
            v = list(dict.fromkeys(v)) if ok else v
        elif kind == "yesno":
            ok = v in ("yes", "no")
        elif kind == "rules":
            ok = v == "yes"
        else:
            ok = False
        if not ok:
            q_text = " ".join(strip_emoji(re.sub("<[^>]+>", " ", t(_q, user["lang"]))).split())
            return _err(f"«{q_text[:60]}…» savoliga javob to'g'ri emas")
        answers[field] = v.strip() if isinstance(v, str) else v
    app_id = await db.create_application(uid, app_type, answers)
    _later(notify_admins_application(bot(), app_id), "application")
    return {"id": app_id}


# ---------------- klub haqida, FAQ, hujjatlar ----------------
@router.get("/info")
async def info(tg: dict = Depends(tg_user)):
    lang = await db.get_lang(tg["id"])
    about = [{"key": k, "title": strip_emoji(t(k, lang)), "html": tg_html(t(f"{k}_text", lang))}
             for k in ABOUT if f"{k}_text" in T]
    faq = [{"id": f["id"], "q": f["question"], "a": tg_html(f["answer"])} for f in await db.faq_list(lang)]
    docs = [{"key": k, "name": DOC_NAMES[k], "url": f"/docs/{k}"} for k, n in DOC_FILES.items() if (DOCS / n).exists()]
    return {"about": about, "faq": faq, "docs": docs, "motto": SITE_DEFAULTS["motto"]}


public = APIRouter()


@public.get("/docs/{key}")
async def doc(key: str):
    name = DOC_FILES.get(key)
    if not name or not (DOCS / name).exists():
        raise HTTPException(404)
    return FileResponse(DOCS / name, filename=name)

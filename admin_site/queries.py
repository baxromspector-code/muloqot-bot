"""Admin sayti uchun SQL so'rovlar (faqat o'qish). Bot bilan bir xil PostgreSQL bazasidan foydalanadi."""
import json
from datetime import date, datetime, timedelta

import asyncpg

import db
from texts import APP_FIELDS, OPTIONS, member_level, opt


def _j(v):
    if isinstance(v, datetime):
        return v.strftime("%Y-%m-%d %H:%M")
    if isinstance(v, date):
        return v.isoformat()
    return v


def _rows(records) -> list[dict]:
    return [{k: _j(v) for k, v in r.items()} for r in records]


def _pool() -> asyncpg.Pool:
    return db._p()


async def _all(sql: str, *args) -> list[dict]:
    return _rows(await _pool().fetch(sql, *args))


async def _val(sql: str, *args):
    return await _pool().fetchval(sql, *args)


# ---------------- umumiy ko'rinish ----------------
async def overview() -> dict:
    now = datetime.now()
    day30 = now - timedelta(days=29)
    since = datetime(day30.year, day30.month, day30.day)
    kpi = {
        "users_total": await _val("SELECT COUNT(*) FROM users"),
        "registered": await _val("SELECT COUNT(*) FROM users WHERE registered"),
        "new_week": await _val("SELECT COUNT(*) FROM users WHERE registered AND created_at >= $1",
                               now - timedelta(days=7)),
        "members": await _val("SELECT COUNT(*) FROM members WHERE status='active' AND academic_year=$1",
                              db.academic_year()),
        "apps_pending": await _val("SELECT COUNT(*) FROM applications WHERE status='pending'"),
        "appeals_open": await _val("SELECT COUNT(*) FROM appeals WHERE status IN ('new','in_review')"),
        "events_open": await _val("SELECT COUNT(*) FROM events WHERE active AND NOT finished"),
        "tickets_used": await _val("SELECT COUNT(*) FROM tickets WHERE status='used'"),
        "active_24h": await _val("SELECT COUNT(DISTINCT user_id) FROM activity WHERE created_at >= $1",
                                 now - timedelta(hours=24)),
        "actions_24h": await _val("SELECT COUNT(*) FROM activity WHERE created_at >= $1", now - timedelta(hours=24)),
        "no_photo": await _val("SELECT COUNT(*) FROM users WHERE registered AND photo_id IS NULL"),
    }
    days = [(since + timedelta(days=i)).date() for i in range(30)]
    reg = {r["d"]: r["n"] for r in await _pool().fetch(
        "SELECT created_at::date d, COUNT(*) n FROM users WHERE registered AND created_at >= $1 GROUP BY 1", since)}
    act = {r["d"]: (r["u"], r["n"]) for r in await _pool().fetch(
        "SELECT created_at::date d, COUNT(DISTINCT user_id) u, COUNT(*) n FROM activity "
        "WHERE created_at >= $1 GROUP BY 1", since)}
    apps = {r["d"]: r["n"] for r in await _pool().fetch(
        "SELECT created_at::date d, COUNT(*) n FROM applications WHERE created_at >= $1 GROUP BY 1", since)}
    series = {
        "days": [d.isoformat() for d in days],
        "registrations": [reg.get(d, 0) for d in days],
        "active_users": [act.get(d, (0, 0))[0] for d in days],
        "actions": [act.get(d, (0, 0))[1] for d in days],
        "applications": [apps.get(d, 0) for d in days],
    }
    return {
        "kpi": kpi,
        "series": series,
        "app_status": await _all("SELECT status k, COUNT(*) n FROM applications GROUP BY 1 ORDER BY 2 DESC"),
        "directions": await _all("SELECT direction k, COUNT(*) n FROM users WHERE registered "
                                 "GROUP BY 1 ORDER BY 2 DESC LIMIT 8"),
        "courses": await _all("SELECT course k, COUNT(*) n FROM users WHERE registered GROUP BY 1 ORDER BY 1"),
        "sections": [{"k": opt("section", r["k"]) if r["k"] else "—", "n": r["n"]} for r in await _all(
            "SELECT section k, COUNT(*) n FROM members WHERE status='active' GROUP BY 1 ORDER BY 2 DESC")],
        "langs": await _all("SELECT lang k, COUNT(*) n FROM users GROUP BY 1 ORDER BY 2 DESC"),
        "top": await _all(
            "SELECT u.user_id, u.full_name, u.direction, COALESCE(SUM(p.amount),0)::int pts "
            "FROM users u JOIN points p ON p.user_id=u.user_id GROUP BY u.user_id ORDER BY pts DESC LIMIT 8"),
        "feed": await feed(14),
        "upcoming": await _all(
            "SELECT e.id, e.title, e.kind, e.date_text, e.place, e.capacity, "
            "(SELECT COUNT(*) FROM tickets t WHERE t.event_id=e.id AND t.status<>'cancelled')::int taken "
            "FROM events e WHERE e.active AND NOT e.finished ORDER BY e.starts_at NULLS LAST, e.id LIMIT 5"),
    }


async def feed(limit: int = 20) -> list[dict]:
    return await _all(
        """
        SELECT * FROM (
          SELECT 'register' t, u.created_at ts, u.user_id, u.full_name, u.direction info FROM users u WHERE u.registered
          UNION ALL
          SELECT 'application', a.created_at, a.user_id, u.full_name, a.status FROM applications a
            JOIN users u USING(user_id)
          UNION ALL
          SELECT 'member', m.joined_at, m.user_id, u.full_name, m.number FROM members m JOIN users u USING(user_id)
          UNION ALL
          SELECT 'appeal', ap.created_at, ap.user_id, u.full_name, ap.kind FROM appeals ap JOIN users u USING(user_id)
          UNION ALL
          SELECT 'checkin', t.used_at, t.user_id, u.full_name, e.title FROM tickets t
            JOIN users u USING(user_id) JOIN events e ON e.id=t.event_id WHERE t.status='used'
        ) x ORDER BY ts DESC LIMIT $1
        """, limit)


# ---------------- talabalar ----------------
STUDENTS_SQL = """
SELECT u.user_id, u.full_name, u.username, u.phone, u.direction, u.course, u.group_name, u.student_id,
       u.lang, u.registered, u.created_at, (u.photo_id IS NOT NULL) has_photo,
       m.number member_no, m.section, m.status member_status, m.joined_at, m.level member_level,
       la.status app_status, la.created_at app_at,
       COALESCE(pt.total, 0)::int points, COALESCE(pt.sem, 0)::int points_sem,
       COALESCE(tk.used, 0)::int attended, COALESCE(tk.taken, 0)::int tickets,
       ac.last_seen, COALESCE(ac.n30, 0)::int actions_30d
FROM users u
LEFT JOIN members m ON m.user_id = u.user_id
LEFT JOIN LATERAL (SELECT status, created_at FROM applications a WHERE a.user_id=u.user_id
                   ORDER BY id DESC LIMIT 1) la ON TRUE
LEFT JOIN (SELECT user_id, SUM(amount) total, SUM(amount) FILTER (WHERE created_at >= $1) sem
           FROM points GROUP BY user_id) pt ON pt.user_id = u.user_id
LEFT JOIN (SELECT user_id, COUNT(*) FILTER (WHERE status='used') used,
                  COUNT(*) FILTER (WHERE status<>'cancelled') taken FROM tickets GROUP BY user_id) tk
          ON tk.user_id = u.user_id
LEFT JOIN (SELECT user_id, MAX(created_at) last_seen, COUNT(*) FILTER (WHERE created_at >= $2) n30
           FROM activity GROUP BY user_id) ac ON ac.user_id = u.user_id
ORDER BY u.created_at DESC
"""


def student_status(r: dict) -> str:
    if r.get("member_no") and r.get("member_status") == "active":
        return "member"
    if r.get("app_status") in ("pending", "returned"):
        return "applicant"
    if r.get("registered"):
        return "registered"
    return "guest"


async def students() -> list[dict]:
    rows = await _all(STUDENTS_SQL, db.semester_start(), datetime.now() - timedelta(days=30))
    for r in rows:
        r["status"] = student_status(r)
        r["section_name"] = opt("section", r["section"]) if r.get("section") else None
    return rows


def _fmt_answer(key: str, value) -> str:
    groups = {"edu_lang": "edu_lang", "section": "section", "directions": "directions", "skills": "skills",
              "hours": "hours", "days": "days", "time": "time"}
    if isinstance(value, list):
        g = groups.get(key)
        return ", ".join(opt(g, str(v)) if g else str(v) for v in value)
    if key in groups and isinstance(value, str) and value in OPTIONS.get(groups[key], {}):
        return opt(groups[key], value)
    if key == "app_type":
        return {"new": "Yangi a'zolik", "renew": "A'zolikni yangilash"}.get(str(value), str(value))
    if isinstance(value, bool):
        return "Ha" if value else "Yo'q"
    return "" if value is None else str(value)


async def student(user_id: int) -> dict | None:
    rows = await _all(STUDENTS_SQL.replace("ORDER BY u.created_at DESC", "WHERE u.user_id = $3"),
                      db.semester_start(), datetime.now() - timedelta(days=30), user_id)
    if not rows:
        return None
    s = rows[0]
    s["status"] = student_status(s)
    s["section_name"] = opt("section", s["section"]) if s.get("section") else None
    went, held = await db.attendance(user_id)
    mem = {"status": s.get("member_status"), "level": s.get("member_level")} if s.get("member_no") else None
    s["level_name"] = opt("level", member_level(mem, went, held))
    apps = await _all("SELECT id, app_type, data, status, reason, section, created_at, decided_at "
                      "FROM applications WHERE user_id=$1 ORDER BY id DESC", user_id)
    labels = dict(APP_FIELDS)
    for a in apps:
        data = a.pop("data")
        data = json.loads(data) if isinstance(data, str) else (data or {})
        a["answers"] = [{"k": labels.get(k, k), "v": _fmt_answer(k, data[k])} for k, _ in APP_FIELDS
                        if k in data and data[k] not in (None, "", [])]
    s["applications"] = apps
    s["points_log"] = await _all("SELECT amount, reason, created_at FROM points WHERE user_id=$1 "
                                 "ORDER BY created_at DESC LIMIT 30", user_id)
    s["tickets_log"] = await _all(
        "SELECT e.title, e.kind, e.date_text, t.status, t.created_at, t.used_at FROM tickets t "
        "JOIN events e ON e.id=t.event_id WHERE t.user_id=$1 ORDER BY t.created_at DESC", user_id)
    s["appeals"] = await _all(
        "SELECT a.id, a.kind, a.status, a.created_at, "
        "(SELECT text FROM appeal_messages m WHERE m.appeal_id=a.id ORDER BY id LIMIT 1) first_text "
        "FROM appeals a WHERE a.user_id=$1 ORDER BY a.id DESC", user_id)
    s["activity"] = await _all("SELECT kind, action, created_at FROM activity WHERE user_id=$1 "
                               "ORDER BY id DESC LIMIT 25", user_id)
    return s


async def photo_id(user_id: int) -> str | None:
    return await _val("SELECT photo_id FROM users WHERE user_id=$1", user_id)


async def user_name(user_id: int) -> str | None:
    return await _val("SELECT COALESCE(NULLIF(full_name, ''), username) FROM users WHERE user_id=$1", user_id)


# ---------------- arizalar, tadbirlar, murojaatlar ----------------
async def applications() -> list[dict]:
    rows = await _all(
        "SELECT a.id, a.user_id, u.full_name, u.direction, u.course, u.group_name, a.app_type, a.status, "
        "a.reason, a.section, a.created_at, a.decided_at FROM applications a JOIN users u USING(user_id) "
        "ORDER BY a.id DESC")
    for r in rows:
        r["section_name"] = opt("section", r["section"]) if r.get("section") else None
    return rows


async def events() -> list[dict]:
    return await _all(
        "SELECT e.id, e.title, e.kind, e.date_text, e.place, e.capacity, e.points, e.volunteers, e.active, "
        "e.finished, e.starts_at, e.created_at, "
        "COUNT(t.id) FILTER (WHERE t.status<>'cancelled')::int taken, "
        "COUNT(t.id) FILTER (WHERE t.status='used')::int used, "
        "(SELECT COUNT(*) FROM volunteers v WHERE v.event_id=e.id AND v.status='accepted')::int vols "
        "FROM events e LEFT JOIN tickets t ON t.event_id=e.id GROUP BY e.id "
        "ORDER BY e.starts_at DESC NULLS LAST, e.id DESC")


async def appeals() -> list[dict]:
    return await _all(
        "SELECT a.id, a.user_id, u.full_name, u.username, a.kind, a.status, a.created_at, "
        "(SELECT text FROM appeal_messages m WHERE m.appeal_id=a.id ORDER BY id LIMIT 1) first_text, "
        "(SELECT COUNT(*) FROM appeal_messages m WHERE m.appeal_id=a.id)::int messages, "
        "(SELECT MAX(created_at) FROM appeal_messages m WHERE m.appeal_id=a.id) last_at "
        "FROM appeals a JOIN users u USING(user_id) ORDER BY a.id DESC")


# ---------------- bot faolligi ----------------
async def activity(days: int = 30) -> dict:
    since = datetime.now() - timedelta(days=days)
    heat = await _all("SELECT EXTRACT(ISODOW FROM created_at)::int dow, EXTRACT(HOUR FROM created_at)::int h, "
                      "COUNT(*)::int n FROM activity WHERE created_at >= $1 GROUP BY 1, 2", since)
    return {
        "heatmap": heat,
        "kinds": await _all("SELECT kind k, COUNT(*)::int n FROM activity WHERE created_at >= $1 "
                            "GROUP BY 1 ORDER BY 2 DESC", since),
        "actions": await _all("SELECT COALESCE(action, kind) k, COUNT(*)::int n, COUNT(DISTINCT user_id)::int u "
                              "FROM activity WHERE created_at >= $1 AND kind IN ('button','command','callback') "
                              "GROUP BY 1 ORDER BY 2 DESC LIMIT 15", since),
        "hours": await _all("SELECT EXTRACT(HOUR FROM created_at)::int h, COUNT(*)::int n FROM activity "
                            "WHERE created_at >= $1 GROUP BY 1 ORDER BY 1", since),
        "recent": await _all("SELECT a.kind, a.action, a.created_at, a.user_id, u.full_name FROM activity a "
                             "LEFT JOIN users u USING(user_id) ORDER BY a.id DESC LIMIT 40"),
        "totals": {
            "actions": await _val("SELECT COUNT(*) FROM activity WHERE created_at >= $1", since),
            "users": await _val("SELECT COUNT(DISTINCT user_id) FROM activity WHERE created_at >= $1", since),
            "dau": await _val("SELECT COUNT(DISTINCT user_id) FROM activity WHERE created_at >= $1",
                              datetime.now() - timedelta(hours=24)),
            "wau": await _val("SELECT COUNT(DISTINCT user_id) FROM activity WHERE created_at >= $1",
                              datetime.now() - timedelta(days=7)),
        },
    }

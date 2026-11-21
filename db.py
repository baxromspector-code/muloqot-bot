"""PostgreSQL bilan ishlash (asyncpg).

Barcha funksiyalar dict qaytaradi; vaqt ustunlari (TIMESTAMP) 'YYYY-MM-DD HH:MM' satriga aylantiriladi,
shuning uchun handlerlar bazaning turiga bog'liq emas.
"""
import json
import secrets
from datetime import datetime

import asyncpg

from config import DATABASE_URL

_pool: asyncpg.Pool | None = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id       BIGINT PRIMARY KEY,
    lang          VARCHAR(2) NOT NULL DEFAULT 'uz',
    username      TEXT,
    full_name     TEXT,
    direction     TEXT,
    course        VARCHAR(4),
    group_name    TEXT,
    student_id    TEXT,
    phone         TEXT,
    registered    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS applications (
    id            SERIAL PRIMARY KEY,
    user_id       BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    app_type      VARCHAR(10) NOT NULL DEFAULT 'new',      -- new | renew
    data          JSONB NOT NULL DEFAULT '{}'::jsonb,      -- blanka javoblari
    status        VARCHAR(10) NOT NULL DEFAULT 'pending',  -- pending | returned | accepted | rejected
    reason        TEXT,
    section       VARCHAR(20),
    created_at    TIMESTAMP NOT NULL,
    decided_at    TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_applications_user ON applications(user_id);

CREATE TABLE IF NOT EXISTS members (
    user_id       BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    number        VARCHAR(20) UNIQUE NOT NULL,             -- MLQ-26-001
    section       VARCHAR(20),
    academic_year VARCHAR(9) NOT NULL,                     -- 2026/2027
    status        VARCHAR(10) NOT NULL DEFAULT 'active',
    joined_at     TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id            SERIAL PRIMARY KEY,
    title         TEXT NOT NULL,
    kind          VARCHAR(10) NOT NULL DEFAULT 'event',    -- session | event
    description   TEXT,
    date_text     TEXT,
    place         TEXT,
    capacity      INTEGER NOT NULL DEFAULT 0,              -- 0 = cheklanmagan
    points        INTEGER NOT NULL DEFAULT 1,
    volunteers    INTEGER NOT NULL DEFAULT 0,
    active        BOOLEAN NOT NULL DEFAULT TRUE,           -- ro'yxatga olish ochiq
    finished      BOOLEAN NOT NULL DEFAULT FALSE,          -- o'tkazildi (davomat hisobiga kiradi)
    created_at    TIMESTAMP NOT NULL,
    finished_at   TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tickets (
    id            SERIAL PRIMARY KEY,
    event_id      INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id       BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token         VARCHAR(16) NOT NULL,
    status        VARCHAR(10) NOT NULL DEFAULT 'active',   -- active | used | cancelled
    created_at    TIMESTAMP NOT NULL,
    used_at       TIMESTAMP,
    UNIQUE (event_id, user_id)
);

CREATE TABLE IF NOT EXISTS points (
    id            SERIAL PRIMARY KEY,
    user_id       BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    amount        INTEGER NOT NULL,
    reason        TEXT,
    created_at    TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_points_user ON points(user_id, created_at);

CREATE TABLE IF NOT EXISTS appeals (
    id            SERIAL PRIMARY KEY,
    user_id       BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    kind          VARCHAR(12) NOT NULL DEFAULT 'question', -- question | suggestion | complaint
    status        VARCHAR(10) NOT NULL DEFAULT 'new',      -- new | in_review | answered | closed
    created_at    TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS appeal_messages (
    id            SERIAL PRIMARY KEY,
    appeal_id     INTEGER NOT NULL REFERENCES appeals(id) ON DELETE CASCADE,
    sender        VARCHAR(5) NOT NULL,                     -- user | admin
    text          TEXT,
    file_id       TEXT,
    file_type     VARCHAR(10),
    created_at    TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS faq (
    id            SERIAL PRIMARY KEY,
    lang          VARCHAR(2) NOT NULL,
    question      TEXT NOT NULL,
    answer        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS volunteers (
    id            SERIAL PRIMARY KEY,
    event_id      INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id       BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    status        VARCHAR(10) NOT NULL DEFAULT 'pending',  -- pending | accepted | rejected
    created_at    TIMESTAMP NOT NULL,
    UNIQUE (event_id, user_id)
);

CREATE TABLE IF NOT EXISTS deletion_requests (
    id            SERIAL PRIMARY KEY,
    user_id       BIGINT NOT NULL,
    status        VARCHAR(10) NOT NULL DEFAULT 'pending',  -- pending | done
    created_at    TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS file_cache (
    name          TEXT PRIMARY KEY,
    file_id       TEXT NOT NULL
);

-- aiogram FSM holatlari (bot qayta ishga tushganda jarayonlar yo'qolmasligi uchun)
CREATE TABLE IF NOT EXISTS fsm_storage (
    key           TEXT PRIMARY KEY,
    state         TEXT,
    data          JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- rejalashtiruvchi uchun kalit-qiymat (oxirgi kunlik hisobot sanasi va h.k.)
CREATE TABLE IF NOT EXISTS meta (
    key           TEXT PRIMARY KEY,
    value         TEXT
);

-- 2-versiya: tadbirning haqiqiy boshlanish vaqti va eslatma belgisi
ALTER TABLE events ADD COLUMN IF NOT EXISTS starts_at TIMESTAMP;
ALTER TABLE events ADD COLUMN IF NOT EXISTS reminded BOOLEAN NOT NULL DEFAULT FALSE;

-- 3-versiya: foydalanuvchi surati (guvohnoma va kirishda yuzni solishtirish uchun)
ALTER TABLE users ADD COLUMN IF NOT EXISTS photo_id TEXT;
ALTER TABLE members ADD COLUMN IF NOT EXISTS level VARCHAR(12);  -- qo'lda: leader | expert | honorary

-- 4-versiya: bot faolligi jurnali (admin sayti statistikasi uchun; xabar matni saqlanmaydi)
CREATE TABLE IF NOT EXISTS activity (
    id            BIGSERIAL PRIMARY KEY,
    user_id       BIGINT NOT NULL,
    kind          VARCHAR(10) NOT NULL,                    -- command | button | text | photo | callback | contact ...
    action        VARCHAR(40),
    created_at    TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_activity_time ON activity(created_at);
CREATE INDEX IF NOT EXISTS idx_activity_user ON activity(user_id, created_at);

-- 6-versiya: foydalanuvchi suratining nusxasi (bot tokeni almashsa ham surat yo'qolmaydi)
CREATE TABLE IF NOT EXISTS user_photos (
    user_id       BIGINT PRIMARY KEY,
    file_id       TEXT,
    data          BYTEA NOT NULL,
    updated_at    TIMESTAMP NOT NULL
);

-- 5-versiya: ochiq sayt — admin paneldan boshqariladigan e'lon/reklamalar, rasmlar va sozlamalar
CREATE TABLE IF NOT EXISTS site_media (
    id            VARCHAR(32) PRIMARY KEY,
    mime          VARCHAR(40) NOT NULL,
    data          BYTEA NOT NULL,
    caption       TEXT,
    in_gallery    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMP NOT NULL
);
CREATE TABLE IF NOT EXISTS site_posts (
    id            SERIAL PRIMARY KEY,
    kind          VARCHAR(10) NOT NULL DEFAULT 'ad',       -- ad (reklama) | news (e'lon)
    title         TEXT NOT NULL,
    body          TEXT,
    image_id      VARCHAR(32) REFERENCES site_media(id) ON DELETE SET NULL,
    link_url      TEXT,
    link_label    TEXT,
    pinned        BOOLEAN NOT NULL DEFAULT FALSE,
    active        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP NOT NULL,
    updated_at    TIMESTAMP NOT NULL
);
"""


# ---------------- yordamchilar ----------------
def now() -> datetime:
    return datetime.now().replace(second=0, microsecond=0)


def academic_year(dt: datetime | None = None) -> str:
    dt = dt or datetime.now()
    start = dt.year if dt.month >= 9 else dt.year - 1
    return f"{start}/{start + 1}"


def semester_start(dt: datetime | None = None) -> datetime:
    dt = dt or datetime.now()
    if dt.month >= 9:
        return datetime(dt.year, 9, 1)
    if dt.month >= 2:
        return datetime(dt.year, 2, 1)
    return datetime(dt.year - 1, 9, 1)


def month_start(dt: datetime | None = None) -> datetime:
    dt = dt or datetime.now()
    return datetime(dt.year, dt.month, 1)


def _conv(value):
    return value.strftime("%Y-%m-%d %H:%M") if isinstance(value, datetime) else value


def _row(record) -> dict | None:
    return {k: _conv(v) for k, v in record.items()} if record is not None else None


def _p() -> asyncpg.Pool:
    assert _pool is not None, "db.init() chaqirilmagan"
    return _pool


async def init() -> None:
    global _pool
    _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    # Jadval tuzilishi faqat o'zgarganda qo'llanadi (SCHEMA matnining xeshi bazada saqlanadi).
    # Sabab: ALTER TABLE ... IF NOT EXISTS ham jadvalni qisqa qulflaydi — bot, sayt va saytning
    # bir nechta ishchi jarayoni bir vaqtda ishga tushganda ishlab turgan so'rovlar bilan deadlock bo'lardi.
    # Advisory lock — bir vaqtda faqat bitta jarayon tuzilishni yangilaydi.
    import hashlib
    digest = hashlib.sha256(SCHEMA.encode()).hexdigest()[:16]
    async with _pool.acquire() as conn:
        has_meta = await conn.fetchval("SELECT to_regclass('public.meta') IS NOT NULL")
        if has_meta and await conn.fetchval("SELECT value FROM meta WHERE key='schema_digest'") == digest:
            return
        await conn.execute("SELECT pg_advisory_lock(727001)")
        try:
            await conn.execute(SCHEMA)
            await conn.execute("INSERT INTO meta(key, value) VALUES('schema_digest', $1) "
                               "ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value", digest)
        finally:
            await conn.execute("SELECT pg_advisory_unlock(727001)")


async def close() -> None:
    if _pool:
        await _pool.close()


async def _one(sql: str, *args) -> dict | None:
    return _row(await _p().fetchrow(sql, *args))


async def _all(sql: str, *args) -> list[dict]:
    return [_row(r) for r in await _p().fetch(sql, *args)]


async def _exec(sql: str, *args) -> None:
    await _p().execute(sql, *args)


async def _val(sql: str, *args):
    return await _p().fetchval(sql, *args)


async def _count(sql: str, *args) -> int:
    return int(await _val(sql, *args) or 0)


# ---------------- users ----------------
async def get_user(user_id: int):
    return await _one("SELECT * FROM users WHERE user_id=$1", user_id)


async def get_lang(user_id: int) -> str:
    return await _val("SELECT lang FROM users WHERE user_id=$1", user_id) or "uz"


async def set_lang(user_id: int, lang: str) -> None:
    await _exec(
        "INSERT INTO users(user_id, lang, created_at) VALUES($1,$2,$3) "
        "ON CONFLICT (user_id) DO UPDATE SET lang=EXCLUDED.lang",
        user_id, lang, now(),
    )


async def save_profile(user_id: int, d: dict) -> None:
    await _exec(
        "UPDATE users SET username=$1, full_name=$2, direction=$3, course=$4, group_name=$5, student_id=$6, "
        "phone=$7, photo_id=$8, registered=TRUE WHERE user_id=$9",
        d.get("username"), d["full_name"], d["direction"], str(d["course"]), d["group_name"],
        d["student_id"], d["phone"], d.get("photo_id"), user_id,
    )


PROFILE_FIELDS = {"full_name", "direction", "course", "group_name", "student_id", "phone", "photo_id"}


async def update_user_field(user_id: int, field: str, value: str) -> None:
    if field not in PROFILE_FIELDS:  # SQL'ga faqat oq ro'yxatdagi ustun nomi tushadi
        raise ValueError(field)
    await _exec(f"UPDATE users SET {field}=$1 WHERE user_id=$2", str(value), user_id)


async def registered_ids() -> list[int]:
    return [r["user_id"] for r in await _p().fetch("SELECT user_id FROM users WHERE registered")]


async def delete_user_data(user_id: int) -> None:
    """Rozilik qaytarib olinganda (Nizom 7.9). ON DELETE CASCADE bog'liq yozuvlarni ham o'chiradi."""
    async with _p().acquire() as conn:
        async with conn.transaction():
            await conn.execute("DELETE FROM users WHERE user_id=$1", user_id)
            await conn.execute("DELETE FROM user_photos WHERE user_id=$1", user_id)


async def log_activity(user_id: int, kind: str, action: str | None) -> None:
    await _exec("INSERT INTO activity(user_id, kind, action, created_at) VALUES($1,$2,$3,$4)",
                user_id, kind, (action or "")[:40] or None, datetime.now())


async def stats() -> dict:
    return {
        "users": await _count("SELECT COUNT(*) FROM users WHERE registered"),
        "members": await _count("SELECT COUNT(*) FROM members WHERE status='active' AND academic_year=$1",
                                academic_year()),
        "apps_pending": await _count("SELECT COUNT(*) FROM applications WHERE status='pending'"),
        "appeals_open": await _count("SELECT COUNT(*) FROM appeals WHERE status IN ('new','in_review')"),
        "events": await _count("SELECT COUNT(*) FROM events WHERE active AND NOT finished"),
        "tickets_used": await _count("SELECT COUNT(*) FROM tickets WHERE status='used'"),
    }


# ---------------- a'zolik arizalari ----------------
async def create_application(user_id: int, app_type: str, data: dict) -> int:
    return await _val(
        "INSERT INTO applications(user_id, app_type, data, created_at) VALUES($1,$2,$3::jsonb,$4) RETURNING id",
        user_id, app_type, json.dumps(data, ensure_ascii=False), now(),
    )


async def get_application(app_id: int):
    return await _one("SELECT * FROM applications WHERE id=$1", app_id)


async def last_application(user_id: int):
    return await _one("SELECT * FROM applications WHERE user_id=$1 ORDER BY id DESC LIMIT 1", user_id)


async def decide_application(app_id: int, status: str, reason: str | None = None, section: str | None = None):
    await _exec("UPDATE applications SET status=$1, reason=$2, section=$3, decided_at=$4 WHERE id=$5",
                status, reason, section, now(), app_id)


async def all_applications():
    return await _all("SELECT * FROM applications ORDER BY id")


# ---------------- a'zolar ----------------
async def get_member(user_id: int):
    return await _one("SELECT * FROM members WHERE user_id=$1", user_id)


async def set_member_level(user_id: int, level: str | None) -> None:
    """Qo'lda daraja: leader | expert | honorary; None — avtomatik (davomat bo'yicha nomzod/faol)."""
    await _exec("UPDATE members SET level=$2 WHERE user_id=$1", user_id, level)


async def get_member_by_number(number: str):
    return await _one("SELECT * FROM members WHERE number=$1", number.upper())


async def upsert_member(user_id: int, section: str) -> str:
    """A'zoni qo'shadi yoki yangilaydi, guvohnoma raqamini qaytaradi (MLQ-26-001)."""
    year = academic_year()
    async with _p().acquire() as conn:
        async with conn.transaction():
            old = await conn.fetchrow("SELECT number FROM members WHERE user_id=$1 FOR UPDATE", user_id)
            if old:
                await conn.execute("UPDATE members SET section=$1, academic_year=$2, status='active' WHERE user_id=$3",
                                   section, year, user_id)
                return old["number"]
            yy = datetime.now().strftime("%y")
            # bir vaqtda ikki admin qabul qilsa ham raqam takrorlanmasligi uchun
            await conn.execute("SELECT pg_advisory_xact_lock(7712026)")
            seq = await conn.fetchval("SELECT COUNT(*) FROM members WHERE number LIKE $1", f"MLQ-{yy}-%") + 1
            number = f"MLQ-{yy}-{seq:03d}"
            await conn.execute(
                "INSERT INTO members(user_id, number, section, academic_year, joined_at) VALUES($1,$2,$3,$4,$5)",
                user_id, number, section, year, now(),
            )
            return number


async def all_members():
    return await _all(
        "SELECT m.*, u.full_name, u.phone, u.username, u.direction, u.group_name, u.course, u.student_id "
        "FROM members m JOIN users u ON u.user_id=m.user_id ORDER BY m.number"
    )


# ---------------- ball va davomat ----------------
async def add_points(user_id: int, amount: int, reason: str) -> None:
    await _exec("INSERT INTO points(user_id, amount, reason, created_at) VALUES($1,$2,$3,$4)",
                user_id, amount, reason, now())


async def total_points(user_id: int, since: datetime | None = None) -> int:
    if since:
        return await _count("SELECT COALESCE(SUM(amount),0) FROM points WHERE user_id=$1 AND created_at>=$2",
                            user_id, since)
    return await _count("SELECT COALESCE(SUM(amount),0) FROM points WHERE user_id=$1", user_id)


async def leaderboard(since: datetime | None = None, limit: int = 10):
    if since:
        return await _all(
            "SELECT p.user_id, u.full_name, SUM(p.amount) AS total FROM points p JOIN users u USING (user_id) "
            "WHERE p.created_at>=$1 GROUP BY p.user_id, u.full_name HAVING SUM(p.amount)>0 "
            "ORDER BY total DESC LIMIT $2", since, limit,
        )
    return await _all(
        "SELECT p.user_id, u.full_name, SUM(p.amount) AS total FROM points p JOIN users u USING (user_id) "
        "GROUP BY p.user_id, u.full_name HAVING SUM(p.amount)>0 ORDER BY total DESC LIMIT $1", limit,
    )


async def user_rank(user_id: int) -> int:
    mine = await total_points(user_id)
    return await _count(
        "SELECT COUNT(*) FROM (SELECT user_id FROM points GROUP BY user_id HAVING SUM(amount)>$1) s", mine
    ) + 1


async def attendance(user_id: int) -> tuple[int, int]:
    """(qatnashgan, o'tkazilgan) — joriy semestrda yakunlangan tadbirlar bo'yicha."""
    since = semester_start()
    held = await _count("SELECT COUNT(*) FROM events WHERE finished AND finished_at>=$1", since)
    went = await _count(
        "SELECT COUNT(*) FROM tickets t JOIN events e ON e.id=t.event_id "
        "WHERE t.user_id=$1 AND t.status='used' AND e.finished AND e.finished_at>=$2",
        user_id, since,
    )
    return went, held


# ---------------- murojaatlar ----------------
async def create_appeal(user_id: int, kind: str) -> int:
    return await _val("INSERT INTO appeals(user_id, kind, created_at) VALUES($1,$2,$3) RETURNING id",
                      user_id, kind, now())


async def add_appeal_message(appeal_id: int, sender: str, text: str | None = None,
                             file_id: str | None = None, file_type: str | None = None) -> None:
    await _exec("INSERT INTO appeal_messages(appeal_id, sender, text, file_id, file_type, created_at) "
                "VALUES($1,$2,$3,$4,$5,$6)", appeal_id, sender, text, file_id, file_type, now())


async def get_appeal(appeal_id: int):
    return await _one("SELECT * FROM appeals WHERE id=$1", appeal_id)


async def set_appeal_status(appeal_id: int, status: str) -> None:
    await _exec("UPDATE appeals SET status=$1 WHERE id=$2", status, appeal_id)


async def user_appeals(user_id: int, limit: int = 10):
    return await _all("SELECT * FROM appeals WHERE user_id=$1 ORDER BY id DESC LIMIT $2", user_id, limit)


async def appeal_messages(appeal_id: int):
    return await _all("SELECT * FROM appeal_messages WHERE appeal_id=$1 ORDER BY id", appeal_id)


# ---------------- FAQ ----------------
async def faq_list(lang: str):
    if lang == "un":  # yangi alifbo: o'zbekcha savollar avtomatik o'giriladi
        from alphabet import to_new
        rows = await _all("SELECT * FROM faq WHERE lang='uz' ORDER BY id")
        return [{**r, "question": to_new(r["question"]), "answer": to_new(r["answer"])} for r in rows]
    return await _all("SELECT * FROM faq WHERE lang=$1 ORDER BY id", lang)


async def faq_get(faq_id: int):
    return await _one("SELECT * FROM faq WHERE id=$1", faq_id)


async def faq_add(lang: str, question: str, answer: str) -> int:
    return await _val("INSERT INTO faq(lang, question, answer) VALUES($1,$2,$3) RETURNING id", lang, question, answer)


async def faq_delete(faq_id: int) -> None:
    await _exec("DELETE FROM faq WHERE id=$1", faq_id)


async def faq_all():
    return await _all("SELECT * FROM faq ORDER BY lang, id")


# ---------------- tadbirlar ----------------
def parse_event_date(text: str) -> datetime | None:
    """'24.11.2026 16:00' (yoki '24.11.2026') -> datetime."""
    for fmt in ("%d.%m.%Y %H:%M", "%d.%m.%Y"):
        try:
            return datetime.strptime(text.strip(), fmt)
        except ValueError:
            continue
    return None


async def add_event(d: dict) -> int:
    starts_at = d.get("starts_at")
    if isinstance(starts_at, str):  # FSM'dan satr ko'rinishida keladi
        starts_at = datetime.fromisoformat(starts_at)
    return await _val(
        "INSERT INTO events(title, kind, description, date_text, starts_at, place, capacity, points, volunteers, "
        "created_at) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) RETURNING id",
        d["title"], d["kind"], d["description"], d["date_text"], starts_at, d["place"],
        d["capacity"], d["points"], d["volunteers"], now(),
    )


async def get_event(event_id: int):
    return await _one("SELECT * FROM events WHERE id=$1", event_id)


async def open_events():
    return await _all("SELECT * FROM events WHERE active AND NOT finished ORDER BY starts_at NULLS LAST, id")


async def volunteer_events():
    return await _all("SELECT * FROM events WHERE active AND NOT finished AND volunteers>0 "
                      "ORDER BY starts_at NULLS LAST, id")


async def events_to_remind(until: datetime):
    """Boshlanishiga `until` gacha qolgan, hali eslatilmagan tadbirlar."""
    return await _all("SELECT * FROM events WHERE NOT finished AND NOT reminded AND starts_at IS NOT NULL "
                      "AND starts_at>$1 AND starts_at<=$2", now(), until)


async def mark_reminded(event_id: int) -> None:
    await _exec("UPDATE events SET reminded=TRUE WHERE id=$1", event_id)


async def close_started_events() -> int:
    """Boshlangan tadbirlarda ro'yxatga olishni yopadi."""
    result = await _p().execute("UPDATE events SET active=FALSE WHERE active AND NOT finished "
                                "AND starts_at IS NOT NULL AND starts_at<=$1", now())
    return int(result.split()[-1])


async def events_to_autofinish(before: datetime):
    """`before` dan oldin boshlangan, lekin hali yakunlanmagan tadbirlar."""
    return await _all("SELECT * FROM events WHERE NOT finished AND starts_at IS NOT NULL AND starts_at<=$1", before)


# ---------------- muddat nazorati ----------------
async def pending_applications():
    return await _all("SELECT a.*, u.full_name FROM applications a JOIN users u USING (user_id) "
                      "WHERE a.status='pending' ORDER BY a.id")


async def open_appeals():
    return await _all("SELECT a.*, u.full_name FROM appeals a JOIN users u USING (user_id) "
                      "WHERE a.status IN ('new','in_review') ORDER BY a.id")


async def get_meta(key: str) -> str | None:
    return await _val("SELECT value FROM meta WHERE key=$1", key)


async def set_meta(key: str, value: str) -> None:
    await _exec("INSERT INTO meta(key, value) VALUES($1,$2) ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value",
                key, value)


# ---------------- FSM ----------------
async def fsm_set_state(key: str, state: str | None) -> None:
    await _exec("INSERT INTO fsm_storage(key, state) VALUES($1,$2) "
                "ON CONFLICT (key) DO UPDATE SET state=EXCLUDED.state", key, state)


async def fsm_get_state(key: str) -> str | None:
    return await _val("SELECT state FROM fsm_storage WHERE key=$1", key)


async def fsm_set_data(key: str, data_json: str) -> None:
    await _exec("INSERT INTO fsm_storage(key, data) VALUES($1,$2::jsonb) "
                "ON CONFLICT (key) DO UPDATE SET data=EXCLUDED.data", key, data_json)


async def fsm_get_data(key: str) -> str | None:
    return await _val("SELECT data::text FROM fsm_storage WHERE key=$1", key)


async def recent_events(limit: int = 15):
    return await _all("SELECT * FROM events ORDER BY id DESC LIMIT $1", limit)


async def set_event_active(event_id: int, active: bool) -> None:
    await _exec("UPDATE events SET active=$1 WHERE id=$2", active, event_id)


async def finish_event(event_id: int) -> None:
    await _exec("UPDATE events SET finished=TRUE, active=FALSE, finished_at=$1 WHERE id=$2", now(), event_id)


async def taken_seats(event_id: int) -> int:
    return await _count("SELECT COUNT(*) FROM tickets WHERE event_id=$1 AND status IN ('active','used')", event_id)


async def event_participants(event_id: int):
    return await _all(
        "SELECT t.*, u.full_name, u.phone, u.group_name FROM tickets t JOIN users u ON u.user_id=t.user_id "
        "WHERE t.event_id=$1 AND t.status IN ('active','used') ORDER BY t.id", event_id,
    )


# ---------------- chiptalar ----------------
def ticket_code(ticket_id: int) -> str:
    return f"EVT-{ticket_id:04d}"


def parse_ticket_code(text: str) -> tuple[int, str | None] | None:
    """'EVT-0012' yoki QR ichidagi 'MULOQOT:EVT-0012:token' ni (id, token) ga ajratadi."""
    text = text.strip().upper()
    token = None
    if text.startswith("MULOQOT:"):
        parts = text.split(":")
        if len(parts) != 3:
            return None
        text, token = parts[1], parts[2]
    if not text.startswith("EVT-") or not text[4:].isdigit():
        return None
    return int(text[4:]), token


async def get_ticket(event_id: int, user_id: int):
    return await _one("SELECT * FROM tickets WHERE event_id=$1 AND user_id=$2", event_id, user_id)


async def get_ticket_by_id(ticket_id: int):
    return await _one("SELECT * FROM tickets WHERE id=$1", ticket_id)


async def create_ticket(event_id: int, user_id: int) -> int:
    """Chipta yaratadi; bekor qilingan chipta bo'lsa qayta faollashtiradi."""
    return await _val(
        "INSERT INTO tickets(event_id, user_id, token, created_at) VALUES($1,$2,$3,$4) "
        "ON CONFLICT (event_id, user_id) DO UPDATE SET status='active', token=EXCLUDED.token, "
        "created_at=EXCLUDED.created_at RETURNING id",
        event_id, user_id, secrets.token_hex(4).upper(), now(),
    )


async def cancel_ticket(ticket_id: int) -> None:
    await _exec("UPDATE tickets SET status='cancelled' WHERE id=$1 AND status='active'", ticket_id)


async def use_ticket(ticket_id: int) -> bool:
    """Chiptani ishlatilgan deb belgilaydi. Faqat faol chipta uchun True (ikki marta skanerlashdan himoya)."""
    result = await _p().execute("UPDATE tickets SET status='used', used_at=$1 WHERE id=$2 AND status='active'",
                                now(), ticket_id)
    return result.endswith(" 1")


async def user_tickets(user_id: int):
    return await _all(
        "SELECT t.*, e.title, e.date_text, e.place, e.finished FROM tickets t JOIN events e ON e.id=t.event_id "
        "WHERE t.user_id=$1 AND t.status IN ('active','used') ORDER BY t.id DESC LIMIT 20", user_id,
    )


# ---------------- ko'ngillilar ----------------
async def get_volunteer(event_id: int, user_id: int):
    return await _one("SELECT * FROM volunteers WHERE event_id=$1 AND user_id=$2", event_id, user_id)


async def add_volunteer(event_id: int, user_id: int) -> int:
    return await _val("INSERT INTO volunteers(event_id, user_id, created_at) VALUES($1,$2,$3) RETURNING id",
                      event_id, user_id, now())


async def get_volunteer_by_id(vid: int):
    return await _one("SELECT * FROM volunteers WHERE id=$1", vid)


async def set_volunteer_status(vid: int, status: str) -> None:
    await _exec("UPDATE volunteers SET status=$1 WHERE id=$2", status, vid)


# ---------------- o'chirish so'rovlari ----------------
async def add_deletion_request(user_id: int) -> int:
    return await _val("INSERT INTO deletion_requests(user_id, created_at) VALUES($1,$2) RETURNING id",
                      user_id, now())


async def get_deletion_request(req_id: int):
    return await _one("SELECT * FROM deletion_requests WHERE id=$1", req_id)


async def finish_deletion_request(req_id: int) -> None:
    await _exec("UPDATE deletion_requests SET status='done' WHERE id=$1", req_id)


# ---------------- Telegram file_id keshi ----------------
async def cached_file(name: str) -> str | None:
    return await _val("SELECT file_id FROM file_cache WHERE name=$1", name)


async def cache_file(name: str, file_id: str) -> None:
    await _exec("INSERT INTO file_cache(name, file_id) VALUES($1,$2) "
                "ON CONFLICT (name) DO UPDATE SET file_id=EXCLUDED.file_id", name, file_id)


# ---------------- surat nusxasi ----------------
async def get_user_photo(user_id: int):
    return await _p().fetchrow("SELECT file_id, data FROM user_photos WHERE user_id=$1", user_id)


async def save_user_photo(user_id: int, file_id: str | None, data: bytes) -> None:
    await _exec("INSERT INTO user_photos(user_id, file_id, data, updated_at) VALUES($1,$2,$3,$4) "
                "ON CONFLICT (user_id) DO UPDATE SET file_id=EXCLUDED.file_id, data=EXCLUDED.data, "
                "updated_at=EXCLUDED.updated_at", user_id, file_id, data, now())

"""Ochiq sayt mazmuni: e'lon/reklamalar, rasmlar (galereya) va sozlamalar (manzil, telefon, tarmoqlar).

Admin paneldan o'zgartiriladi, asosiy sahifada (/) hammaga ko'rinadi. Rasmlar bazada saqlanadi:
yuklashda Pillow bilan qayta kodlanadi (EXIF va yashirin ma'lumot o'chadi, 1600 px gacha kichraytiriladi).
"""
import base64
import io
import secrets
from datetime import datetime

from PIL import Image, ImageOps

import db
from config import SITE_DEFAULTS

from .queries import _all, _pool, _val

SETTING_KEYS = tuple(SITE_DEFAULTS)
MAX_UPLOAD = 8 * 1024 * 1024      # base64 dan keyingi xom hajm
MAX_SIDE = 1600
KINDS = ("ad", "news")


# ---------------- sozlamalar (meta jadvalida «site:<kalit>») ----------------
async def settings() -> dict:
    rows = await _all("SELECT key, value FROM meta WHERE key LIKE 'site:%'")
    saved = {r["key"][5:]: r["value"] for r in rows}
    return {k: saved.get(k, v) for k, v in SITE_DEFAULTS.items()}


URL_KEYS = ("telegram", "instagram", "bot")


def _safe_url(v: str) -> str:
    if not v:
        return v
    if v.startswith("@"):                          # @kanal -> https://t.me/kanal
        return "https://t.me/" + v[1:]
    return v if v.startswith(("https://", "http://", "tg://")) else "https://" + v.lstrip("/")


async def save_settings(data: dict) -> dict:
    async with _pool().acquire() as conn:
        for k in SETTING_KEYS:
            if k in data:
                v = str(data[k] or "").strip()[:2000]
                if k in URL_KEYS:
                    v = _safe_url(v)
                await conn.execute("INSERT INTO meta(key, value) VALUES($1, $2) "
                                   "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value", "site:" + k, v)
    return await settings()


# ---------------- rasmlar ----------------
def _process(raw: bytes) -> tuple[bytes, str]:
    img = Image.open(io.BytesIO(raw))
    img.verify()                                   # buzilgan/yolg'on fayl bo'lsa xato
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(raw)))
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    out = io.BytesIO()
    if img.mode in ("RGBA", "LA", "P") and "transparency" in img.info or img.mode in ("RGBA", "LA"):
        img.convert("RGBA").save(out, "PNG", optimize=True)
        return out.getvalue(), "image/png"
    img.convert("RGB").save(out, "JPEG", quality=86, optimize=True, progressive=True)
    return out.getvalue(), "image/jpeg"


async def add_media(data_b64: str, caption: str = "", in_gallery: bool = False) -> dict:
    if "," in data_b64[:100]:                      # «data:image/png;base64,....»
        data_b64 = data_b64.split(",", 1)[1]
    raw = base64.b64decode(data_b64, validate=False)
    if not raw or len(raw) > MAX_UPLOAD:
        raise ValueError("Rasm hajmi 8 MB dan oshmasin")
    try:
        data, mime = _process(raw)
    except Exception as e:  # noqa: BLE001
        raise ValueError("Bu fayl rasm emas (JPG, PNG yoki WEBP yuklang)") from e
    mid = secrets.token_hex(16)
    await _pool().execute("INSERT INTO site_media(id, mime, data, caption, in_gallery, created_at) "
                          "VALUES($1, $2, $3, $4, $5, $6)", mid, mime, data, (caption or "").strip()[:300],
                          bool(in_gallery), db.now())
    return {"id": mid, "url": f"/media/{mid}", "caption": caption, "in_gallery": bool(in_gallery)}


async def media(mid: str):
    return await _pool().fetchrow("SELECT data, mime FROM site_media WHERE id = $1", mid)


async def gallery() -> list[dict]:
    rows = await _all("SELECT id, caption, created_at FROM site_media WHERE in_gallery ORDER BY created_at DESC")
    return [{**r, "url": f"/media/{r['id']}"} for r in rows]


async def update_media(mid: str, data: dict) -> None:
    if "caption" in data:
        await _pool().execute("UPDATE site_media SET caption = $2 WHERE id = $1", mid, str(data["caption"] or "")[:300])
    if "in_gallery" in data:
        await _pool().execute("UPDATE site_media SET in_gallery = $2 WHERE id = $1", mid, bool(data["in_gallery"]))


async def delete_media(mid: str) -> None:
    await _pool().execute("DELETE FROM site_media WHERE id = $1", mid)


# ---------------- e'lon va reklamalar ----------------
def _clean_post(d: dict) -> dict:
    title = str(d.get("title") or "").strip()[:200]
    if not title:
        raise ValueError("Sarlavha yozilmagan")
    link = str(d.get("link_url") or "").strip()[:500]
    if link and not link.startswith(("https://", "http://", "tg://")):
        link = "https://" + link
    return {
        "kind": d.get("kind") if d.get("kind") in KINDS else "ad",
        "title": title,
        "body": str(d.get("body") or "").strip()[:4000],
        "image_id": (str(d.get("image_id")) or None) if d.get("image_id") else None,
        "link_url": link or None,
        "link_label": str(d.get("link_label") or "").strip()[:60] or None,
        "pinned": bool(d.get("pinned")),
        "active": bool(d.get("active", True)),
    }


def _post_out(r: dict) -> dict:
    return {**r, "image_url": f"/media/{r['image_id']}" if r.get("image_id") else None}


async def posts(only_active: bool = False) -> list[dict]:
    where = "WHERE active" if only_active else ""
    rows = await _all(f"SELECT * FROM site_posts {where} ORDER BY pinned DESC, created_at DESC, id DESC")
    return [_post_out(r) for r in rows]


async def create_post(d: dict) -> dict:
    p = _clean_post(d)
    now = db.now()
    pid = await _val("INSERT INTO site_posts(kind, title, body, image_id, link_url, link_label, pinned, active, "
                     "created_at, updated_at) VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$9) RETURNING id",
                     p["kind"], p["title"], p["body"], p["image_id"], p["link_url"], p["link_label"],
                     p["pinned"], p["active"], now)
    return (await _all("SELECT * FROM site_posts WHERE id = $1", pid))[0]


async def update_post(pid: int, d: dict) -> dict | None:
    p = _clean_post(d)
    await _pool().execute("UPDATE site_posts SET kind=$2, title=$3, body=$4, image_id=$5, link_url=$6, link_label=$7, "
                          "pinned=$8, active=$9, updated_at=$10 WHERE id=$1", pid, p["kind"], p["title"], p["body"],
                          p["image_id"], p["link_url"], p["link_label"], p["pinned"], p["active"], db.now())
    rows = await _all("SELECT * FROM site_posts WHERE id = $1", pid)
    return _post_out(rows[0]) if rows else None


async def delete_post(pid: int) -> None:
    await _pool().execute("DELETE FROM site_posts WHERE id = $1", pid)


# ---------------- ochiq sahifa uchun ----------------
async def public_events() -> list[dict]:
    return await _all("""
        SELECT e.id, e.title, e.kind, e.description, e.date_text, e.place, e.capacity, e.starts_at,
               (SELECT count(*) FROM tickets t WHERE t.event_id = e.id AND t.status <> 'cancelled') AS taken
        FROM events e WHERE e.active AND NOT e.finished
        ORDER BY e.starts_at NULLS LAST, e.created_at DESC LIMIT 6""")


async def public_stats() -> dict:
    return {
        "members": await _val("SELECT count(*) FROM members") or 0,
        "events": await _val("SELECT count(*) FROM events WHERE finished") or 0,
        "students": await _val("SELECT count(*) FROM users WHERE registered") or 0,
    }


async def page_data() -> dict:
    return {"s": await settings(), "posts": await posts(True), "events": await public_events(),
            "gallery": await gallery(), "stats": await public_stats(), "year": datetime.now().year}

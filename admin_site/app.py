"""MULOQOT sayti: ochiq asosiy sahifa (/) va maxfiy admin panel (/admin).

Asosiy sahifa hammaga ochiq: e'lon va reklamalar, tadbirlar, rasmlar, manzil, telefon, tarmoqlar.
Admin panelga kirish: PANEL_ADMIN_IDS dagi admin botga /panel yozadi va bir martalik havola oladi.
Boshqalar uchun /admin va /login «sahifa topilmadi» qaytaradi — panel borligi ham bilinmaydi.
Google orqali kirish ixtiyoriy (GOOGLE_CLIENT_ID va GOOGLE_CLIENT_SECRET berilgan bo'lsa).

    python -m admin_site            # kiut_bot papkasidan
"""
import logging
import mimetypes
import os
import sys
import time
from collections import OrderedDict
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Body, Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

mimetypes.add_type("image/webp", ".webp")  # Windows'da .webp turi ro'yxatda yo'q — nosniff bilan rasm chiqmay qolardi
from starlette.datastructures import MutableHeaders
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db  # noqa: E402
import panel_link  # noqa: E402
import photos  # noqa: E402
from config import (ADMIN_ALLOW_ANY_GOOGLE, ADMIN_BASE_URL, ADMIN_DEV_LOGIN, ADMIN_GOOGLE_EMAILS, ADMIN_HTTPS,  # noqa: E402
                    ADMIN_SECRET_KEY, ADMIN_THEME, ADMIN_THEME_SWITCH, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
                    PANEL_ADMIN_IDS)

from texts import DIRECTIONS, LEGACY_OPTIONS, OPTIONS, T, strip_emoji  # noqa: E402

from . import content as sc  # noqa: E402
from . import miniapp  # noqa: E402
from . import queries as q  # noqa: E402
from . import tg_webhook  # noqa: E402

log = logging.getLogger("admin_site")
HERE = Path(__file__).resolve().parent
SESSION_DAYS = 30
HINT_COOKIE = "mlq_hint"           # oxirgi kirgan Google akkaunt (avtomatik qayta kirish uchun)
THEMES = ("diplomat", "oq", "aurora", "skeuo", "glass")
# Tanlagichda ko'rinadigan mavzular (qolganlari faqat ?theme= orqali)
SWITCH_THEMES = (("skeuo", "Qaymoq"), ("glass", "Glass"), ("diplomat", "Diplomat"))
PRIVATE = ("/admin", "/api", "/auth", "/login", "/logout")

templates = Jinja2Templates(directory=HERE / "templates")
templates.env.globals["theme_switch"] = ADMIN_THEME_SWITCH
templates.env.globals["switch_themes"] = SWITCH_THEMES
# CSS/JS manzillariga versiya: yangilangandan keyin brauzer eski nusxani ishlatmasin
templates.env.globals["v"] = str(int(max(p.stat().st_mtime for p in (HERE / "static").rglob("*.*"))))

oauth = None
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    from authlib.integrations.starlette_client import OAuth, OAuthError

    oauth = OAuth()
    oauth.register(
        "google",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
else:
    OAuthError = Exception  # type: ignore[misc,assignment]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await db.init()
    if tg_webhook.ENABLED:  # Render: bot ham shu jarayonda, webhook orqali
        await tg_webhook.start()
    yield
    if tg_webhook.ENABLED:
        await tg_webhook.stop()
    await miniapp.close()
    await db.close()


try:  # orjson — standart json'dan bir necha barobar tez (o'rnatilgan bo'lsa)
    import orjson  # noqa: F401
    from fastapi.responses import ORJSONResponse as _JSONDefault
except ImportError:
    _JSONDefault = JSONResponse
app = FastAPI(title="MULOQOT", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan,
              default_response_class=_JSONDefault)
app.add_middleware(SessionMiddleware, secret_key=ADMIN_SECRET_KEY, session_cookie="mlq_admin",
                   max_age=SESSION_DAYS * 86400, same_site="lax", https_only=ADMIN_HTTPS)
app.add_middleware(GZipMiddleware, minimum_size=800)   # HTML/CSS/JS/JSON siqib yuboriladi (mobil internetda tez)
app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
app.include_router(miniapp.router, prefix="/api/app")
app.include_router(miniapp.public)
app.include_router(tg_webhook.router)
# Telegram Mini App: Telegram Web (web.telegram.org) ilovani iframe ichida ochadi
TG_FRAME = "frame-ancestors 'self' https://web.telegram.org https://*.telegram.org"


class SecurityHeaders:
    """Xavfsizlik va kesh sarlavhalari. Oddiy ASGI qatlami — Starlette'ning @app.middleware("http")
    (BaseHTTPMiddleware) har bir so'rovga sezilarli qo'shimcha vaqt qo'shardi; yuklama sinovida tezlikni oshirdi."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.inner(scope, receive, send)
        path = scope["path"]
        query = scope.get("query_string", b"").decode("latin-1")

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                h = MutableHeaders(scope=message)
                if path.startswith(PRIVATE):
                    h["X-Robots-Tag"] = "noindex, nofollow"  # admin qismi qidiruv tizimlariga chiqmaydi
                if path == "/app":
                    h["Content-Security-Policy"] = TG_FRAME
                else:
                    h["X-Frame-Options"] = "DENY"
                h["X-Content-Type-Options"] = "nosniff"
                h["Referrer-Policy"] = "same-origin"
                if path.startswith("/api/"):
                    h["Cache-Control"] = "no-store"
                elif path.startswith("/static/") and message["status"] == 200:
                    # ?v=... versiyali fayllar o'zgarmaydi — telefon ularni qayta yuklamaydi
                    h["Cache-Control"] = ("public, max-age=31536000, immutable" if "v=" in query
                                          else "public, max-age=86400")
            await send(message)

        await self.inner(scope, receive, send_with_headers)


app.add_middleware(SecurityHeaders)


# ---------------- autentifikatsiya ----------------
def is_allowed(email: str | None) -> bool:
    return bool(email) and (ADMIN_ALLOW_ANY_GOOGLE or email.lower() in ADMIN_GOOGLE_EMAILS)


def current_admin(request: Request) -> dict | None:
    admin = request.session.get("admin")
    if not admin:
        return None
    # ro'yxatdan chiqarilgan ID/email darhol kirish huquqini yo'qotadi
    if admin.get("tg"):
        return admin if admin["tg"] in PANEL_ADMIN_IDS else None
    if admin.get("dev"):
        return admin if ADMIN_DEV_LOGIN else None
    return admin if is_allowed(admin.get("email")) else None


def require_admin(request: Request) -> dict:
    admin = current_admin(request)
    if not admin:
        raise HTTPException(401, "login required")
    return admin


def require_admin_write(request: Request) -> dict:
    """O'zgartiruvchi so'rovlar: admin + so'rov o'z sahifamizdan kelganini tekshirish (CSRF himoyasi)."""
    admin = require_admin(request)
    origin = request.headers.get("origin")
    if request.headers.get("x-mlq") != "1" or (origin and origin.split("://", 1)[-1] != request.url.netloc):
        raise HTTPException(403, "bad origin")
    return admin


def _redirect_uri(request: Request) -> str:
    if ADMIN_BASE_URL:
        return ADMIN_BASE_URL.rstrip("/") + "/auth/callback"
    return str(request.url_for("auth_callback"))


def _is_local(request: Request) -> bool:
    """Faqat shu kompyuterdan, proksisiz to'g'ridan-to'g'ri kirish. Server ochiq manzilda (0.0.0.0) tursa yoki
    so'rov proksi orqali kelsa — hech qachon lokal emas (X-Forwarded-For'ni soxtalashtirib bo'lmasin)."""
    if os.getenv("ADMIN_HOST", "127.0.0.1") not in ("127.0.0.1", "::1", "localhost"):
        return False
    if any(k in request.headers for k in ("x-forwarded-for", "forwarded", "x-real-ip")):
        return False
    return (request.client.host if request.client else "") in ("127.0.0.1", "::1", "localhost")


@app.get("/robots.txt", include_in_schema=False)
async def robots():
    lines = ["User-agent: *", "Allow: /"] + [f"Disallow: {p}" for p in PRIVATE]
    return Response("\n".join(lines) + "\n", media_type="text/plain")


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request, error: str = "", manual: int = 0):
    if current_admin(request):
        return RedirectResponse("/admin", 303)
    if oauth is None and not (ADMIN_DEV_LOGIN and _is_local(request)):
        raise HTTPException(404)            # Google sozlanmagan: kirish faqat bot /panel orqali
    hint = request.cookies.get(HINT_COOKIE, "")
    return templates.TemplateResponse(request, "login.html", {
        "hint": hint if is_allowed(hint) else "",
        "auto": bool(hint) and is_allowed(hint) and not error and not manual and oauth is not None,
        "error": error,
        "google_ready": oauth is not None,
        "dev_login": ADMIN_DEV_LOGIN and _is_local(request),
        "theme": request.query_params.get("theme") if ADMIN_THEME_SWITCH and request.query_params.get("theme") in THEMES else ADMIN_THEME,
    })


@app.get("/auth/google")
async def auth_google(request: Request, silent: int = 0):
    if oauth is None:
        raise HTTPException(404)
    hint = request.cookies.get(HINT_COOKIE, "")
    extra = {"login_hint": hint} if is_allowed(hint) else {}
    if silent and extra:
        extra["prompt"] = "none"            # jim kirish: Google oynasi ko'rinmaydi
    else:
        extra["prompt"] = "select_account"
    request.session["silent"] = bool(silent and extra.get("prompt") == "none")
    return await oauth.google.authorize_redirect(request, _redirect_uri(request), **extra)


@app.get("/auth/callback", name="auth_callback")
async def auth_callback(request: Request):
    silent = request.session.pop("silent", False)
    if oauth is None:
        raise HTTPException(404)
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        log.info("Google kirish xatosi: %s", e)
        # jim kirish o'tmadi (Google'dan chiqib ketilgan) — tugma bilan kirish sahifasi
        return RedirectResponse("/login?manual=1" if silent else "/login?error=google", 303)
    info = token.get("userinfo") or {}
    email = (info.get("email") or "").lower()
    if not info.get("email_verified") or not is_allowed(email):
        log.warning("Ruxsatsiz kirish urinishi: %s", email or "?")
        resp = RedirectResponse("/login?error=denied", 303)
        resp.delete_cookie(HINT_COOKIE)
        return resp
    request.session["admin"] = {"email": email, "name": info.get("name") or email,
                                "picture": info.get("picture") or "", "at": int(time.time())}
    log.info("Admin kirdi: %s", email)
    resp = RedirectResponse("/admin", 303)
    resp.set_cookie(HINT_COOKIE, email, max_age=365 * 86400, httponly=True, samesite="lax", secure=ADMIN_HTTPS)
    return resp


@app.get("/auth/tg")
async def auth_tg(request: Request, t: str = ""):
    """Bot /panel havolasi: imzolangan, 5 daqiqalik, bir martalik. Faqat PANEL_ADMIN_IDS uchun."""
    uid = await panel_link.read_token(t)
    if not uid:
        log.warning("Yaroqsiz yoki eskirgan panel havolasi")
        raise HTTPException(404)
    name = await q.user_name(uid) or f"Admin {uid}"
    request.session["admin"] = {"tg": uid, "name": name, "email": f"Telegram ID {uid}", "picture": "",
                                "at": int(time.time())}
    log.info("Admin kirdi (Telegram): %s", uid)
    return RedirectResponse("/admin", 303)


@app.get("/auth/dev")
async def auth_dev(request: Request, next: str = "/admin"):
    """Faqat ADMIN_DEV_LOGIN=1 va faqat shu kompyuterdan (127.0.0.1) — sinash uchun."""
    if not (ADMIN_DEV_LOGIN and _is_local(request)):
        raise HTTPException(404)
    request.session["admin"] = {"email": "dev@localhost", "name": "Sinov admin", "picture": "", "dev": True,
                                "at": int(time.time())}
    return RedirectResponse(next if next.startswith("/") and not next.startswith("//") else "/admin", 303)


@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    resp = RedirectResponse("/", 303)
    resp.delete_cookie(HINT_COOKIE)  # «Chiqish» — avtomatik kirish ham to'xtaydi
    return resp


# ---------------- ochiq sayt ----------------
@app.get("/", response_class=HTMLResponse)
async def public_home(request: Request):
    return templates.TemplateResponse(request, "public.html", await sc.page_data())


@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    """Maxfiylik siyosati (BotFather va sayt uchun) — docs/maxfiylik-siyosati.txt dan."""
    lines = [x.strip() for x in (HERE.parent / "docs" / "maxfiylik-siyosati.txt").read_text(encoding="utf-8").splitlines()]
    title, meta, blocks = lines[0], lines[1], []
    for line in lines[2:]:
        if not line:
            continue
        if line[:2].rstrip(".").isdigit() and line[1:3].startswith(". ") or line[:3].rstrip(". ").isdigit():
            blocks.append({"kind": "h", "text": line})
        elif line.startswith("•"):
            if not blocks or blocks[-1]["kind"] != "ul":
                blocks.append({"kind": "ul", "lines": []})
            blocks[-1]["lines"].append(line.lstrip("• ").strip())
        else:
            blocks.append({"kind": "p", "text": line})
    return templates.TemplateResponse(request, "privacy.html", {"title": title, "meta": meta, "blocks": blocks})


@app.get("/media/{mid}")
async def public_media(mid: str):
    row = await sc.media(mid) if mid.isalnum() and len(mid) <= 32 else None
    if not row:
        raise HTTPException(404)
    return Response(row["data"], media_type=row["mime"], headers={"Cache-Control": "public, max-age=86400"})


# ---------------- Telegram Mini App ----------------
@app.get("/app", response_class=HTMLResponse)
async def mini_app(request: Request):
    """Bot ichidagi ilova. Ma'lumotlar faqat Telegram imzolagan initData bilan beriladi (/api/app/*)."""
    return templates.TemplateResponse(request, "miniapp.html", {})


# ---------------- admin panel ----------------
@app.get("/admin", response_class=HTMLResponse)
async def index(request: Request):
    admin = current_admin(request)
    if not admin:
        raise HTTPException(404)            # begonalar uchun panel umuman ko'rinmaydi
    theme = request.query_params.get("theme")
    return templates.TemplateResponse(request, "index.html", {
        "admin": admin, "theme": theme if ADMIN_THEME_SWITCH and theme in THEMES else ADMIN_THEME, "themes": THEMES,
        "meta": {
            "labels": {k: strip_emoji(v[0]) for k, v in T.items() if k.startswith(("m_", "btn_"))},
            "directions": DIRECTIONS,
            "sections": {k: v[0] for k, v in {**LEGACY_OPTIONS["section"], **OPTIONS["section"]}.items()},
            "levels": {k: v[0] for k, v in OPTIONS["level"].items()},
            "me": {"name": admin.get("name"), "email": admin.get("email"), "picture": admin.get("picture")},
        },
    })


# ---------------- API (o'qish) ----------------
@app.get("/api/overview")
async def api_overview(_=Depends(require_admin)):
    return await q.overview()


@app.get("/api/students")
async def api_students(_=Depends(require_admin)):
    return await q.students()


@app.get("/api/students/{user_id}")
async def api_student(user_id: int, _=Depends(require_admin)):
    s = await q.student(user_id)
    if not s:
        raise HTTPException(404)
    return s


@app.get("/api/applications")
async def api_applications(_=Depends(require_admin)):
    return await q.applications()


@app.get("/api/events")
async def api_events(_=Depends(require_admin)):
    return await q.events()


@app.get("/api/appeals")
async def api_appeals(_=Depends(require_admin)):
    return await q.appeals()


@app.get("/api/activity")
async def api_activity(days: int = 30, _=Depends(require_admin)):
    return await q.activity(max(1, min(days, 365)))


_photo_cache: "OrderedDict[int, tuple[bytes, str]]" = OrderedDict()
_photo_missing: dict[int, float] = {}  # topilmagan suratlar (10 daqiqa qayta so'ralmaydi)


@app.get("/api/photo/{user_id}")
async def api_photo(user_id: int, _=Depends(require_admin)):
    """Talaba surati Telegram'dan olinadi (bot tokeni brauzerga chiqmaydi)."""
    if user_id in _photo_cache:
        _photo_cache.move_to_end(user_id)
        data, ctype = _photo_cache[user_id]
        return Response(data, media_type=ctype, headers={"Cache-Control": "private, max-age=3600"})
    if _photo_missing.get(user_id, 0) > time.time():
        raise HTTPException(404)
    file_id = await q.photo_id(user_id)
    _photo_missing[user_id] = time.time() + 600  # muvaffaqiyatli bo'lsa pastda o'chiriladi
    data = await photos.user_photo(user_id, file_id, miniapp.tg_file)   # Telegram yoki bazadagi nusxa
    if not data:
        raise HTTPException(404)
    ctype = "image/png" if data[:4] == b"\x89PNG" else "image/jpeg"
    _photo_missing.pop(user_id, None)
    _photo_cache[user_id] = (data, ctype)
    while len(_photo_cache) > 300:
        _photo_cache.popitem(last=False)
    return Response(data, media_type=ctype, headers={"Cache-Control": "private, max-age=3600"})


# ---------------- sayt mazmunini boshqarish (admin) ----------------
def _bad(e: ValueError):
    return JSONResponse({"detail": str(e)}, 400)


@app.get("/api/site/settings")
async def api_site_settings(_=Depends(require_admin)):
    return await sc.settings()


@app.put("/api/site/settings")
async def api_site_settings_save(data: dict = Body(...), _=Depends(require_admin_write)):
    return await sc.save_settings(data)


@app.get("/api/site/posts")
async def api_site_posts(_=Depends(require_admin)):
    return await sc.posts()


@app.post("/api/site/posts")
async def api_site_post_create(data: dict = Body(...), _=Depends(require_admin_write)):
    try:
        return await sc.create_post(data)
    except ValueError as e:
        return _bad(e)


@app.put("/api/site/posts/{pid}")
async def api_site_post_update(pid: int, data: dict = Body(...), _=Depends(require_admin_write)):
    try:
        p = await sc.update_post(pid, data)
    except ValueError as e:
        return _bad(e)
    if not p:
        raise HTTPException(404)
    return p


@app.delete("/api/site/posts/{pid}")
async def api_site_post_delete(pid: int, _=Depends(require_admin_write)):
    await sc.delete_post(pid)
    return {"ok": True}


@app.get("/api/site/gallery")
async def api_site_gallery(_=Depends(require_admin)):
    return await sc.gallery()


@app.post("/api/site/media")
async def api_site_media(data: dict = Body(...), _=Depends(require_admin_write)):
    try:
        return await sc.add_media(str(data.get("data") or ""), str(data.get("caption") or ""),
                                  bool(data.get("in_gallery")))
    except ValueError as e:
        return _bad(e)


@app.put("/api/site/media/{mid}")
async def api_site_media_update(mid: str, data: dict = Body(...), _=Depends(require_admin_write)):
    await sc.update_media(mid, data)
    return {"ok": True}


@app.delete("/api/site/media/{mid}")
async def api_site_media_delete(mid: str, _=Depends(require_admin_write)):
    await sc.delete_media(mid)
    return {"ok": True}


NOT_FOUND_HTML = """<!doctype html><html lang="uz"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Sahifa topilmadi</title></head>
<body style="margin:0;min-height:100vh;display:grid;place-items:center;font-family:system-ui,sans-serif;background:#efe9df;color:#2a241e">
<div style="text-align:center;padding:24px"><h1 style="font-size:72px;margin:0">404</h1><p>Sahifa topilmadi</p>
<a href="/" style="color:#8a6a46;font-weight:700">Bosh sahifaga qaytish</a></div></body></html>"""


@app.exception_handler(StarletteHTTPException)
async def http_errors(request: Request, exc: StarletteHTTPException):
    if request.url.path.startswith("/api/"):
        return JSONResponse({"detail": exc.detail}, exc.status_code)
    if exc.status_code in (401, 404):        # admin qismi borligi ham bilinmasin
        return HTMLResponse(NOT_FOUND_HTML, 404)
    return HTMLResponse(f"<h1>{exc.status_code}</h1>", exc.status_code)


def main() -> None:
    import uvicorn

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    # Bir nechta jarayon (ADMIN_WORKERS) — barcha protsessor yadrolari ishlaydi: minglab kishi bir vaqtda kirganda
    # navbat qisqaradi. backlog — bir vaqtda kutayotgan ulanishlar navbati. Har bir so'rovni jurnalga yozish
    # o'chirilgan (access_log) — yuqori yuklamada sezilarli vaqt olardi; xatolar baribir yoziladi.
    workers = max(1, int(os.getenv("ADMIN_WORKERS", "1")))
    uvicorn.run("admin_site.app:app" if workers > 1 else app, host=os.getenv("ADMIN_HOST", "127.0.0.1"),
                port=int(os.getenv("PORT") or os.getenv("ADMIN_PORT", "8080")), proxy_headers=True, forwarded_allow_ips="*",
                workers=workers, backlog=4096, access_log=os.getenv("ADMIN_ACCESS_LOG", "0") == "1",
                timeout_keep_alive=15)

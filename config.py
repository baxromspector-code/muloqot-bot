import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _load_env(path: Path) -> None:
    """Minimal .env loader (qo'shimcha kutubxonasiz)."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env(BASE_DIR / ".env")


def _int(name: str) -> int:
    try:
        return int(os.getenv(name, "0") or 0)
    except ValueError:
        return 0


BOT_TOKEN = os.getenv("BOT_TOKEN", "")
# Admin buyruqlaridan foydalana oladiganlar (vergul bilan). Tartib muhim: birinchisi — asosiy admin.
_ADMIN_LIST = [int(x) for x in os.getenv("ADMIN_IDS", "").replace(" ", "").split(",") if x.strip().isdigit()]
ADMIN_IDS = set(_ADMIN_LIST)
# Arizalar, murojaatlar, ko'ngillilar tushadigan chat (Kengash guruhi).
# Guruh hali sozlanmagan bo'lsa — birinchi adminning shaxsiy chatiga yuboriladi.
ADMIN_CHAT_ID = _int("ADMIN_CHAT_ID") or (_ADMIN_LIST[0] if _ADMIN_LIST else 0)
# Shikoyatlar tushadigan chat (Etika va intizom komissiyasi). Bo'sh bo'lsa ADMIN_CHAT_ID ishlatiladi.
COMPLAINT_CHAT_ID = _int("COMPLAINT_CHAT_ID") or ADMIN_CHAT_ID
# PostgreSQL ulanishi: postgresql://foydalanuvchi:parol@host:5432/baza
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://muloqot:muloqot@localhost:5432/muloqot")
# FSM holatlarini saqlash uchun Redis (ixtiyoriy). Bo'sh bo'lsa xotirada saqlanadi.
REDIS_URL = os.getenv("REDIS_URL", "")

TELEGRAM_URL = os.getenv("TELEGRAM_URL", "https://t.me/kiut_muloqot")
INSTAGRAM_URL = os.getenv("INSTAGRAM_URL", "https://instagram.com/kiut.muloqot")

# Tugmalarda rasmiy custom emoji belgilari (bot egasida Telegram Premium bo'lsa ishlaydi;
# Telegram rad etsa bot avtomatik oddiy tugmalarga qaytadi). 0 — o'chirish.
BUTTON_ICONS = os.getenv("BUTTON_ICONS", "1") not in ("0", "false", "no", "")

# Guvohnoma va chipta dizayni: diplomat | light | un_blue | gold
CARD_THEME = os.getenv("CARD_THEME", "diplomat")

ASSETS = BASE_DIR / "assets"
DOCS = BASE_DIR / "docs"

# ---------------- maxfiy admin sayti (admin_site) ----------------
# Google Cloud Console → APIs & Services → Credentials → OAuth client ID (Web application)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
# Saytga kira oladigan Google akkauntlar (vergul bilan)
ADMIN_GOOGLE_EMAILS = {x.strip().lower() for x in os.getenv("ADMIN_GOOGLE_EMAILS", "").split(",") if x.strip()}
# 1 — istalgan tasdiqlangan Google akkaunt kira oladi (ro'yxat cheklovi o'chiq). Ehtiyot bo'ling: talabalar ma'lumoti!
ADMIN_ALLOW_ANY_GOOGLE = os.getenv("ADMIN_ALLOW_ANY_GOOGLE", "0") in ("1", "true", "yes")
# Sessiya cookie'sini imzolash kaliti. Bo'sh bo'lsa bot tokenidan hosil qilinadi.
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "") or __import__("hashlib").sha256(
    ("muloqot-admin:" + BOT_TOKEN).encode()).hexdigest()
# Sayt manzili (masalan https://admin.muloqot.uz) — Google redirect URI shundan quriladi
ADMIN_BASE_URL = os.getenv("ADMIN_BASE_URL", "")
# HTTPS orqali ishlaganda 1 (cookie faqat https'da yuboriladi)
ADMIN_HTTPS = os.getenv("ADMIN_HTTPS", "0") in ("1", "true", "yes")
# Faqat sinov uchun: Google sozlanmaguncha 127.0.0.1 dan parolsiz kirish
ADMIN_DEV_LOGIN = os.getenv("ADMIN_DEV_LOGIN", "0") in ("1", "true", "yes")
# Dizayn varianti: diplomat | oq | aurora | skeuo (Qaymoq) | glass
ADMIN_THEME = os.getenv("ADMIN_THEME", "skeuo")  # asosiy: «Qaymoq» (shisha tugmalar bilan); Glass va Diplomat doiracha orqali
# Saytda dizaynni almashtirish doirachalarini ko'rsatish (1) yoki yashirish (0)
ADMIN_THEME_SWITCH = os.getenv("ADMIN_THEME_SWITCH", "0") in ("1", "true", "yes")
# Admin panelga botdagi /panel orqali kira oladigan Telegram ID'lar (vergul bilan). Bo'sh bo'lsa — ADMIN_IDS.
PANEL_ADMIN_IDS = {int(x) for x in os.getenv("PANEL_ADMIN_IDS", "").replace(" ", "").split(",") if x.isdigit()} \
    or set(_ADMIN_LIST)
# Sayt manzili (bot /panel havolasi shundan quriladi). Bo'sh bo'lsa ADMIN_BASE_URL yoki shu kompyuter.
# RENDER_EXTERNAL_URL — Render o'zi beradi (https://<servis>.onrender.com)
SITE_URL = (os.getenv("SITE_URL", "") or ADMIN_BASE_URL or os.getenv("RENDER_EXTERNAL_URL", "") or
            f"http://127.0.0.1:{os.getenv('ADMIN_PORT', '8080')}").rstrip("/")


def site_url() -> str:
    """Joriy sayt manzili. Vaqtinchalik tunnel (tools/tunnel.py) manzilni .env da yangilab turadi,
    shuning uchun har safar .env dan o'qiladi — botni qayta yoqish shart emas. .env bo'lmasa SITE_URL."""
    try:
        for line in (BASE_DIR / ".env").read_text(encoding="utf-8").splitlines():
            if line.startswith("SITE_URL="):
                value = line.split("=", 1)[1].strip().strip('"').strip("'").rstrip("/")
                if value:
                    return value
    except OSError:
        pass
    return SITE_URL

# ---------------- ochiq sayt (asosiy sahifa) — boshlang'ich qiymatlar ----------------
# Admin paneldagi «Sayt ma'lumotlari» bo'limida o'zgartiriladi; bu yerdagilar faqat birinchi ishga tushish uchun.
SITE_DEFAULTS = {
    "phone": os.getenv("SITE_PHONE", "+998 78 129 40 40"),
    "address": os.getenv("SITE_ADDRESS", "Toshkent sh., Yakkasaroy tumani, Shota Rustaveli ko'chasi, 156"),
    "map_query": os.getenv("SITE_MAP_QUERY", "Kimyo International University in Tashkent"),
    "telegram": TELEGRAM_URL,
    "instagram": INSTAGRAM_URL,
    "bot": os.getenv("SITE_BOT_URL", "https://t.me/KIUT_muloqotbot"),
    "email": os.getenv("SITE_EMAIL", ""),
    "hero_title": "MULOQOT",
    "hero_subtitle": "Xalqaro munosabatlar klubi · Kimyo International University in Tashkent",
    "motto": "Bilimdan ko'nikmaga, ko'nikmadan yetakchilikka",
    "about": ("KIUT talabalarini xalqaro masalalar atrofida birlashtirib, darsda olingan bilimni debat, Model UN, "
              "simulyatsiya va tahliliy ish orqali amaliy ko'nikmaga aylantiramiz. A'zolik barcha fakultet "
              "talabalari uchun ochiq va bepul."),
    "hours": "Dushanba–Juma, 08:30–18:00",
}

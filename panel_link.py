"""Admin panelga kirish havolasi: bot /panel buyrug'ida yaratadi, sayt tekshiradi.

Havola imzolangan (ADMIN_SECRET_KEY), 5 daqiqa amal qiladi va faqat bir marta ishlatiladi.
Faqat PANEL_ADMIN_IDS ro'yxatidagi Telegram ID uchun yaratiladi va qabul qilinadi.
"""
import secrets
import time

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config import ADMIN_SECRET_KEY, PANEL_ADMIN_IDS, site_url

TTL = 300  # soniya
_signer = URLSafeTimedSerializer(ADMIN_SECRET_KEY, salt="muloqot-panel-login")


def make_link(user_id: int) -> str:
    if user_id not in PANEL_ADMIN_IDS:
        raise PermissionError("not a panel admin")
    token = _signer.dumps({"u": user_id, "n": secrets.token_urlsafe(8)})
    return f"{site_url()}/auth/tg?t={token}"


async def read_token(token: str) -> int | None:
    """To'g'ri, muddati o'tmagan va hali ishlatilmagan bo'lsa — Telegram ID, aks holda None.

    «Ishlatildi» belgisi bazada (meta jadvali) saqlanadi: sayt bir nechta jarayonda ishlaganda ham
    havola faqat BIR marta ochiladi (xotiradagi belgi har bir jarayonda alohida bo'lardi)."""
    try:
        data = _signer.loads(token, max_age=TTL)
    except (SignatureExpired, BadSignature):
        return None
    uid, nonce = data.get("u"), data.get("n")
    if not isinstance(uid, int) or uid not in PANEL_ADMIN_IDS or not nonce or not isinstance(nonce, str):
        return None
    import db  # sikl importdan qochish uchun shu yerda
    now = time.time()
    # CASE — boshqa meta qiymatlari (matn) float'ga o'girilmasin
    await db._exec("DELETE FROM meta WHERE CASE WHEN key LIKE 'panel_nonce:%' THEN value::float8 < $1 ELSE FALSE END",
                   now)
    first_use = await db._val("INSERT INTO meta(key, value) VALUES($1, $2) ON CONFLICT (key) DO NOTHING RETURNING key",
                              "panel_nonce:" + nonce, str(now + TTL))
    return uid if first_use else None

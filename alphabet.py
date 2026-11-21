"""Amaldagi o'zbek lotin alifbosidan 2026-yilgi yangi alifboga o'girish.

«Lotin yozuviga asoslangan o'zbek alifbosini joriy etish to'g'risida»gi qonun (2026-yil 21-oktabrda imzolangan,
2027-yil 22-apreldan kuchga kiradi): Sh→Ş, Ch→Ç, O'→Ö, G'→Ğ; Ng alohida harf emas (n+g bo'lib qoladi);
tutuq belgisi (a'zo, ma'lumot) saqlanadi.

Havolalar, @username, /buyruqlar, {o'zgaruvchilar}, HTML teglar va email manzillar o'zgarmaydi.
"""
import re

# o'/g' dagi belgi: ' ‘ ` ʻ ’ (har xil klaviaturalarda har xil yoziladi)
_APOS = "'‘`ʻ’"
_PROTECT = re.compile(
    r"(https?://\S+|tg://\S+|www\.\S+|[\w.+-]+@[\w-]+\.[\w.]+|@\w+|(?<![\w])/[a-z_]+|\{[^{}]*\}|<[^<>]+>|&\w+;|#\w*\d\w*)"
)
_RULES = [
    (re.compile(f"O[{_APOS}]"), "Ö"), (re.compile(f"o[{_APOS}]"), "ö"),
    (re.compile(f"G[{_APOS}]"), "Ğ"), (re.compile(f"g[{_APOS}]"), "ğ"),
    (re.compile(r"SH"), "Ş"), (re.compile(r"Sh"), "Ş"), (re.compile(r"sh"), "ş"),
    (re.compile(r"CH"), "Ç"), (re.compile(r"Ch"), "Ç"), (re.compile(r"ch"), "ç"),
]
# Yangi alifboga o'girilmaydigan so'zlar (nomlar, xorijiy atamalar)
_KEEP = {"LinkedIn", "Instagram", "Telegram", "Model UN", "MUN", "Microsoft", "Google", "Excel", "PowerPoint", "Word"}
_KEEP_RE = re.compile("|".join(re.escape(w) for w in sorted(_KEEP, key=len, reverse=True)))


def _convert_plain(s: str) -> str:
    parts, last = [], 0
    for m in _KEEP_RE.finditer(s):
        parts.append(_apply(s[last:m.start()]))
        parts.append(m.group(0))
        last = m.end()
    parts.append(_apply(s[last:]))
    return "".join(parts)


def _apply(s: str) -> str:
    for rx, rep in _RULES:
        s = rx.sub(rep, s)
    return s


def to_new(text: str | None) -> str | None:
    """Matnni yangi alifboga o'giradi (himoyalangan qismlarga tegmaydi)."""
    if not text:
        return text
    out, last = [], 0
    for m in _PROTECT.finditer(text):
        out.append(_convert_plain(text[last:m.start()]))
        out.append(m.group(0))
        last = m.end()
    out.append(_convert_plain(text[last:]))
    return "".join(out)

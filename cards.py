"""A'zolik guvohnomasi va tadbir QR-chiptasi rasmlarini yaratish (Pillow).

Dizayn mavzulari (THEMES) — `.env` dagi CARD_THEME bilan tanlanadi:
diplomat (to'q ko'k + sariq), light (oq, minimal), un_blue (BMT ko'k), gold (qora + oltin).
"""
import io
import textwrap
from functools import lru_cache

import qrcode
from PIL import Image, ImageDraw, ImageFont
from qrcode.constants import ERROR_CORRECT_M

from config import ASSETS, CARD_THEME

WHITE = (255, 255, 255)
LIGHT = (240, 244, 248)

# Har bir mavzu: guvohnoma (card_*), chipta (t_*) va umumiy ranglar
THEMES: dict[str, dict] = {
    "diplomat": dict(
        name="Diplomat", stripes=[(36, 104, 200), (212, 166, 58), (38, 150, 148)],  # yangi logo ranglari: ko'k · oltin · zangori
        card_bg=(11, 46, 79), card_bg2=None, card_title=(244, 196, 48), card_text=WHITE,
        card_label=(64, 178, 200), card_sub=(190, 205, 220), frame=WHITE,
        band_bg=(244, 196, 48), band_text=(11, 46, 79), qr_fg=(11, 46, 79), border=None,
        t_bg=WHITE, t_head=(11, 46, 79), t_head2=None, t_head_title=(244, 196, 48), t_head_text=WHITE,
        t_label=(110, 124, 140), t_text=(11, 46, 79), t_code=(20, 66, 106), t_box=(64, 178, 200),
        t_foot=(11, 46, 79), t_foot_text=WHITE, t_notch=LIGHT,
    ),
    "light": dict(
        name="Oq minimal", stripes=[(36, 104, 200), (212, 166, 58), (38, 150, 148)],  # yangi logo ranglari: ko'k · oltin · zangori
        card_bg=(248, 250, 252), card_bg2=None, card_title=(11, 46, 79), card_text=(20, 30, 45),
        card_label=(0, 128, 150), card_sub=(110, 124, 140), frame=(214, 224, 234),
        band_bg=(11, 46, 79), band_text=WHITE, qr_fg=(11, 46, 79), border=(214, 224, 234),
        t_bg=WHITE, t_head=(240, 246, 250), t_head2=None, t_head_title=(0, 128, 150), t_head_text=(11, 46, 79),
        t_label=(120, 132, 148), t_text=(20, 30, 45), t_code=(0, 128, 150), t_box=(214, 224, 234),
        t_foot=(0, 128, 150), t_foot_text=WHITE, t_notch=(225, 232, 240),
    ),
    "un_blue": dict(
        name="BMT ko'k", stripes=[WHITE, (160, 215, 245), WHITE],
        card_bg=(0, 104, 178), card_bg2=(0, 158, 219), card_title=WHITE, card_text=WHITE,
        card_label=(185, 228, 250), card_sub=(205, 232, 248), frame=WHITE,
        band_bg=WHITE, band_text=(0, 104, 178), qr_fg=(0, 84, 150), border=None,
        t_bg=WHITE, t_head=(0, 104, 178), t_head2=(0, 158, 219), t_head_title=(185, 228, 250), t_head_text=WHITE,
        t_label=(110, 130, 150), t_text=(0, 60, 110), t_code=(0, 120, 200), t_box=(0, 158, 219),
        t_foot=(0, 104, 178), t_foot_text=WHITE, t_notch=(225, 240, 250),
    ),
    "gold": dict(
        name="Premium oltin", stripes=[(212, 175, 55), (240, 214, 130), (212, 175, 55)],
        card_bg=(22, 22, 26), card_bg2=None, card_title=(212, 175, 55), card_text=(245, 240, 228),
        card_label=(212, 175, 55), card_sub=(170, 160, 140), frame=(212, 175, 55),
        band_bg=(212, 175, 55), band_text=(22, 22, 26), qr_fg=(22, 22, 26), border=(212, 175, 55),
        t_bg=(250, 247, 238), t_head=(22, 22, 26), t_head2=None, t_head_title=(212, 175, 55),
        t_head_text=(245, 240, 228), t_label=(140, 125, 95), t_text=(30, 28, 24), t_code=(160, 125, 30),
        t_box=(212, 175, 55), t_foot=(22, 22, 26), t_foot_text=(212, 175, 55), t_notch=(230, 222, 200),
    ),
}

_FONT_CANDIDATES = {
    True: ["arialbd.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf",
           "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf"],
    False: ["arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "C:/Windows/Fonts/arial.ttf"],
}


def _theme(name: str | None) -> dict:
    return THEMES.get(name or CARD_THEME) or THEMES["diplomat"]


@lru_cache(maxsize=64)
def font(size: int, bold: bool = False):
    for name in _FONT_CANDIDATES[bold]:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


@lru_cache(maxsize=4)
def _logo(size: int) -> Image.Image | None:
    path = ASSETS / "logo.png"
    if not path.exists():
        return None
    img = Image.open(path)
    if img.mode != "RGBA":  # oq fonni shaffof qilamiz — doiradan oq to'rtburchak chiqib turmasin
        import numpy as np
        a = np.asarray(img.convert("RGB")).astype(np.float32)
        d = np.clip((255 - a) / 255, 0, 1).max(axis=2)
        alpha = (np.clip((d - 0.03) / 0.35, 0, 1) * 255).astype(np.uint8)
        img = img.convert("RGB")
        img.putalpha(Image.fromarray(alpha))
    img.thumbnail((size, size))
    return img


@lru_cache(maxsize=8)
def logo_round(size: int) -> Image.Image | None:
    """Logotipdagi daraxt + BMT gerbi qismi, doira shaklida (pastdagi yozuvsiz) — kichik belgilar uchun."""
    mark = ASSETS / "logo_mark.png"   # tools/apply_new_logo.py yasaydi: faqat belgi, shaffof fon
    if mark.exists():
        m = Image.open(mark).convert("RGBA")
        out = Image.new("RGBA", (size, size), (255, 255, 255, 0))
        disc = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ImageDraw.Draw(disc).ellipse((0, 0, size - 1, size - 1), fill=(255, 255, 255, 255))
        out.alpha_composite(disc)
        inner = round(size * 0.84)                 # doira chetidan joy qoladi — barglar kesilmaydi
        m = m.resize((inner, inner), Image.Resampling.LANCZOS)
        out.alpha_composite(m, ((size - inner) // 2, (size - inner) // 2))
        return out
    path = ASSETS / "logo.png"
    if not path.exists():
        return None
    src = Image.open(path).convert("RGBA")
    side = min(src.width, int(src.height * 0.84))  # pastki «MULOQOT» yozuvini kesib tashlaymiz
    left = (src.width - side) // 2
    sq = src.crop((left, 0, left + side, side)).resize((size, size), Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(sq, (0, 0), mask)
    return out


def paste_logo_round(img: Image.Image, center: tuple[int, int], size: int, ring=None, ring_w: int = 4) -> None:
    logo = logo_round(size)
    if not logo:
        return
    x, y = center[0] - size // 2, center[1] - size // 2
    if ring:
        ImageDraw.Draw(img).ellipse((x - ring_w, y - ring_w, x + size + ring_w, y + size + ring_w), fill=ring)
    img.paste(logo, (x, y), logo)


def _logo_bg() -> tuple:
    """Logotip fon rangi — doira shu rangda chiziladi, chegara ko'rinmasin."""
    logo = _logo(64)
    if not logo:
        return LIGHT
    px = logo.getpixel((1, 1))
    return (255, 255, 255) if len(px) == 4 and px[3] < 20 else px[:3]


def _qr(data: str, size: int, fg) -> Image.Image:
    qr = qrcode.QRCode(border=1, box_size=10, error_correction=ERROR_CORRECT_M)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fg, back_color="white")
    pil = img.get_image() if hasattr(img, "get_image") else img
    return pil.convert("RGB").resize((size, size), Image.Resampling.NEAREST)


def _gradient(size: tuple[int, int], top, bottom) -> Image.Image:
    w, h = size
    base = Image.new("RGB", (1, h))
    for y in range(h):
        k = y / max(h - 1, 1)
        base.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * k) for i in range(3)))
    return base.resize((w, h))


def _center(draw: ImageDraw.ImageDraw, y: int, text: str, fnt, fill, width: int) -> int:
    box = draw.textbbox((0, 0), text, font=fnt)
    draw.text(((width - (box[2] - box[0])) / 2, y), text, font=fnt, fill=fill)
    return int(y + (box[3] - box[1]))


def _fit(draw, text: str, max_w: int, start: int, bold=True, min_size=18):
    size = start
    while size > min_size and draw.textlength(text, font=font(size, bold)) > max_w:
        size -= 2
    return font(size, bold)


def _png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def _photo_3x4(photo: bytes, w: int, h: int) -> Image.Image | None:
    """Suratni 3×4 nisbatda markazdan kesadi."""
    try:
        img = Image.open(io.BytesIO(photo)).convert("RGB")
    except Exception:
        return None
    ratio = w / h
    if img.width / img.height > ratio:  # keng — yon tomonlarini kesamiz
        nw = int(img.height * ratio)
        img = img.crop(((img.width - nw) // 2, 0, (img.width + nw) // 2, img.height))
    else:  # baland — yuqori qismini saqlab, pastini kesamiz (yuz odatda tepada)
        nh = int(img.width / ratio)
        top = max(0, int((img.height - nh) * 0.25))
        img = img.crop((0, top, img.width, top + nh))
    return img.resize((w, h), Image.Resampling.LANCZOS)


def membership_card(full_name: str, number: str, section: str, group: str, valid_year: str,
                    photo: bytes | None = None, theme: str | None = None) -> bytes:
    th = _theme(theme)
    W, H = 640, 1000
    img = _gradient((W, H), th["card_bg"], th["card_bg2"]) if th["card_bg2"] else Image.new("RGB", (W, H), th["card_bg"])
    d = ImageDraw.Draw(img)
    if th["border"]:
        d.rectangle((14, 14, W - 15, H - 15), outline=th["border"], width=3)

    # yuqori chiziqlar (brend ranglari)
    for i, c in enumerate(th["stripes"]):
        d.rectangle((40 + i * 70, 40, 100 + i * 70, 46), fill=c)
    d.text((W - 40, 34), f"№ {number}", font=font(24, True), fill=th["card_text"], anchor="ra")

    face = _photo_3x4(photo, 225, 300) if photo else None
    if face:
        # 3×4 surat ramkada, burchakda kichik logotip
        x0, y0 = (W - 225) // 2, 80
        d.rounded_rectangle((x0 - 8, y0 - 8, x0 + 233, y0 + 308), radius=14, fill=th["frame"])
        img.paste(face, (x0, y0))
        paste_logo_round(img, (x0 + 225, y0 + 290), 92, ring=th["frame"])
    else:
        # surat bo'lmasa — logotip doirada
        d.ellipse((W / 2 - 150, 90, W / 2 + 150, 390), fill=_logo_bg(), outline=th["frame"], width=3)
        logo = _logo(250)
        if logo:
            img.paste(logo, (int(W / 2 - logo.width / 2), int(240 - logo.height / 2)), logo)

    y = _center(d, 420, "A'ZOLIK GUVOHNOMASI", font(34, True), th["card_title"], W) + 10
    _center(d, y, "MEMBERSHIP CARD · KIUT TALABALAR KLUBI", font(18), th["card_sub"], W)

    # ism
    name_lines = textwrap.wrap(full_name.upper(), 22) or ["—"]
    y = 520
    for line in name_lines[:2]:
        y = _center(d, y, line, _fit(d, line, W - 80, 40), th["card_text"], W) + 12

    # ma'lumotlar + QR
    y = max(y + 20, 640)
    rows = [("BO'LIMI", section), ("GURUH", group), ("AMAL MUDDATI", f"{valid_year} o'quv yili")]
    for label, value in rows:
        d.text((50, y), label, font=font(18, True), fill=th["card_label"])
        d.text((50, y + 24), value, font=_fit(d, value, 330, 26, False), fill=th["card_text"])
        y += 70
    d.rounded_rectangle((W - 250, 630, W - 40, 840), radius=16, fill=WHITE,
                        outline=th["border"] or WHITE, width=2)
    img.paste(_qr(f"MULOQOT:MEMBER:{number}", 190, th["qr_fg"]), (W - 240, 640))

    # pastki lenta
    d.rectangle((0, H - 120, W, H), fill=th["band_bg"])
    _center(d, H - 108, "A'ZO", font(40, True), th["band_text"], W)
    _center(d, H - 52, "DIPLOMATIYA MULOQOTDAN BOSHLANADI", font(18, True), th["band_text"], W)
    return _png(img)


def ticket(event_title: str, date_text: str, place: str, code: str, owner: str, payload: str,
           theme: str | None = None) -> bytes:
    th = _theme(theme)
    W, H = 640, 1040
    img = Image.new("RGB", (W, H), th["t_bg"])
    d = ImageDraw.Draw(img)

    # sarlavha
    if th["t_head2"]:
        img.paste(_gradient((W, 190), th["t_head"], th["t_head2"]), (0, 0))
    else:
        d.rectangle((0, 0, W, 190), fill=th["t_head"])
    paste_logo_round(img, (95, 95), 126, ring=WHITE, ring_w=3)
    d.text((185, 40), "MULOQOT · KIUT", font=font(22, True), fill=th["t_head_title"])
    title_lines = textwrap.wrap(event_title.upper(), 20) or ["—"]
    ty = 74
    for line in title_lines[:3]:
        d.text((185, ty), line, font=_fit(d, line, W - 210, 32), fill=th["t_head_text"])
        ty += 38
    for i, c in enumerate(th["stripes"]):
        d.rectangle((i * W / 3, 190, (i + 1) * W / 3, 198), fill=c)

    # sana va joy
    d.text((40, 225), "SANA VA VAQT", font=font(18, True), fill=th["t_label"])
    d.text((340, 225), "JOY", font=font(18, True), fill=th["t_label"])
    for i, line in enumerate(textwrap.wrap(date_text or "—", 18)[:2]):
        d.text((40, 252 + i * 30), line, font=font(26, True), fill=th["t_text"])
    for i, line in enumerate(textwrap.wrap(place or "—", 18)[:2]):
        d.text((340, 252 + i * 30), line, font=font(26, True), fill=th["t_text"])

    # QR
    d.rounded_rectangle((150, 340, W - 150, 690), radius=24, outline=th["t_box"], width=4, fill=WHITE)
    img.paste(_qr(payload, 300, th["qr_fg"]), (170, 365))

    # perforatsiya
    for x in range(20, W - 20, 28):
        d.line((x, 730, x + 14, 730), fill=th["t_notch"], width=3)
    d.ellipse((-25, 705, 25, 755), fill=th["t_notch"])
    d.ellipse((W - 25, 705, W + 25, 755), fill=th["t_notch"])

    y = _center(d, 760, "CHIPTA RAQAMI", font(20, True), th["t_label"], W) + 10
    y = _center(d, y, code, font(54, True), th["t_code"], W) + 26
    y = _center(d, y, "CHIPTA EGASI", font(20, True), th["t_label"], W) + 10
    _center(d, y, owner, _fit(d, owner, W - 80, 34), th["t_text"], W)

    d.rectangle((0, H - 70, W, H), fill=th["t_foot"])
    _center(d, H - 50, "Kirishda QR kodni ko'rsating · @kiut_muloqot", font(20, True), th["t_foot_text"], W)
    return _png(img)

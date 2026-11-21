"""Rasmiy emoji to'plami (MULOQOT · KIUT) — @Adliya to'plami uslubida, davlat tashkilotlari uchun.

Har bir nishon bitta keng rasm qilib chiziladi va 100×100 bo'laklarga kesiladi; xabarda yonma-yon
qo'yilganda yaxlit nishon bo'ladi.

    python tools/make_official_emoji.py   ->  dizayn/emoji_rasmiy/<to'plam>/NN.png  +  dizayn/emoji-rasmiy-namuna.png

@Stickers: /newemojipack -> Static emoji -> fayllarni papka va raqam tartibida yuklash, har biriga mos emoji.
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import cards  # noqa: E402

OUT = ROOT / "dizayn" / "emoji_rasmiy"
T = 100
DEEP = (10, 61, 122)       # rasmiy to'q ko'k
KIUT = (0, 152, 218)       # KIUT ko'k
WHITE = (255, 255, 255)
GOLD = (196, 160, 60)
TOP, BOTTOM = 14, T - 15   # nishon balandligi (Adliya kabi: bo'lakning o'rta qismi)


def _shield(h: int) -> Image.Image | None:
    p = ROOT / "assets" / "kiut_shield.png"
    if not p.exists():
        return None
    img = Image.open(p).convert("RGBA")
    return img.resize((int(img.width * h / img.height), h), Image.Resampling.LANCZOS)


def spaced_width(d, text, fnt, spacing) -> float:
    return sum(d.textlength(ch, font=fnt) for ch in text) + spacing * (len(text) - 1)


def draw_spaced(d, x, y, text, fnt, fill, spacing) -> None:
    for ch in text:
        d.text((x, y), ch, font=fnt, fill=fill)
        x += d.textlength(ch, font=fnt) + spacing


def _emblem(img: Image.Image, kind: str | None, cx: int, ring) -> None:
    if kind == "muloqot":
        cards.paste_logo_round(img, (cx, T // 2), 60, ring=ring, ring_w=3)
    elif kind == "kiut":
        sh = _shield(64)
        if sh:
            img.paste(sh, (cx - sh.width // 2, T // 2 - sh.height // 2), sh)


def badge(text: str, *, fill, fg, border, emblem: str | None = None, size: int = 50, spacing: int = 4,
          min_tiles: int = 1, inner_line: bool = False) -> Image.Image:
    """Bir qatorli nishon. Bo'laklar soni matn uzunligiga qarab avtomatik."""
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    fnt = cards.font(size, True)
    tw = spaced_width(tmp, text, fnt, spacing)
    lead = T if emblem else 0
    tiles = max(min_tiles, math.ceil((lead + tw + 44) / T))
    w = tiles * T
    img = Image.new("RGBA", (w, T), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((2, TOP, w - 3, BOTTOM), radius=8, fill=fill, outline=border, width=5)
    if inner_line:
        d.rounded_rectangle((9, TOP + 7, w - 10, BOTTOM - 7), radius=5, outline=(255, 255, 255, 150), width=2)
    _emblem(img, emblem, T // 2, border)
    box = tmp.textbbox((0, 0), text, font=fnt)
    x = lead + (w - lead - tw) / 2
    y = (T - (box[3] - box[1])) / 2 - box[1]
    draw_spaced(d, x, y, text, fnt, fg, spacing)
    return img


def badge2(top: str, bottom: str, *, emblem: str, tiles: int, fill=DEEP, fg_top=(190, 215, 240), fg_bottom=WHITE):
    """Ikki qatorli rasmiy nishon (Adliya'dagi «O'zbekiston Respublikasi Adliya vazirligi» kabi)."""
    w = tiles * T
    img = Image.new("RGBA", (w, T), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((2, TOP, w - 3, BOTTOM), radius=8, fill=fill)
    d.rounded_rectangle((8, TOP + 6, w - 9, BOTTOM - 6), radius=5, outline=GOLD, width=2)
    if emblem == "kiut":
        d.ellipse((T // 2 - 34, T // 2 - 34, T // 2 + 34, T // 2 + 34), fill=WHITE)
    _emblem(img, emblem, T // 2, WHITE)
    f1 = cards._fit(d, top, w - T - 24, 18, bold=True, min_size=11)
    f2 = cards._fit(d, bottom, w - T - 24, 23, bold=True, min_size=11)
    draw_spaced(d, T + 2, 28, top, f1, fg_top, 1)
    draw_spaced(d, T + 2, 50, bottom, f2, fg_bottom, 2)
    return img


def icon(kind: str) -> Image.Image:
    img = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if kind == "muloqot":
        cards.paste_logo_round(img, (50, 50), 88, ring=DEEP, ring_w=5)
        return img
    if kind == "kiut":
        sh = _shield(92)
        if sh:
            img.paste(sh, (50 - sh.width // 2, 50 - sh.height // 2), sh)
        return img
    d.ellipse((6, 6, 94, 94), fill=DEEP, outline=WHITE, width=3)
    if kind == "check":
        d.line([(28, 52), (44, 68), (73, 35)], fill=WHITE, width=10, joint="curve")
    elif kind == "warn":
        d.rounded_rectangle((44, 22, 56, 60), radius=5, fill=WHITE)
        d.ellipse((43, 66, 57, 80), fill=WHITE)
    elif kind == "info":
        d.ellipse((43, 20, 57, 34), fill=WHITE)
        d.rounded_rectangle((44, 40, 56, 80), radius=5, fill=WHITE)
    return img


def slice_save(banner: Image.Image, name: str) -> list[Path]:
    folder = OUT / name
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in range(banner.width // T):
        p = folder / f"{i + 1:02d}.png"
        banner.crop((i * T, 0, (i + 1) * T, T)).save(p)
        paths.append(p)
    return paths


SETS = {
    # nomi: (nishon, izoh)
    "01_assalomu_alaykum": (lambda: badge("ASSALOMU ALAYKUM", fill=WHITE, fg=DEEP, border=DEEP, emblem="muloqot", size=40, spacing=3),
                            "Salomlashish"),
    "02_xush_kelibsiz": (lambda: badge("XUSH KELIBSIZ", fill=WHITE, fg=DEEP, border=DEEP, emblem="muloqot", size=42, spacing=3),
                         "Botga kirganda"),
    "03_muloqot": (lambda: badge("MULOQOT", fill=WHITE, fg=DEEP, border=DEEP, emblem="muloqot", size=52, spacing=6),
                   "Klub nomi"),
    "04_universitet": (lambda: badge2("TOSHKENT KIMYO XALQARO", "UNIVERSITETI", emblem="kiut", tiles=6),
                       "Universitet (ruxsat kerak)"),
    "05_klub": (lambda: badge2("XALQARO MUNOSABATLAR", "KLUBI · MULOQOT", emblem="muloqot", tiles=6),
                "Klub rasmiy nishoni"),
    "06_elon": (lambda: badge("E'LON", fill=DEEP, fg=WHITE, border=DEEP, size=44, spacing=5, min_tiles=2, inner_line=True),
                "E'lonlar"),
    "07_tadbir": (lambda: badge("TADBIR", fill=DEEP, fg=WHITE, border=DEEP, size=44, spacing=5, min_tiles=2, inner_line=True),
                  "Tadbirlar"),
    "08_azolik": (lambda: badge("A'ZOLIK", fill=DEEP, fg=WHITE, border=DEEP, size=44, spacing=5, min_tiles=2, inner_line=True),
                  "A'zolik"),
    "09_murojaat": (lambda: badge("MUROJAAT", fill=DEEP, fg=WHITE, border=DEEP, size=42, spacing=4, min_tiles=2, inner_line=True),
                    "Murojaatlar"),
    "10_hujjatlar": (lambda: badge("HUJJATLAR", fill=DEEP, fg=WHITE, border=DEEP, size=42, spacing=4, min_tiles=2, inner_line=True),
                     "Hujjatlar"),
    "11_diqqat": (lambda: badge("DIQQAT", fill=WHITE, fg=(170, 30, 40), border=(170, 30, 40), size=44, spacing=5, min_tiles=2),
                  "Muhim xabarlar"),
    "12_tasdiqlandi": (lambda: badge("TASDIQLANDI", fill=WHITE, fg=(20, 110, 60), border=(20, 110, 60), size=40, spacing=3),
                       "Ariza qabul qilinganda"),
    "13_rahmat": (lambda: badge("RAHMAT", fill=WHITE, fg=DEEP, border=DEEP, size=44, spacing=5, min_tiles=2),
                  "Minnatdorchilik"),
}
ICONS = ["muloqot", "kiut", "check", "warn", "info"]


def main() -> None:
    if OUT.exists():
        for p in sorted(OUT.rglob("*.png"), reverse=True):
            p.unlink()
    built = {name: (slice_save(make(), name), note) for name, (make, note) in SETS.items()}
    icon_dir = OUT / "14_belgilar"
    icon_dir.mkdir(parents=True, exist_ok=True)
    for i, k in enumerate(ICONS, 1):
        icon(k).save(icon_dir / f"{i:02d}_{k}.png")
    total = sum(len(v[0]) for v in built.values()) + len(ICONS)

    # ---------- namuna varag'i ----------
    S = 56  # xabarda «katta emoji» o'lchami
    W = 1500
    rows = list(built.items())
    H = 150 + math.ceil(len(rows) / 2) * 112 + 420
    prev = Image.new("RGB", (W, H), (236, 240, 245))
    d = ImageDraw.Draw(prev)
    d.text((40, 30), "MULOQOT · KIUT — rasmiy emoji to'plami", font=cards.font(40, True), fill=DEEP)
    d.text((40, 86), f"{total} ta emoji · 100×100 · @Adliya uslubida · oq/to'q ko'k, katta harflar", font=cards.font(22),
           fill=(80, 95, 110))
    for idx, (name, (paths, note)) in enumerate(rows):
        col, row = idx % 2, idx // 2
        x0, y0 = 40 + col * 730, 150 + row * 112
        d.rounded_rectangle((x0, y0, x0 + 700, y0 + 96), radius=16, fill=WHITE)
        x = x0 + 16
        for p in paths:
            tile = Image.open(p).resize((S, S), Image.Resampling.LANCZOS)
            prev.paste(tile, (x, y0 + 20), tile)
            x += S
        d.text((x0 + 700 - 16, y0 + 36), f"{note} · {len(paths)} bo'lak", font=cards.font(18), fill=(100, 115, 130),
               anchor="ra")
    # belgilar
    y = 150 + math.ceil(len(rows) / 2) * 112 + 10
    d.text((40, y), "Alohida belgilar:", font=cards.font(22, True), fill=DEEP)
    for i, k in enumerate(ICONS):
        prev.paste(Image.open(icon_dir / f"{i + 1:02d}_{k}.png").resize((70, 70)), (260 + i * 90, y - 20),
                   Image.open(icon_dir / f"{i + 1:02d}_{k}.png").resize((70, 70)))
    # xabar namunasi (Telegram kunduzgi mavzusi)
    y += 80
    d.text((40, y), "Botdagi salomlashish xabari namunasi:", font=cards.font(22, True), fill=DEEP)
    bx, by = 40, y + 40
    d.rounded_rectangle((bx, by, bx + 900, by + 250), radius=22, fill=WHITE, outline=(210, 220, 230))
    x = bx + 24
    for p in built["01_assalomu_alaykum"][0]:
        t = Image.open(p).resize((44, 44), Image.Resampling.LANCZOS)
        prev.paste(t, (x, by + 22), t)
        x += 44
    lines = ["MULOQOT — Toshkent Kimyo xalqaro universiteti talabalarining",
             "xalqaro munosabatlar klubi rasmiy boti.", "", "Kerakli bo'limni tanlang."]
    for i, line in enumerate(lines):
        d.text((bx + 24, by + 84 + i * 32), line, font=cards.font(24), fill=(25, 35, 50))
    x = bx + 24
    for p in built["07_tadbir"][0]:
        t = Image.open(p).resize((40, 40), Image.Resampling.LANCZOS)
        prev.paste(t, (bx + 560 + (x - bx - 24), by + 196), t)
        x += 40
    d.text((bx + 560 + (x - bx - 24) + 10, by + 202), "24.11 · 16:00", font=cards.font(22, True), fill=DEEP)
    prev.save(ROOT / "dizayn" / "emoji-rasmiy-namuna.png")
    print("tayyor:", total, "ta emoji ->", OUT)


if __name__ == "__main__":
    main()

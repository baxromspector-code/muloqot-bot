"""MULOQOT custom emoji to'plami uchun 100×100 bo'laklar (@Adliya to'plami uslubida).

Yozuv bitta keng nishon qilib chiziladi va 100 px bo'laklarga kesiladi: emojilar xabarda yonma-yon
qo'yilganda yaxlit nishon bo'lib ko'rinadi.

    python tools/make_emoji.py        ->  dizayn/emoji/*.png  +  dizayn/emoji-namuna.png
@Stickers botida: /newemojipack -> Static -> har bir PNG ni tartib bilan yuklash.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import cards  # noqa: E402

OUT = ROOT / "dizayn" / "emoji"
NAVY, BLUE, YELLOW, WHITE = (11, 46, 79), (28, 92, 168), (244, 196, 48), (255, 255, 255)
T = 100  # Telegram custom emoji o'lchami


def slice_banner(banner: Image.Image, prefix: str) -> list[Path]:
    paths = []
    for i in range(banner.width // T):
        tile = banner.crop((i * T, 0, (i + 1) * T, T))
        p = OUT / f"{prefix}_{i + 1:02d}.png"
        tile.save(p)
        paths.append(p)
    return paths


def word_banner(text: str, tiles: int, bg, fg, border, logo_first: bool) -> Image.Image:
    """Oq (yoki rangli) nishon: chap tomonda logotip bo'lagi, keyin yozuv. Ramka hamma bo'laklar bo'ylab."""
    w = tiles * T
    img = Image.new("RGBA", (w, T), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((2, 14, w - 3, T - 15), radius=10, fill=bg, outline=border, width=5)
    x0 = 0
    if logo_first:
        cards.paste_logo_round(img, (T // 2, T // 2), 62, ring=border, ring_w=3)
        x0 = T
    fnt = cards._fit(d, text, w - x0 - 18, 60, bold=True, min_size=20)
    box = d.textbbox((0, 0), text, font=fnt)
    tx = x0 + (w - x0 - (box[2] - box[0])) / 2 - box[0]
    ty = (T - (box[3] - box[1])) / 2 - box[1]
    d.text((tx, ty), text, font=fnt, fill=fg)
    return img


def two_line_banner(top: str, bottom: str, tiles: int, bg, fg_top, fg_bottom) -> Image.Image:
    w = tiles * T
    img = Image.new("RGBA", (w, T), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((2, 14, w - 3, T - 15), radius=10, fill=bg)
    cards.paste_logo_round(img, (T // 2, T // 2), 56, ring=YELLOW, ring_w=3)
    f1 = cards._fit(d, top, w - T - 16, 24, bold=True, min_size=12)
    f2 = cards._fit(d, bottom, w - T - 16, 30, bold=True, min_size=12)
    d.text((T + 4, 24), top, font=f1, fill=fg_top)
    d.text((T + 4, 50), bottom, font=f2, fill=fg_bottom)
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()
    sets = {
        # 1) «MULOQOT» — oq fon, ko'k ramka (Adliya uslubi)
        "muloqot": word_banner("MULOQOT", 5, WHITE, BLUE, BLUE, logo_first=True),
        # 2) to'q ko'k fon, sariq yozuv — rasmiy nishon
        "klub": two_line_banner("KIUT · TOSHKENT", "Xalqaro munosabatlar klubi", 5, NAVY, YELLOW, WHITE),
        # 3) qisqa «KIUT MULOQOT» — sariq fon
        "qisqa": word_banner("MULOQOT", 3, YELLOW, NAVY, NAVY, logo_first=False),
    }
    files = {k: slice_banner(v, k) for k, v in sets.items()}
    # bitta logotip emojisi
    single = Image.new("RGBA", (T, T), (0, 0, 0, 0))
    cards.paste_logo_round(single, (T // 2, T // 2), 92, ring=BLUE, ring_w=4)
    single.save(OUT / "logo.png")

    # ---- namuna: Telegram xabarida qanday ko'rinadi ----
    W = 980
    prev = Image.new("RGB", (W, 760), (14, 22, 33))
    d = ImageDraw.Draw(prev)
    d.text((30, 24), "MULOQOT emoji to'plami — xabarda ko'rinishi", font=cards.font(30, True), fill=WHITE)
    y = 90
    for key, label in [("muloqot", "1) «MULOQOT» nishoni (oq, Adliya uslubida) — 5 bo'lak"),
                       ("klub", "2) Rasmiy nishon (to'q ko'k) — 5 bo'lak"),
                       ("qisqa", "3) Qisqa sariq nishon — 3 bo'lak")]:
        d.text((30, y), label, font=cards.font(20), fill=(150, 170, 190))
        bubble_w = 60 * len(files[key]) + 40
        d.rounded_rectangle((30, y + 32, 30 + bubble_w, y + 132), radius=18, fill=(24, 37, 51))
        for i, p in enumerate(files[key]):  # katta emoji ko'rinishi (xabarda faqat emojilar bo'lsa)
            tile = Image.open(p).resize((60, 60), Image.Resampling.LANCZOS)
            prev.paste(tile, (50 + i * 60, y + 52), tile)
        # bo'laklar alohida (yuklash tartibi)
        for i, p in enumerate(files[key]):
            tile = Image.open(p)
            x = 30 + bubble_w + 40 + i * 108
            if x + 100 < W:
                d.rectangle((x - 2, y + 30, x + 101, y + 133), outline=(60, 80, 100))
                prev.paste(tile, (x, y + 32), tile)
        y += 170
    d.text((30, y + 10), "Matn ichida:", font=cards.font(20), fill=(150, 170, 190))
    d.rounded_rectangle((30, y + 42, W - 30, y + 112), radius=18, fill=(24, 37, 51))
    x = 50
    for p in files["muloqot"]:
        tile = Image.open(p).resize((34, 34), Image.Resampling.LANCZOS)
        prev.paste(tile, (x, y + 60), tile)
        x += 34
    d.text((x + 12, y + 64), "klubiga xush kelibsiz! Kerakli bo'limni tanlang 👇", font=cards.font(22), fill=WHITE)
    prev.save(ROOT / "dizayn" / "emoji-namuna.png")
    print("tayyor:", sum(len(v) for v in files.values()) + 1, "ta emoji")


if __name__ == "__main__":
    main()

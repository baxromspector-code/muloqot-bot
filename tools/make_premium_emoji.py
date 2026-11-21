"""MULOQOT premium emoji to'plami (2-avlod, TINIQ) — Telegram video emoji: WEBM/VP9, 100×100, alfa, ≤3 s.

Eski to'plam nega xira edi va bu yerda nima o'zgardi:
  • yozuv plitka balandligining ~45% i edi, ikki qatorli nishonlar ham bor edi → Telegram emoji'ni ~20px
    ko'rsatganda harflar loyqalanardi. Endi: faqat BITTA qator, nishon 80px, harf balandligi ~44px, Segoe UI Black;
  • kuchli siqish (crf 30–50) → endi crf 12–20 (har bir fayl ≤ 250 KB);
  • yaltiroq nur endi faqat fonda yuradi — harflar ustidan o'tmaydi, ular har doim to'liq tiniq.

    python tools/make_premium_emoji.py
Natija: dizayn/emoji_premium/NN_nom/KK.webm, dizayn/emoji_premium/namuna.png va namuna.mp4
"""
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dizayn" / "emoji_premium"
T, FPS, N, SS = 100, 30, 87, 4          # plitka, kadr/s, 2.9 s, supersampling
TOP, BOT = 10, 90                       # nishon balandligi 80px
FONT = "C:/Windows/Fonts/seguibl.ttf"   # Segoe UI Black — kichik o'lchamda ham qalin va aniq
FONT_FALLBACK = "C:/Windows/Fonts/ariblk.ttf"

# ranglar: (fon yuqorisi, fon pasti, chekka)
NAVY = ((34, 74, 140), (12, 44, 98), (214, 180, 106))     # rasmiy to'q ko'k + oltin chekka
RED = ((214, 46, 62), (160, 18, 36), (255, 214, 214))      # e'lon / yangilik — diqqat
UN = ((40, 150, 225), (0, 104, 178), (220, 240, 255))      # BMT havorangi
GOLD = ((214, 176, 92), (160, 120, 40), (255, 240, 200))   # prezident

# (papka nomi, yozuv, rang, qidiruv emojisi) — Islom aka ro'yxati bo'yicha
ITEMS = [
    ("01_rasmiy_bayonot", "RASMIY BAYONOT", NAVY, "📜"),
    ("02_elon", "E'LON", RED, "📢"),
    ("03_muloqot_klubi", "MULOQOT KLUBI", NAVY, "🌐"),
    ("04_muloqot_oilasi", "MULOQOT OILASI", NAVY, "🤝"),
    ("05_zakovat", "ZAKOVAT", NAVY, "🧠"),
    ("06_debat", "DEBAT", NAVY, "🎤"),
    ("07_model_un", "MODEL UN", UN, "🇺🇳"),
    ("08_mun", "MUN", UN, "🇺🇳"),
    ("09_bmt", "BMT", UN, "🌍"),
    ("10_yangilik", "YANGILIK", RED, "🆕"),
    ("11_news", "NEWS", RED, "📰"),
    ("12_rasmiy_malumot", "RASMIY MA'LUMOT", NAVY, "ℹ️"),
    ("13_rasmiy_xabar", "RASMIY XABAR", NAVY, "✉️"),
    ("14_prezident", "MULOQOT KLUBI PREZIDENTI", GOLD, "👔"),
    ("15_travel", "MULOQOT TRAVEL", NAVY, "✈️"),
    ("16_volunteers", "MULOQOT VOLUNTEERS", NAVY, "🙋"),
    ("17_hamkorlik", "MULOQOT HAMKORLIK", NAVY, "🤝"),
]


def font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.truetype(FONT_FALLBACK, size)


def text_width(fnt, text: str, track: float) -> float:
    return sum(fnt.getlength(ch) for ch in text) + track * (len(text) - 1)


def banner(text: str, colors) -> tuple[Image.Image, Image.Image]:
    """Statik nishon va undagi harflar niqobi (nur harflar ustidan o'tmasligi uchun)."""
    top_c, bot_c, edge = colors
    fnt = font(60 * SS)
    track = 3 * SS
    tw = text_width(fnt, text, track)
    pad = 26 * SS
    tiles = max(1, math.ceil((tw + 2 * pad) / (T * SS)))
    W, H = tiles * T * SS, T * SS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # fon: yuqoridan pastga gradient (shisha kabi yaltiroq), yumaloq uchlar
    grad = np.linspace(0, 1, (BOT - TOP) * SS)[:, None]
    col = np.array(top_c) * (1 - grad) + np.array(bot_c) * grad
    fill = Image.fromarray(np.repeat(col[:, None, :], W, axis=1).astype(np.uint8), "RGB").convert("RGBA")
    mask = Image.new("L", (W, (BOT - TOP) * SS), 0)
    md = ImageDraw.Draw(mask)
    inset = 3 * SS
    md.rounded_rectangle((inset, 0, W - 1 - inset, (BOT - TOP) * SS - 1), radius=18 * SS, fill=255)
    img.paste(fill, (0, TOP * SS), mask)
    d = ImageDraw.Draw(img)
    # yuqori yarmida yumshoq shisha aksi
    gloss = Image.new("L", (W, (BOT - TOP) * SS), 0)
    gd = ImageDraw.Draw(gloss)
    gd.rounded_rectangle((inset + 6 * SS, 3 * SS, W - inset - 6 * SS, 30 * SS), radius=14 * SS, fill=46)
    gl = Image.new("RGBA", (W, (BOT - TOP) * SS), (255, 255, 255, 0))  # oq, shaffofligi — niqobdan
    gl.putalpha(Image.fromarray(np.minimum(np.asarray(gloss), np.asarray(mask))))
    img.alpha_composite(gl, (0, TOP * SS))
    # ingichka chekka (rangli) — qorong'i va yorug' Telegram fonida ham ajralib turadi
    d.rounded_rectangle((inset, TOP * SS, W - 1 - inset, BOT * SS - 1), radius=18 * SS, outline=(*edge, 255), width=3 * SS)
    # yozuv: markazda, oq, juda qalin
    tmask = Image.new("L", (W, H), 0)
    tdraw = ImageDraw.Draw(tmask)
    x = (W - tw) / 2
    asc, desc = fnt.getmetrics()
    bbox = fnt.getbbox("HMULOQOT")
    cap_h = bbox[3] - bbox[1]
    y = (TOP + BOT) / 2 * SS - cap_h / 2 - bbox[1]
    for ch in text:
        tdraw.text((x, y), ch, font=fnt, fill=255)
        x += fnt.getlength(ch) + track
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))  # harf ostida 2px soya — kichik o'lchamda ajralib turadi
    sh_alpha = Image.new("L", (W, H), 0)
    sh_alpha.paste(tmask.point(lambda v: v * (90 / 255)), (0, 2 * SS))
    shadow.putalpha(sh_alpha)
    img.alpha_composite(shadow)
    img.paste(Image.new("RGBA", (W, H), (255, 255, 255, 255)), (0, 0), tmask)
    small = img.resize((W // SS, H // SS), Image.Resampling.LANCZOS)
    tm_small = tmask.resize((W // SS, H // SS), Image.Resampling.LANCZOS)
    return small, tm_small


def frames_for(base: Image.Image, tmask: Image.Image) -> list[Image.Image]:
    """Yaltiroq nur faqat fon bo'ylab o'tadi (1.3 s), keyin chekkada oltin uchqun yuguradi."""
    w = base.width
    arr0 = np.asarray(base).astype(np.float32)
    alpha = arr0[..., 3] / 255.0
    textm = np.asarray(tmask).astype(np.float32) / 255.0
    bg_only = alpha * (1 - textm)
    ys, xs = np.mgrid[0:T, 0:w]
    frames = []
    for i in range(N):
        t = i / FPS
        arr = arr0.copy()
        p = (t - 0.2) / 1.3
        if 0 <= p <= 1:
            c = -80 + (1 - (1 - p) ** 2) * (w + 160)
            dist = (xs + (ys - T / 2) * 0.6) - c
            band = np.exp(-(dist / 18.0) ** 2) * 0.55 + np.exp(-((dist + 34) / 7.0) ** 2) * 0.3
            a = band * bg_only
            for ch in range(3):
                arr[..., ch] = arr[..., ch] * (1 - a) + 255 * a
        frames.append(Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA"))
    return frames


def encode(frames: list[Image.Image], dst: Path) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        for i, f in enumerate(frames):
            f.save(Path(tmp) / f"{i:03d}.png")
        for crf in (12, 16, 20, 26, 32):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(Path(tmp) / "%03d.png"),
                            "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", str(crf),
                            "-auto-alt-ref", "0", "-deadline", "good", "-cpu-used", "1", "-row-mt", "1",
                            "-an", str(dst)], check=True)
            if dst.stat().st_size <= 250_000:
                break
    return dst.stat().st_size


def logo_frames() -> list[Image.Image]:
    """Alohida emoji: klub logotipi (oq doira ichida), sekin «nafas oladi»."""
    mark = ROOT / "assets" / "logo_mark.png"  # yangi logo belgisi (shaffof fon) — tools/apply_new_logo.py
    if mark.exists():
        src = Image.open(mark).convert("RGBA")
    else:
        src = Image.open(ROOT / "assets" / "logo.png").convert("RGBA")
        side = min(src.size)
        src = src.crop(((src.width - side) // 2, 0, (src.width + side) // 2, side))  # daraxt + gerb qismi
    out = []
    for i in range(N):
        t = i / FPS
        s = 1 + 0.035 * math.sin(2 * math.pi * t / (N / FPS))
        big = Image.new("RGBA", (T * SS, T * SS), (0, 0, 0, 0))
        d = ImageDraw.Draw(big)
        r = 47 * SS * s
        c = 50 * SS
        d.ellipse((c - r, c - r, c + r, c + r), fill=(255, 255, 255, 255), outline=(*NAVY[1], 255), width=4 * SS)
        lg = src.resize((int(80 * SS * s),) * 2, Image.Resampling.LANCZOS)
        big.alpha_composite(lg, (int(c - lg.width / 2), int(c - lg.height / 2)))
        out.append(big.resize((T, T), Image.Resampling.LANCZOS))
    return out


def main() -> None:
    if OUT.exists():
        for p in OUT.iterdir():
            if p.is_dir():
                shutil.rmtree(p)
    OUT.mkdir(parents=True, exist_ok=True)
    sheet, biggest, count = [], 0, 0
    for name, text, colors, _emoji in ITEMS:
        base, tm = banner(text, colors)
        frames = frames_for(base, tm)
        folder = OUT / name
        folder.mkdir(exist_ok=True)
        tiles = base.width // T
        for k in range(tiles):
            biggest = max(biggest, encode([f.crop((k * T, 0, (k + 1) * T, T)) for f in frames], folder / f"{k + 1:02d}.webm"))
            count += 1
        sheet.append((text, frames))
        print(f"{text}: {tiles} bo'lak")
    lf = logo_frames()
    (OUT / "18_logo").mkdir(exist_ok=True)
    biggest = max(biggest, encode(lf, OUT / "18_logo" / "01.webm"))
    count += 1
    print(f"tayyor: {count} ta emoji, eng kattasi {biggest // 1024} KB")

    # ---- namuna: Telegram'dagi kabi kichik (24px) va katta ko'rinish ----
    def preview(fi: int) -> Image.Image:
        Wd = 1500
        rows = len(sheet) + 1
        pv = Image.new("RGB", (Wd, 90 + rows * 64), (240, 242, 246))
        d = ImageDraw.Draw(pv)
        d.text((30, 22), "MULOQOT premium emoji — tiniq (2-avlod)", font=font(30), fill=NAVY[1])
        d.text((30, 60), "chapda: chatdagi haqiqiy o'lcham (24px)   ·   o'ngda: kattalashtirilgan", font=ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 18), fill=(90, 100, 120))
        y = 96
        for text, frames in sheet:
            f = frames[fi]
            sm = f.resize((f.width * 24 // T, 24), Image.Resampling.LANCZOS)
            pv.paste(sm, (30, y + 14), sm)
            bg = f.resize((f.width * 56 // T, 56), Image.Resampling.LANCZOS)
            pv.paste(bg, (360, y), bg)
            y += 64
        lg = lf[fi].resize((56, 56), Image.Resampling.LANCZOS)
        pv.paste(lf[fi].resize((24, 24), Image.Resampling.LANCZOS), (30, y + 14), lf[fi].resize((24, 24), Image.Resampling.LANCZOS))
        pv.paste(lg, (360, y), lg)
        return pv
    preview(0).save(OUT / "namuna.png")
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(N):
            preview(i).save(Path(tmp) / f"{i:03d}.png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(Path(tmp) / "%03d.png"),
                        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                        str(OUT / "namuna.mp4")], check=True)
    print("namuna:", OUT / "namuna.png")


if __name__ == "__main__":
    main()

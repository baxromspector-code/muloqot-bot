"""Animatsiyali rasmiy emoji to'plami (MULOQOT · KIUT) — Telegram video emoji (WEBM/VP9, 100×100, alfa kanal).

Nishonlar make_official_emoji.py dagi bilan bir xil; ustiga harakat qo'shiladi:
  • yaltiroq nur nishon bo'ylab chapdan o'ngga o'tadi (bo'laklar bir-biriga ulanib ketadi);
  • gerb «yurak urishi» kabi kattalashadi, halqasi bo'ylab nur aylanadi;
  • burchaklarda yulduzchalar chaqnaydi; DIQQAT — qizil chegara pulsi;
  • belgilar: ✔ chiziladi, ❗ silkinadi, ℹ nuqtasi sakraydi.
Hammasi uzluksiz aylanadi (loop), 2.9 s, 30 fps.

    python tools/make_animated_emoji.py
Natija: dizayn/emoji_anim/<to'plam>/NN.webm  +  dizayn/emoji-anim-namuna.mp4 (ko'rib chiqish uchun)
"""
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import cards  # noqa: E402
import make_official_emoji as off  # noqa: E402

OUT = ROOT / "dizayn" / "emoji_anim"
T = off.T
FPS = 30
N = 87                      # 2.9 s (Telegram: ≤ 3 s)
SS = 4                      # supersampling
DEEP, GOLD, WHITE = off.DEEP, off.GOLD, off.WHITE
RED, GREEN = (170, 30, 40), (20, 110, 60)


# ---------------------------------------------------------------- yordamchilar
def ease_out(x: float) -> float:
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def bump(t: float, start: float, dur: float) -> float:
    """0→1→0 silliq tepalik (start..start+dur soniya)."""
    x = (t - start) / dur
    return math.sin(math.pi * x) ** 2 if 0 <= x <= 1 else 0.0


def hi(w: int, h: int = T) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def down(img: Image.Image) -> Image.Image:
    return img.resize((img.width // SS, img.height // SS), Image.Resampling.LANCZOS)


def star(d: ImageDraw.ImageDraw, cx: float, cy: float, r: float, color) -> None:
    """To'rt qirrali yulduzcha (SS koordinatada)."""
    k = r * 0.22
    pts = [(cx, cy - r), (cx + k, cy - k), (cx + r, cy), (cx + k, cy + k),
           (cx, cy + r), (cx - k, cy + k), (cx - r, cy), (cx - k, cy - k)]
    d.polygon(pts, fill=color)


def shine(base: Image.Image, t: float, color, strength: float, t0: float = 0.25, t1: float = 1.35) -> Image.Image:
    """Diagonal yaltiroq nur — faqat nishon ustida (base alfa bo'yicha)."""
    if not (t0 <= t <= t1):
        return base.copy()
    w = base.width
    p = ease_out((t - t0) / (t1 - t0)) * 0.85 + (t - t0) / (t1 - t0) * 0.15
    c = -60 + p * (w + 120)
    ys, xs = np.mgrid[0:T, 0:w]
    dist = (xs + (ys - T / 2) * 0.55) - c
    band = np.exp(-(dist / 16.0) ** 2) * 0.9 + np.exp(-((dist + 30) / 6.0) ** 2) * 0.45
    arr = np.asarray(base).astype(np.float32)
    a = band * (arr[..., 3] / 255.0) * strength
    for ch in range(3):
        arr[..., ch] = arr[..., ch] * (1 - a) + color[ch] * a
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")


def emblem_anim(frame: Image.Image, base: Image.Image, t: float, ring_r: int) -> None:
    """Gerb: yurak urishi (1.0→1.07) + halqa bo'ylab aylanuvchi nur."""
    s = 1 + 0.07 * bump(t, 0.0, 0.42) + 0.04 * bump(t, 0.42, 0.34)
    R = ring_r + 3
    patch = base.crop((T // 2 - R, T // 2 - R, T // 2 + R, T // 2 + R))
    mask = Image.new("L", (R * 2 * SS, R * 2 * SS), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, R * 2 * SS - 1, R * 2 * SS - 1), fill=255)
    mask = mask.resize((R * 2, R * 2), Image.Resampling.LANCZOS)
    patch.putalpha(Image.fromarray(np.minimum(np.asarray(patch.getchannel("A")), np.asarray(mask))))
    if s > 1.001:
        size = round(R * 2 * s)
        big = patch.resize((size, size), Image.Resampling.LANCZOS)
        frame.alpha_composite(big, (T // 2 - size // 2, T // 2 - size // 2))
    # aylanuvchi nur (halqa ustida) — bir aylanish = bitta loop, uzluksiz
    lay, d = hi(T)
    ang = -90 + 360 * t / (N / FPS)
    rr = ring_r * s * SS
    cx = cy = T // 2 * SS
    for i in range(14):
        a0 = ang - i * 6
        alpha = int(235 * (1 - i / 14) ** 1.6)
        d.arc((cx - rr, cy - rr, cx + rr, cy + rr), a0 - 6, a0, fill=(255, 255, 255, alpha), width=int(2.6 * SS))
    frame.alpha_composite(down(lay))


# ---------------------------------------------------------------- nishonlar
# nomi: (nishon yasovchi, uslub, gerb halqa radiusi yoki None)
SETS = {name: make for name, (make, _) in off.SETS.items()}
STYLE = {
    "01_assalomu_alaykum": ("light", 33), "02_xush_kelibsiz": ("light", 33), "03_muloqot": ("light", 33),
    "04_universitet": ("dark", 34), "05_klub": ("dark", 33),
    "06_elon": ("dark", None), "07_tadbir": ("dark", None), "08_azolik": ("dark", None),
    "09_murojaat": ("dark", None), "10_hujjatlar": ("dark", None),
    "11_diqqat": ("alert", None), "12_tasdiqlandi": ("ok", None), "13_rahmat": ("light", None),
}


def banner_frames(name: str) -> list[Image.Image]:
    base = SETS[name]()
    style, ring = STYLE[name]
    w = base.width
    color, strength = {"light": (GOLD, 0.75), "dark": ((255, 255, 255), 0.55),
                       "alert": ((255, 120, 120), 0.6), "ok": ((80, 200, 130), 0.6)}[style]
    lead = T if ring else 0
    sparkles = [  # (x, y, boshlanish, radius)
        (w - 13, off.TOP + 1, 1.30, 12),
        (lead + 18, off.BOTTOM - 1, 1.62, 10),
        (w * 0.62, off.TOP, 1.95, 8),
    ]
    frames = []
    for i in range(N):
        t = i / FPS
        fr = shine(base, t, color, strength)
        if ring:
            emblem_anim(fr, base, t, ring)
        lay, d = hi(w)
        if style == "alert":  # qizil chegara pulsi — ikki marta
            p = max(bump(t, 1.5, 0.5), bump(t, 2.05, 0.5))
            if p:
                g = int(4 * p * SS)
                d.rounded_rectangle((2 * SS - g, off.TOP * SS - g, (w - 3) * SS + g, off.BOTTOM * SS + g),
                                    radius=10 * SS, outline=(*RED, int(200 * p)), width=int(3 * SS))
        for sx, sy, st, sr in sparkles:
            p = bump(t, st, 0.45)
            if p:
                star(d, sx * SS, sy * SS, sr * p * SS, (255, 255, 255, int(255 * p)))
                star(d, sx * SS, sy * SS, sr * p * 0.55 * SS, (*GOLD, int(255 * p)))
        fr.alpha_composite(down(lay))
        frames.append(fr)
    return frames


# ---------------------------------------------------------------- alohida belgilar
def circle_icon(t: float, kind: str) -> Image.Image:
    pop = 1 + 0.08 * bump(t, 0.0, 0.35)
    lay, d = hi(T)
    c, r = 50 * SS, 44 * SS * pop
    d.ellipse((c - r, c - r, c + r, c + r), fill=(*DEEP, 255), outline=(255, 255, 255, 255), width=3 * SS)
    if kind == "check":  # chiziladi, turadi, oxirida so'nadi
        draw = ease_out((t - 0.15) / 0.45)
        fade = 1 - ease_out((t - 2.55) / 0.3)
        pts = [(28, 52), (44, 68), (73, 35)]
        seg1 = math.dist(pts[0], pts[1])
        total = seg1 + math.dist(pts[1], pts[2])
        L = draw * total
        path = [pts[0]]
        if L <= seg1:
            path.append(tuple(pts[0][k] + (pts[1][k] - pts[0][k]) * L / seg1 for k in range(2)))
        else:
            q = (L - seg1) / (total - seg1)
            path += [pts[1], tuple(pts[1][k] + (pts[2][k] - pts[1][k]) * q for k in range(2))]
        if draw > 0 and fade > 0:
            sp = [((x - 50) * pop * SS + c, (y - 50) * pop * SS + c) for x, y in path]
            col = (255, 255, 255, int(255 * fade))
            d.line(sp, fill=col, width=int(10 * SS * pop), joint="curve")
            for x, y in (sp[0], sp[-1]):
                rr = 5 * SS * pop
                d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=col)
    elif kind == "warn":  # silkinish
        ang = math.sin(t * 2 * math.pi * 6) * 9 * bump(t, 0.9, 0.7)
        sub, sd = hi(T)
        sd.rounded_rectangle((44 * SS, 22 * SS, 56 * SS, 60 * SS), radius=5 * SS, fill=WHITE)
        sd.ellipse((43 * SS, 66 * SS, 57 * SS, 80 * SS), fill=WHITE)
        lay.alpha_composite(sub.rotate(ang, resample=Image.Resampling.BICUBIC, center=(c, c)))
    elif kind == "info":  # nuqta sakraydi
        jump = -10 * bump(t, 0.9, 0.5) + 2 * bump(t, 1.4, 0.2)
        y0 = (20 + jump) * SS
        d.ellipse((43 * SS, y0, 57 * SS, y0 + 14 * SS), fill=WHITE)
        squash = 1 - 0.08 * bump(t, 1.35, 0.25)
        d.rounded_rectangle((44 * SS, (80 - 40 * squash) * SS, 56 * SS, 80 * SS), radius=5 * SS, fill=WHITE)
    img = down(lay)
    img = shine(img, t, (255, 255, 255), 0.35, 1.3, 2.2)
    return img


def icon_frames(kind: str) -> list[Image.Image]:
    if kind in ("check", "warn", "info"):
        return [circle_icon(i / FPS, kind) for i in range(N)]
    base = off.icon(kind)
    frames = []
    for i in range(N):
        t = i / FPS
        if kind == "muloqot":
            fr = Image.new("RGBA", (T, T), (0, 0, 0, 0))
            fr.alpha_composite(base)
            emblem_anim(fr, base, t, 47)
        else:  # kiut qalqoni: yengil tebranish + nur
            dy = math.sin(2 * math.pi * t / (N / FPS)) * 2.5
            fr = Image.new("RGBA", (T, T), (0, 0, 0, 0))
            fr.alpha_composite(shine(base, t, (255, 255, 255), 0.6, 0.4, 1.5), (0, round(dy)))
        frames.append(fr)
    return frames


# ---------------------------------------------------------------- yozish
def encode(frames: list[Image.Image], dst: Path) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        for i, f in enumerate(frames):
            f.save(Path(tmp) / f"{i:03d}.png")
        for crf in (30, 36, 42, 50):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(Path(tmp) / "%03d.png"),
                            "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", str(crf),
                            "-deadline", "good", "-row-mt", "1", "-an", str(dst)], check=True)
            if dst.stat().st_size <= 250_000:
                break
    return dst.stat().st_size


def main() -> None:
    if OUT.exists():  # ids.json (yuklangan to'plam ID lari) saqlanadi
        for d in OUT.iterdir():
            if d.is_dir():
                shutil.rmtree(d)
    sheets: list[tuple[str, list[Image.Image]]] = []
    count, biggest = 0, 0
    for name in SETS:
        frames = banner_frames(name)
        sheets.append((name, frames))
        folder = OUT / name
        folder.mkdir(parents=True, exist_ok=True)
        for k in range(frames[0].width // T):
            tiles = [f.crop((k * T, 0, (k + 1) * T, T)) for f in frames]
            biggest = max(biggest, encode(tiles, folder / f"{k + 1:02d}.webm"))
            count += 1
        print(name, frames[0].width // T, "bo'lak")
    icon_dir = OUT / "14_belgilar"
    icon_dir.mkdir(exist_ok=True)
    icons = []
    for i, k in enumerate(off.ICONS, 1):
        frames = icon_frames(k)
        icons.append(frames)
        biggest = max(biggest, encode(frames, icon_dir / f"{i:02d}_{k}.webm"))
        count += 1
    print(f"tayyor: {count} ta video emoji, eng kattasi {biggest // 1024} KB -> {OUT}")

    # ---------- ko'rib chiqish videosi (oq fon, 2x) ----------
    Z = 2
    W = 1600
    H = 60 + (len(sheets) + 1) * 112 + 40
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(N * 2):
            fi = i % N
            pv = Image.new("RGB", (W, H), (236, 240, 245))
            d = ImageDraw.Draw(pv)
            d.text((40, 18), "MULOQOT · KIUT — animatsiyali emoji to'plami", font=cards.font(30, True), fill=DEEP)
            for r, (name, frames) in enumerate(sheets):
                f = frames[fi]
                big = f.resize((f.width * Z // 2 + f.width // 2, T * Z // 2 + T // 2), Image.Resampling.LANCZOS)
                pv.paste(big, (40, 66 + r * 112), big)
            for j, frames in enumerate(icons):
                big = frames[fi].resize((150, 150), Image.Resampling.LANCZOS)
                pv.paste(big, (40 + j * 170, 66 + len(sheets) * 112 - 10), big)
            pv.save(Path(tmp) / f"{i:03d}.png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(Path(tmp) / "%03d.png"),
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
                        str(ROOT / "dizayn" / "emoji-anim-namuna.mp4")], check=True)
    print("namuna: dizayn/emoji-anim-namuna.mp4")


if __name__ == "__main__":
    main()

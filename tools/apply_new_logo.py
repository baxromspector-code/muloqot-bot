"""Yangi logotipni (Islom aka, 2026-11-20) loyihaning barcha joylariga qo'yadi.

    python tools/apply_new_logo.py <logo.jpg|png>

Yaratiladi / yangilanadi:
  assets/logo.png            — to'liq logo (daraxt + gerb + «MULOQOT»): guvohnoma, chipta, kartalar
  assets/logo_mark.png       — faqat belgi (daraxt + gerb, yozuvsiz), shaffof fon: dumaloq joylar uchun
  admin_site/static/logo.png — sayt, admin panel, Mini App, favicon (oq kvadrat, belgi markazda)
  admin_site/static/miniapp/logo-bg.webp — Mini App fonidagi xira logo
  assets/banner.png          — botdagi salomlashish banneri (logo qutisi va rangli chiziqlar)
  ../admin_video/public/logo.png — bot avatar/intro videolari (Remotion) uchun
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
WHITE_T = 238  # bundan oq piksel — fon


def to_alpha(img: Image.Image) -> Image.Image:
    """Oq fonni shaffof qiladi (yumshoq chekka bilan), ranglarni fon aralashmasidan tozalaydi."""
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    bg = np.array([255, 255, 255], np.float32)
    d = np.clip((bg - a) / bg, 0, 1).max(axis=2)
    alpha = np.clip((d - 0.03) / 0.35, 0, 1)
    safe = np.maximum(alpha, 1e-3)[..., None]
    rgb = np.clip((a - bg * (1 - safe)) / safe, 0, 255)
    return Image.fromarray(np.dstack([rgb, alpha * 255]).astype(np.uint8), "RGBA")


def text_top(img: Image.Image) -> int:
    """«MULOQOT» yozuvi boshlanadigan qator: pastki 45% dagi eng katta oq oraliqdan keyin."""
    g = np.asarray(img.convert("L"))
    ink = (g < WHITE_T).sum(axis=1)
    h = len(ink)
    best, run, gap_end = 0, 0, int(h * 0.8)
    for y in range(int(h * 0.55), h):
        if ink[y] <= 2:
            run += 1
        else:
            if run > best:        # faqat ortidan yana rasm keladigan oraliq (ildiz ↔ yozuv), pastki hoshiya emas
                best, gap_end = run, y
            run = 0
    return gap_end


def bbox(img: Image.Image, y1: int) -> tuple[int, int, int, int]:
    g = np.asarray(img.convert("L"))[:y1]
    ys, xs = np.where(g < WHITE_T)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def main(src_path: str) -> None:
    src = Image.open(src_path).convert("RGB")
    full = ROOT / "assets" / "logo.png"
    src.save(full, optimize=True)

    ty = text_top(src)
    x0, y0, x1, y1 = bbox(src, ty - 4)
    mark = src.crop((x0, y0, x1, y1))
    side = max(mark.size)
    sq = Image.new("RGB", (side, side), (255, 255, 255))
    sq.paste(mark, ((side - mark.width) // 2, (side - mark.height) // 2))
    to_alpha(sq).resize((1024, 1024), Image.Resampling.LANCZOS).save(ROOT / "assets" / "logo_mark.png", optimize=True)
    print(f"yozuv {ty}-qatordan boshlanadi; belgi: {mark.size}")

    # sayt / ilova / favicon: oq kvadrat, belgi 84% (doira ichida kesilmasligi uchun chetdan joy)
    web = Image.new("RGB", (512, 512), (255, 255, 255))
    m = to_alpha(sq).resize((430, 430), Image.Resampling.LANCZOS)
    web.paste(m, (41, 41), m)
    web.save(ROOT / "admin_site" / "static" / "logo.png", optimize=True)
    vid = ROOT.parent / "admin_video" / "public" / "logo.png"
    if vid.parent.exists():
        web.save(vid, optimize=True)

    # Mini App foni: to'liq logo, shaffof
    bgw = to_alpha(src)
    bgw = bgw.resize((540, round(540 * bgw.height / bgw.width)), Image.Resampling.LANCZOS)
    bgw.save(ROOT / "admin_site" / "static" / "miniapp" / "logo-bg.webp", "WEBP", quality=72, method=6)
    print("logo-bg.webp:", bgw.size)

    # bot banneri: logo qutisi va rangli chiziqlar (yangi logo ranglari: ko'k · oltin · zangori)
    bpath = ROOT / "assets" / "banner.png"
    ban = Image.open(bpath).convert("RGB")
    d = ImageDraw.Draw(ban)
    box = (107, 106, 474, 535)
    d.rounded_rectangle(box, radius=28, fill=(255, 255, 255))
    full_rgba = to_alpha(src)
    bw, bh = box[2] - box[0] - 40, box[3] - box[1] - 40
    k = min(bw / full_rgba.width, bh / full_rgba.height)
    fl = full_rgba.resize((round(full_rgba.width * k), round(full_rgba.height * k)), Image.Resampling.LANCZOS)
    ban.paste(fl, (box[0] + (box[2] - box[0] - fl.width) // 2, box[1] + (box[3] - box[1] - fl.height) // 2), fl)
    for (bx0, bx1), col in zip(((566, 657), (676, 767), (786, 877)), ((36, 104, 200), (212, 166, 58), (38, 150, 148))):
        d.rectangle((bx0, 450, bx1, 460), fill=col)
    ban.save(bpath, optimize=True)
    print("tayyor")


if __name__ == "__main__":
    main(sys.argv[1])

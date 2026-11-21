"""Rasmiy emoji to'plamini Telegram'ga yuklash (Bot API createNewStickerSet).

To'plam egasi — OWNER_ID foydalanuvchi (u botni /start qilgan bo'lishi shart).
To'plam nomi Telegram talabi bo'yicha «..._by_<bot_username>» bilan tugaydi.

    python tools/upload_emoji.py          # statik  (dizayn/emoji_rasmiy, *.png)
    python tools/upload_emoji.py --anim   # animatsiyali (dizayn/emoji_anim, *.webm)
Natija: t.me/addemoji/<nom> havolasi va <papka>/ids.json (bot uchun custom_emoji_id lar).
"""
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aiogram import Bot  # noqa: E402
from aiogram.exceptions import TelegramBadRequest  # noqa: E402
from aiogram.types import FSInputFile, InputSticker  # noqa: E402

from config import ADMIN_IDS, BOT_TOKEN  # noqa: E402

ANIM = "--anim" in sys.argv
SRC = ROOT / "dizayn" / ("emoji_anim" if ANIM else "emoji_rasmiy")
EXT, FORMAT = ("webm", "video") if ANIM else ("png", "static")
OWNER_ID = 7089836188 if 7089836188 in ADMIN_IDS else sorted(ADMIN_IDS)[0]  # to'plam egasi — bot egasi
SHORT = "muloqot_anim" if ANIM else "muloqot_kiut"
TITLE = "MULOQOT · KIUT — animatsiyali" if ANIM else "MULOQOT · KIUT — rasmiy"

# Har bir papka bo'laklariga mos emoji (qidiruvda shu emoji orqali topiladi)
EMOJI = {
    "01_assalomu_alaykum": "👋", "02_xush_kelibsiz": "🤝", "03_muloqot": "🌐", "04_universitet": "🏛",
    "05_klub": "🌍", "06_elon": "📢", "07_tadbir": "📅", "08_azolik": "🪪", "09_murojaat": "✉️",
    "10_hujjatlar": "📄", "11_diqqat": "⚠️", "12_tasdiqlandi": "✅", "13_rahmat": "🙏",
}
ICON_EMOJI = {"muloqot": "🌳", "kiut": "🎓", "check": "✔️", "warn": "❗", "info": "ℹ️"}


def collect() -> list[tuple[Path, str]]:
    items = []
    for folder in sorted(p for p in SRC.iterdir() if p.is_dir()):
        for f in sorted(folder.glob(f"*.{EXT}")):
            if folder.name in EMOJI:
                items.append((f, EMOJI[folder.name]))
            else:  # 14_belgilar/01_muloqot.png
                items.append((f, ICON_EMOJI.get(f.stem.split("_", 1)[1], "⭐")))
    return items


def sticker(path: Path, emoji: str) -> InputSticker:
    return InputSticker(sticker=FSInputFile(path), format=FORMAT, emoji_list=[emoji],
                        keywords=["muloqot", "kiut", path.parent.name.split("_", 1)[-1]])


async def main() -> None:
    bot = Bot(BOT_TOKEN)
    me = await bot.get_me()
    name = f"{SHORT}_by_{me.username}"
    items = collect()
    print(f"{len(items)} ta emoji, egasi {OWNER_ID}, nom: {name}")
    try:
        try:
            existing = await bot.get_sticker_set(name)
            print(f"To'plam allaqachon bor ({len(existing.stickers)} ta) — yangidan yaratish uchun avval o'chiring.")
            return
        except TelegramBadRequest:
            pass
        first, rest = items[:50], items[50:]
        await bot.create_new_sticker_set(user_id=OWNER_ID, name=name, title=TITLE,
                                         stickers=[sticker(p, e) for p, e in first], sticker_type="custom_emoji")
        print(f"yaratildi: {len(first)} ta")
        for p, e in rest:
            await bot.add_sticker_to_set(user_id=OWNER_ID, name=name, sticker=sticker(p, e))
        print(f"qo'shildi: {len(rest)} ta")

        st = await bot.get_sticker_set(name)
        ids = {}
        for (p, _), s in zip(items, st.stickers):
            ids.setdefault(p.parent.name, []).append(s.custom_emoji_id)
        (SRC / "ids.json").write_text(json.dumps({"set": name, "emoji": ids}, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
        print(f"jami to'plamda: {len(st.stickers)} ta")
        print(f"havola: https://t.me/addemoji/{name}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

"""Tiniq premium emoji to'plamini (dizayn/emoji_premium) Telegram'ga yuklash — @KIUT_muloqotbot nomidan.

    python tools/upload_premium_emoji.py
Natija: t.me/addemoji/muloqot_by_KIUT_muloqotbot va dizayn/emoji_premium/ids.json
(bot tugmalaridagi belgilar shu fayldan olinadi: keyboards.py, «19_belgilar»).
"""
import asyncio
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from aiogram import Bot  # noqa: E402
from aiogram.exceptions import TelegramBadRequest  # noqa: E402
from aiogram.types import FSInputFile, InputSticker  # noqa: E402

from config import BOT_TOKEN  # noqa: E402
import make_premium_emoji as pe  # noqa: E402

SRC = ROOT / "dizayn" / "emoji_premium"
OWNER_ID = 7089836188
SHORT, TITLE = "muloqot", "MULOQOT · KIUT"
ICONS = ["muloqot", "kiut", "check", "warn", "info"]          # bot tugmalari shu tartibda o'qiydi
ICON_EMOJI = {"muloqot": "🌳", "kiut": "🎓", "check": "✔️", "warn": "❗", "info": "ℹ️"}
EMOJI = {name: e for name, _t, _c, e in pe.ITEMS}
SKIP = {"18_logo"}                                             # logo belgilar ichida (muloqot) bor


def prepare_icons() -> Path:
    """Bot tugmalari uchun 5 ta belgi (eski to'plamdagi chizmalar — matnsiz, xiralik muammosi yo'q)."""
    dst = SRC / "19_belgilar"
    dst.mkdir(exist_ok=True)
    old = ROOT / "dizayn" / "emoji_anim" / "14_belgilar"
    for i, k in enumerate(ICONS, 1):
        shutil.copy(old / f"{i:02d}_{k}.webm", dst / f"{i:02d}_{k}.webm")
    return dst


def collect() -> list[tuple[Path, str, str]]:
    items = []
    for folder in sorted(p for p in SRC.iterdir() if p.is_dir() and p.name not in SKIP):
        for f in sorted(folder.glob("*.webm")):
            if folder.name == "19_belgilar":
                k = f.stem.split("_", 1)[1]
                items.append((f, ICON_EMOJI[k], k))
            else:
                items.append((f, EMOJI[folder.name], folder.name.split("_", 1)[1]))
    return items


def sticker(path: Path, emoji: str, kw: str) -> InputSticker:
    return InputSticker(sticker=FSInputFile(path), format="video", emoji_list=[emoji],
                        keywords=["muloqot", "kiut", kw.replace("_", " ")])


async def main() -> None:
    prepare_icons()
    bot = Bot(BOT_TOKEN)
    try:
        me = await bot.get_me()
        name = f"{SHORT}_by_{me.username}"
        items = collect()
        print(f"{len(items)} ta emoji, egasi {OWNER_ID}, nom: {name}")
        try:
            st = await bot.get_sticker_set(name)
            print(f"To'plam allaqachon bor ({len(st.stickers)} ta) — to'xtatildi.")
            return
        except TelegramBadRequest:
            pass
        first, rest = items[:50], items[50:]
        await bot.create_new_sticker_set(user_id=OWNER_ID, name=name, title=TITLE,
                                         stickers=[sticker(*x) for x in first], sticker_type="custom_emoji")
        print(f"yaratildi: {len(first)} ta")
        for i, x in enumerate(rest, 1):
            for attempt in range(4):
                try:
                    await bot.add_sticker_to_set(user_id=OWNER_ID, name=name, sticker=sticker(*x))
                    break
                except Exception as e:  # Telegram limiti — kutib qayta urinamiz
                    wait = getattr(e, "retry_after", 3 * (attempt + 1))
                    print("  qayta urinish:", x[0].parent.name, x[0].name, e)
                    await asyncio.sleep(wait)
            if i % 10 == 0:
                print(f"  qo'shildi: {i}/{len(rest)}")
        st = await bot.get_sticker_set(name)
        ids: dict[str, list[str]] = {}
        for (p, _e, _k), s in zip(items, st.stickers):
            ids.setdefault(p.parent.name, []).append(s.custom_emoji_id)
        (SRC / "ids.json").write_text(json.dumps({"set": name, "emoji": ids}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"jami to'plamda: {len(st.stickers)} ta (kutilgan {len(items)})")
        print(f"havola: https://t.me/addemoji/{name}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

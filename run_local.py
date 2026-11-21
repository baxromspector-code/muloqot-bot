"""PostgreSQL o'rnatilmagan kompyuterda botni sinash uchun.

Ichki PostgreSQL (pgserver) ni ./pgdata papkasida ishga tushiradi va botni unga ulaydi.
Ma'lumotlar ./pgdata da saqlanadi va qayta ishga tushirganda yo'qolmaydi.

    pip install pgserver
    python run_local.py

Serverda (production) buning o'rniga oddiy PostgreSQL yoki docker compose ishlating.
"""
import asyncio
import os
from pathlib import Path

import pgserver

BASE = Path(__file__).resolve().parent
# cleanup_mode=None: bot to'xtasa ham PostgreSQL ishlab turadi (keskin o'chib, tiklanishga tushmasligi uchun);
# keyingi ishga tushirishda o'sha server qayta ishlatiladi.
server = pgserver.get_server(BASE / "pgdata", cleanup_mode=None)
os.environ["DATABASE_URL"] = server.get_uri()

import bot  # noqa: E402  (DATABASE_URL o'rnatilgandan keyin import qilinadi)

if __name__ == "__main__":
    if (BASE / ".env").exists() and any(l.strip() == "HOSTED=render" for l in (BASE / ".env").read_text(encoding="utf-8").splitlines()):
        raise SystemExit("HOSTED=render: bot Render'da ishlaydi. Noutbukda yoqsangiz Render'dagi webhook o'chadi. "
                         "Qaytarish uchun .env dan HOSTED=render qatorini olib tashlang.")
    print(f"PostgreSQL: {server.get_uri()}")
    asyncio.run(bot.main())

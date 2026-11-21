"""Admin saytini bot bilan bir xil ichki PostgreSQL (pgserver, ./pgdata) ga ulab ishga tushiradi.

    python run_admin_local.py      # http://127.0.0.1:8080
"""
import os
from pathlib import Path

import pgserver

BASE = Path(__file__).resolve().parent
server = pgserver.get_server(BASE / "pgdata", cleanup_mode=None)
os.environ["DATABASE_URL"] = server.get_uri()
# Windows'da sayt bitta jarayonda ishlaydi: ko'p jarayonli uvicorn u yerda select() tsikliga o'tadi va
# 512 dan ortiq bir vaqtdagi ulanishda qulaydi (yuklama sinovida tasdiqlangan). Linux serverda ADMIN_WORKERS=4.
os.environ.setdefault("ADMIN_WORKERS", "1" if os.name == "nt" else str(min(4, os.cpu_count() or 1)))

from admin_site.app import main  # noqa: E402

if __name__ == "__main__":
    main()

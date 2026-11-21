"""Shu kompyuterdagi bazani (pgserver, ./pgdata) serverga ko'chirish uchun SQL faylga saqlaydi.

    python tools/export_db.py            ->  muloqot-backup.sql

Faylda foydalanuvchilar, arizalar, tadbirlar, e'lonlar va rasmlar bor — uni hech kimga bermang.
Serverda tiklash: DEPLOY.md, 6-qadam.
"""
import subprocess
import sys
from pathlib import Path

import pgserver

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "muloqot-backup.sql"

server = pgserver.get_server(ROOT / "pgdata", cleanup_mode=None)
pg_dump = Path(pgserver.__file__).parent / "pginstall" / "bin" / ("pg_dump.exe" if sys.platform == "win32" else "pg_dump")
cmd = [str(pg_dump), "--no-owner", "--no-privileges", "--clean", "--if-exists", "--dbname", server.get_uri(),
       "--file", str(OUT)]
subprocess.run(cmd, check=True)
print(f"Saqlandi: {OUT} ({OUT.stat().st_size // 1024} KB)")

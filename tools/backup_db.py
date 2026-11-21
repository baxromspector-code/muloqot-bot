"""Bazaning kunlik zaxirasi (pg_dump, siqilgan «custom» format) — 14 kun saqlanadi.

Avtomatik: bot ishlab turganda rejalashtiruvchi (scheduler.py) har 5 daqiqada tekshiradi va oxirgi zaxiradan
24 soat o'tgan bo'lsa yangisini oladi (kompyuter tunda o'chiq bo'lsa ham, yoqilgach birinchi imkonda).

Qo'lda:
    python tools/backup_db.py            # hozir zaxira olish (24 soat o'tmagan bo'lsa ham)
    python tools/backup_db.py --list     # mavjud zaxiralar

Zaxira papkasi: BACKUP_DIR (.env) yoki %USERPROFILE%\\MULOQOT_zaxira — loyiha papkasidan TASHQARIDA,
loyiha papkasi o'chsa ham zaxira qoladi.

Tiklash (EHTIYOT: hozirgi ma'lumotlar zaxiradagisi bilan almashtiriladi; avval bot va saytni to'xtating):
    pg_restore --clean --if-exists --no-owner -d "<DATABASE_URL>" "<zaxira fayli>"
"""
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

KEEP_DAYS = 14
MIN_KEEP = 3              # eng yangi 3 tasi har doim qoladi
EVERY_HOURS = 24
BACKUP_DIR = Path(os.getenv("BACKUP_DIR") or Path.home() / "MULOQOT_zaxira")
PREFIX = "muloqot-"


def _tool(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    try:
        import pgserver
        cand = Path(pgserver.__file__).parent / "pginstall" / "bin" / (name + (".exe" if os.name == "nt" else ""))
        if cand.exists():
            return str(cand)
    except ImportError:
        pass
    raise FileNotFoundError(f"{name} topilmadi (PostgreSQL client)")


def backups() -> list[Path]:
    return sorted(BACKUP_DIR.glob(f"{PREFIX}*.dump"), key=lambda p: p.stat().st_mtime, reverse=True)


def due() -> bool:
    files = backups()
    return not files or time.time() - files[0].stat().st_mtime > EVERY_HOURS * 3600


def _prune() -> list[str]:
    removed = []
    for i, f in enumerate(backups()):
        if i >= MIN_KEEP and time.time() - f.stat().st_mtime > KEEP_DAYS * 86400:
            f.unlink(missing_ok=True)
            removed.append(f.name)
    return removed


def make_backup(database_url: str) -> Path:
    """pg_dump → vaqtinchalik fayl → pg_restore --list bilan tekshiriladi → asl nomga ko'chiriladi."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    dst = BACKUP_DIR / f"{PREFIX}{datetime.now():%Y-%m-%d_%H%M}.dump"
    tmp = dst.with_suffix(".part")
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    subprocess.run([_tool("pg_dump"), "-Fc", "-Z", "6", "--no-owner", "-f", str(tmp), database_url],
                   check=True, capture_output=True, timeout=600, creationflags=flags)
    check = subprocess.run([_tool("pg_restore"), "--list", str(tmp)], capture_output=True, timeout=120,
                           creationflags=flags)
    if check.returncode != 0 or tmp.stat().st_size == 0:
        tmp.unlink(missing_ok=True)
        raise RuntimeError("zaxira fayli tekshiruvdan o'tmadi: " + check.stderr.decode(errors="replace")[:300])
    tmp.replace(dst)
    _prune()
    return dst


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "")
    if url and "localhost:5432" not in url:
        return url
    root = Path(__file__).resolve().parents[1]
    import pgserver  # lokal ishga tushirish (run_local.py bilan bir xil ichki PostgreSQL)
    return pgserver.get_server(root / "pgdata", cleanup_mode=None).get_uri()


if __name__ == "__main__":
    if "--list" in sys.argv:
        for f in backups():
            print(f"{f.name}  {f.stat().st_size // 1024} KB")
        print("papka:", BACKUP_DIR)
    else:
        p = make_backup(_database_url())
        print(f"zaxira tayyor: {p} ({p.stat().st_size // 1024} KB)")

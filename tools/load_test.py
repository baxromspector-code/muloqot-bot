"""Yuklama sinovi: N ta a'zo BIR VAQTDA Mini App'ga kiradi (bosh sahifa ochilishi: /me + /events + /rating).

    python tools/load_test.py [N]        # standart N=3000; sayt 127.0.0.1:8080 da ishlab turgan bo'lsin

Bazaga vaqtinchalik sinov foydalanuvchilari qo'shiladi (ID 9 100 000 000 dan boshlab, guvohnoma «LT-…»)
va sinov tugagach (xato bo'lsa ham) user_id ustuni bor barcha jadvallardan butunlay o'chiriladi.
So'rovlar to'g'ridan-to'g'ri lokal serverga boradi (tunnel/Cloudflare orqali emas).
"""
import asyncio
import hashlib
import hmac
import json
import statistics
import sys
import time
import urllib.parse
from collections import Counter
from datetime import datetime
from pathlib import Path

import aiohttp
import asyncpg
import pgserver

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import BOT_TOKEN  # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
BASE_ID = 9_100_000_000
URL = "http://127.0.0.1:8080/api/app"
SECRET = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()


def init_data(uid: int) -> str:
    user = json.dumps({"id": uid, "first_name": f"Sinov{uid - BASE_ID}"}, separators=(",", ":"))
    d = {"auth_date": str(int(time.time())), "query_id": f"lt{uid}", "user": user}
    dcs = "\n".join(f"{k}={d[k]}" for k in sorted(d))
    d["hash"] = hmac.new(SECRET, dcs.encode(), hashlib.sha256).hexdigest()
    return urllib.parse.urlencode(d)


async def setup(conn) -> None:
    now = datetime.now()
    year = f"{now.year}/{now.year + 1}" if now.month >= 9 else f"{now.year - 1}/{now.year}"
    users = [(BASE_ID + i, ("uz", "ru", "en", "ko", "un")[i % 5], f"Sinov A'zo {i}", "Xalqaro munosabatlar",
              str(1 + i % 4), f"LT-{i % 40}", f"LT{i:06d}", f"+99890{i:07d}", True, now) for i in range(N)]
    await conn.copy_records_to_table("users", records=users, columns=[
        "user_id", "lang", "full_name", "direction", "course", "group_name", "student_id", "phone", "registered",
        "created_at"])
    members = [(BASE_ID + i, f"LT-{i:05d}", ("intl", "youth", "media", "law", "innov", "research")[i % 6], year,
                "active", now) for i in range(N)]
    await conn.copy_records_to_table("members", records=members, columns=[
        "user_id", "number", "section", "academic_year", "status", "joined_at"])


async def cleanup(conn) -> dict:
    tables = await conn.fetch("SELECT table_name FROM information_schema.columns "
                              "WHERE table_schema='public' AND column_name='user_id'")
    removed = {}
    # avval bog'liq jadvallar, oxirida users
    for t in sorted((r["table_name"] for r in tables), key=lambda x: x == "users"):
        res = await conn.execute(f'DELETE FROM "{t}" WHERE user_id >= $1 AND user_id < $2', BASE_ID, BASE_ID + 1_000_000)
        n = int(res.split()[-1])
        if n:
            removed[t] = n
    return removed


async def one_user(session, uid: int, paths: list[str]) -> list[tuple[str, int, float]]:
    hdr = {"X-Tg-Init": init_data(uid)}
    out = []
    for p in paths:
        t0 = time.perf_counter()
        try:
            async with session.get(URL + p, headers=hdr) as r:
                await r.read()
                out.append((p, r.status, time.perf_counter() - t0))
        except Exception as e:
            out.append((p, type(e).__name__, time.perf_counter() - t0))
    return out


def report(name: str, results: list, wall: float) -> dict:
    flat = [x for r in results for x in r]
    ok = [x[2] for x in flat if x[1] == 200]
    codes = Counter(str(x[1]) for x in flat)
    q = statistics.quantiles(ok, n=100) if len(ok) > 2 else [0] * 99
    users_ok = sum(1 for r in results if all(x[1] == 200 for x in r))
    print(f"\n=== {name} ===")
    print(f"foydalanuvchi: {len(results)} · so'rov: {len(flat)} · umumiy vaqt: {wall:.1f} s · "
          f"o'tkazuvchanlik: {len(flat) / wall:.0f} so'rov/s")
    print(f"natija kodlari: {dict(codes)} · to'liq muvaffaqiyatli kirish: {users_ok}/{len(results)}")
    if ok:
        print(f"javob vaqti: o'rtacha {statistics.mean(ok) * 1000:.0f} ms · p50 {q[49] * 1000:.0f} ms · "
              f"p95 {q[94] * 1000:.0f} ms · p99 {q[98] * 1000:.0f} ms · eng sekin {max(ok) * 1000:.0f} ms")
    per_path = {}
    for p in sorted({x[0] for x in flat}):
        v = [x[2] for x in flat if x[0] == p and x[1] == 200]
        if v:
            per_path[p] = round(statistics.median(v) * 1000)
    print("yo'llar bo'yicha (median ms):", per_path)
    return {"users_ok": users_ok, "codes": dict(codes), "wall": wall}


async def run(paths: list[str], name: str) -> dict:
    conn = aiohttp.TCPConnector(limit=0, force_close=False)
    timeout = aiohttp.ClientTimeout(total=180)
    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as s:
        t0 = time.perf_counter()
        results = await asyncio.gather(*(one_user(s, BASE_ID + i, paths) for i in range(N)))
        return report(name, results, time.perf_counter() - t0)


async def main() -> None:
    srv = pgserver.get_server(ROOT / "pgdata", cleanup_mode=None)
    conn = await asyncpg.connect(srv.get_uri())
    try:
        left = await cleanup(conn)  # oldingi to'xtatilgan sinovdan qolgan bo'lsa
        if left:
            print("oldingi sinov qoldig'i o'chirildi:", left)
        t0 = time.perf_counter()
        await setup(conn)
        print(f"{N} ta sinov a'zosi yaratildi ({time.perf_counter() - t0:.1f} s)")
        await run(["/me"], f"1-SINOV: {N} a'zo bir vaqtda kiradi (/me)")
        await run(["/me", "/events", "/rating"], f"2-SINOV: {N} a'zo bir vaqtda bosh sahifani ochadi (/me → /events → /rating)")
    finally:
        removed = await cleanup(conn)
        rest = await conn.fetchval("SELECT COUNT(*) FROM users WHERE user_id >= $1", BASE_ID)
        print(f"\nsinov ma'lumotlari o'chirildi: {removed} · qolgan sinov foydalanuvchisi: {rest}")
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

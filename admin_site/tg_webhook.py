"""Bot WEBHOOK rejimida — sayt bilan bitta jarayonda (Render kabi bepul hostinglar uchun: u yerda alohida
fon jarayoni yo'q va 15 daqiqa so'rov bo'lmasa servis uxlaydi; Telegram xabari kelganda uyg'onadi).

Yoqish: BOT_WEBHOOK=1. Noutbukda (polling, python bot.py / run_local.py) bu o'chiq.
    POST /tg/webhook  — Telegram yangilanishlari (maxfiy sarlavha bilan tekshiriladi)
    GET  /healthz     — tiriklik tekshiruvi
KEEP_AWAKE=1 — servis o'zini har 10 daqiqada tekshirib turadi (uxlamaydi, eslatmalar o'z vaqtida ketadi).
"""
import asyncio
import contextlib
import hashlib
import hmac
import logging
import os

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse, Response

log = logging.getLogger("tg_webhook")
ENABLED = os.getenv("BOT_WEBHOOK", "0") in ("1", "true", "yes")
KEEP_AWAKE = os.getenv("KEEP_AWAKE", "0") in ("1", "true", "yes")
PATH = "/tg/webhook"
router = APIRouter()
_state: dict = {}
_inflight: set[asyncio.Task] = set()


def _secret() -> str:
    from config import BOT_TOKEN
    return hashlib.sha256(("muloqot-webhook:" + BOT_TOKEN).encode()).hexdigest()[:48]


async def _keep_awake(url: str) -> None:
    import httpx
    async with httpx.AsyncClient(timeout=20) as client:
        while True:
            await asyncio.sleep(600)
            with contextlib.suppress(Exception):
                await client.get(url)


async def start() -> None:
    import bot as botmod
    import scheduler
    from config import site_url

    bot, dp = botmod.create()
    await botmod.setup_bot_profile(bot)
    url = site_url()
    await bot.set_webhook(f"{url}{PATH}", secret_token=_secret(), drop_pending_updates=False,
                          allowed_updates=dp.resolve_used_update_types(), max_connections=20)
    tasks = [asyncio.create_task(scheduler.run(bot))]
    if KEEP_AWAKE:
        tasks.append(asyncio.create_task(_keep_awake(f"{url}/healthz")))
    _state.update(bot=bot, dp=dp, tasks=tasks)
    log.info("Webhook o'rnatildi: %s%s", url, PATH)


async def stop() -> None:
    for t in _state.get("tasks", []):
        t.cancel()
    if _inflight:  # ishlanayotgan xabarlar tugasin (ko'pi bilan 10 soniya)
        await asyncio.wait(_inflight, timeout=10)
    if "bot" in _state:
        await _state["bot"].session.close()
    _state.clear()


async def _process(update) -> None:
    try:
        await _state["dp"].feed_update(_state["bot"], update)
    except Exception:
        log.exception("Yangilanishni ishlashda xato")


@router.post(PATH, include_in_schema=False)
async def telegram_update(request: Request):
    if not _state or not hmac.compare_digest(request.headers.get("x-telegram-bot-api-secret-token", ""), _secret()):
        raise HTTPException(404)
    from aiogram.types import Update
    update = Update.model_validate(await request.json(), context={"bot": _state["bot"]})
    task = asyncio.create_task(_process(update))  # Telegram'ga darhol 200 — u kutib qolmasin
    _inflight.add(task)
    task.add_done_callback(_inflight.discard)
    return Response(status_code=200)


@router.get("/healthz", include_in_schema=False)
async def healthz():
    return PlainTextResponse("ok")

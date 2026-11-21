"""Vaqtinchalik https tunnel (Cloudflare quick tunnel) — server/domen olinguncha Mini App botda ochilishi uchun.

Ishga tushirish (sayt 8080-portda ishlab turgan bo'lsin):
    python tools/tunnel.py

Nima qiladi:
  1. cloudflared orqali https://<tasodifiy>.trycloudflare.com manzil oladi;
  2. .env dagi SITE_URL ni shu manzilga yangilaydi (bot va /panel havolalari uni har safar .env dan o'qiydi);
  3. botning «Ilova» menyu tugmasini darhol yangi manzilga o'rnatadi;
  Doimiy rejim: .env da TUNNEL_NAME va TUNNEL_HOSTNAME bo'lsa (tools/named_tunnel_setup.ps1 yozadi),
  o'z domeningizdagi o'zgarmas manzil ishlatiladi — Telegram eski manzilni eslab qolish muammosi bo'lmaydi.
  4. har 30 soniyada manzilni tekshiradi: Cloudflare tunnelni uzib qo'ysa (530/1033 xatosi),
     cloudflared'ni qayta ishga tushiradi va 1–3-qadamlarni yangi manzil bilan takrorlaydi.
To'xtatish: Ctrl+C (yoki stop_all.ps1). Haqiqiy serverga o'tilgach (DEPLOY.md) bu skript kerak emas.
"""
import json
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".env"
PORT = 8080
URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
CHECK_EVERY = 30      # soniya
# Internet bor-u tunnel ketma-ket shuncha tekshiruvda javob bermasa (20 x 30 s = 10 daqiqa) yangi tunnel ochiladi.
# Qisqa uzilishlarda cloudflared o'zi qayta ulanadi va MANZIL SAQLANADI — yangi tunnel esa yangi manzil degani,
# Telegram esa eski manzilni eslab qoladi. Shuning uchun almashtirish — faqat oxirgi chora.
FAILS_TO_RESTART = 20


def log(msg: str) -> None:
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}", flush=True)


def find_cloudflared() -> str:
    for c in (shutil.which("cloudflared"), r"C:\Program Files (x86)\cloudflared\cloudflared.exe",
              r"C:\Program Files\cloudflared\cloudflared.exe"):
        if c and Path(c).exists():
            return c
    sys.exit("cloudflared topilmadi: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/")


def env_get(key: str) -> str:
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def env_set(key: str, value: str) -> None:
    s = ENV.read_text(encoding="utf-8")
    if re.search(rf"(?m)^{key}=", s):
        s = re.sub(rf"(?m)^{key}=.*$", f"{key}={value}", s)
    else:
        s = s.rstrip("\n") + f"\n{key}={value}\n"
    ENV.write_text(s, encoding="utf-8")


def set_menu_button(url: str) -> None:
    token = env_get("BOT_TOKEN")
    button = {"type": "web_app", "text": "Ilova", "web_app": {"url": f"{url}/app"}}
    data = urllib.parse.urlencode({"menu_button": json.dumps(button)}).encode()
    for attempt in range(5):
        try:
            with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/setChatMenuButton", data, timeout=20) as r:
                ok = json.loads(r.read()).get("ok")
            log("Bot «Ilova» tugmasi: " + ("o'rnatildi" if ok else "o'rnatilmadi"))
            return
        except (urllib.error.URLError, OSError) as e:
            log(f"Ilova tugmasini o'rnatib bo'lmadi ({e}), qayta urinish...")
            time.sleep(5 * (attempt + 1))


def menu_url() -> str:
    token = env_get("BOT_TOKEN")
    try:
        with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/getChatMenuButton", timeout=20) as r:
            return (json.loads(r.read()).get("result") or {}).get("web_app", {}).get("url", "")
    except Exception:
        return ""


def internet_ok() -> bool:
    """Internet bormi: Telegram serveri istalgan HTTP javob bersa (hatto 404) — bor."""
    try:
        urllib.request.urlopen("https://api.telegram.org", timeout=10)
        return True
    except urllib.error.HTTPError:
        return True
    except Exception:
        return False


def http_ok(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return r.status == 200
    except Exception:
        return False


def run_once(exe: str) -> None:
    """cloudflared'ni bir marta ishga tushiradi; tunnel uzilsa yoki jarayon tugasa qaytadi.
    --protocol http2: TCP orqali ulanadi. Standart QUIC (UDP) bu tarmoqda tez-tez «timeout» bo'lib, tunnel uzilardi."""
    name, host = env_get("TUNNEL_NAME"), env_get("TUNNEL_HOSTNAME")
    cmd = [exe, "tunnel", "--no-autoupdate", "--protocol", "http2", "--url", f"http://127.0.0.1:{PORT}"]
    state = {"url": None, "ready": False}
    if name and host:  # doimiy tunnel (o'z domeningiz): manzil hech qachon o'zgarmaydi
        cmd += ["run", name]
        state["url"] = "https://" + host.removeprefix("https://").strip("/")
        if env_get("SITE_URL") != state["url"]:
            env_set("SITE_URL", state["url"])
        log(f"Tunnel manzili: {state['url']}  (doimiy, tunnel «{name}»)")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")

    def reader() -> None:  # chiqishni oxirigacha o'qiymiz, aks holda cloudflared qotib qoladi
        assert proc.stdout is not None
        for line in proc.stdout:
            if " ERR " in line:
                log("cloudflared: " + line.strip()[:200])
            if not state["url"] and (m := URL_RE.search(line)):
                state["url"] = m.group(0)
                env_set("SITE_URL", state["url"])
                log(f"Tunnel manzili: {state['url']}  (Mini App: {state['url']}/app) — .env SITE_URL yangilandi")
            if state["url"] and not state["ready"] and "Registered tunnel connection" in line:
                state["ready"] = True
                set_menu_button(state["url"])
                log("Tunnel ishlayapti")

    threading.Thread(target=reader, daemon=True).start()
    started, fails = time.time(), 0
    try:
        while proc.poll() is None:
            time.sleep(CHECK_EVERY)
            if not state["ready"]:
                if time.time() - started > 180:
                    log("Tunnel 3 daqiqada ulanmadi — qayta urinamiz")
                    break
                continue
            if not http_ok(f"http://127.0.0.1:{PORT}/"):
                fails = 0  # sayt o'zi o'chiq — tunnel aybdor emas, kutamiz
                continue
            if not internet_ok():
                continue  # internet o'zi yo'q — tunnelni almashtirish foyda bermaydi, kutamiz
            if http_ok(state["url"] + "/"):
                if fails:
                    log("Tunnel tiklandi (manzil o'zgarmadi)")
                fails = 0
                current = menu_url()  # botdagi «Ilova» tugmasi eski manzilda qolib ketmasin
                if current and current != state["url"] + "/app":
                    log(f"Ilova tugmasi eski manzilda edi ({current}) — tuzatilmoqda")
                    set_menu_button(state["url"])
            else:
                fails += 1
                if fails in (1, 5, 10, 15) or fails >= FAILS_TO_RESTART:
                    log(f"Tunnel javob bermadi ({fails}/{FAILS_TO_RESTART}), cloudflared qayta ulanishini kutyapmiz")
                if fails >= FAILS_TO_RESTART:
                    log("Tunnel 10 daqiqa tiklanmadi — yangi tunnel ochilmoqda")
                    break
    finally:
        proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill()


def main() -> None:
    exe = find_cloudflared()
    while True:
        try:
            run_once(exe)
        except KeyboardInterrupt:
            return
        time.sleep(5)


if __name__ == "__main__":
    main()

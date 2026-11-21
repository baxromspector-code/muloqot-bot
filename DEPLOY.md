# MULOQOT — serverga chiqarish (domen + VPS + HTTPS)

Natija: `https://muloqotclub.uz` — ochiq sayt, `/admin` — panel (botdagi `/panel` orqali), `/app` — Telegram ilova.
Bot, sayt, baza, HTTPS va kunlik zaxira bitta buyruq bilan ishga tushadi (`docker compose`).

## 0. Nima kerak

| Narsa | Tavsiya | Taxminiy narx |
|---|---|---|
| Domen | `muloqotclub.uz` — aHOST | 27 000 so'm/yil |
| VPS | Toshkentdagi data-markaz (telefonda eng tez), **Ubuntu 24.04**, 1–2 vCPU, **2 GB RAM**, 20 GB SSD | ~90 000–210 000 so'm/oy |

1 GB RAM yetmaydi (baza + bot + sayt + yuzni aniqlash kutubxonasi). Narxlar o'zgaradi — sotib olishdan oldin tekshiring.

## 1. Domenni serverga ulash (DNS)

aHOST paneli → domen → **DNS boshqaruvi** → ikkita yozuv:

| Turi | Nomi | Qiymati |
|---|---|---|
| A | `@` | VPS IP manzili |
| A | `www` | VPS IP manzili |

DNS tarqalishi 10 daqiqadan bir necha soatgacha. Tekshirish: `ping muloqotclub.uz` VPS IP'sini ko'rsatishi kerak.

## 2. Serverga ulanish va Docker o'rnatish

```bash
ssh root@VPS_IP
curl -fsSL https://get.docker.com | sh
mkdir -p /opt/muloqot
```

## 3. Bazani shu kompyuterdan eksport qilish

`kiut_bot` papkasida (Windows):

```bash
python tools/export_db.py
```

`muloqot-backup.sql` paydo bo'ladi — unda talabalar ma'lumotlari bor, hech kimga bermang.

## 4. Fayllarni serverga yuborish

```bash
scp -r admin_site assets docs handlers tools dizayn *.py requirements.txt Dockerfile docker-compose.yml Caddyfile .dockerignore .env muloqot-backup.sql root@VPS_IP:/opt/muloqot/
```

`pgdata` papkasini yubormang — baza 6-qadamda fayldan tiklanadi.

## 5. Server sozlamalari (.env)

Serverda `nano /opt/muloqot/.env` va **qo'shing**:

```
DOMAIN=muloqotclub.uz
POSTGRES_PASSWORD=uzun-tasodifiy-parol
```

Parolni yaratish: `openssl rand -hex 16`. `SITE_URL`, `ADMIN_HTTPS`, `DATABASE_URL` ni yozish shart emas — docker-compose o'zi qo'yadi.

## 6. Ishga tushirish

> **Muhim:** avval shu kompyuterdagi botni to'xtating. Bitta bot ikki joyda ishlasa, Telegram xato beradi.

```bash
cd /opt/muloqot
docker compose up -d db
docker compose exec -T db psql -U muloqot muloqot < muloqot-backup.sql
docker compose up -d --build
```

Birinchi ishga tushishda Caddy HTTPS sertifikatini o'zi oladi (1–2 daqiqa).

## 7. Tekshirish

- `https://muloqotclub.uz` — ochiq sayt ochiladi;
- botga `/panel` — havola admin panelni ochadi;
- botda pastki chap burchakda **«Ilova»** tugmasi chiqadi (yoki `/app`).

## Kundalik ishlar

| Vazifa | Buyruq |
|---|---|
| Holat | `docker compose ps` |
| Bot loglari | `docker compose logs -f bot` |
| Sayt loglari | `docker compose logs -f web` |
| Yangilash (yangi fayllar yuborilgach) | `docker compose up -d --build` |
| Qayta ishga tushirish | `docker compose restart` |
| Zaxiralar | `/opt/muloqot/backups/` — har kuni, 14 kun saqlanadi |

Zaxiradan tiklash: `gunzip -c backups/muloqot-YYYY-MM-DD.sql.gz | docker compose exec -T db psql -U muloqot muloqot`.

## Google orqali kirish (ixtiyoriy)

Google Cloud Console → Credentials → OAuth client → Redirect URI: `https://muloqotclub.uz/auth/callback`.
`.env` ga `GOOGLE_CLIENT_SECRET=...` va `ADMIN_GOOGLE_EMAILS=...` yozib, `docker compose up -d`.

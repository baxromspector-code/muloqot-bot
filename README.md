# MULOQOT klubi boti

KIUT talabalarining «MULOQOT» xalqaro munosabatlar klubi uchun Telegram bot.
Namuna sifatida @SP_KIUT_support_bot olingan. Klubning ustavi, nizomi, a'zolik blankasi va taqdimoti
asosida qurilgan (`TOPSHIRIQ.md`, `BOT_TAHLILI.md`).

**Texnologiyalar:** Python 3.11+, aiogram 3, PostgreSQL (asyncpg), Pillow + qrcode.
**Tillar:** o'zbek, rus, ingliz, koreys.

## Imkoniyatlar
| Foydalanuvchi | Admin (Kengash / Bosh kotib) |
|---|---|
| Ro'yxatdan o'tish (F.I.Sh, yo'nalish, kurs, guruh, guvohnoma, telefon, rozilik) | Arizani qabul qilish → bo'limga yo'naltirish → guvohnoma avtomatik |
| 📝 A'zo bo'lish — blankaning to'liq elektron shakli (8 bo'lim) | ↩️ To'ldirishga qaytarish (izoh bilan) / ❌ rad etish (Ustav 4.6 dagi 3 sabab) |
| 🪪 Elektron guvohnoma `MLQ-26-001` (QR bilan), toifa, davomat, ball | `/addevent` — mashg'ulot/tadbir, hammaga e'lon |
| 📅 Bepul tadbirlar → QR-chipta `EVT-0001` | `/check` yoki QR matni — kirishda davomat + avtomatik ball |
| ✉️ Savol / taklif / shikoyat (shikoyat — Intizom hay'atiga, maxfiy) | Murojaatga javob, holat, yopish |
| 🏆 Reyting (oyning faol a'zolari), 🙋 ko'ngillilik | `/ball` — Nizom 2.4 bo'yicha ball |
| ℹ️ Klub haqida, 📄 hujjatlar (PDF/Word/PPTX), ❓ FAQ | `/addfaq`, `/broadcast`, `/export` (CSV), `/stats` |
| ⚙️ Til, profil, ma'lumotlarni o'chirish (Nizom 7.9) | O'chirish so'rovini tasdiqlash |

Menyu tugmasi har qanday boshlangan jarayonni bekor qiladi. Namuna botda bu xato bor edi:
menyu tugmasi murojaat matni bo'lib ketardi.

**Avtomatik ishlar** (`scheduler.py`, har 5 daqiqada):
- tadbirdan 24 soat oldin chipta olganlarga eslatma yuboriladi;
- tadbir boshlanganda ro'yxatga olish yopiladi, 6 soatdan keyin tadbir yakunlangan deb davomatga kiritiladi;
- har kuni 09:00 da muddat nazorati: Kengash 10 ish kunida ko'rmagan arizalar, 3 ish kunida qabul
  qilinmagan shikoyatlar, javobsiz murojaatlar admin va Intizom hay'ati guruhlariga eslatiladi.

**Qulayliklar:** yarim to'ldirilgan ariza bot qayta ishga tushsa ham saqlanadi (holatlar PostgreSQL'da);
qaytarilgan arizada javoblar saqlanadi va faqat kerakli joyi tahrirlanadi; profilda bitta maydonni o'zgartirish
mumkin; bot tavsifi va buyruqlari 4 tilda avtomatik o'rnatiladi.

## O'rnatish

### 1-usul: Docker (PostgreSQL bilan birga)
```bash
cp .env.example .env      # BOT_TOKEN, ADMIN_CHAT_ID, ADMIN_IDS ni to'ldiring
docker compose up -d --build
```

### 2-usul: qo'lda
```bash
pip install -r requirements.txt
# PostgreSQL'da baza yarating:
#   CREATE USER muloqot WITH PASSWORD 'muloqot';
#   CREATE DATABASE muloqot OWNER muloqot;
cp .env.example .env      # DATABASE_URL va boshqalarni to'ldiring
python bot.py
```
Jadvallar birinchi ishga tushishda avtomatik yaratiladi.

## Sozlash (.env)
- `BOT_TOKEN` — @BotFather dan.
- `DATABASE_URL` — `postgresql://user:parol@host:5432/baza`.
- `ADMIN_CHAT_ID` — Kengash guruhi. Botni guruhga qo'shing; ID ni bilish uchun guruhga @getidsbot ni qo'shing.
  Arizalar, murojaatlar, ko'ngillilar va o'chirish so'rovlari shu guruhga tushadi; guruhdagi har bir a'zo tugmalarni bosa oladi.
- `COMPLAINT_CHAT_ID` — Intizom hay'ati guruhi (ixtiyoriy).
- `ADMIN_IDS` — shaxsiy chatda `/addevent`, `/check` va boshqa buyruqlarni ishlata oladiganlar.
- `REDIS_URL` — ixtiyoriy. Bot qayta ishga tushganda yarim to'ldirilgan blanka yo'qolmasligi uchun (`pip install redis`).

## Kirishda davomat olish
Navbatchi ishtirokchining chiptasini **rasmga olib** (yoki skrinshotini) botga yuboradi — bot QR'ni o'zi o'qiydi.
QR o'qilmasa, `/check EVT-0001` deb yozish ham mumkin. Bot ishtirokchi ismini ko'rsatadi, davomatni
belgilaydi va ball qo'shadi. Bir chiptani ikki marta ishlatib bo'lmaydi, soxta QR rad etiladi.
Tadbir boshlanganidan 6 soat o'tib avtomatik yakunlanadi (yoki `/events` → «🏁 Yakunlash») va davomat foiziga
kiradi (faol a'zo uchun semestrda kamida 2/3 qatnashish kerak, Ustav 4.3).

Tadbir qo'shishda sana `24.11.2026 16:00` formatida kiritiladi.

## Mahalliy kompyuterda sinash (PostgreSQL o'rnatmasdan)
```bash
pip install pgserver
python run_local.py
```
Ichki PostgreSQL `pgdata/` papkasida ishga tushadi.

## Sayt: ochiq sahifa va maxfiy admin panel

Bitta veb-ilova (`admin_site/`), bot bilan bir xil PostgreSQL bazasi:

- **`/` — ochiq sahifa (hammaga):** e'lon va reklamalar, yaqin tadbirlar (bazadan), klub haqida, galereya, manzil, telefon, xarita, Telegram, Instagram va bot havolalari. Telefonda ham moslashadi.
- **`/admin` — admin panel (faqat adminlarga):** begonalar uchun `/admin` va `/login` «sahifa topilmadi» qaytaradi, panel borligi ham bilinmaydi.

### Telegram ilovasi (Mini App) — `/app`

Botdagi imkoniyatlar bitta oynada, Apple uslubidagi qorong'i shisha dizaynda: bosh sahifa (tadbirlar, ball, haftalik kalendar),
tadbirga yozilish va QR-chipta, chiptani bekor qilish, ko'ngillilik, reyting, a'zolik guvohnomasi, bosqichma-bosqich a'zolik
arizasi, murojaat yuborish va javob yozish, profilni tahrirlash, til, klub haqida, savol-javob, hujjatlar, ma'lumotlarni o'chirish.

- Har bir so'rov Telegram imzolagan `initData` bilan tekshiriladi (bot tokeni bilan HMAC) — boshqa birov nomidan foydalanib bo'lmaydi.
- Admin xabarnomalari (ariza, murojaat, ko'ngilli, o'chirish so'rovi) botdagi bilan bir xil yuboriladi.
- Ro'yxatdan o'tish (telefon va surat) botda qoladi; murojaatga fayl biriktirish ham botda.
- Telegram Mini App faqat **https** manzilda ochiladi: `SITE_URL=https://...` yozilsa, botda «Ilova» menyu tugmasi va `/app` buyrug'i avtomatik yoqiladi.

### Admin panelga kirish

1. `PANEL_ADMIN_IDS` dagi admin (bo'sh bo'lsa — `ADMIN_IDS`) botga **`/panel`** yozadi (faqat shaxsiy chatda).
2. Bot bir martalik havola yuboradi: **5 daqiqa** amal qiladi, faqat **bir marta** ochiladi.
3. Havola ochilgach sessiya 30 kun saqlanadi. «Chiqish» — ochiq sahifaga qaytaradi.

ID ro'yxatdan olib tashlangan admin darhol kirish huquqini yo'qotadi. Google orqali kirish ixtiyoriy: `GOOGLE_CLIENT_ID` va `GOOGLE_CLIENT_SECRET` berilsa `/login` ishlaydi (faqat `ADMIN_GOOGLE_EMAILS`).

### Ochiq saytni boshqarish (admin panel → «Sayt»)

- **E'lon va reklamalar:** sarlavha, matn, rasm, havola tugmasi; «Muhim» (tepada turadi), «Saytda ko'rinsin» (yashirish).
- **Galereya:** bir nechta rasmni birdaniga yuklash, izoh yozish, o'chirish.
- **Sayt ma'lumotlari:** nom, tavsif, shior, «Biz haqimizda», telefon, email, manzil, xarita, ish vaqti, Telegram/Instagram/bot havolalari.

Rasmlar bazada saqlanadi; yuklashda qayta kodlanadi (EXIF va yashirin ma'lumot o'chadi) va 1600 px gacha kichraytiriladi.

### Admin panel imkoniyatlari

- **Sahifalar:** umumiy ko'rinish, talabalar, arizalar, tadbirlar, murojaatlar, bot faolligi (issiqlik xaritasi, eng ko'p bosilgan bo'limlar, jonli lenta) va «Sayt» bo'limi.
- **Talabalar bo'limi:**
  - tezkor qidiruv: ism, @username, telefon, talaba ID, guruh, MLQ-raqam; lotin va kirill yozuvida;
  - filtrlar: holat, yo'nalish, kurs, guruh, bo'lim, til, surat, faollik, ball, sana; har bir filtrda nechta talaba borligi ko'rinadi;
  - tezkor filtrlar, saralash, jadval yoki kartalar ko'rinishi;
  - Excel (CSV) eksport;
  - talaba kartochkasi: surat, ariza javoblari, ballar, tadbirlar, murojaatlar;
  - **Ctrl+K** — istalgan joydan talaba qidirish.
- **Dizayn:** asosiy — **Qaymoq** (shisha tugmalar bilan); **Glass** va **Diplomat** doiracha orqali tanlanadi (`ADMIN_THEME`, `ADMIN_THEME_SWITCH=1`).
- **Xavfsizlik:** admin qismi qidiruv tizimlarida ko'rinmaydi (`noindex`, `robots.txt`), sayt iframe ichida ochilmaydi, bot tokeni brauzerga chiqmaydi (suratlar server orqali beriladi), o'zgartiruvchi so'rovlar boshqa saytlardan qabul qilinmaydi (CSRF himoyasi).
- **Faollik jurnali:** xabar matni saqlanmaydi, faqat turi (tugma, buyruq, matn) yoziladi.

Ishga tushirish:

```bash
pip install -r requirements.txt
python -m admin_site          # ochiq sahifa: http://127.0.0.1:8080 · panel: botda /panel
```

Serverga qo'yganda `.env` ga `SITE_URL=https://domen.uz` yozing — bot `/panel` havolasini shu manzil bilan beradi.

Google sozlamasi (ixtiyoriy): Google Cloud Console → APIs & Services → Credentials → OAuth client ID (Web application). Redirect URI: `https://SAYT/auth/callback`. Olingan ID va secret `.env` ga yoziladi (`.env.example` ga qarang). Serverda saytni HTTPS (Nginx yoki Caddy) orqali chiqaring va `ADMIN_HTTPS=1` qiling.


## Matnlarni o'zgartirish
Barcha matnlar `texts.py` da, har biri 4 tilda. Rahbariyat, ijtimoiy tarmoqlar va «Klub haqida» bo'limlari ham shu yerda.
Hujjat fayllari `docs/` papkasida, logotip `assets/logo.png` da.

## Fayllar
```
bot.py            ishga tushirish, routerlar tartibi
config.py         .env sozlamalari
db.py             PostgreSQL (asyncpg) — jadvallar va so'rovlar
texts.py          4 tildagi matnlar, blanka variantlari
keyboards.py      tugmalar
cards.py          guvohnoma va QR-chipta rasmlari
handlers/
  start.py        /start, til, ro'yxatdan o'tish
  menu.py         asosiy menyu, klub haqida, hujjatlar, FAQ, sozlamalar
  membership.py   a'zolik blankasi
  events.py       tadbirlar, chiptalar, ko'ngillilar
  appeals.py      murojaatlar (foydalanuvchi + admin)
  admin.py        admin buyruqlari va qarorlar
```

## Vaqtinchalik tunnel (server olinguncha)

Mini App faqat https manzilda ochiladi. Server/domen bo'lmaguncha kompyuterdagi saytni Cloudflare tunnel orqali chiqaramiz:

```bash
python tools/tunnel.py
```

Skript `https://….trycloudflare.com` manzil oladi, `.env` dagi `SITE_URL` ni yangilaydi va botning «Ilova» tugmasini shu manzilga o'rnatadi.
Skript tunnelni har 30 soniyada tekshiradi: uzilsa o'zi yangisini ochadi, `.env` va «Ilova» tugmasini yangilaydi. Bot va `/panel` havolalari manzilni har safar `.env` dan o'qiydi — botni qayta yoqish shart emas. Tunnel TCP (`--protocol http2`) orqali ishlaydi, chunki bu tarmoqda QUIC (UDP) tez-tez uzilardi.

### Avtoyuklash (Windows)

- `start_all.ps1` — tunnel, bot va saytni yashirin oynada ketma-ket ishga tushiradi (internetni kutadi, PostgreSQL qulf fayllarini tozalaydi, ikki marta ishga tushmaydi). Jurnal: `autostart.log`.
- `stop_all.ps1` — hammasini to'g'ri to'xtatadi.
- `tools/autostart_install.ps1` — Windows'ga kirganda `start_all.ps1` o'zi ishga tushishi uchun Startup papkasiga yorliq qo'yadi (`-Remove` — olib tashlash). Loyiha papkasi ko'chirilsa, qayta ishga tushiring.

### Doimiy manzil (o'z domeningiz bilan, server shart emas)

Bepul tunnel manzili har qayta ishga tushganda o'zgaradi, Telegram esa eski manzilni eslab qolishi mumkin. Domen bo'lsa — o'zgarmas manzil:

1. Domenni oling (masalan muloqotclub.uz).
2. [dash.cloudflare.com](https://dash.cloudflare.com) da bepul akkaunt oching → **Add a domain** → Free reja.
3. Domen sotuvchisi (aHOST) panelida nameserverlarni Cloudflare bergan ikkita manzilga almashtiring (kuchga kirishi 1–24 soat).
4. Domen Cloudflare'da «Active» bo'lgach:
   ```
   powershell -ExecutionPolicy Bypass -File tools\named_tunnel_setup.ps1 -Hostname app.muloqotclub.uz
   ```
5. `stop_all.ps1`, keyin `start_all.ps1`. Mini App: `https://app.muloqotclub.uz/app` — endi hech qachon o'zgarmaydi.

### Bazaning zaxirasi (kompyuterda ishlaganda)

- Bot ishlab turganda har kuni avtomatik zaxira oladi (oxirgisidan 24 soat o'tsa; kompyuter tunda o'chiq bo'lsa, yoqilgach). Zaxira olinmasa — bot egasiga Telegram'da xabar keladi.
- Papka: `%USERPROFILE%\MULOQOT_zaxira` (loyiha papkasidan tashqarida; `.env` dagi `BACKUP_DIR` bilan o'zgartiriladi). 14 kun saqlanadi, eng yangi 3 tasi har doim qoladi.
- Qo'lda: `python tools/backup_db.py` (hozir olish), `python tools/backup_db.py --list` (ro'yxat).
- Tiklash (hozirgi ma'lumot zaxiradagisi bilan almashadi — avval `stop_all.ps1`):
  `pg_restore --clean --if-exists --no-owner -d "<DATABASE_URL>" "<zaxira fayli>"`
- Serverda (Docker) zaxirani `backup` xizmati oladi — DEPLOY.md.

### Doimiy manzil: Tailscale Funnel (hozir ishlatilmoqda)

- Manzil: `https://muloqot.tail621cf0.ts.net` (Mini App: `/app`) — kompyuter qayta yonsa ham o'zgarmaydi, bepul, kartasiz.
- Tailscale Windows xizmati sifatida o'zi ishga tushadi; Funnel sozlamasi saqlanadi. `.env`: `SITE_URL=` shu manzil va `TUNNEL=tailscale` — `start_all.ps1` Cloudflare tunnelni ishga tushirmaydi.
- Tekshirish: `tailscale funnel status`. O'chirish: `tailscale funnel --https=443 off`.
- Cloudflare tunnelga qaytish: `.env` dan `TUNNEL=tailscale` qatorini olib tashlang va `start_all.ps1` ni qayta ishga tushiring.
- **Kompyuter yonishi bilan (Windows'ga kirmasdan ham):** «Планировщик заданий» dagi `MULOQOT bot (kompyuter yonganda)` vazifasi — yonganidan 1 daqiqa keyin `start_all.ps1` ni ishga tushiradi (S4U, parol saqlanmaydi; xato bo'lsa 3 marta qayta urinadi). O'rnatish/olib tashlash (administrator): `tools\autostart_task.ps1` / `tools\autostart_task.ps1 -Remove`. Windows'ga kirilganda Startup yorlig'i ham ishga tushadi, lekin `start_all.ps1` ikki marta ishga tushmaydi.

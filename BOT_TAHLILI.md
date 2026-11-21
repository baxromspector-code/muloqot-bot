# @SP_KIUT_support_bot — tahlil (2026-11-17)

Asl bot tugmalarini bosib o'rganilgan. Klon shu tuzilishga asoslangan.

## Ro'yxatdan o'tish (/start)
1. Til: Ўзбекча / Русский (inline)
2. Ism-familiya (matn)
3. Maqom: «KIUT talabasi» / «Hamkor universitet talabasi» (inline)
4. Kafedra: ~38 ta kafedra ro'yxati (inline, har biri alohida qatorda)
5. Kurs: 1–4 (inline, bir qatorda)
6. Guruh (matn, masalan 23-01)
7. Talaba ID (matn, 3–30 belgi: lotin harf, raqam, «-», «/»)
8. Telefon — «📱 Raqamni yuborish» (request_contact)
9. Shaxsiy ma'lumotlardan foydalanishga rozilik — «✅ Roziman»
10. Ma'lumotlar xulosasi → «Ro'yxatdan o'tdingiz!»

## Asosiy menyu (reply keyboard, 2 ustun)
| | |
|---|---|
| 📅 Tadbirlar | ✉️ Murojaat qilish |
| ❓ Ko'p beriladigan savollar | 📋 Mening murojaatlarim |
| 🎟 Mening chiptalarim | 🙋 Volontyor bo'lish |
| ℹ️ Parlament haqida | ⚙️ Sozlamalar |

Buyruqlar menyusi: faqat `/start` — «Bosh menyu».

## Bo'limlar
- **Murojaat**: matn 10–2000 belgi → keyin rasm/hujjat/ovoz qo'shish (hisoblagich) → «✅ Yuborish».
  Raqam beriladi (#0031). Holatlar: ko'rib chiqilmoqda → javob berildi. Javob kelganda «✍️ Javob yozish».
- **Mening murojaatlarim**: oxirgi 10 ta, inline `#0031 · 💬 Javob berildi · 17.11`, ichida yozishmalar tarixi.
- **FAQ**: hozircha bo'sh («Savollar hali qo'shilmagan»).
- **Tadbirlar**: sana, joy, kimlar uchun, band joylar (159/200), chipta narxi, «✍️ Yozilish», «⬅️ Orqaga». Kirishda QR-chipta.
- **Mening chiptalarim**: «Sizda hozircha chiptalar yo'q».
- **Volontyor bo'lish**: «Hozircha volontyorlar qabul qilinadigan tadbirlar yo'q».
- **Parlament haqida**: maqsad, rahbariyat, 7 ta departament/qo'mita.
- **Sozlamalar**: profil + «✏️ Profilni tahrirlash» (ro'yxatdan o'tishni qaytadan boshlaydi) + «🌐 Tilni o'zgartirish».

## Asl botdagi xato
Murojaat matni kutilayotganda menyu tugmasi bosilsa, u murojaat matni sifatida yuborilib ketadi.
Klonda menyu tugmalari har qanday holatni (FSM) bekor qiladi.

"""Bot matnlari. Har bir kalit: (o'zbekcha, ruscha, inglizcha, koreyscha).

Klub hujjatlari yangi alifboda yozilgan; bot foydalanuvchilarga tanish bo'lishi uchun
amaldagi lotin alifbosida (o', g', sh, ch). Kerak bo'lsa shu faylda almashtiring.
"""

from alphabet import to_new

# "un" — o'zbek tili 2026-yilgi yangi alifboda (Ş, Ç, Ö, Ğ). Matnlari o'zbekchadan avtomatik o'giriladi.
LANGS = ("uz", "un", "ru", "en", "ko")
TG_LANGS = ("uz", "ru", "en", "ko")      # Telegram til kodlari (bot tavsifi uchun)
LANG_NAMES = {"uz": "🇺🇿 O'zbekcha", "un": "🇺🇿 Özbekça (yangi alifbo)", "ru": "🇷🇺 Русский", "en": "🇬🇧 English",
              "ko": "🇰🇷 한국어"}
_COL = {"uz": 0, "ru": 1, "en": 2, "ko": 3}   # T va OPTIONS dagi ustun tartibi

# Ro'yxatdan o'tishdagi yo'nalishlar (xalqaro munosabatlar — klub yadrosi, birinchi o'rinda)
DIRECTIONS = [
    "Xalqaro munosabatlar", "Amaliy informatika", "Amaliy kosmetologiya", "Aniq fanlar",
    "Arxitektura va shaharsozlik", "Axborot texnologiyalari", "Bank ishi va buxgalteriya hisobi",
    "Energetika va amaliy fanlar", "Ijtimoiy-gumanitar fanlar", "Ingliz ta'limi", "Ingliz tili",
    "Jarrohlik fanlari", "Kimyo va biologiya", "Klinik fanlar", "Koreys filologiyasi", "Libos dizayni",
    "Maktabgacha va boshlang'ich ta'lim metodikasi", "Mashinasozlik texnologiyasi", "Maxsus pedagogika",
    "Menejment va marketing", "Moliya", "Pedagogika va psixologiya", "Pediatrik fanlar", "Qurilish",
    "Rangtasvir", "Rus tili", "Tarix", "Tarjima nazariyasi va amaliyoti", "Terapevtik fanlar",
    "Terapevtik stomatologiya", "Tibbiy biologik fanlar", "Tibbiy fundamental fanlar", "Turizm",
    "Xalqaro iqtisodiyot", "Xirurgik stomatologiya", "Yo'l harakati muhandisligi va boshqaruvi",
]

T: dict[str, tuple[str, str, str, str]] = {
    # ================= umumiy =================
    "choose_lang": ("Tilni tanlang:", "Выберите язык:", "Choose a language:", "언어를 선택하세요:"),
    "lang_set": ("✅ Til: O'zbekcha", "✅ Язык: Русский", "✅ Language: English", "✅ 언어: 한국어"),
    "welcome_new": (
        "Assalomu alaykum! 👋\n<b>MULOQOT</b> — KIUT talabalarining xalqaro munosabatlar klubi rasmiy boti.\n"
        "<i>«Muloqot qil, dalil keltir, yechim top.»</i>\n\nBotdan foydalanish uchun qisqa ro'yxatdan o'ting.",
        "Здравствуйте! 👋\n<b>MULOQOT</b> — официальный бот клуба международных отношений студентов KIUT.\n"
        "<i>«Веди диалог, приводи аргументы, находи решение.»</i>\n\nЧтобы пользоваться ботом, пройдите короткую регистрацию.",
        "Hello! 👋\n<b>MULOQOT</b> is the official bot of the KIUT students' International Relations Club.\n"
        "<i>“Talk, bring evidence, find a solution.”</i>\n\nPlease complete a short registration to use the bot.",
        "안녕하세요! 👋\n<b>MULOQOT</b>은 KIUT 학생 국제관계 클럽의 공식 봇입니다.\n"
        "<i>“대화하고, 근거를 제시하고, 해결책을 찾자.”</i>\n\n봇을 사용하려면 간단한 등록을 완료하세요.",
    ),
    "welcome_back": (
        "Xush kelibsiz, <b>{name}</b>! Kerakli bo'limni tanlang 👇",
        "Добро пожаловать, <b>{name}</b>! Выберите раздел 👇",
        "Welcome, <b>{name}</b>! Choose a section 👇",
        "<b>{name}</b>님, 환영합니다! 메뉴를 선택하세요 👇",
    ),
    "need_register": ("Avval ro'yxatdan o'ting: /start", "Сначала зарегистрируйтесь: /start",
                      "Please register first: /start", "먼저 등록하세요: /start"),
    "unknown": ("Tushunmadim 🤔 Pastdagi menyudan foydalaning.", "Не понял 🤔 Воспользуйтесь меню ниже.",
                "Sorry, I didn't get that 🤔 Please use the menu below.", "이해하지 못했어요 🤔 아래 메뉴를 사용하세요."),
    "btn_back": ("⬅️ Orqaga", "⬅️ Назад", "⬅️ Back", "⬅️ 뒤로"),
    "btn_cancel": ("❌ Bekor qilish", "❌ Отменить", "❌ Cancel", "❌ 취소"),
    "btn_skip": ("⏭ O'tkazib yuborish", "⏭ Пропустить", "⏭ Skip", "⏭ 건너뛰기"),
    "btn_done": ("✅ Davom etish", "✅ Продолжить", "✅ Continue", "✅ 계속"),
    "btn_yes": ("✅ Ha", "✅ Да", "✅ Yes", "✅ 예"),
    "btn_no": ("❌ Yo'q", "❌ Нет", "❌ No", "❌ 아니요"),
    "cancelled": ("❌ Bekor qilindi.", "❌ Отменено.", "❌ Cancelled.", "❌ 취소되었습니다."),
    "pick_one": ("Kamida bittasini tanlang.", "Выберите хотя бы один вариант.", "Select at least one option.",
                 "하나 이상 선택하세요."),

    # ================= ro'yxatdan o'tish =================
    "ask_name": ("✍️ Familiya, ism, otasining ismi (masalan: Aliyev Jasur Akmalovich):",
                 "✍️ Фамилия, имя, отчество (например: Алиев Жасур Акмалович):",
                 "✍️ Your full name (e.g. Aliyev Jasur Akmalovich):",
                 "✍️ 성명을 입력하세요 (예: Aliyev Jasur Akmalovich):"),
    "bad_name": ("❗ Ism 3–80 belgidan iborat bo'lishi kerak.", "❗ Имя должно содержать 3–80 символов.",
                 "❗ Name must be 3–80 characters long.", "❗ 이름은 3–80자여야 합니다."),
    "ask_direction": ("🎓 Yo'nalishingizni tanlang:", "🎓 Выберите направление:", "🎓 Choose your field of study:",
                      "🎓 전공을 선택하세요:"),
    "ask_course": ("📚 Kursingiz:", "📚 Ваш курс:", "📚 Your year of study:", "📚 학년:"),
    "course_master": ("Magistratura", "Магистратура", "Master's", "석사"),
    "ask_group": ("👥 Guruhingiz (masalan: INR-903U):", "👥 Ваша группа (например: INR-903U):",
                  "👥 Your group (e.g. INR-903U):", "👥 그룹 (예: INR-903U):"),
    "bad_group": ("❗ Guruh 1–20 belgidan iborat bo'lishi kerak.", "❗ Группа: 1–20 символов.",
                  "❗ Group must be 1–20 characters.", "❗ 그룹은 1–20자여야 합니다."),
    "ask_student_id": ("🪪 Talabalik guvohnomasi raqami:", "🪪 Номер студенческого билета:",
                       "🪪 Student ID number:", "🪪 학생증 번호:"),
    "bad_student_id": (
        "❗ Raqam 3–30 belgidan iborat bo'lishi kerak (lotin harflari, raqamlar, «-» yoki «/»).",
        "❗ Номер: 3–30 символов (латиница, цифры, «-» или «/»).",
        "❗ ID must be 3–30 characters (Latin letters, digits, “-” or “/”).",
        "❗ 번호는 3–30자 (영문, 숫자, “-”, “/”)여야 합니다."),
    "ask_photo": (
        "📸 Yuzingiz aniq ko'rinadigan suratingizni yuboring (3×4 hujjat surati yoki selfi).\n"
        "Surat a'zolik guvohnomasiga qo'yiladi va tadbirga kirishda chipta egasini tasdiqlash uchun ishlatiladi.",
        "📸 Отправьте фото, где хорошо видно лицо (фото 3×4 или селфи).\n"
        "Оно будет на удостоверении и используется для подтверждения владельца билета на входе.",
        "📸 Send a photo where your face is clearly visible (3×4 ID photo or a selfie).\n"
        "It goes on your membership card and is used to verify the ticket holder at the entrance.",
        "📸 얼굴이 잘 보이는 사진을 보내주세요 (3×4 증명사진 또는 셀카).\n"
        "회원증에 들어가며 행사 입장 시 티켓 소유자 확인에 사용됩니다."),
    "bad_photo": ("❗ Iltimos, surat yuboring (fayl yoki matn emas).", "❗ Пожалуйста, отправьте фотографию.",
                  "❗ Please send a photo.", "❗ 사진을 보내주세요."),
    "no_face": (
        "🙂 Suratda yuz aniqlanmadi. Yorug' joyda, yuzingiz to'liq va to'g'ridan ko'rinadigan surat yuboring.",
        "🙂 На фото не найдено лицо. Сфотографируйтесь при хорошем свете, лицо прямо и полностью.",
        "🙂 No face detected. Please send a well-lit photo with your face fully visible and facing the camera.",
        "🙂 얼굴이 감지되지 않았습니다. 밝은 곳에서 얼굴 전체가 정면으로 보이는 사진을 보내주세요."),
    "photo_ok": ("✅ Surat qabul qilindi.", "✅ Фото принято.", "✅ Photo saved.", "✅ 사진이 저장되었습니다."),
    "need_photo": (
        "📸 Davom etishdan oldin profilingizga surat qo'shing — endi bu majburiy.",
        "📸 Перед продолжением добавьте фото в профиль — теперь это обязательно.",
        "📸 Please add a profile photo before continuing — it's now required.",
        "📸 계속하기 전에 프로필 사진을 추가하세요 — 이제 필수입니다."),
    "ask_phone": ("📱 Telefon raqamingizni yuborish uchun pastdagi tugmani bosing 👇",
                  "📱 Нажмите кнопку ниже, чтобы отправить номер 👇",
                  "📱 Tap the button below to share your phone number 👇",
                  "📱 아래 버튼을 눌러 전화번호를 보내세요 👇"),
    "btn_send_phone": ("📱 Raqamni yuborish", "📱 Отправить номер", "📱 Share phone number", "📱 번호 보내기"),
    "bad_phone": ("❗ Iltimos, pastdagi tugma orqali o'z raqamingizni yuboring.",
                  "❗ Отправьте свой номер кнопкой ниже.", "❗ Please share your own number with the button below.",
                  "❗ 아래 버튼으로 본인 번호를 보내주세요."),
    "phone_ok": ("✅ Raqam qabul qilindi.", "✅ Номер принят.", "✅ Phone number saved.", "✅ 번호가 저장되었습니다."),
    "consent": (
        "📄 <b>Shaxsga doir ma'lumotlarni qayta ishlashga rozilik</b>\n\n"
        "Ma'lumotlaringiz faqat klub ishi uchun (ro'yxatga olish, davomat, tadbirlar haqida xabar berish) "
        "ishlatiladi va himoyalangan hisobda saqlanadi. Uchinchi shaxsga faqat roziligingiz bilan yoki "
        "qonunda nazarda tutilgan hollarda beriladi. Roziligingizni istalgan vaqtda qaytarib olishingiz "
        "mumkin — ma'lumot 5 ish kuni ichida o'chiriladi (Nizom 7.9, O'RQ-547).",
        "📄 <b>Согласие на обработку персональных данных</b>\n\n"
        "Данные используются только для работы клуба (регистрация, посещаемость, уведомления о мероприятиях) "
        "и хранятся в защищённом аккаунте. Третьим лицам передаются только с вашего согласия или в случаях, "
        "предусмотренных законом. Согласие можно отозвать в любое время — данные удаляются в течение "
        "5 рабочих дней (Положение 7.9, ЗРУ-547).",
        "📄 <b>Consent to personal data processing</b>\n\n"
        "Your data is used only for club work (registration, attendance, event notifications) and stored in a "
        "protected account. It is shared with third parties only with your consent or where required by law. "
        "You may withdraw consent at any time — data is deleted within 5 working days (Regulations 7.9).",
        "📄 <b>개인정보 처리 동의</b>\n\n"
        "개인정보는 클럽 활동(등록, 출석, 행사 알림)에만 사용되며 보호된 계정에 보관됩니다. "
        "본인 동의 또는 법률이 정한 경우에만 제3자에게 제공됩니다. 언제든지 동의를 철회할 수 있으며 "
        "데이터는 5영업일 이내에 삭제됩니다 (규정 7.9)."),
    "btn_agree": ("✅ Roziman", "✅ Согласен(на)", "✅ I agree", "✅ 동의합니다"),
    "registered": (
        "🎉 Ro'yxatdan o'tdingiz! Siz endi klub <b>ishtirokchisisiz</b>: ochiq tadbirlarga yozilishingiz mumkin.\n"
        "To'liq a'zo bo'lish uchun «📝 A'zo bo'lish» bo'limida blankani to'ldiring.",
        "🎉 Регистрация завершена! Теперь вы <b>участник</b> клуба и можете записываться на открытые мероприятия.\n"
        "Чтобы стать членом клуба, заполните анкету в разделе «📝 Вступить в клуб».",
        "🎉 You're registered! You are now a club <b>participant</b> and can sign up for open events.\n"
        "To become a full member, fill in the form in «📝 Join the club».",
        "🎉 등록 완료! 이제 클럽 <b>참가자</b>로서 공개 행사에 신청할 수 있습니다.\n"
        "정회원이 되려면 «📝 클럽 가입»에서 신청서를 작성하세요."),
    "profile": (
        "👤 F.I.Sh: {full_name}\n🎓 Yo'nalish: {direction}\n📚 Kurs: {course}\n👥 Guruh: {group}\n"
        "🪪 Guvohnoma: {student_id}\n📱 Telefon: {phone}",
        "👤 ФИО: {full_name}\n🎓 Направление: {direction}\n📚 Курс: {course}\n👥 Группа: {group}\n"
        "🪪 Студ. билет: {student_id}\n📱 Телефон: {phone}",
        "👤 Name: {full_name}\n🎓 Field: {direction}\n📚 Year: {course}\n👥 Group: {group}\n"
        "🪪 Student ID: {student_id}\n📱 Phone: {phone}",
        "👤 성명: {full_name}\n🎓 전공: {direction}\n📚 학년: {course}\n👥 그룹: {group}\n"
        "🪪 학생증: {student_id}\n📱 전화: {phone}"),

    # ================= asosiy menyu =================
    "m_join": ("📝 A'zo bo'lish", "📝 Вступить в клуб", "📝 Join the club", "📝 클럽 가입"),
    "m_membership": ("🪪 Mening a'zoligim", "🪪 Моё членство", "🪪 My membership", "🪪 내 회원정보"),
    "m_events": ("📅 Tadbirlar", "📅 Мероприятия", "📅 Events", "📅 행사"),
    "m_tickets": ("🎟 Chiptalarim", "🎟 Мои билеты", "🎟 My tickets", "🎟 내 티켓"),
    "m_appeal": ("✉️ Murojaat", "✉️ Обращение", "✉️ Contact us", "✉️ 문의하기"),
    "m_my_appeals": ("📋 Murojaatlarim", "📋 Мои обращения", "📋 My requests", "📋 내 문의"),
    "m_rating": ("🏆 Reyting", "🏆 Рейтинг", "🏆 Rating", "🏆 랭킹"),
    "m_volunteer": ("🙋 Ko'ngilli bo'lish", "🙋 Волонтёрство", "🙋 Volunteer", "🙋 봉사하기"),
    "m_about": ("ℹ️ Klub haqida", "ℹ️ О клубе", "ℹ️ About the club", "ℹ️ 클럽 소개"),
    "m_docs": ("📄 Hujjatlar", "📄 Документы", "📄 Documents", "📄 문서"),
    "m_faq": ("❓ Savollar", "❓ Вопросы", "❓ FAQ", "❓ 자주 묻는 질문"),
    "m_settings": ("⚙️ Sozlamalar", "⚙️ Настройки", "⚙️ Settings", "⚙️ 설정"),

    # ================= a'zolik arizasi (blanka) =================
    "join_intro": (
        "📝 <b>MULOQOT klubiga a'zolik arizasi</b>\n\nA'zolik ixtiyoriy va bepul (Ustav 4.2, 8.3). "
        "Kengash 10 ish kuni ichida javob beradi. A'zolik 1 o'quv yiliga beriladi.\n"
        "Blanka 8 bo'limdan iborat, taxminan 5–7 daqiqa. Ro'yxatdagi ma'lumotlaringiz avtomatik qo'shiladi.\n\n"
        "Ariza turini tanlang:",
        "📝 <b>Анкета на вступление в клуб MULOQOT</b>\n\nЧленство добровольное и бесплатное (Устав 4.2, 8.3). "
        "Совет отвечает в течение 10 рабочих дней. Членство выдаётся на 1 учебный год.\n"
        "8 разделов, около 5–7 минут. Данные регистрации добавятся автоматически.\n\nВыберите тип заявки:",
        "📝 <b>MULOQOT club membership application</b>\n\nMembership is voluntary and free (Charter 4.2, 8.3). "
        "The Council replies within 10 working days. Membership is valid for 1 academic year.\n"
        "8 sections, about 5–7 minutes. Your registration data is added automatically.\n\nChoose application type:",
        "📝 <b>MULOQOT 클럽 가입 신청서</b>\n\n가입은 자율적이며 무료입니다 (정관 4.2, 8.3). "
        "위원회가 10영업일 이내에 답변합니다. 회원 자격은 1학년도 동안 유효합니다.\n"
        "8개 섹션, 약 5–7분 소요. 등록 정보는 자동으로 추가됩니다.\n\n신청 유형을 선택하세요:"),
    "app_new": ("🆕 Yangi a'zo", "🆕 Новый член", "🆕 New member", "🆕 신규 회원"),
    "app_renew": ("🔄 A'zolikni yangilash", "🔄 Продление членства", "🔄 Renew membership", "🔄 회원 갱신"),
    "join_pending": ("⏳ Sizning <b>#{id}</b> arizangiz ko'rib chiqilmoqda. Kengash 10 ish kuni ichida javob beradi.",
                     "⏳ Ваша заявка <b>#{id}</b> на рассмотрении. Совет ответит в течение 10 рабочих дней.",
                     "⏳ Your application <b>#{id}</b> is under review. The Council replies within 10 working days.",
                     "⏳ 신청서 <b>#{id}</b>를 검토 중입니다. 위원회가 10영업일 이내에 답변합니다."),
    "join_already": ("✅ Siz {year} o'quv yili uchun klub a'zosisiz. «🪪 Mening a'zoligim» bo'limini ko'ring.",
                     "✅ Вы член клуба на {year} учебный год. Смотрите «🪪 Моё членство».",
                     "✅ You are a club member for the {year} academic year. See «🪪 My membership».",
                     "✅ {year} 학년도 클럽 회원입니다. «🪪 내 회원정보»를 확인하세요."),
    "q_email": ("📧 <b>1. Aloqa</b>\nElektron pochtangiz:", "📧 <b>1. Контакты</b>\nВаш e-mail:",
                "📧 <b>1. Contacts</b>\nYour e-mail:", "📧 <b>1. 연락처</b>\n이메일 주소:"),
    "bad_email": ("❗ Email noto'g'ri. Masalan: name@gmail.com", "❗ Неверный e-mail. Пример: name@gmail.com",
                  "❗ Invalid e-mail. Example: name@gmail.com", "❗ 잘못된 이메일입니다. 예: name@gmail.com"),
    "q_social": ("🔗 Instagram yoki LinkedIn (ixtiyoriy):", "🔗 Instagram или LinkedIn (необязательно):",
                 "🔗 Instagram or LinkedIn (optional):", "🔗 Instagram 또는 LinkedIn (선택):"),
    "q_edu_lang": ("🗣 <b>2. O'quv ma'lumotlari</b>\nTa'lim tilingiz:", "🗣 <b>2. Учёба</b>\nЯзык обучения:",
                   "🗣 <b>2. Studies</b>\nLanguage of instruction:", "🗣 <b>2. 학업 정보</b>\n수업 언어:"),
    "q_section": ("🧩 <b>3. Qiziqishlar</b>\nQaysi bo'limda ishlashni xohlaysiz?",
                  "🧩 <b>3. Интересы</b>\nВ каком отделе хотите работать?",
                  "🧩 <b>3. Interests</b>\nWhich section would you like to work in?",
                  "🧩 <b>3. 관심 분야</b>\n어느 부서에서 활동하고 싶나요?"),
    "q_directions": ("🧭 Qaysi yo'nalish sizga eng qiziq? (faqat bittasini tanlang)",
                     "🧭 Какое направление вам интереснее всего? (выберите одно)",
                     "🧭 Which activity interests you most? (choose one)",
                     "🧭 가장 관심 있는 활동은? (하나만 선택)"),
    "q_languages": ("🌐 <b>4. Tillar va tajriba</b>\nTillarni va darajasini yozing (masalan: Ingliz B2, Rus C1, Koreys A2):",
                    "🌐 <b>4. Языки и опыт</b>\nУкажите языки и уровень (например: английский B2, русский C1):",
                    "🌐 <b>4. Languages & experience</b>\nList languages and levels (e.g. English B2, Russian C1):",
                    "🌐 <b>4. 언어와 경험</b>\n언어와 수준을 적어주세요 (예: 영어 B2, 러시아어 C1):"),
    "q_mun": ("🎤 Model UN, debat yoki forumlarda qatnashganmisiz? Qaysilarida?",
              "🎤 Участвовали ли вы в Model UN, дебатах или форумах? В каких?",
              "🎤 Have you taken part in Model UN, debates or forums? Which ones?",
              "🎤 모의유엔, 토론, 포럼에 참가한 적이 있나요? 어디였나요?"),
    "q_other_exp": ("🤝 Boshqa klub, tashabbus yoki ko'ngillilik tajribangiz:",
                    "🤝 Опыт в других клубах, инициативах или волонтёрстве:",
                    "🤝 Other club, initiative or volunteering experience:",
                    "🤝 다른 클럽, 프로젝트, 봉사 경험:"),
    "q_skills": ("💪 Kuchli ko'nikmalaringiz (bir nechtasini belgilang):", "💪 Сильные навыки (можно несколько):",
                 "💪 Your strongest skills (select several):", "💪 강점 기술 (여러 개 선택 가능):"),
    "q_certs": ("🏅 Sertifikat yoki yutuqlar (ixtiyoriy):", "🏅 Сертификаты или достижения (необязательно):",
                "🏅 Certificates or achievements (optional):", "🏅 자격증 또는 수상 경력 (선택):"),
    "q_mot1": ("💬 <b>5. Motivatsiya</b> (2–4 jumla yetarli)\nNega MULOQOT klubiga qo'shilmoqchisiz?",
               "💬 <b>5. Мотивация</b> (достаточно 2–4 предложений)\nПочему вы хотите вступить в MULOQOT?",
               "💬 <b>5. Motivation</b> (2–4 sentences are enough)\nWhy do you want to join MULOQOT?",
               "💬 <b>5. 지원 동기</b> (2–4문장이면 충분)\nMULOQOT에 가입하려는 이유는?"),
    "q_mot2": ("💬 Klubda nimani o'rganmoqchisiz va bir yildan keyin qanday natijaga erishmoqchisiz?",
               "💬 Чему хотите научиться в клубе и какого результата достичь через год?",
               "💬 What do you want to learn in the club and what result do you expect in a year?",
               "💬 클럽에서 무엇을 배우고 1년 후 어떤 성과를 얻고 싶나요?"),
    "q_mot3": ("💬 Klubga qanday hissa qo'sha olasiz?", "💬 Какой вклад вы можете внести в клуб?",
               "💬 How can you contribute to the club?", "💬 클럽에 어떻게 기여할 수 있나요?"),
    "q_issue": ("🌍 Sizni qiziqtiradigan bitta xalqaro masalani yozing va nega muhimligini qisqa tushuntiring (ixtiyoriy):",
                "🌍 Назовите одну международную проблему, которая вас интересует, и почему она важна (необязательно):",
                "🌍 Name one international issue you care about and briefly explain why it matters (optional):",
                "🌍 관심 있는 국제 이슈 하나와 그 중요성을 간단히 적어주세요 (선택):"),
    "bad_motivation": ("❗ Javob 20–1500 belgidan iborat bo'lsin.", "❗ Ответ: 20–1500 символов.",
                       "❗ Answer must be 20–1500 characters.", "❗ 답변은 20–1500자여야 합니다."),
    "bad_text": ("❗ Javob 2–1000 belgidan iborat bo'lsin.", "❗ Ответ: 2–1000 символов.",
                 "❗ Answer must be 2–1000 characters.", "❗ 답변은 2–1000자여야 합니다."),
    "q_hours": ("⏰ <b>6. Vaqt va ishtirok</b>\nHaftasiga qancha vaqt ajrata olasiz?",
                "⏰ <b>6. Время и участие</b>\nСколько времени в неделю можете уделять?",
                "⏰ <b>6. Time & participation</b>\nHow much time per week can you give?",
                "⏰ <b>6. 시간과 참여</b>\n주당 얼마나 시간을 낼 수 있나요?"),
    "q_days": ("📆 Qulay kunlar:", "📆 Удобные дни:", "📆 Convenient days:", "📆 가능한 요일:"),
    "q_time": ("🕔 Qulay vaqt:", "🕔 Удобное время:", "🕔 Convenient time:", "🕔 가능한 시간:"),
    "q_online": ("💻 Onlayn mashg'ulotlarda qatnasha olasizmi?", "💻 Можете участвовать онлайн?",
                 "💻 Can you attend online sessions?", "💻 온라인 활동에 참여할 수 있나요?"),
    "q_rules": (
        "📜 <b>7. Ustav va majburiyatlar</b>\n\n"
        "• MULOQOT klubi Ustavi va Nizomi bilan tanishdim va ularga amal qilaman.\n"
        "• Universitet ichki tartib va kiyinish qoidalariga rioya qilaman.\n"
        "• Olgan vazifamni muddatida bajaraman yoki oldindan xabar beraman.\n"
        "• Klub siyosiy betaraf ekanini bilaman: tadbirlarda siyosiy targ'ibot qilmayman.\n"
        "• Boshqalarning fikri va qadr-qimmatini hurmat qilaman.\n"
        "• A'zolik bepul ekanini va klub talabalardan naqd pul yig'masligini bilaman.\n\n"
        "Klub mashg'ulotlari dars vaqtiga qo'yilmaydi; klub ishi darsga kelmaslik uchun asos bo'lmaydi.",
        "📜 <b>7. Устав и обязательства</b>\n\n"
        "• Я ознакомился(ась) с Уставом и Положением клуба и буду их соблюдать.\n"
        "• Соблюдаю правила внутреннего распорядка и дресс-код университета.\n"
        "• Выполняю задачи в срок или заранее предупреждаю.\n"
        "• Клуб политически нейтрален: я не веду политическую агитацию.\n"
        "• Уважаю мнение и достоинство других.\n"
        "• Знаю, что членство бесплатное и клуб не собирает с студентов наличные.\n\n"
        "Занятия клуба не проводятся во время пар; работа в клубе не освобождает от занятий.",
        "📜 <b>7. Charter & commitments</b>\n\n"
        "• I have read the club Charter and Regulations and will follow them.\n"
        "• I follow the university's internal rules and dress code.\n"
        "• I complete tasks on time or notify in advance.\n"
        "• The club is politically neutral: I will not campaign politically.\n"
        "• I respect others' opinions and dignity.\n"
        "• I know membership is free and the club does not collect cash from students.\n\n"
        "Club sessions are never held during classes; club work is not a reason to miss classes.",
        "📜 <b>7. 정관과 의무</b>\n\n"
        "• 클럽 정관과 규정을 읽었으며 이를 준수하겠습니다.\n"
        "• 대학 내부 규칙과 복장 규정을 지키겠습니다.\n"
        "• 맡은 일을 기한 내에 수행하거나 미리 알리겠습니다.\n"
        "• 클럽은 정치적으로 중립이며, 정치 선전을 하지 않겠습니다.\n"
        "• 타인의 의견과 존엄을 존중하겠습니다.\n"
        "• 회원 가입은 무료이며 클럽은 학생에게 현금을 걷지 않음을 알고 있습니다.\n\n"
        "클럽 활동은 수업 시간에 진행되지 않으며, 수업 불참의 사유가 되지 않습니다."),
    "btn_accept_all": ("✅ Barchasiga roziman", "✅ Согласен(на) со всем", "✅ I agree to all", "✅ 모두 동의합니다"),
    "q_photo": ("📸 <b>8. Rozilik</b>\nTadbirlarda olingan foto va videolarda aks etishimga va ularni klub sahifalarida "
                "joylashtirishga roziman (ixtiyoriy):",
                "📸 <b>8. Согласие</b>\nСогласен(на) на съёмку на мероприятиях и публикацию фото/видео на страницах клуба "
                "(необязательно):",
                "📸 <b>8. Consent</b>\nI agree to appear in event photos/videos and to their publication on club pages "
                "(optional):",
                "📸 <b>8. 동의</b>\n행사 사진·영상 촬영 및 클럽 페이지 게시에 동의합니다 (선택):"),
    "app_summary": ("📝 <b>Arizangizni tekshiring</b>\n\n{body}\n\nHammasi to'g'rimi?",
                    "📝 <b>Проверьте заявку</b>\n\n{body}\n\nВсё верно?",
                    "📝 <b>Check your application</b>\n\n{body}\n\nIs everything correct?",
                    "📝 <b>신청서를 확인하세요</b>\n\n{body}\n\n모두 맞나요?"),
    "btn_submit": ("📨 Arizani yuborish", "📨 Отправить заявку", "📨 Submit application", "📨 신청서 제출"),
    "btn_edit_answers": ("✏️ Javobni tahrirlash", "✏️ Изменить ответ", "✏️ Edit an answer", "✏️ 답변 수정"),
    "edit_pick": ("✏️ Qaysi javobni o'zgartirasiz?", "✏️ Какой ответ изменить?", "✏️ Which answer do you want to change?",
                  "✏️ 어떤 답변을 수정할까요?"),
    "app_returned_resume": (
        "↩️ <b>#{id}</b> arizangiz to'ldirish uchun qaytarilgan.\n\nIzoh: <i>{reason}</i>\n\n"
        "Javoblaringiz saqlangan — «✏️ Javobni tahrirlash» orqali kerakli joyini to'g'rilab, qayta yuboring.",
        "↩️ Заявка <b>#{id}</b> возвращена на доработку.\n\nКомментарий: <i>{reason}</i>\n\n"
        "Ваши ответы сохранены — исправьте нужное через «✏️ Изменить ответ» и отправьте снова.",
        "↩️ Application <b>#{id}</b> was returned for completion.\n\nComment: <i>{reason}</i>\n\n"
        "Your answers are saved — fix what's needed via «✏️ Edit an answer» and resubmit.",
        "↩️ 신청서 <b>#{id}</b>가 보완을 위해 반려되었습니다.\n\n의견: <i>{reason}</i>\n\n"
        "답변은 저장되어 있습니다 — «✏️ 답변 수정»으로 필요한 부분을 고친 뒤 다시 제출하세요."),
    "btn_restart": ("🔁 Qaytadan to'ldirish", "🔁 Заполнить заново", "🔁 Start over", "🔁 다시 작성"),
    "app_sent": ("✅ Arizangiz qabul qilindi. Raqami: <b>#{id}</b>\n"
                 "Bosh kotib 3 ish kuni ichida ma'lumotni tekshiradi, Kengash 10 ish kuni ichida qaror qabul qiladi.",
                 "✅ Заявка принята. Номер: <b>#{id}</b>\n"
                 "Главный секретарь проверит данные за 3 рабочих дня, Совет примет решение за 10 рабочих дней.",
                 "✅ Application received. Number: <b>#{id}</b>\n"
                 "The Secretary checks it within 3 working days; the Council decides within 10 working days.",
                 "✅ 신청서가 접수되었습니다. 번호: <b>#{id}</b>\n"
                 "사무국장이 3영업일 이내에 확인하고, 위원회가 10영업일 이내에 결정합니다."),
    "app_accepted": ("🎉 Tabriklaymiz! <b>#{id}</b> arizangiz qabul qilindi.\n"
                     "Siz MULOQOT klubi a'zosisiz. Guvohnoma: <b>{number}</b>\nBo'lim: <b>{section}</b>\n"
                     "Amal qiladi: {year} o'quv yili.\n\n14 kun ichida tanishtiruv mashg'ulotiga taklif qilinasiz.",
                     "🎉 Поздравляем! Заявка <b>#{id}</b> принята.\n"
                     "Вы член клуба MULOQOT. Удостоверение: <b>{number}</b>\nОтдел: <b>{section}</b>\n"
                     "Действует: {year} учебный год.\n\nВ течение 14 дней вас пригласят на вводное занятие.",
                     "🎉 Congratulations! Application <b>#{id}</b> is accepted.\n"
                     "You are a MULOQOT member. Card: <b>{number}</b>\nSection: <b>{section}</b>\n"
                     "Valid for: {year} academic year.\n\nYou'll be invited to an orientation session within 14 days.",
                     "🎉 축하합니다! 신청서 <b>#{id}</b>가 승인되었습니다.\n"
                     "MULOQOT 회원이 되었습니다. 회원증: <b>{number}</b>\n부서: <b>{section}</b>\n"
                     "유효 기간: {year} 학년도.\n\n14일 이내에 오리엔테이션에 초대됩니다."),
    "app_returned": ("↩️ <b>#{id}</b> arizangiz to'ldirish uchun qaytarildi.\n\nIzoh: {reason}\n\n"
                     "5 ish kuni ichida «📝 A'zo bo'lish» orqali qayta yuboring.",
                     "↩️ Заявка <b>#{id}</b> возвращена на доработку.\n\nКомментарий: {reason}\n\n"
                     "Отправьте её снова через «📝 Вступить в клуб» в течение 5 рабочих дней.",
                     "↩️ Application <b>#{id}</b> was returned for completion.\n\nComment: {reason}\n\n"
                     "Please resubmit via «📝 Join the club» within 5 working days.",
                     "↩️ 신청서 <b>#{id}</b>가 보완을 위해 반려되었습니다.\n\n의견: {reason}\n\n"
                     "5영업일 이내에 «📝 클럽 가입»에서 다시 제출하세요."),
    "app_rejected": ("❌ <b>#{id}</b> arizangiz rad etildi.\nSabab: {reason}\n\nSavollar bo'lsa — «✉️ Murojaat».",
                     "❌ Заявка <b>#{id}</b> отклонена.\nПричина: {reason}\n\nЕсть вопросы — «✉️ Обращение».",
                     "❌ Application <b>#{id}</b> was rejected.\nReason: {reason}\n\nQuestions? Use «✉️ Contact us».",
                     "❌ 신청서 <b>#{id}</b>가 거절되었습니다.\n사유: {reason}\n\n문의는 «✉️ 문의하기»를 이용하세요."),
    "rej_not_student": ("KIUT talabasi emas", "Не является студентом KIUT", "Not a KIUT student", "KIUT 학생이 아님"),
    "rej_incomplete": ("Blanka belgilangan muddatda to'liq to'ldirilmagan", "Анкета не заполнена полностью в срок",
                       "The form was not fully completed on time", "신청서가 기한 내에 완성되지 않음"),
    "rej_banned": ("A'zolik bekor qilinganiga 1 yil bo'lmagan", "С момента отмены членства не прошёл 1 год",
                   "Less than 1 year since membership was revoked", "회원 자격 취소 후 1년이 지나지 않음"),

    # ================= a'zolik holati =================
    "ms_participant": (
        "🪪 <b>Mening a'zoligim</b>\n\nDaraja: <b>Kuzatuvchi</b>\nOchiq tadbirlarga qatnasha olasiz.\n"
        "A'zo bo'lish uchun — «📝 A'zo bo'lish».\n\n⭐ Ball: <b>{points}</b> · Reytingda: {rank}-o'rin\n"
        "📊 Davomat (semestr): {went}/{held}",
        "🪪 <b>Моё членство</b>\n\nУровень: <b>Наблюдатель</b>\nМожете посещать открытые мероприятия.\n"
        "Чтобы вступить — «📝 Вступить в клуб».\n\n⭐ Баллы: <b>{points}</b> · Место в рейтинге: {rank}\n"
        "📊 Посещаемость (семестр): {went}/{held}",
        "🪪 <b>My membership</b>\n\nLevel: <b>Observer</b>\nYou can attend open events.\n"
        "To join — «📝 Join the club».\n\n⭐ Points: <b>{points}</b> · Rank: #{rank}\n"
        "📊 Attendance (semester): {went}/{held}",
        "🪪 <b>내 회원정보</b>\n\n등급: <b>참관인</b>\n공개 행사에 참여할 수 있습니다.\n"
        "가입하려면 «📝 클럽 가입».\n\n⭐ 포인트: <b>{points}</b> · 순위: {rank}위\n"
        "📊 출석 (학기): {went}/{held}"),
    "ms_member": (
        "🪪 <b>Mening a'zoligim</b>\n\nDaraja: <b>{category}</b>\nGuvohnoma: <b>{number}</b>\nBo'lim: {section}\n"
        "Amal qiladi: {year} o'quv yili {expired}\n\n⭐ Ball: <b>{points}</b> (shu oy: {month_points}) · "
        "Reytingda: {rank}-o'rin\n📊 Davomat (semestr): {went}/{held} — {active_note}",
        "🪪 <b>Моё членство</b>\n\nУровень: <b>{category}</b>\nУдостоверение: <b>{number}</b>\nОтдел: {section}\n"
        "Действует: {year} учебный год {expired}\n\n⭐ Баллы: <b>{points}</b> (за месяц: {month_points}) · "
        "Место: {rank}\n📊 Посещаемость (семестр): {went}/{held} — {active_note}",
        "🪪 <b>My membership</b>\n\nLevel: <b>{category}</b>\nCard: <b>{number}</b>\nSection: {section}\n"
        "Valid for: {year} {expired}\n\n⭐ Points: <b>{points}</b> (this month: {month_points}) · "
        "Rank: #{rank}\n📊 Attendance (semester): {went}/{held} — {active_note}",
        "🪪 <b>내 회원정보</b>\n\n등급: <b>{category}</b>\n회원증: <b>{number}</b>\n부서: {section}\n"
        "유효 기간: {year} 학년도 {expired}\n\n⭐ 포인트: <b>{points}</b> (이번 달: {month_points}) · "
        "순위: {rank}위\n📊 출석 (학기): {went}/{held} — {active_note}"),
    "cat_member": ("A'zo", "Член клуба", "Member", "회원"),
    "level_changed": ("🎖 A'zolik darajangiz: <b>{level}</b>\nTabriklaymiz! Batafsil — «🪪 Mening a'zoligim».",
                      "🎖 Ваш уровень членства: <b>{level}</b>\nПоздравляем! Подробнее — «🪪 Моё членство».",
                      "🎖 Your membership level: <b>{level}</b>\nCongratulations! Details — «🪪 My membership».",
                      "🎖 회원 등급: <b>{level}</b>\n축하합니다! 자세히 — «🪪 내 회원정보»."),
    "cat_active": ("Faol a'zo", "Активный член", "Active member", "활동 회원"),
    "expired": ("⚠️ muddati o'tgan — 30 kun ichida yangilang (📝 A'zo bo'lish → 🔄 Yangilash)",
                "⚠️ срок истёк — продлите в течение 30 дней (📝 → 🔄 Продление)",
                "⚠️ expired — renew within 30 days (📝 → 🔄 Renew)",
                "⚠️ 만료됨 — 30일 이내에 갱신하세요 (📝 → 🔄 갱신)"),
    "active_yes": ("faol a'zo talabi bajarilmoqda ✅", "требование активного члена выполняется ✅",
                   "active member requirement met ✅", "활동 회원 요건 충족 ✅"),
    "active_no": ("faol a'zo uchun kamida 2/3 qatnashish kerak", "для активного члена нужно посетить ≥ 2/3",
                  "≥ 2/3 attendance needed for active status", "활동 회원은 2/3 이상 출석 필요"),
    "btn_card": ("🪪 Guvohnomani olish", "🪪 Получить удостоверение", "🪪 Get membership card", "🪪 회원증 받기"),

    # ================= reyting =================
    "rating": (
        "🏆 <b>Reyting</b>\n\n<b>Shu oyning faol a'zolari:</b>\n{month}\n\n<b>Umumiy reyting:</b>\n{total}\n\n"
        "Sizning ballingiz: <b>{mine}</b> ({rank}-o'rin)\n\n<i>Ball: mashg'ulot — 1, ko'ngilli yordam — 2, "
        "tahliliy matn — 3, debat/MUN — 3, loyihaga mas'ul — 5 (Nizom 2.4).</i>",
        "🏆 <b>Рейтинг</b>\n\n<b>Активисты месяца:</b>\n{month}\n\n<b>Общий рейтинг:</b>\n{total}\n\n"
        "Ваши баллы: <b>{mine}</b> (место {rank})\n\n<i>Баллы: занятие — 1, волонтёрство — 2, аналитический текст — 3, "
        "дебаты/MUN — 3, ответственный за проект — 5 (Положение 2.4).</i>",
        "🏆 <b>Rating</b>\n\n<b>Most active this month:</b>\n{month}\n\n<b>Overall:</b>\n{total}\n\n"
        "Your points: <b>{mine}</b> (rank #{rank})\n\n<i>Points: session — 1, volunteering — 2, analytical piece — 3, "
        "debate/MUN — 3, project lead — 5 (Regulations 2.4).</i>",
        "🏆 <b>랭킹</b>\n\n<b>이달의 활동 회원:</b>\n{month}\n\n<b>전체 랭킹:</b>\n{total}\n\n"
        "내 포인트: <b>{mine}</b> ({rank}위)\n\n<i>포인트: 정기 활동 1, 봉사 2, 분석 글 3, 토론/MUN 3, "
        "프로젝트 책임자 5 (규정 2.4).</i>"),
    "rating_empty": ("hali ball yo'q", "пока нет баллов", "no points yet", "아직 포인트 없음"),
    "points_added": ("⭐ Sizga <b>{amount}</b> ball qo'shildi: {reason}\nJami: <b>{total}</b>",
                     "⭐ Вам начислено <b>{amount}</b> балл(ов): {reason}\nВсего: <b>{total}</b>",
                     "⭐ You received <b>{amount}</b> point(s): {reason}\nTotal: <b>{total}</b>",
                     "⭐ <b>{amount}</b> 포인트가 적립되었습니다: {reason}\n합계: <b>{total}</b>"),

    # ================= murojaat =================
    "appeal_kind": ("✉️ Murojaat turini tanlang:", "✉️ Выберите тип обращения:", "✉️ Choose request type:",
                    "✉️ 문의 유형을 선택하세요:"),
    "kind_question": ("❓ Savol", "❓ Вопрос", "❓ Question", "❓ 질문"),
    "kind_suggestion": ("💡 Taklif / loyiha", "💡 Предложение / проект", "💡 Suggestion / project", "💡 제안 / 프로젝트"),
    "kind_complaint": ("⚖️ Shikoyat (maxfiy)", "⚖️ Жалоба (конфиденциально)", "⚖️ Complaint (confidential)",
                       "⚖️ 불만 제기 (비공개)"),
    "complaint_note": ("⚖️ Shikoyat Etika va intizom komissiyasiga yuboriladi va maxfiy saqlanadi. Komissiya 3 ish kuni ichida "
                       "qabul qilinganini bildiradi va 10 ish kuni ichida yozma qaror beradi. "
                       "Shikoyat qilgan a'zoga qarshi qasos chorasi taqiqlanadi (Ustav 9.5).",
                       "⚖️ Жалоба направляется в Комиссию по этике и дисциплине и хранится конфиденциально. Комиссия "
                       "подтвердит получение за 3 рабочих дня и вынесет решение за 10 рабочих дней. "
                       "Преследование заявителя запрещено (Устав 9.5).",
                       "⚖️ Complaints go to the Ethics & Discipline Commission and are kept confidential. The Commission confirms "
                       "receipt within 3 working days and decides within 10 working days. Retaliation is "
                       "prohibited (Charter 9.5).",
                       "⚖️ 신고는 윤리·징계위원회에 전달되며 비공개로 처리됩니다. 위원회는 3영업일 이내에 접수를 "
                       "확인하고 10영업일 이내에 결정합니다. 신고자에 대한 보복은 금지됩니다 (정관 9.5)."),
    "appeal_ask_text": ("✍️ Murojaatingizni batafsil yozing (10–2000 belgi).\n"
                        "Rasm, hujjat yoki ovozli xabarni keyingi qadamda qo'shishingiz mumkin.",
                        "✍️ Подробно опишите обращение (10–2000 символов).\n"
                        "Фото, документ или голосовое можно добавить на следующем шаге.",
                        "✍️ Describe your request in detail (10–2000 characters).\n"
                        "You can attach a photo, document or voice message in the next step.",
                        "✍️ 문의 내용을 자세히 적어주세요 (10–2000자).\n"
                        "다음 단계에서 사진, 문서, 음성 메시지를 첨부할 수 있습니다."),
    "appeal_bad_len": ("❗ Matn 10–2000 belgidan iborat bo'lishi kerak (hozir: {n}).",
                       "❗ Текст: 10–2000 символов (сейчас: {n}).",
                       "❗ Text must be 10–2000 characters (now: {n}).", "❗ 10–2000자여야 합니다 (현재: {n})."),
    "appeal_text_ok": ("📎 Matn qabul qilindi. Xohlasangiz, rasm, hujjat yoki ovozli xabar qo'shing (hozir: {n} ta).\n"
                       "Tayyor bo'lgach «✅ Yuborish» tugmasini bosing.",
                       "📎 Текст принят. При желании добавьте файлы (сейчас: {n}).\nЗатем нажмите «✅ Отправить».",
                       "📎 Text received. Attach files if you like (now: {n}).\nThen tap «✅ Send».",
                       "📎 내용이 접수되었습니다. 원하면 파일을 첨부하세요 (현재: {n}개).\n준비되면 «✅ 보내기»를 누르세요."),
    "appeal_file_added": ("📎 Qo'shildi ({n}/{max}).", "📎 Добавлено ({n}/{max}).", "📎 Added ({n}/{max}).",
                          "📎 추가됨 ({n}/{max})."),
    "appeal_file_limit": ("❗ Ko'pi bilan {max} ta fayl.", "❗ Не более {max} файлов.", "❗ Up to {max} files.",
                          "❗ 최대 {max}개 파일."),
    "btn_send": ("✅ Yuborish", "✅ Отправить", "✅ Send", "✅ 보내기"),
    "appeal_sent": ("✅ Murojaatingiz qabul qilindi. Raqami: <b>#{id}</b>\nJavob shu yerga keladi.",
                    "✅ Обращение принято. Номер: <b>#{id}</b>\nОтвет придёт сюда.",
                    "✅ Request received. Number: <b>#{id}</b>\nThe reply will come here.",
                    "✅ 문의가 접수되었습니다. 번호: <b>#{id}</b>\n답변은 여기로 옵니다."),
    "appeal_in_review": ("🔄 <b>#{id}</b> murojaatingiz ko'rib chiqilmoqda.", "🔄 Обращение <b>#{id}</b> рассматривается.",
                         "🔄 Request <b>#{id}</b> is being reviewed.", "🔄 문의 <b>#{id}</b>를 검토 중입니다."),
    "appeal_answer": ("💬 <b>#{id}</b> murojaatingizga javob:\n\n{text}", "💬 Ответ на обращение <b>#{id}</b>:\n\n{text}",
                      "💬 Reply to request <b>#{id}</b>:\n\n{text}", "💬 문의 <b>#{id}</b>에 대한 답변:\n\n{text}"),
    "appeal_closed": ("✅ <b>#{id}</b> murojaatingiz yopildi.", "✅ Обращение <b>#{id}</b> закрыто.",
                      "✅ Request <b>#{id}</b> is closed.", "✅ 문의 <b>#{id}</b>가 종료되었습니다."),
    "btn_reply": ("✍️ Javob yozish", "✍️ Ответить", "✍️ Reply", "✍️ 답장하기"),
    "reply_ask": ("✍️ <b>#{id}</b> bo'yicha javobingizni yozing:", "✍️ Напишите ответ по обращению <b>#{id}</b>:",
                  "✍️ Write your reply to <b>#{id}</b>:", "✍️ <b>#{id}</b>에 대한 답장을 쓰세요:"),
    "reply_sent": ("✅ Javobingiz yuborildi.", "✅ Ответ отправлен.", "✅ Reply sent.", "✅ 답장을 보냈습니다."),
    "appeal_is_closed": ("Bu murojaat yopilgan.", "Это обращение закрыто.", "This request is closed.",
                         "종료된 문의입니다."),
    "my_appeals_title": ("📋 <b>Murojaatlarim</b> (oxirgi 10 ta):", "📋 <b>Мои обращения</b> (последние 10):",
                         "📋 <b>My requests</b> (last 10):", "📋 <b>내 문의</b> (최근 10개):"),
    "my_appeals_empty": ("Sizda hali murojaatlar yo'q.", "У вас пока нет обращений.", "You have no requests yet.",
                         "아직 문의가 없습니다."),
    "appeal_detail": ("📨 <b>Murojaat #{id}</b> · {kind}\n📌 Holat: {status}\n🕒 Yuborilgan: {date}\n\n{history}",
                      "📨 <b>Обращение #{id}</b> · {kind}\n📌 Статус: {status}\n🕒 Отправлено: {date}\n\n{history}",
                      "📨 <b>Request #{id}</b> · {kind}\n📌 Status: {status}\n🕒 Sent: {date}\n\n{history}",
                      "📨 <b>문의 #{id}</b> · {kind}\n📌 상태: {status}\n🕒 보낸 날짜: {date}\n\n{history}"),
    "you": ("Siz", "Вы", "You", "나"),
    "club": ("Klub", "Клуб", "Club", "클럽"),
    "attachment": ("📎 ilova", "📎 вложение", "📎 attachment", "📎 첨부파일"),
    "st_new": ("🆕 Yangi", "🆕 Новое", "🆕 New", "🆕 신규"),
    "st_in_review": ("🔄 Ko'rib chiqilmoqda", "🔄 На рассмотрении", "🔄 In review", "🔄 검토 중"),
    "st_answered": ("💬 Javob berildi", "💬 Дан ответ", "💬 Answered", "💬 답변 완료"),
    "st_closed": ("✅ Yopildi", "✅ Закрыто", "✅ Closed", "✅ 종료"),

    # ================= tadbirlar =================
    "events_empty": ("📅 Hozircha ochiq tadbirlar yo'q. E'lonlar: @kiut_muloqot",
                     "📅 Пока нет открытых мероприятий. Анонсы: @kiut_muloqot",
                     "📅 No open events right now. Announcements: @kiut_muloqot",
                     "📅 현재 열린 행사가 없습니다. 공지: @kiut_muloqot"),
    "events_title": ("📅 <b>Tadbirlar</b> — barchasi bepul.\nTanlang:", "📅 <b>Мероприятия</b> — все бесплатно.\nВыберите:",
                     "📅 <b>Events</b> — all free.\nChoose one:", "📅 <b>행사</b> — 모두 무료입니다.\n선택하세요:"),
    "kind_session": ("Haftalik mashg'ulot", "Еженедельное занятие", "Weekly session", "정기 활동"),
    "kind_event": ("Tadbir", "Мероприятие", "Event", "행사"),
    "event_card": ("<b>{title}</b>\n<i>{kind}</i>\n\n🗓 Sana: {date}\n📍 Joy: {place}\n🎫 Joylar: {seats}\n"
                   "⭐ Qatnashgani uchun: {points} ball\n💳 Narxi: bepul\n\n{description}",
                   "<b>{title}</b>\n<i>{kind}</i>\n\n🗓 Дата: {date}\n📍 Место: {place}\n🎫 Места: {seats}\n"
                   "⭐ За участие: {points} балл(ов)\n💳 Цена: бесплатно\n\n{description}",
                   "<b>{title}</b>\n<i>{kind}</i>\n\n🗓 Date: {date}\n📍 Venue: {place}\n🎫 Seats: {seats}\n"
                   "⭐ Attendance: {points} point(s)\n💳 Price: free\n\n{description}",
                   "<b>{title}</b>\n<i>{kind}</i>\n\n🗓 날짜: {date}\n📍 장소: {place}\n🎫 좌석: {seats}\n"
                   "⭐ 참석 포인트: {points}\n💳 가격: 무료\n\n{description}"),
    "unlimited": ("cheklanmagan", "без ограничений", "unlimited", "제한 없음"),
    "btn_register_event": ("✍️ Yozilish", "✍️ Записаться", "✍️ Sign up", "✍️ 신청하기"),
    "btn_cancel_ticket": ("🚫 Chiptani bekor qilish", "🚫 Отменить билет", "🚫 Cancel ticket", "🚫 티켓 취소"),
    "event_full": ("😔 Joylar tugagan.", "😔 Мест нет.", "😔 No seats left.", "😔 좌석이 없습니다."),
    "event_closed": ("Bu tadbirga ro'yxatdan o'tish yopilgan.", "Регистрация закрыта.", "Registration is closed.",
                     "신청이 마감되었습니다."),
    "ticket_caption": ("🎟 <b>{title}</b>\n🗓 {date}\n📍 {place}\n🔑 Chipta: <code>{code}</code>\n\n"
                       "Kirishda QR-chiptani ko'rsating — davomat va ball shu orqali hisoblanadi.",
                       "🎟 <b>{title}</b>\n🗓 {date}\n📍 {place}\n🔑 Билет: <code>{code}</code>\n\n"
                       "Покажите QR-билет на входе — так отмечается посещаемость и баллы.",
                       "🎟 <b>{title}</b>\n🗓 {date}\n📍 {place}\n🔑 Ticket: <code>{code}</code>\n\n"
                       "Show this QR ticket at the entrance — it records your attendance and points.",
                       "🎟 <b>{title}</b>\n🗓 {date}\n📍 {place}\n🔑 티켓: <code>{code}</code>\n\n"
                       "입장 시 QR 티켓을 보여주세요 — 출석과 포인트가 기록됩니다."),
    "ticket_cancelled": ("🚫 Chipta bekor qilindi.", "🚫 Билет отменён.", "🚫 Ticket cancelled.", "🚫 티켓이 취소되었습니다."),
    "tickets_empty": ("Sizda hozircha chiptalar yo'q. «📅 Tadbirlar» bo'limidan yozilishingiz mumkin.",
                      "У вас пока нет билетов. Записаться можно в «📅 Мероприятия».",
                      "You have no tickets yet. Sign up in «📅 Events».",
                      "아직 티켓이 없습니다. «📅 행사»에서 신청하세요."),
    "tickets_title": ("🎟 <b>Chiptalarim</b>:", "🎟 <b>Мои билеты</b>:", "🎟 <b>My tickets</b>:", "🎟 <b>내 티켓</b>:"),
    "checked_in": ("✅ «{title}» — davomat belgilandi. Xush kelibsiz!", "✅ «{title}» — посещение отмечено. Добро пожаловать!",
                   "✅ «{title}» — attendance recorded. Welcome!", "✅ «{title}» — 출석이 기록되었습니다. 환영합니다!"),
    "event_reminder": ("🔔 Eslatma: «{title}» — {date}, {place}. Chiptangiz «🎟 Chiptalarim» bo'limida.",
                       "🔔 Напоминание: «{title}» — {date}, {place}. Билет в «🎟 Мои билеты».",
                       "🔔 Reminder: «{title}» — {date}, {place}. Your ticket is in «🎟 My tickets».",
                       "🔔 알림: «{title}» — {date}, {place}. 티켓은 «🎟 내 티켓»에 있습니다."),

    # ================= ko'ngillilar =================
    "vol_empty": ("Hozircha ko'ngillilar kerak bo'lgan tadbirlar yo'q.", "Сейчас волонтёры не требуются.",
                  "No events need volunteers right now.", "현재 봉사자가 필요한 행사가 없습니다."),
    "vol_title": ("🙋 Ko'ngillilar kerak bo'lgan tadbirlar (ko'ngilli yordam — 2 ball):",
                  "🙋 Мероприятия, где нужны волонтёры (волонтёрство — 2 балла):",
                  "🙋 Events looking for volunteers (volunteering — 2 points):",
                  "🙋 봉사자를 모집하는 행사 (봉사 — 2 포인트):"),
    "vol_applied": ("✅ Arizangiz yuborildi. Natija shu yerga keladi.", "✅ Заявка отправлена. Результат придёт сюда.",
                    "✅ Application sent. You'll be notified here.", "✅ 신청이 완료되었습니다. 결과는 여기로 옵니다."),
    "vol_already": ("Siz bu tadbirga allaqachon ariza bergansiz.", "Вы уже подали заявку.", "You have already applied.",
                    "이미 신청했습니다."),
    "vol_accepted": ("🎉 «{title}» tadbiriga ko'ngilli sifatida qabul qilindingiz!",
                     "🎉 Вы приняты волонтёром на «{title}»!", "🎉 You're accepted as a volunteer for «{title}»!",
                     "🎉 «{title}» 봉사자로 선정되었습니다!"),
    "vol_rejected": ("«{title}» bo'yicha ko'ngillilik arizangiz bu safar qabul qilinmadi. Rahmat!",
                     "Заявка волонтёра на «{title}» в этот раз не принята. Спасибо!",
                     "Your volunteer application for «{title}» wasn't accepted this time. Thank you!",
                     "«{title}» 봉사 신청이 이번에는 선정되지 않았습니다. 감사합니다!"),
    "btn_apply_vol": ("🙋 Ariza berish", "🙋 Подать заявку", "🙋 Apply", "🙋 신청하기"),

    # ================= FAQ / hujjatlar =================
    "faq_empty": ("❓ Savollar hali qo'shilmagan. Savolingiz bo'lsa — «✉️ Murojaat».",
                  "❓ Вопросы пока не добавлены. Есть вопрос — «✉️ Обращение».",
                  "❓ No FAQ yet. Have a question? Use «✉️ Contact us».",
                  "❓ 아직 등록된 질문이 없습니다. 문의는 «✉️ 문의하기»."),
    "faq_title": ("❓ <b>Ko'p beriladigan savollar</b>\nSavolni tanlang:", "❓ <b>Частые вопросы</b>\nВыберите вопрос:",
                  "❓ <b>FAQ</b>\nChoose a question:", "❓ <b>자주 묻는 질문</b>\n질문을 선택하세요:"),
    "docs_title": ("📄 <b>Klub hujjatlari</b>\nKerakli hujjatni tanlang:", "📄 <b>Документы клуба</b>\nВыберите документ:",
                   "📄 <b>Club documents</b>\nChoose a document:", "📄 <b>클럽 문서</b>\n문서를 선택하세요:"),
    "doc_ustav": ("📘 Ustav", "📘 Устав", "📘 Charter", "📘 정관"),
    "doc_nizom": ("📗 Nizom", "📗 Положение", "📗 Regulations", "📗 규정"),
    "doc_blanka": ("📝 A'zolik blankasi (Word)", "📝 Анкета (Word)", "📝 Membership form (Word)", "📝 가입 신청서 (Word)"),
    "doc_taqdimot": ("📊 Taqdimot", "📊 Презентация", "📊 Presentation", "📊 프레젠테이션"),
    "doc_missing": ("Fayl hozircha mavjud emas.", "Файл пока недоступен.", "File is not available yet.",
                    "파일을 아직 사용할 수 없습니다."),
    "docs_note": ("<i>Ustav va nizom loyiha holatida: tashkiliy yig'ilishda qabul qilinib, universitet bilan "
                  "kelishilgunga qadar rasmiy hujjat hisoblanmaydi.</i>",
                  "<i>Устав и положение — проекты: официальными они станут после принятия на учредительном "
                  "собрании и согласования с университетом.</i>",
                  "<i>The Charter and Regulations are drafts until adopted at the founding meeting and approved "
                  "by the university.</i>",
                  "<i>정관과 규정은 창립 총회 채택 및 대학 승인 전까지 초안입니다.</i>"),

    # ================= sozlamalar =================
    "settings": ("⚙️ <b>Sozlamalar</b>\n\nProfilingiz:\n\n{profile}", "⚙️ <b>Настройки</b>\n\nВаш профиль:\n\n{profile}",
                 "⚙️ <b>Settings</b>\n\nYour profile:\n\n{profile}", "⚙️ <b>설정</b>\n\n내 프로필:\n\n{profile}"),
    "btn_edit_profile": ("✏️ Profilni tahrirlash", "✏️ Редактировать профиль", "✏️ Edit profile", "✏️ 프로필 수정"),
    "btn_change_lang": ("🌐 Tilni o'zgartirish", "🌐 Сменить язык", "🌐 Change language", "🌐 언어 변경"),
    "edit_profile_pick": ("✏️ Qaysi ma'lumotni o'zgartirasiz?", "✏️ Что изменить?", "✏️ What do you want to change?",
                          "✏️ 무엇을 수정할까요?"),
    "pf_full_name": ("👤 F.I.Sh", "👤 ФИО", "👤 Name", "👤 성명"),
    "pf_direction": ("🎓 Yo'nalish", "🎓 Направление", "🎓 Field", "🎓 전공"),
    "pf_course": ("📚 Kurs", "📚 Курс", "📚 Year", "📚 학년"),
    "pf_group_name": ("👥 Guruh", "👥 Группа", "👥 Group", "👥 그룹"),
    "pf_student_id": ("🪪 Guvohnoma", "🪪 Студ. билет", "🪪 Student ID", "🪪 학생증"),
    "pf_phone": ("📱 Telefon", "📱 Телефон", "📱 Phone", "📱 전화"),
    "pf_photo_id": ("📸 Surat", "📸 Фото", "📸 Photo", "📸 사진"),
    "pf_all": ("🔁 Hammasini qaytadan", "🔁 Всё заново", "🔁 Redo everything", "🔁 전체 다시"),
    "pf_saved": ("✅ Saqlandi.", "✅ Сохранено.", "✅ Saved.", "✅ 저장되었습니다."),
    "bot_description": (
        "MULOQOT — KIUT talabalarining xalqaro munosabatlar klubi.\n\n"
        "Bu bot orqali: klubga a'zo bo'lasiz va elektron guvohnoma olasiz, debat, Model UN va treninglarga "
        "QR-chipta bilan yozilasiz, ball va reytingingizni kuzatasiz, savol, taklif yoki shikoyat yuborasiz.\n\n"
        "A'zolik ixtiyoriy va bepul. Boshlash uchun «Start» ni bosing.",
        "MULOQOT — клуб международных отношений студентов KIUT.\n\n"
        "Через бота можно: вступить в клуб и получить электронное удостоверение, записаться на дебаты, Model UN и "
        "тренинги по QR-билету, следить за баллами и рейтингом, отправить вопрос, предложение или жалобу.\n\n"
        "Членство добровольное и бесплатное. Нажмите «Start», чтобы начать.",
        "MULOQOT — the KIUT students' International Relations Club.\n\n"
        "With this bot you can join the club and get an e-membership card, sign up for debates, Model UN and "
        "trainings with a QR ticket, track your points and rating, and send questions, ideas or complaints.\n\n"
        "Membership is voluntary and free. Tap «Start» to begin.",
        "MULOQOT — KIUT 학생 국제관계 클럽입니다.\n\n"
        "이 봇으로 클럽에 가입하고 전자 회원증을 받고, QR 티켓으로 토론·모의유엔·트레이닝에 신청하고, "
        "포인트와 랭킹을 확인하고, 질문·제안·신고를 보낼 수 있습니다.\n\n가입은 자율적이며 무료입니다. «Start»를 누르세요."),
    "bot_short_description": (
        "KIUT xalqaro munosabatlar klubi: a'zolik guvohnomasi, tadbirlar, QR-chipta, reyting.",
        "Клуб международных отношений KIUT: членский билет, мероприятия, QR-билеты, рейтинг.",
        "KIUT International Relations Club: membership card, events, QR tickets, rating.",
        "KIUT 국제관계 클럽: 회원증, 행사, QR 티켓, 랭킹."),
    "cmd_start": ("Bosh menyu", "Главное меню", "Main menu", "메인 메뉴"),
    "btn_delete_data": ("🗑 Ma'lumotlarimni o'chirish", "🗑 Удалить мои данные", "🗑 Delete my data", "🗑 내 데이터 삭제"),
    "delete_confirm": ("⚠️ Roziligingizni qaytarib olib, barcha ma'lumotlaringizni (a'zolik, ball, chiptalar, "
                       "murojaatlar) o'chirishni so'raysizmi? Ma'lumot 5 ish kuni ichida o'chiriladi.",
                       "⚠️ Отозвать согласие и удалить все ваши данные (членство, баллы, билеты, обращения)? "
                       "Данные будут удалены в течение 5 рабочих дней.",
                       "⚠️ Withdraw consent and delete all your data (membership, points, tickets, requests)? "
                       "Data will be deleted within 5 working days.",
                       "⚠️ 동의를 철회하고 모든 데이터(회원정보, 포인트, 티켓, 문의)를 삭제하시겠습니까? "
                       "데이터는 5영업일 이내에 삭제됩니다."),
    "delete_requested": ("✅ So'rovingiz qabul qilindi. Ma'lumotlaringiz 5 ish kuni ichida o'chiriladi.",
                         "✅ Запрос принят. Данные будут удалены в течение 5 рабочих дней.",
                         "✅ Request received. Your data will be deleted within 5 working days.",
                         "✅ 요청이 접수되었습니다. 5영업일 이내에 데이터가 삭제됩니다."),
    "data_deleted": ("🗑 Ma'lumotlaringiz o'chirildi. Qaytish uchun: /start", "🗑 Ваши данные удалены. Вернуться: /start",
                     "🗑 Your data has been deleted. To come back: /start", "🗑 데이터가 삭제되었습니다. 다시 시작: /start"),

    # ================= klub haqida =================
    "about_menu": ("ℹ️ <b>MULOQOT — xalqaro munosabatlar klubi</b>\n<i>Bilimdan ko'nikmaga, ko'nikmadan yetakchilikka</i>\n\nBo'limni tanlang:",
                   "ℹ️ <b>MULOQOT — клуб международных отношений</b>\n<i>От знаний к навыкам, от навыков к лидерству</i>\n\nВыберите раздел:",
                   "ℹ️ <b>MULOQOT — International Relations Club</b>\n<i>From knowledge to skills, from skills to leadership</i>\n\nChoose a topic:",
                   "ℹ️ <b>MULOQOT — 국제관계 클럽</b>\n<i>지식에서 역량으로, 역량에서 리더십으로</i>\n\n항목을 선택하세요:"),
    "ab_mission": ("🎯 Maqsad va missiya", "🎯 Цель и миссия", "🎯 Goal & mission", "🎯 목표와 미션"),
    "ab_directions": ("🧭 Yo'nalishlar", "🧭 Направления", "🧭 Activities", "🧭 활동 분야"),
    "ab_modules": ("🌍 Tematik modullar", "🌍 Тематические модули", "🌍 Thematic modules", "🌍 주제별 모듈"),
    "ab_structure": ("🏛 Boshqaruv", "🏛 Управление", "🏛 Governance", "🏛 운영 구조"),
    "ab_leaders": ("👥 Rahbariyat", "👥 Руководство", "👥 Leadership", "👥 운영진"),
    "ab_rhythm": ("🗓 Ish tartibi", "🗓 Ритм работы", "🗓 How we work", "🗓 활동 일정"),
    "ab_links": ("🔗 Ijtimoiy tarmoqlar", "🔗 Соцсети", "🔗 Social media", "🔗 소셜 미디어"),
    "ab_mission_text": (
        "🎯 <b>Bosh maqsad</b>\nKIUT talabalarini xalqaro masalalar atrofida birlashtirib, darsda olingan bilimni "
        "debat, Model UN, simulyatsiya va tahliliy ish orqali amaliy ko'nikmaga aylantirish.\n\n"
        "<b>Missiya:</b> talabalarni muloqot orqali muammo yechadigan, dalil bilan gapiradigan va mas'uliyatni "
        "o'z zimmasiga oladigan yosh yetakchilar sifatida shakllantirish.\n\n"
        "<b>Vizyon:</b> MULOQOT KIUTda xalqaro munosabatlar bo'yicha eng faol amaliy maydonga aylanadi.\n\n"
        "<b>Tamoyillar:</b> ixtiyoriylik, teng imkoniyat, ochiqlik, mas'uliyat, akademik halollik, dunyoviylik, "
        "siyosiy betaraflik.\n\nA'zolik barcha fakultet talabalari uchun ochiq va bepul.",
        "🎯 <b>Главная цель</b>\nОбъединить студентов KIUT вокруг международных вопросов и превратить знания "
        "с занятий в практические навыки через дебаты, Model UN, симуляции и аналитику.\n\n"
        "<b>Миссия:</b> воспитывать молодых лидеров, которые решают проблемы через диалог, говорят аргументированно "
        "и берут на себя ответственность.\n\n<b>Видение:</b> MULOQOT — самая активная практическая площадка KIUT "
        "по международным отношениям.\n\n<b>Принципы:</b> добровольность, равные возможности, открытость, "
        "ответственность, академическая честность, светскость, политическая нейтральность.\n\n"
        "Членство открыто для студентов всех факультетов и бесплатно.",
        "🎯 <b>Main goal</b>\nTo unite KIUT students around international issues and turn classroom knowledge into "
        "practical skills through debate, Model UN, simulations and analysis.\n\n"
        "<b>Mission:</b> to develop young leaders who solve problems through dialogue, argue with evidence and take "
        "responsibility.\n\n<b>Vision:</b> MULOQOT becomes KIUT's most active practical platform for international "
        "relations.\n\n<b>Principles:</b> voluntariness, equal opportunity, openness, responsibility, academic "
        "integrity, secularism, political neutrality.\n\nMembership is open to all faculties and free.",
        "🎯 <b>핵심 목표</b>\nKIUT 학생들을 국제 이슈를 중심으로 모으고, 토론·모의유엔·시뮬레이션·분석을 통해 "
        "수업에서 배운 지식을 실무 역량으로 바꿉니다.\n\n<b>미션:</b> 대화로 문제를 해결하고, 근거로 말하며, "
        "책임을 지는 젊은 리더를 양성합니다.\n\n<b>비전:</b> KIUT에서 가장 활발한 국제관계 실습의 장.\n\n"
        "<b>원칙:</b> 자율성, 기회 균등, 개방성, 책임, 학문적 정직성, 세속성, 정치적 중립.\n\n"
        "모든 학부 학생에게 열려 있으며 무료입니다."),
    "ab_directions_text": (
        "🧭 <b>Sakkiz yo'nalish</b>\n\n"
        "🎤 <b>Debat</b> — muntazam mashg'ulotlar va ichki turnirlar <i>(Xalqaro munosabatlar)</i>\n"
        "🇺🇳 <b>Model UN</b> — universitet ichidagi konferensiyalar, delegat tayyorlash <i>(Xalqaro munosabatlar)</i>\n"
        "🔄 <b>Simulyatsiyalar</b> — muzokara va inqirozni boshqarish <i>(Xalqaro munosabatlar)</i>\n"
        "📊 <b>Tahliliy ishlar</b> — xalqaro masalalar bo'yicha tahlil va sharhlar <i>(Ta'lim va ilmiy-tadqiqot)</i>\n"
        "🎓 <b>Treninglar</b> — notiqlik, jamoa va loyiha boshqaruvi <i>(Yoshlar salohiyati va liderlik)</i>\n"
        "🤝 <b>Ochiq uchrashuvlar</b> — diplomatlar va soha mutaxassislari bilan <i>(Xalqaro munosabatlar)</i>\n"
        "📣 <b>Media va PR</b> — ijtimoiy tarmoqlar, foto-video, dizayn va klub haqidagi xabarlar <i>(Media va jamoatchilik bilan aloqalar)</i>\n"
        "🆘 <b>KIUT SOS</b> — tartib-intizomni nazorat qiluvchi guruh <i>(Etika va intizom komissiyasi bilan)</i>\n\n"
        "Haftalik mashg'ulot 60 daqiqa: 10 daqiqa mavzu, 40 daqiqa mashq, 10 daqiqa fikr-mulohaza.",
        "🧭 <b>Восемь направлений</b>\n\n"
        "🎤 <b>Дебаты</b> — регулярные занятия и внутренние турниры <i>(Международные отношения)</i>\n"
        "🇺🇳 <b>Model UN</b> — конференции внутри университета, подготовка делегатов <i>(Международные отношения)</i>\n"
        "🔄 <b>Симуляции</b> — переговоры и кризисное управление <i>(Международные отношения)</i>\n"
        "📊 <b>Аналитика</b> — анализ и комментарии по международным вопросам <i>(Образование и исследования)</i>\n"
        "🎓 <b>Тренинги</b> — ораторское мастерство, командная работа, управление проектами <i>(Потенциал молодёжи и лидерство)</i>\n"
        "🤝 <b>Открытые встречи</b> — с дипломатами и экспертами <i>(Международные отношения)</i>\n"
        "📣 <b>Медиа и PR</b> — соцсети, фото и видео, дизайн и новости клуба <i>(Медиа и связи с общественностью)</i>\n"
        "🆘 <b>KIUT SOS</b> — группа, которая следит за порядком и дисциплиной <i>(вместе с Комиссией по этике и дисциплине)</i>\n\n"
        "Еженедельное занятие — 60 минут: 10 мин тема, 40 мин практика, 10 мин обратная связь.",
        "🧭 <b>Eight activities</b>\n\n"
        "🎤 <b>Debate</b> — regular sessions and internal tournaments <i>(International relations)</i>\n"
        "🇺🇳 <b>Model UN</b> — on-campus conferences, delegate training <i>(International relations)</i>\n"
        "🔄 <b>Simulations</b> — negotiation and crisis management <i>(International relations)</i>\n"
        "📊 <b>Analysis</b> — analysis and commentary on international issues <i>(Education & research)</i>\n"
        "🎓 <b>Trainings</b> — public speaking, teamwork, project management <i>(Youth potential & leadership)</i>\n"
        "🤝 <b>Open meetings</b> — with diplomats and experts <i>(International relations)</i>\n"
        "📣 <b>Media & PR</b> — social media, photo and video, design and club news <i>(Media & public relations)</i>\n"
        "🆘 <b>KIUT SOS</b> — a team that monitors order and discipline <i>(with the Ethics & Discipline Commission)</i>\n\n"
        "Weekly session — 60 min: 10 min topic, 40 min practice, 10 min feedback.",
        "🧭 <b>8개 활동 분야</b>\n\n"
        "🎤 <b>토론</b> — 정기 활동과 내부 대회 <i>(국제관계)</i>\n"
        "🇺🇳 <b>모의유엔</b> — 교내 회의, 대표단 준비 <i>(국제관계)</i>\n"
        "🔄 <b>시뮬레이션</b> — 협상과 위기관리 <i>(국제관계)</i>\n"
        "📊 <b>분석</b> — 국제 이슈 분석과 논평 <i>(교육·연구)</i>\n"
        "🎓 <b>트레이닝</b> — 스피치, 팀워크, 프로젝트 관리 <i>(청년 역량·리더십)</i>\n"
        "🤝 <b>공개 만남</b> — 외교관 및 전문가와의 대화 <i>(국제관계)</i>\n"
        "📣 <b>미디어·PR</b> — SNS, 사진·영상, 디자인, 클럽 소식 <i>(미디어·대외협력)</i>\n"
        "🆘 <b>KIUT SOS</b> — 질서와 규율을 관리하는 그룹 <i>(윤리·징계위원회와 함께)</i>\n\n"
        "정기 활동 60분: 주제 10분, 실습 40분, 피드백 10분."),
    "ab_modules_text": (
        "🌍 <b>Olti modul: global masala, O'zbekiston nuqtai nazari</b>\n\n"
        "1. <b>Geosiyosat</b> — ko'p qutblilik, o'rta davlatlar, Markaziy Osiyo\n"
        "2. <b>Iqtisodiy diplomatiya</b> — savdo, investitsiya, transport koridorlari\n"
        "3. <b>Xalqaro xavfsizlik</b> — terrorizm, kiberxavfsizlik, Afg'oniston\n"
        "4. <b>Texnologiya</b> — sun'iy intellekt, kosmos, raqamli diplomatiya\n"
        "5. <b>Iqlim va ekologiya</b> — Parij kelishuvi, Orol, suv-energetika\n"
        "6. <b>Inson xavfsizligi</b> — inson huquqlari, sog'liq, BMT islohoti",
        "🌍 <b>Шесть модулей: глобальная проблема, взгляд Узбекистана</b>\n\n"
        "1. <b>Геополитика</b> — многополярность, средние державы, Центральная Азия\n"
        "2. <b>Экономическая дипломатия</b> — торговля, инвестиции, транспортные коридоры\n"
        "3. <b>Международная безопасность</b> — терроризм, кибербезопасность, Афганистан\n"
        "4. <b>Технологии</b> — ИИ, космос, цифровая дипломатия\n"
        "5. <b>Климат и экология</b> — Парижское соглашение, Арал, вода и энергетика\n"
        "6. <b>Безопасность человека</b> — права человека, здоровье, реформа ООН",
        "🌍 <b>Six modules: global issue, Uzbekistan's perspective</b>\n\n"
        "1. <b>Geopolitics</b> — multipolarity, middle powers, Central Asia\n"
        "2. <b>Economic diplomacy</b> — trade, investment, transport corridors\n"
        "3. <b>International security</b> — terrorism, cybersecurity, Afghanistan\n"
        "4. <b>Technology</b> — AI, space, digital diplomacy\n"
        "5. <b>Climate & ecology</b> — Paris Agreement, Aral Sea, water-energy\n"
        "6. <b>Human security</b> — human rights, health, UN reform",
        "🌍 <b>6개 모듈: 글로벌 이슈, 우즈베키스탄의 관점</b>\n\n"
        "1. <b>지정학</b> — 다극화, 중견국, 중앙아시아\n"
        "2. <b>경제 외교</b> — 무역, 투자, 교통 회랑\n"
        "3. <b>국제 안보</b> — 테러리즘, 사이버 보안, 아프가니스탄\n"
        "4. <b>기술</b> — 인공지능, 우주, 디지털 외교\n"
        "5. <b>기후와 환경</b> — 파리 협정, 아랄해, 물·에너지\n"
        "6. <b>인간 안보</b> — 인권, 보건, 유엔 개혁"),
    "ab_structure_text": (
        "🏛 <b>Boshqaruv</b> <i>(tashkiliy boshqaruv modeli, 2026)</i>\n\n"
        "<b>Oliy boshqaruv kengashi</b> — strategiya, nizomlar va rahbariyat ustidan nazorat; kamida har chorakda yig'iladi.\n"
        "<b>Rahbariyat</b> — Prezident, Birinchi vitse-prezident, Ijrochi direktor, yo'nalish kuratorlari, maslahatchilar.\n"
        "<b>Markaziy tuzilmalar</b> — Bosh kotibiyat · Tashqi aloqalar va hamkorlik · Monitoring va tahlil · "
        "Inson resurslari va a'zolik · Tadbirlar va protokol.\n"
        "<b>Etika va intizom komissiyasi</b> — mustaqil; shikoyat va nizolarni maxfiy ko'rib chiqadi.\n\n"
        "<b>Olti bo'lim:</b>\n"
        "1. Xalqaro munosabatlar, diplomatiya va global hamkorlik\n"
        "2. Yoshlar salohiyati, liderlik va professional rivojlanish\n"
        "3. Axborot siyosati, media va jamoatchilik bilan aloqalar\n"
        "4. Huquqiy savodxonlik, inson huquqlari va jamoat siyosati\n"
        "5. Innovatsion tashabbuslar, tadbirkorlik va ijtimoiy loyihalar\n"
        "6. Ta'lim, ilmiy-tadqiqot va bilimlarni amaliyotga tatbiq etish\n\n"
        "<b>A'zolik darajalari:</b> kuzatuvchi → nomzod a'zo → faol a'zo → yetakchi a'zo · ekspert/mentor · faxriy a'zo.",
        "🏛 <b>Управление</b> <i>(организационная модель, 2026)</i>\n\n"
        "<b>Высший совет</b> — стратегия, положения и контроль руководства; собирается не реже раза в квартал.\n"
        "<b>Руководство</b> — Президент, Первый вице-президент, Исполнительный директор, кураторы направлений, советники.\n"
        "<b>Центральные структуры</b> — Генеральный секретариат · Внешние связи и партнёрство · Мониторинг и анализ · "
        "Кадры и членство · Мероприятия и протокол.\n"
        "<b>Комиссия по этике и дисциплине</b> — независимая; конфиденциально рассматривает жалобы и споры.\n\n"
        "<b>Шесть отделов:</b>\n"
        "1. Международные отношения, дипломатия и глобальное сотрудничество\n"
        "2. Потенциал молодёжи, лидерство и профессиональное развитие\n"
        "3. Информационная политика, медиа и связи с общественностью\n"
        "4. Правовая грамотность, права человека и публичная политика\n"
        "5. Инновации, предпринимательство и социальные проекты\n"
        "6. Образование, исследования и внедрение знаний в практику\n\n"
        "<b>Уровни членства:</b> наблюдатель → кандидат → активный член → ведущий член · эксперт/ментор · почётный член.",
        "🏛 <b>Governance</b> <i>(organisational model, 2026)</i>\n\n"
        "<b>Supreme Board</b> — strategy, regulations and oversight of leadership; meets at least quarterly.\n"
        "<b>Leadership</b> — President, First Vice-President, Executive Director, area curators, advisers.\n"
        "<b>Central units</b> — General Secretariat · External Relations & Partnerships · Monitoring & Analysis · "
        "People & Membership · Events & Protocol.\n"
        "<b>Ethics & Discipline Commission</b> — independent; handles complaints and disputes confidentially.\n\n"
        "<b>Six departments:</b>\n"
        "1. International relations, diplomacy & global cooperation\n"
        "2. Youth potential, leadership & professional development\n"
        "3. Information policy, media & public relations\n"
        "4. Legal literacy, human rights & public policy\n"
        "5. Innovation, entrepreneurship & social projects\n"
        "6. Education, research & knowledge into practice\n\n"
        "<b>Membership levels:</b> observer → candidate → active member → lead member · expert/mentor · honorary member.",
        "🏛 <b>운영 구조</b> <i>(조직 운영 모델, 2026)</i>\n\n"
        "<b>최고 운영위원회</b> — 전략, 규정, 운영진 감독; 최소 분기 1회 개최.\n"
        "<b>운영진</b> — 회장, 제1부회장, 사무총장(집행), 분야 담당, 자문위원.\n"
        "<b>중앙 조직</b> — 사무국 · 대외협력 · 모니터링·분석 · 인사·회원 · 행사·의전.\n"
        "<b>윤리·징계위원회</b> — 독립 기구; 신고와 분쟁을 비공개로 처리.\n\n"
        "<b>6개 부서:</b>\n"
        "1. 국제관계·외교·글로벌 협력\n"
        "2. 청년 역량·리더십·전문성 개발\n"
        "3. 정보 정책·미디어·대외협력\n"
        "4. 법률 소양·인권·공공정책\n"
        "5. 혁신·창업·사회 프로젝트\n"
        "6. 교육·연구·지식의 실천\n\n"
        "<b>회원 등급:</b> 참관인 → 후보 회원 → 활동 회원 → 리더 회원 · 전문가/멘토 · 명예 회원."),
    "ab_leaders_text": (
        "👥 <b>Rahbariyat</b>\n\n<b>Kengash raisi</b> — Usarov I. I. (tashabbuskor)\n"
        "<b>Kengash kotibi</b> — Isroilova M. E.\n<b>Kengash ijrochisi</b> — Irisbayev O. E.\n"
        "<b>Kengash maslahatchisi</b> — Tursunov M. T.\n\n"
        "• <b>Kotib</b> — kerakli xat-hujjatlar va qilinadigan ishlar rejasini tuzadi.\n"
        "• <b>Ijrochi</b> — ishlar ijrosini ta'minlaydi.\n"
        "• <b>Maslahatchi</b> — ijrochi va kotibning ishlar jadvali bilan tanishadi, reja konsepsiyasini amalda "
        "bosqichlar asosida bayonnoma va hisobotlarga aylantiradi.\n\n"
        "<i>Birinchi Kengash tashkiliy yig'ilishda saylanadi.</i>",
        "👥 <b>Руководство</b>\n\n<b>Председатель совета</b> — Усаров И. И. (инициатор)\n"
        "<b>Секретарь</b> — Исроилова М. Э.\n<b>Исполнитель</b> — Ирисбаев О. Э.\n<b>Советник</b> — Турсунов М. Т.\n\n"
        "• <b>Секретарь</b> — готовит письма, документы и план работ.\n"
        "• <b>Исполнитель</b> — обеспечивает выполнение работ.\n"
        "• <b>Советник</b> — изучает график работ, оформляет протоколы и отчёты по этапам плана.\n\n"
        "<i>Первый Совет избирается на учредительном собрании.</i>",
        "👥 <b>Leadership</b>\n\n<b>Council Chair</b> — Usarov I. I. (founder)\n<b>Secretary</b> — Isroilova M. E.\n"
        "<b>Executive</b> — Irisbayev O. E.\n<b>Adviser</b> — Tursunov M. T.\n\n"
        "• <b>Secretary</b> — prepares letters, documents and the work plan.\n"
        "• <b>Executive</b> — ensures tasks are carried out.\n"
        "• <b>Adviser</b> — reviews the work schedule and prepares minutes and reports by plan stages.\n\n"
        "<i>The first Council is elected at the founding meeting.</i>",
        "👥 <b>운영진</b>\n\n<b>위원장</b> — Usarov I. I. (설립자)\n<b>서기</b> — Isroilova M. E.\n"
        "<b>집행</b> — Irisbayev O. E.\n<b>고문</b> — Tursunov M. T.\n\n"
        "• <b>서기</b> — 공문, 문서, 업무 계획을 작성합니다.\n• <b>집행</b> — 업무 수행을 책임집니다.\n"
        "• <b>고문</b> — 업무 일정을 검토하고 단계별 회의록과 보고서를 작성합니다.\n\n"
        "<i>첫 위원회는 창립 총회에서 선출됩니다.</i>"),
    "ab_rhythm_text": (
        "🗓 <b>Klub doimiy ritmda ishlaydi</b>\n\n• Har hafta — 1 ta mashg'ulot: debat, MUN yoki trening\n"
        "• Har 2 haftada — Kengash yig'ilishi\n• Har oy — 1 ta katta tadbir yoki ochiq uchrashuv\n"
        "• Har 30 kunda — dekanatga qisqa hisobot\n• Har semestr — Umumiy yig'ilish, moliyaviy hisobot\n"
        "• Har o'quv yili — rasmiy yangilash, saylov (aprel–may)\n\n"
        "<b>Birinchi 90 kun maqsadi:</b> 4 debat mashg'uloti, 1 ichki Model UN, 2 ochiq uchrashuv, "
        "1 hamkorlik kelishuvi loyihasi.\nImtihon davrida yirik tadbirlar o'tkazilmaydi.",
        "🗓 <b>Клуб работает в постоянном ритме</b>\n\n• Каждую неделю — 1 занятие: дебаты, MUN или тренинг\n"
        "• Каждые 2 недели — заседание Совета\n• Каждый месяц — 1 крупное мероприятие или открытая встреча\n"
        "• Каждые 30 дней — краткий отчёт в деканат\n• Каждый семестр — Общее собрание, финансовый отчёт\n"
        "• Каждый учебный год — обновление статуса, выборы (апрель–май)\n\n"
        "<b>Цели первых 90 дней:</b> 4 дебатных занятия, 1 внутренний Model UN, 2 открытые встречи, "
        "1 проект соглашения о партнёрстве.\nВ период экзаменов крупные мероприятия не проводятся.",
        "🗓 <b>The club works in a steady rhythm</b>\n\n• Weekly — 1 session: debate, MUN or training\n"
        "• Every 2 weeks — Council meeting\n• Monthly — 1 major event or open meeting\n"
        "• Every 30 days — short report to the dean's office\n• Each semester — General Assembly, financial report\n"
        "• Each academic year — official renewal, elections (April–May)\n\n"
        "<b>First 90 days:</b> 4 debate sessions, 1 internal Model UN, 2 open meetings, 1 partnership agreement draft.\n"
        "No major events during exam periods.",
        "🗓 <b>클럽은 일정한 리듬으로 운영됩니다</b>\n\n• 매주 — 정기 활동 1회: 토론, MUN 또는 트레이닝\n"
        "• 2주마다 — 위원회 회의\n• 매월 — 대형 행사 또는 공개 만남 1회\n• 30일마다 — 학장실에 간단한 보고서\n"
        "• 매 학기 — 총회, 재무 보고\n• 매 학년도 — 공식 갱신, 선거 (4–5월)\n\n"
        "<b>첫 90일 목표:</b> 토론 활동 4회, 교내 모의유엔 1회, 공개 만남 2회, 협력 협정 초안 1건.\n"
        "시험 기간에는 대형 행사를 열지 않습니다."),
    "ab_links_text": ("🔗 <b>Bizni kuzating</b>\n\nTelegram: {tg}\nInstagram: {ig}\n\nKIUT · Toshkent",
                      "🔗 <b>Следите за нами</b>\n\nTelegram: {tg}\nInstagram: {ig}\n\nKIUT · Ташкент",
                      "🔗 <b>Follow us</b>\n\nTelegram: {tg}\nInstagram: {ig}\n\nKIUT · Tashkent",
                      "🔗 <b>팔로우하세요</b>\n\nTelegram: {tg}\nInstagram: {ig}\n\nKIUT · 타슈켄트"),
}

# Variantli tanlovlar (ariza uchun). Har bir variant: kalit -> 4 tildagi nom.
OPTIONS: dict[str, dict[str, tuple[str, str, str, str]]] = {
    "edu_lang": {
        "uz": ("O'zbek", "Узбекский", "Uzbek", "우즈베크어"),
        "ru": ("Rus", "Русский", "Russian", "러시아어"),
        "en": ("Ingliz", "Английский", "English", "영어"),
    },
    # 6 ta asosiy bo'lim — «MULOQOT tashkiliy boshqaruv modeli» (2026) bo'yicha
    "section": {
        "intl": ("Xalqaro munosabatlar va diplomatiya", "Международные отношения и дипломатия",
                 "International relations & diplomacy", "국제관계·외교"),
        "youth": ("Yoshlar salohiyati va liderlik", "Потенциал молодёжи и лидерство", "Youth potential & leadership",
                  "청년 역량·리더십"),
        "media": ("Media va jamoatchilik bilan aloqalar", "Медиа и связи с общественностью", "Media & public relations",
                  "미디어·대외협력"),
        "law": ("Huquqiy savodxonlik va inson huquqlari", "Правовая грамотность и права человека",
                "Legal literacy & human rights", "법률 소양·인권"),
        "innov": ("Innovatsiya va ijtimoiy loyihalar", "Инновации и социальные проекты", "Innovation & social projects",
                  "혁신·사회 프로젝트"),
        "research": ("Ta'lim va ilmiy-tadqiqot", "Образование и исследования", "Education & research", "교육·연구"),
        "none": ("Hozircha faqat qatnashaman", "Пока просто участвую", "Just participating for now", "우선 참여만"),
    },
    # a'zolik darajalari (modelning VI bo'limi)
    "level": {
        "observer": ("Kuzatuvchi", "Наблюдатель", "Observer", "참관인"),
        "candidate": ("Nomzod a'zo", "Кандидат в члены", "Candidate member", "후보 회원"),
        "active": ("Faol a'zo", "Активный член", "Active member", "활동 회원"),
        "leader": ("Yetakchi a'zo", "Ведущий член", "Lead member", "리더 회원"),
        "expert": ("Ekspert / mentor", "Эксперт / ментор", "Expert / mentor", "전문가·멘토"),
        "honorary": ("Faxriy a'zo", "Почётный член", "Honorary member", "명예 회원"),
    },
    "directions": {
        "debate": ("Debat", "Дебаты", "Debate", "토론"),
        "mun": ("Model UN", "Model UN", "Model UN", "모의유엔"),
        "sim": ("Simulyatsiya va muzokara", "Симуляции и переговоры", "Simulation & negotiation", "시뮬레이션·협상"),
        "analysis": ("Tahliliy ishlar", "Аналитика", "Analysis", "분석"),
        "training": ("Treninglar", "Тренинги", "Trainings", "트레이닝"),
        "experts": ("Mutaxassislar bilan uchrashuv", "Встречи с экспертами", "Meeting experts", "전문가와의 만남"),
        "media": ("Media va PR", "Медиа и PR", "Media & PR", "미디어·PR"),
        "sos": ("KIUT SOS (tartib-intizom)", "KIUT SOS (порядок и дисциплина)", "KIUT SOS (order & discipline)", "KIUT SOS (질서·규율)"),
    },
    "skills": {
        "speaking": ("Notiqlik", "Ораторство", "Public speaking", "스피치"),
        "writing": ("Yozish va tahlil", "Письмо и анализ", "Writing & analysis", "글쓰기·분석"),
        "translation": ("Tarjima", "Перевод", "Translation", "번역"),
        "design": ("Dizayn", "Дизайн", "Design", "디자인"),
        "media": ("Foto va video", "Фото и видео", "Photo & video", "사진·영상"),
        "smm": ("SMM", "SMM", "SMM", "SMM"),
        "events": ("Tadbir tashkil etish", "Организация мероприятий", "Event organising", "행사 기획"),
    },
    "hours": {
        "lt2": ("2 soatgacha", "до 2 часов", "up to 2 hours", "2시간 이하"),
        "2to4": ("2–4 soat", "2–4 часа", "2–4 hours", "2–4시간"),
        "gt4": ("4 soatdan ko'p", "более 4 часов", "more than 4 hours", "4시간 이상"),
    },
    "days": {
        "mon": ("Dushanba", "Пн", "Mon", "월"), "tue": ("Seshanba", "Вт", "Tue", "화"),
        "wed": ("Chorshanba", "Ср", "Wed", "수"), "thu": ("Payshanba", "Чт", "Thu", "목"),
        "fri": ("Juma", "Пт", "Fri", "금"), "sat": ("Shanba", "Сб", "Sat", "토"),
    },
    "time": {
        "after": ("Darsdan keyin", "После пар", "After classes", "수업 후"),
        "evening": ("Kechqurun", "Вечером", "Evening", "저녁"),
        "weekend": ("Dam olish kuni", "В выходные", "Weekend", "주말"),
    },
}

# Admin uchun ariza xulosasidagi maydon nomlari (o'zbekcha)
APP_FIELDS = [
    ("app_type", "Ariza turi"), ("email", "Email"), ("telegram", "Telegram"), ("social", "Instagram/LinkedIn"),
    ("edu_lang", "Ta'lim tili"), ("section", "Bo'lim"), ("directions", "Yo'nalish"),
    ("languages", "Tillar"), ("mun", "MUN/debat tajribasi"), ("other_exp", "Boshqa tajriba"),
    ("skills", "Ko'nikmalar"), ("certs", "Sertifikatlar"), ("mot1", "Nega qo'shilmoqchi"),
    ("mot2", "Nimani o'rganmoqchi"), ("mot3", "Qanday hissa qo'shadi"), ("issue", "Xalqaro masala"),
    ("hours", "Haftalik vaqt"), ("days", "Qulay kunlar"), ("time", "Qulay vaqt"), ("online", "Onlayn"),
    ("photo_consent", "Foto/video roziligi"),
]


def _idx(lang: str) -> int:
    return _COL.get(lang, 0)


def t(key: str, lang: str = "uz", **kwargs) -> str:
    entry = T.get(key)
    if entry is None:
        return key
    text = entry[_idx(lang)] or entry[0]
    if lang == "un":               # shablon o'giriladi, foydalanuvchi ma'lumotlari ({name} ...) emas
        text = to_new(text)
    return text.format(**kwargs) if kwargs else text


# Eski bo'limlar (2026-yil noyabrgacha) — avval qabul qilingan a'zolar va arizalar to'g'ri ko'rinishi uchun.
# Yangi tanlovlarda chiqmaydi.
LEGACY_OPTIONS: dict[str, dict[str, tuple[str, str, str, str]]] = {
    "section": {
        "debate": ("Debat va MUN", "Дебаты и MUN", "Debate & MUN", "토론·MUN"),
        "academic": ("Akademik", "Академический", "Academic", "학술"),
        "partners": ("Hamkorlik", "Партнёрство", "Partnerships", "협력"),
        "events": ("Tadbirlar", "Мероприятия", "Events", "행사"),
    },
}

# Qo'lda beriladigan darajalar (admin /daraja buyrug'i bilan); qolganlari davomatdan hisoblanadi
MANUAL_LEVELS = ("leader", "expert", "honorary")


def member_level(member, went: int, held: int) -> str:
    """Kuzatuvchi → Nomzod → Faol (2/3 qatnashish) → Yetakchi / Ekspert / Faxriy (admin belgilaydi)."""
    if not member or member["status"] != "active":
        return "observer"
    manual = member.get("level") if hasattr(member, "get") else None
    if manual in MANUAL_LEVELS:
        return manual
    return "active" if held > 0 and went * 3 >= held * 2 else "candidate"


def opt(group: str, key: str, lang: str = "uz") -> str:
    entry = OPTIONS.get(group, {}).get(key) or LEGACY_OPTIONS.get(group, {}).get(key)
    if not entry:
        return key
    return to_new(entry[0]) if lang == "un" else entry[_idx(lang)]


_EMOJI_LETTERLIKE = {"ℹ", "Ⓜ"}  # ℹ va Ⓜ Unicode'da «harf», lekin emoji sifatida ishlatiladi


def is_emoji_token(token: str) -> bool:
    """So'z faqat emoji/belgilardan iboratmi (harf yoki raqam emas)."""
    import unicodedata
    return bool(token) and all(
        ch in _EMOJI_LETTERLIKE or 0xFE00 <= ord(ch) <= 0xFE0F or ord(ch) == 0x200D
        or unicodedata.category(ch)[0] in ("S", "M", "C", "P")
        for ch in token
    )


def strip_emoji(text: str) -> str:
    """'ℹ️ Klub haqida' -> 'Klub haqida' (boshida emoji bo'lmasa — o'zgarishsiz)."""
    head, _, rest = text.partition(" ")
    return rest if rest and is_emoji_token(head) else text


def variants(key: str) -> set[str]:
    """Tugma matnining barcha tillardagi variantlari (filtrlar uchun).

    Tugmaga rasmiy emoji belgisi qo'yilganda matn boshidagi oddiy emoji olib tashlanadi,
    shuning uchun emojisiz ko'rinish ham qo'shiladi.
    """
    texts = set(T[key]) | {to_new(T[key][0])}
    return texts | {strip_emoji(x) for x in texts}

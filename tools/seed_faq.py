"""Botdagi «❓ Savollar» bo'limi uchun boshlang'ich savol-javoblar (klub nizomi va bot qoidalari asosida).

    python tools/seed_faq.py                 # shu kompyuterdagi baza (pgserver)
    python tools/seed_faq.py postgresql://...  # boshqa baza

Biror tilda savollar allaqachon bo'lsa, o'sha til o'tkazib yuboriladi (takror qo'shilmaydi).
Yangi alifbo (Özbekça) uchun alohida yozish shart emas — o'zbekchadan avtomatik o'giriladi.
Keyin adminlar botda /addfaq, /faqlist, /delfaq bilan boshqaradi.
"""
import asyncio
import sys
from pathlib import Path

import asyncpg

ROOT = Path(__file__).resolve().parents[1]

FAQ = {
    "uz": [
        ("Klubga kim a'zo bo'la oladi?",
         "KIUTning <b>barcha fakultet</b> talabalari. A'zolik ixtiyoriy va <b>bepul</b>."),
        ("Qanday a'zo bo'laman?",
         "Botda «📝 A'zo bo'lish» tugmasini bosing va elektron blankani to'ldiring. Kengash arizani "
         "<b>10 ish kuni</b> ichida ko'rib chiqadi, natija shu botga keladi."),
        ("Mashg'ulotlar qanday o'tadi?",
         "Har hafta bitta mashg'ulot: debat, Model UN yoki trening. Davomiyligi 60 daqiqa: 10 daqiqa mavzu, "
         "40 daqiqa mashq, 10 daqiqa fikr-mulohaza. Har oy bitta katta tadbir yoki ochiq uchrashuv bo'ladi. "
         "Imtihon davrida yirik tadbirlar o'tkazilmaydi."),
        ("Tadbirga qanday yozilaman va kiraman?",
         "«📅 Tadbirlar» bo'limida tadbirni tanlab, «Yozilish»ni bosing — QR-chipta keladi. Kirishda QR-kodni "
         "ko'rsatasiz va davomat belgilanadi. Barcha tadbirlar <b>bepul</b>. Bora olmasangiz, chiptani bekor qiling."),
        ("Ballar qanday beriladi?",
         "Nizom 2.4 bo'yicha: mashg'ulot — 1, ko'ngilli yordam — 2, tahliliy matn — 3, debat yoki Model UN — 3, "
         "loyihaga mas'ullik — 5 ball. O'rningizni «🏆 Reyting» bo'limida ko'rasiz."),
        ("Faol a'zo bo'lish uchun nima kerak?",
         "Semestrda o'tkazilgan tadbirlarning <b>kamida 2/3 qismida</b> qatnashish kerak. Holatingiz "
         "«🪪 Mening a'zoligim» bo'limida ko'rinadi."),
        ("A'zolik guvohnomasini qanday olaman?",
         "Arizangiz qabul qilingach, «🪪 Mening a'zoligim» → «Guvohnomani olish». A'zolik bir o'quv yili uchun "
         "beriladi va har yili yangilanadi."),
        ("Ko'ngilli bo'lsam bo'ladimi?",
         "Ha. «🙋 Ko'ngilli bo'lish» bo'limida yordam kerak bo'lgan tadbirlarga ariza bering. Ko'ngilli yordam "
         "uchun 2 ball beriladi."),
        ("Shikoyatim maxfiy saqlanadimi?",
         "Ha. Shikoyat Etika va intizom komissiyasiga yuboriladi va maxfiy saqlanadi. Nizom 8.4 bo'yicha qabul qilingani "
         "3 ish kunida bildiriladi, yozma qaror 10 ish kunida beriladi."),
        ("Ma'lumotlarimni o'chirsam bo'ladimi?",
         "Ha. «⚙️ Sozlamalar» → «Ma'lumotlarimni o'chirish». Ma'lumotlar <b>5 ish kuni</b> ichida o'chiriladi "
         "(Nizom 7.9)."),
    ],
    "ru": [
        ("Кто может вступить в клуб?",
         "Студенты <b>всех факультетов</b> KIUT. Членство добровольное и <b>бесплатное</b>."),
        ("Как вступить?",
         "Нажмите «📝 Вступить в клуб» и заполните электронную анкету. Совет рассматривает заявку в течение "
         "<b>10 рабочих дней</b>, результат придёт в этот бот."),
        ("Как проходят занятия?",
         "Раз в неделю — занятие: дебаты, Model UN или тренинг. 60 минут: 10 минут тема, 40 минут практика, "
         "10 минут обратная связь. Раз в месяц — крупное мероприятие или открытая встреча. "
         "В период экзаменов крупные мероприятия не проводятся."),
        ("Как записаться на мероприятие и пройти на него?",
         "В разделе «📅 Мероприятия» выберите событие и нажмите «Записаться» — придёт QR-билет. На входе "
         "покажите QR-код, посещение отметится. Все мероприятия <b>бесплатные</b>. Если не сможете прийти, "
         "отмените билет."),
        ("Как начисляются баллы?",
         "По Положению 2.4: занятие — 1, волонтёрская помощь — 2, аналитический текст — 3, дебаты или Model UN — 3, "
         "ответственный за проект — 5 баллов. Своё место смотрите в разделе «🏆 Рейтинг»."),
        ("Что нужно, чтобы стать активным членом?",
         "Посетить <b>не менее 2/3</b> мероприятий, проведённых в семестре. Статус виден в разделе «🪪 Моё членство»."),
        ("Как получить удостоверение члена клуба?",
         "После одобрения заявки: «🪪 Моё членство» → «Получить удостоверение». Членство действует один учебный год "
         "и продлевается ежегодно."),
        ("Можно стать волонтёром?",
         "Да. В разделе «🙋 Волонтёрство» подайте заявку на мероприятия, где нужна помощь. За волонтёрскую помощь "
         "начисляется 2 балла."),
        ("Моя жалоба останется конфиденциальной?",
         "Да. Жалоба направляется в Дисциплинарную комиссию и хранится конфиденциально. По Положению 8.4 приём "
         "подтверждается в течение 3 рабочих дней, письменное решение — в течение 10 рабочих дней."),
        ("Можно удалить мои данные?",
         "Да. «⚙️ Настройки» → «Удалить мои данные». Данные удаляются в течение <b>5 рабочих дней</b> "
         "(Положение 7.9)."),
    ],
    "en": [
        ("Who can join the club?",
         "Students of <b>all faculties</b> of KIUT. Membership is voluntary and <b>free</b>."),
        ("How do I join?",
         "Tap «📝 Join the club» and fill in the online form. The Council reviews applications within "
         "<b>10 working days</b>; the result is sent to this bot."),
        ("What are the sessions like?",
         "One session a week: debate, Model UN or a training. 60 minutes: 10 minutes topic, 40 minutes practice, "
         "10 minutes feedback. Once a month there is a major event or an open meeting. "
         "No major events are held during exams."),
        ("How do I register for an event and get in?",
         "In «📅 Events», pick an event and tap «Sign up» — you will get a QR ticket. Show the QR code at the "
         "entrance and your attendance is recorded. All events are <b>free</b>. If you cannot come, cancel the ticket."),
        ("How are points awarded?",
         "Under Regulation 2.4: session — 1, volunteering — 2, analytical piece — 3, debate or Model UN — 3, "
         "project lead — 5 points. See your place in «🏆 Rating»."),
        ("How do I become an active member?",
         "Attend <b>at least 2/3</b> of the events held during the semester. Your status is shown in "
         "«🪪 My membership»."),
        ("How do I get my membership card?",
         "Once your application is accepted: «🪪 My membership» → «Get membership card». Membership is valid for "
         "one academic year and is renewed every year."),
        ("Can I volunteer?",
         "Yes. In «🙋 Volunteer», apply for events that need help. Volunteering earns 2 points."),
        ("Will my complaint stay confidential?",
         "Yes. Complaints go to the Disciplinary Committee and are kept confidential. Under Regulation 8.4, receipt is "
         "confirmed within 3 working days and a written decision is given within 10 working days."),
        ("Can I delete my data?",
         "Yes. «⚙️ Settings» → «Delete my data». Your data is deleted within <b>5 working days</b> (Regulation 7.9)."),
    ],
    "ko": [
        ("누가 클럽에 가입할 수 있나요?",
         "KIUT <b>모든 학부</b> 학생이 가입할 수 있습니다. 가입은 자율이며 <b>무료</b>입니다."),
        ("어떻게 가입하나요?",
         "«📝 클럽 가입»을 누르고 온라인 신청서를 작성하세요. 위원회가 <b>10영업일</b> 이내에 검토하며, "
         "결과는 이 봇으로 전달됩니다."),
        ("정기 활동은 어떻게 진행되나요?",
         "매주 한 번 토론, 모의유엔 또는 트레이닝을 진행합니다. 60분 구성: 주제 10분, 실습 40분, 피드백 10분. "
         "매달 큰 행사나 공개 모임이 한 번 있습니다. 시험 기간에는 큰 행사를 열지 않습니다."),
        ("행사 신청과 입장은 어떻게 하나요?",
         "«📅 행사»에서 행사를 고르고 «신청하기»를 누르면 QR 티켓이 발급됩니다. 입구에서 QR 코드를 보여주면 "
         "출석이 기록됩니다. 모든 행사는 <b>무료</b>입니다. 참석이 어려우면 티켓을 취소해 주세요."),
        ("포인트는 어떻게 받나요?",
         "규정 2.4에 따라 정기 활동 1점, 봉사 2점, 분석 글 3점, 토론·모의유엔 3점, 프로젝트 책임 5점입니다. "
         "순위는 «🏆 랭킹»에서 확인하세요."),
        ("활동 회원이 되려면 무엇이 필요한가요?",
         "학기 중 열린 행사의 <b>2/3 이상</b>에 참석해야 합니다. 상태는 «🪪 내 회원정보»에서 볼 수 있습니다."),
        ("회원증은 어떻게 받나요?",
         "신청이 승인되면 «🪪 내 회원정보» → «회원증 받기»를 누르세요. 회원 자격은 한 학년도 동안 유효하며 "
         "매년 갱신합니다."),
        ("봉사자로 참여할 수 있나요?",
         "네. «🙋 봉사하기»에서 도움이 필요한 행사에 신청하세요. 봉사하면 2점을 받습니다."),
        ("불만 제기 내용은 비공개로 처리되나요?",
         "네. 불만 사항은 징계위원회로 전달되며 비공개로 보관됩니다. 규정 8.4에 따라 3영업일 이내에 접수를 "
         "알리고, 10영업일 이내에 서면 결정을 드립니다."),
        ("내 정보를 삭제할 수 있나요?",
         "네. «⚙️ 설정» → «내 데이터 삭제»를 누르세요. 정보는 <b>5영업일</b> 이내에 삭제됩니다 (규정 7.9)."),
    ],
}


async def main(uri: str) -> None:
    conn = await asyncpg.connect(uri)
    try:
        for lang, items in FAQ.items():
            if await conn.fetchval("SELECT count(*) FROM faq WHERE lang=$1", lang):
                print(f"{lang}: savollar bor — o'tkazildi")
                continue
            await conn.executemany("INSERT INTO faq(lang, question, answer) VALUES($1,$2,$3)",
                                   [(lang, q, a) for q, a in items])
            print(f"{lang}: {len(items)} ta savol qo'shildi")
    finally:
        await conn.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        import pgserver
        target = pgserver.get_server(ROOT / "pgdata", cleanup_mode=None).get_uri()
    asyncio.run(main(target))

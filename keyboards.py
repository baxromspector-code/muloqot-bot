import json
import logging

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from config import BASE_DIR, BUTTON_ICONS
from texts import DIRECTIONS, LANG_NAMES, OPTIONS, opt, strip_emoji, t

log = logging.getLogger("keyboards")

# ======================= tugma ranglari va belgilari =======================
# Telegram ranglari: success (yashil) — tasdiqlash, danger (qizil) — bekor/o'chirish, primary (ko'k) — asosiy amal.
STYLE_EXACT = {
    "agree": "success", "app_submit": "success", "rules_ok": "success", "delete_yes": "success",
    "cancel": "danger", "delete_data": "danger", "delete_no": "primary",
    "app_edit": "primary", "my_card": "primary", "edit_profile": "primary", "change_lang": "primary",
    "skip": None,
}
STYLE_PREFIX = [
    ("evreg:", "success"), ("ap_ok:", "success"), ("ap_sec:", "success"), ("v_ok:", "success"), ("a_close:", "success"),
    ("atype:", "success"), ("faqlang:", "primary"),
    ("tkcancel:", "danger"), ("ap_no:", "danger"), ("ap_rej:", "danger"), ("v_no:", "danger"), ("del_ok:", "danger"),
    ("ureply:", "primary"), ("a_reply:", "primary"), ("a_review:", "primary"), ("ap_ret:", "primary"),
    ("manydone:", "primary"), ("vol:", "primary"), ("ev_announce:", "primary"), ("ev_finish:", "primary"),
    ("appedit:", "primary"), ("akind:", "primary"),
]
# Rasmiy emoji to'plamidagi alohida belgilar (dizayn/emoji_anim/ids.json, «14_belgilar»)
ICON_EXACT = {"agree": "check", "app_submit": "check", "rules_ok": "check", "my_card": "muloqot",
              "delete_data": "warn"}
ICON_PREFIX = [("about:", "info"), ("ap_ok:", "check"), ("evreg:", "check")]
MENU_STYLE = {"m_join": "success", "m_events": "primary", "m_appeal": "primary"}
MENU_ICON = {"m_about": "muloqot", "m_faq": "info", "m_membership": "muloqot"}

ICON_IDS: dict[str, str] = {}
ICONS_ENABLED = False
_ORIGINAL_TEXT: dict[tuple[str, str], str] = {}  # (belgisiz matn, icon_id) -> asl matn (qaytarish uchun)


def _load_icons() -> None:
    """Tugma belgilari: yangi tiniq to'plam (emoji_premium, «19_belgilar»), bo'lmasa eski (emoji_anim, «14_belgilar»)."""
    global ICONS_ENABLED
    if not BUTTON_ICONS:
        return
    for folder, key in (("emoji_premium", "19_belgilar"), ("emoji_anim", "14_belgilar")):
        path = BASE_DIR / "dizayn" / folder / "ids.json"
        if path.exists():
            break
    else:
        return
    try:
        ids = json.loads(path.read_text(encoding="utf-8"))["emoji"].get(key, [])
        ICON_IDS.update(dict(zip(["muloqot", "kiut", "check", "warn", "info"], ids)))
        ICONS_ENABLED = bool(ICON_IDS)
    except Exception:
        log.warning("ids.json o'qilmadi — tugma belgilari o'chirildi", exc_info=True)


_load_icons()


def _match(callback: str, exact: dict, prefix: list):
    if callback in exact:
        return exact[callback]
    for p, v in prefix:
        if callback.startswith(p):
            return v
    return None


def _with_icon(text: str, icon_key: str | None) -> tuple[str, str | None]:
    """Belgi qo'yilsa, matn boshidagi oddiy emoji olib tashlanadi (ikki marta ko'rinmasin)."""
    icon_id = ICON_IDS.get(icon_key or "") if ICONS_ENABLED else None
    if not icon_id:
        return text, None
    short = strip_emoji(text)
    _ORIGINAL_TEXT[(short, icon_id)] = text
    return short, icon_id


def IB(text: str, callback_data: str | None = None, url: str | None = None) -> InlineKeyboardButton:
    key = callback_data or ""
    label, icon_id = _with_icon(text, _match(key, ICON_EXACT, ICON_PREFIX))
    return InlineKeyboardButton(text=label, callback_data=callback_data, url=url,
                                style=_match(key, STYLE_EXACT, STYLE_PREFIX), icon_custom_emoji_id=icon_id)


def KB(text: str, style: str | None = None, icon: str | None = None, **kw) -> KeyboardButton:
    label, icon_id = _with_icon(text, icon)
    return KeyboardButton(text=label, style=style, icon_custom_emoji_id=icon_id, **kw)


def strip_icons(markup) -> bool:
    """Telegram belgilarni rad etsa: belgilarni olib, asl matnni qaytaradi. O'zgarish bo'lsa True."""
    rows = getattr(markup, "inline_keyboard", None) or getattr(markup, "keyboard", None) or []
    changed = False
    for row in rows:
        for btn in row:
            if getattr(btn, "icon_custom_emoji_id", None):
                btn.text = _ORIGINAL_TEXT.get((btn.text, btn.icon_custom_emoji_id), btn.text)
                btn.icon_custom_emoji_id = None
                changed = True
    return changed


def disable_icons() -> None:
    global ICONS_ENABLED
    ICONS_ENABLED = False


def inline(rows: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[IB(x, c) for x, c in row] for row in rows])


def url_kb(rows: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=x, url=u, style="primary") for x, u in row]
                                                 for row in rows])


def lang_kb() -> InlineKeyboardMarkup:
    codes = list(LANG_NAMES)
    return inline([[(LANG_NAMES[c], f"lang:{c}") for c in codes[:2]], [(LANG_NAMES[c], f"lang:{c}") for c in codes[2:]]])


MENU_LAYOUT = [
    ("m_join", "m_membership"), ("m_events", "m_tickets"), ("m_appeal", "m_my_appeals"),
    ("m_rating", "m_volunteer"), ("m_about", "m_docs"), ("m_faq", "m_settings"),
]


def _menu_btn(key: str, lang: str) -> KeyboardButton:
    return KB(t(key, lang), style=MENU_STYLE.get(key), icon=MENU_ICON.get(key))


def main_menu(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[_menu_btn(a, lang), _menu_btn(b, lang)] for a, b in MENU_LAYOUT],
        resize_keyboard=True,
    )


def phone_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KB(t("btn_send_phone", lang), style="success", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True,
    )


def directions_kb() -> InlineKeyboardMarkup:
    return inline([[(name, f"dir:{i}")] for i, name in enumerate(DIRECTIONS)])


def course_kb(lang: str) -> InlineKeyboardMarkup:
    return inline([
        [(f"{n}", f"course:{n}") for n in range(1, 5)],
        [(t("course_master", lang), "course:M")],
    ])


def agree_kb(lang: str) -> InlineKeyboardMarkup:
    return inline([[(t("btn_agree", lang), "agree")]])


def cancel_inline(lang: str) -> InlineKeyboardMarkup:
    return inline([[(t("btn_cancel", lang), "cancel")]])


def skip_kb(lang: str) -> InlineKeyboardMarkup:
    return inline([[(t("btn_skip", lang), "skip")], [(t("btn_cancel", lang), "cancel")]])


def send_cancel_kb(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KB(t("btn_send", lang), style="success"), KB(t("btn_cancel", lang), style="danger")]],
        resize_keyboard=True,
    )


def yes_no_kb(lang: str, prefix: str) -> InlineKeyboardMarkup:
    return inline([[(t("btn_yes", lang), f"{prefix}:yes"), (t("btn_no", lang), f"{prefix}:no")]])


def single_choice_kb(group: str, lang: str, per_row: int = 1) -> InlineKeyboardMarkup:
    keys = list(OPTIONS[group])
    rows = [keys[i:i + per_row] for i in range(0, len(keys), per_row)]
    return inline([[(opt(group, k, lang), f"one:{group}:{k}") for k in row] for row in rows])


def multi_choice_kb(group: str, lang: str, selected: list[str], per_row: int = 2) -> InlineKeyboardMarkup:
    keys = list(OPTIONS[group])
    rows = [keys[i:i + per_row] for i in range(0, len(keys), per_row)]
    out = [[(("✅ " if k in selected else "▫️ ") + opt(group, k, lang), f"many:{group}:{k}") for k in row]
           for row in rows]
    out.append([(t("btn_done", lang), f"manydone:{group}")])
    return inline(out)


def settings_kb(lang: str) -> InlineKeyboardMarkup:
    return inline([
        [(t("btn_edit_profile", lang), "edit_profile")],
        [(t("btn_change_lang", lang), "change_lang")],
        [(t("btn_delete_data", lang), "delete_data")],
    ])


def reply_kb(lang: str, appeal_id: int) -> InlineKeyboardMarkup:
    return inline([[(t("btn_reply", lang), f"ureply:{appeal_id}")]])


def appeal_kind_kb(lang: str) -> InlineKeyboardMarkup:
    return inline([
        [(t("kind_question", lang), "akind:question")],
        [(t("kind_suggestion", lang), "akind:suggestion")],
        [(t("kind_complaint", lang), "akind:complaint")],
        [(t("btn_cancel", lang), "cancel")],
    ])


def about_kb(lang: str) -> InlineKeyboardMarkup:
    keys = ["ab_mission", "ab_directions", "ab_modules", "ab_structure", "ab_leaders", "ab_rhythm", "ab_links"]
    rows = [keys[i:i + 2] for i in range(0, len(keys), 2)]
    return inline([[(t(k, lang), f"about:{k}") for k in row] for row in rows])


def docs_kb(lang: str) -> InlineKeyboardMarkup:
    return inline([
        [(t("doc_ustav", lang), "doc:ustav"), (t("doc_nizom", lang), "doc:nizom")],
        [(t("doc_blanka", lang), "doc:blanka")],
        [(t("doc_taqdimot", lang), "doc:taqdimot")],
    ])


# ---------------- admin chat ----------------
def admin_application_kb(app_id: int) -> InlineKeyboardMarkup:
    return inline([
        [("✅ Qabul qilish", f"ap_ok:{app_id}")],
        [("↩️ To'ldirishga qaytarish", f"ap_ret:{app_id}"), ("❌ Rad etish", f"ap_no:{app_id}")],
    ])


def admin_section_kb(app_id: int) -> InlineKeyboardMarkup:
    keys = list(OPTIONS["section"])
    return inline([[(opt("section", k), f"ap_sec:{app_id}:{k}")] for k in keys])


def admin_reject_kb(app_id: int) -> InlineKeyboardMarkup:
    return inline([
        [("KIUT talabasi emas", f"ap_rej:{app_id}:rej_not_student")],
        [("Blanka to'liq emas, muddat o'tdi", f"ap_rej:{app_id}:rej_incomplete")],
        [("Bekor qilinganiga 1 yil bo'lmagan", f"ap_rej:{app_id}:rej_banned")],
    ])


def admin_appeal_kb(appeal_id: int) -> InlineKeyboardMarkup:
    return inline([
        [("🔄 Ko'rib chiqilmoqda", f"a_review:{appeal_id}"), ("✍️ Javob berish", f"a_reply:{appeal_id}")],
        [("✅ Yopish", f"a_close:{appeal_id}")],
    ])


def admin_volunteer_kb(vid: int) -> InlineKeyboardMarkup:
    return inline([[("✅ Qabul qilish", f"v_ok:{vid}"), ("❌ Rad etish", f"v_no:{vid}")]])


def admin_delete_kb(req_id: int) -> InlineKeyboardMarkup:
    return inline([[("🗑 Ma'lumotlarni o'chirish", f"del_ok:{req_id}")]])


def admin_event_kb(ev) -> InlineKeyboardMarkup:
    eid = ev["id"]
    rows = []
    if not ev["finished"]:
        toggle = ("⏸ Ro'yxatni yopish", f"ev_close:{eid}") if ev["active"] else ("▶️ Ro'yxatni ochish", f"ev_open:{eid}")
        rows.append([toggle, ("🏁 Yakunlash", f"ev_finish:{eid}")])
        rows.append([("🔔 Eslatma yuborish", f"ev_remind:{eid}")])
    rows.append([("👥 Ishtirokchilar (CSV)", f"ev_list:{eid}")])
    return inline(rows)

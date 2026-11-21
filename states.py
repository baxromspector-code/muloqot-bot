from aiogram.fsm.state import State, StatesGroup


class Reg(StatesGroup):
    name = State()
    direction = State()
    course = State()
    group = State()
    student_id = State()
    photo = State()
    phone = State()
    consent = State()


class Join(StatesGroup):
    """A'zolik blankasi. Har bir holat — blankadagi bitta savol."""
    app_type = State()
    email = State()
    social = State()
    edu_lang = State()
    section = State()
    directions = State()
    languages = State()
    mun = State()
    other_exp = State()
    skills = State()
    certs = State()
    mot1 = State()
    mot2 = State()
    mot3 = State()
    issue = State()
    hours = State()
    days = State()
    time = State()
    online = State()
    rules = State()
    photo = State()
    confirm = State()


class Appeal(StatesGroup):
    text = State()
    attach = State()


class UserReply(StatesGroup):
    text = State()


class AdminReply(StatesGroup):
    text = State()


class AdminReturn(StatesGroup):
    reason = State()


class AddEvent(StatesGroup):
    kind = State()
    title = State()
    description = State()
    date_text = State()
    place = State()
    capacity = State()
    points = State()
    volunteers = State()


class AddFaq(StatesGroup):
    lang = State()
    question = State()
    answer = State()


class Broadcast(StatesGroup):
    message = State()

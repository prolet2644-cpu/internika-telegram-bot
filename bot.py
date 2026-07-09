import os
import uuid
import smtplib
import logging
from datetime import datetime
from email.message import EmailMessage
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, Update
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage


# =========================
# ENV
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").rstrip("/")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "internika_secret_123")
WEBHOOK_PATH = f"/webhook/{WEBHOOK_SECRET}"

LOG_SECRET = os.getenv("LOG_SECRET", "internika_log_123")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ORDER_EMAIL_TO = os.getenv("ORDER_EMAIL_TO")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Internika bot")


if not BOT_TOKEN:
    raise RuntimeError("Не задана переменная окружения BOT_TOKEN")

if not WEBHOOK_URL:
    raise RuntimeError("Не задана переменная окружения WEBHOOK_URL")


# =========================
# LOGGING
# =========================

LOG_FILE = "app.log"

logger = logging.getLogger("internika_bot")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(formatter)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)


def log_event(stage, message, **kwargs):
    details = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    if details:
        logger.info(f"{stage} | {message} | {details}")
    else:
        logger.info(f"{stage} | {message}")


def log_error(stage, message, exc=None, **kwargs):
    details = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    base = f"{stage} | {message}"
    if details:
        base += f" | {details}"

    if exc:
        logger.exception(base)
    else:
        logger.error(base)


# =========================
# Справочники Internika
# MVP: поворотно-откидная створка, ручка средняя / переменная
# =========================

MAIN_LOCKS_VARIABLE = [
    {
        "vsf_min": 420,
        "vsf_max": 600,
        "sku": "1077172",
        "name": "Запор основной поворотно-откидной средний",
        "angle_qty": 0,
        "response_qty": 0,
    },
    {
        "vsf_min": 601,
        "vsf_max": 1000,
        "sku": "1088438",
        "name": "Запор основной поворотно-откидной средний",
        "angle_qty": 1,
        "response_qty": 1,
    },
    {
        "vsf_min": 901,
        "vsf_max": 1400,
        "sku": "1088439",
        "name": "Запор основной поворотно-откидной средний",
        "angle_qty": 1,
        "response_qty": 1,
    },
    {
        "vsf_min": 1401,
        "vsf_max": 1800,
        "sku": "1088440",
        "name": "Запор основной поворотно-откидной средний",
        "angle_qty": 1,
        "response_qty": 1,
    },
    {
        "vsf_min": 1601,
        "vsf_max": 2000,
        "sku": "1088441",
        "name": "Запор основной поворотно-откидной средний",
        "angle_qty": 2,
        "response_qty": 2,
    },
    {
        "vsf_min": 2001,
        "vsf_max": 2400,
        "sku": "1088442",
        "name": "Запор основной поворотно-откидной средний",
        "angle_qty": 2,
        "response_qty": 2,
    },
]


SASH_SCISSORS = [
    {
        "shf_min": 325,
        "shf_max": 610,
        "sku": "1077031",
        "name": "Ножницы на створке 250/470",
        "response_qty": 0,
    },
    {
        "shf_min": 611,
        "shf_max": 810,
        "sku": "1077032",
        "name": "Ножницы на створке 350/670",
        "response_qty": 0,
    },
    {
        "shf_min": 811,
        "shf_max": 1010,
        "sku": "1077033",
        "name": "Ножницы на створке 500/870",
        "response_qty": 1,
    },
    {
        "shf_min": 1011,
        "shf_max": 1210,
        "sku": "1077034",
        "name": "Ножницы на створке 500/1070",
        "response_qty": 1,
    },
    {
        "shf_min": 1211,
        "shf_max": 1410,
        "sku": "1077035",
        "name": "Ножницы на створке 500/1270",
        "response_qty": 1,
    },
    {
        "shf_min": 1411,
        "shf_max": 1600,
        "sku": "1077036",
        "name": "Ножницы на створке 500/1470",
        "response_qty": 1,
    },
]


FRAME_SCISSORS = [
    {"system": "12/20-9", "shf_min": 325, "shf_max": 610, "side": "Левое", "sku": "1088661", "name": "Ножницы на раме 12/20-9 250 левое"},
    {"system": "12/20-9", "shf_min": 325, "shf_max": 610, "side": "Правое", "sku": "1088662", "name": "Ножницы на раме 12/20-9 250 правое"},
    {"system": "12/20-9", "shf_min": 611, "shf_max": 810, "side": "Левое", "sku": "1088663", "name": "Ножницы на раме 12/20-9 350 левое"},
    {"system": "12/20-9", "shf_min": 611, "shf_max": 810, "side": "Правое", "sku": "1088664", "name": "Ножницы на раме 12/20-9 350 правое"},
    {"system": "12/20-9", "shf_min": 811, "shf_max": 1600, "side": "Левое", "sku": "1088665", "name": "Ножницы на раме 12/20-9 500 левое"},
    {"system": "12/20-9", "shf_min": 811, "shf_max": 1600, "side": "Правое", "sku": "1088666", "name": "Ножницы на раме 12/20-9 500 правое"},

    {"system": "12/20-13", "shf_min": 325, "shf_max": 610, "side": "Левое", "sku": "1088667", "name": "Ножницы на раме 12/20-13 250 левое"},
    {"system": "12/20-13", "shf_min": 325, "shf_max": 610, "side": "Правое", "sku": "1088668", "name": "Ножницы на раме 12/20-13 250 правое"},
    {"system": "12/20-13", "shf_min": 611, "shf_max": 810, "side": "Левое", "sku": "1088669", "name": "Ножницы на раме 12/20-13 350 левое"},
    {"system": "12/20-13", "shf_min": 611, "shf_max": 810, "side": "Правое", "sku": "1088670", "name": "Ножницы на раме 12/20-13 350 правое"},
    {"system": "12/20-13", "shf_min": 811, "shf_max": 1600, "side": "Левое", "sku": "1088671", "name": "Ножницы на раме 12/20-13 500 левое"},
    {"system": "12/20-13", "shf_min": 811, "shf_max": 1600, "side": "Правое", "sku": "1088672", "name": "Ножницы на раме 12/20-13 500 правое"},

    {"system": "12/22-13", "shf_min": 325, "shf_max": 610, "side": "Левое", "sku": "1088673", "name": "Ножницы на раме 12/22-13 250 левое"},
    {"system": "12/22-13", "shf_min": 325, "shf_max": 610, "side": "Правое", "sku": "1088674", "name": "Ножницы на раме 12/22-13 250 правое"},
    {"system": "12/22-13", "shf_min": 611, "shf_max": 810, "side": "Левое", "sku": "1088675", "name": "Ножницы на раме 12/22-13 350 левое"},
    {"system": "12/22-13", "shf_min": 611, "shf_max": 810, "side": "Правое", "sku": "1088676", "name": "Ножницы на раме 12/22-13 350 правое"},
    {"system": "12/22-13", "shf_min": 811, "shf_max": 1600, "side": "Левое", "sku": "1088677", "name": "Ножницы на раме 12/22-13 500 левое"},
    {"system": "12/22-13", "shf_min": 811, "shf_max": 1600, "side": "Правое", "sku": "1088678", "name": "Ножницы на раме 12/22-13 500 правое"},
]


MIDDLE_LOCKS = [
    {
        "shf_min": 400,
        "shf_max": 700,
        "vsf_min": None,
        "vsf_max": None,
        "sku": "1086563",
        "name": "Запор средний 300/350",
        "response_qty": 1,
    },
    {
        "shf_min": 701,
        "shf_max": 1200,
        "vsf_min": 701,
        "vsf_max": 1200,
        "sku": "1077050",
        "name": "Запор средний 500/550",
        "response_qty": 2,
    },
    {
        "shf_min": 1201,
        "shf_max": 1600,
        "vsf_min": 1201,
        "vsf_max": 1600,
        "sku": "1077051",
        "name": "Запор средний 800/850",
        "response_qty": 2,
    },
    {
        "shf_min": None,
        "shf_max": None,
        "vsf_min": 1601,
        "vsf_max": 2200,
        "sku": "1077052",
        "name": "Запор средний 1450/1550",
        "response_qty": 3,
    },
    {
        "shf_min": None,
        "shf_max": None,
        "vsf_min": 2201,
        "vsf_max": 2400,
        "sku": "1080211",
        "name": "Запор средний 1950/2000",
        "response_qty": 4,
    },
]


RESPONSE_PLATE_PROFILES = {
    "12/20 13, +2 мм": {
        "tilt_turn": "1087144",
        "regular": "1077244",
        "blocker_stop": None,
    },
    "12/20 13, +3,3 мм": {
        "tilt_turn": "1087832",
        "regular": "1087833",
        "blocker_stop": None,
    },
    "12/20 9, +1 мм": {
        "tilt_turn": "1088578",
        "regular": "1082730",
        "blocker_stop": None,
    },
    "Aluplast/Rehau": {
        "tilt_turn": "1077239",
        "regular": "1077245",
        "blocker_stop": "1077298",
    },
    "Veka": {
        "tilt_turn": "1077237",
        "regular": "1077243",
        "blocker_stop": "1084777",
    },
    "KBE 70 AD": {
        "tilt_turn": "1077240",
        "regular": "1077246",
        "blocker_stop": "1077294",
    },
}


DECOR_KITS = {
    "белый": "INT1003.07",
    "темно-коричневый": "INT1003.05",
}


# =========================
# Расчет
# =========================

def in_range(value, min_v, max_v):
    if min_v is not None and value < min_v:
        return False
    if max_v is not None and value > max_v:
        return False
    return True


def find_first(rows, predicate):
    for row in rows:
        if predicate(row):
            return row
    return None


def add_item(items, sku, name, qty=1):
    if not sku:
        return

    if qty is None or int(qty) <= 0:
        return

    items.append(
        {
            "sku": str(sku),
            "name": name,
            "qty": int(qty),
        }
    )


def aggregate_items(items):
    result = {}

    for item in items:
        key = (item["sku"], item["name"])

        if key not in result:
            result[key] = {
                "sku": item["sku"],
                "name": item["name"],
                "qty": 0,
            }

        result[key]["qty"] += item["qty"]

    return list(result.values())


def calculate_internika(shf, vsf, side, system, response_profile, decor_color):
    items = []
    warnings = []
    regular_response_qty = 0

    log_event(
        "CALC_START",
        "Начат расчет",
        shf=shf,
        vsf=vsf,
        side=side,
        system=system,
        response_profile=response_profile,
        decor_color=decor_color,
    )

    if shf < 325 or shf > 1600:
        warnings.append("ШСФ вне базового диапазона 325–1600 мм.")

    if vsf < 420 or vsf > 2400:
        warnings.append("ВСФ вне базового диапазона 420–2400 мм для текущего расчета.")

    main_lock = find_first(
        MAIN_LOCKS_VARIABLE,
        lambda r: in_range(vsf, r["vsf_min"], r["vsf_max"]),
    )

    if main_lock:
        add_item(items, main_lock["sku"], main_lock["name"], 1)
        regular_response_qty += main_lock["response_qty"]

        if shf <= 410:
            add_item(items, "1103192", "Переключатель угловой узкий 1R", 1)
        else:
            if main_lock["angle_qty"] >= 1:
                add_item(items, "1103178", "Переключатель угловой 1R", 1)

            if main_lock["angle_qty"] >= 2:
                add_item(items, "1103183", "Переключатель угловой 2R", 1)
    else:
        warnings.append("Не найден основной запор по высоте створки.")

    if vsf < 1000:
        add_item(items, "1102392", "Шпингалет поворотно-откидного окна нижний ВСФ < 1000", 1)
    else:
        add_item(items, "1102393", "Шпингалет поворотно-откидного окна нижний ВСФ > 1000", 1)

    sash_scissors = find_first(
        SASH_SCISSORS,
        lambda r: in_range(shf, r["shf_min"], r["shf_max"]),
    )

    if sash_scissors:
        add_item(items, sash_scissors["sku"], sash_scissors["name"], 1)
        regular_response_qty += sash_scissors["response_qty"]
    else:
        warnings.append("Не найдены ножницы на створке по ширине.")

    frame_scissors = find_first(
        FRAME_SCISSORS,
        lambda r: (
            r["system"] == system
            and r["side"] == side
            and in_range(shf, r["shf_min"], r["shf_max"])
        ),
    )

    if frame_scissors:
        add_item(items, frame_scissors["sku"], frame_scissors["name"], 1)
    else:
        warnings.append("Не найдены ножницы на раме по системе, стороне и ширине.")

    middle_lock = find_first(
        MIDDLE_LOCKS,
        lambda r: (
            in_range(shf, r["shf_min"], r["shf_max"])
            and in_range(vsf, r["vsf_min"], r["vsf_max"])
        ),
    )

    if middle_lock:
        add_item(items, middle_lock["sku"], middle_lock["name"], 1)
        regular_response_qty += middle_lock["response_qty"]

    add_item(items, "1077266", "Петля на раме верхняя 3 мм со штифтом", 1)
    add_item(items, "1077265", "Петля на раме нижняя 3 мм", 1)
    add_item(items, "1077263", "Петля на створке нижняя 3 мм", 1)
    add_item(items, "1089062", "Блокиратор откидывания", 1)

    profile = RESPONSE_PLATE_PROFILES.get(response_profile)

    if profile:
        add_item(items, profile["tilt_turn"], "Планка ответная поворотно-откидная", 1)
        add_item(items, profile["regular"], "Планка ответная", regular_response_qty)

        if profile.get("blocker_stop"):
            add_item(items, profile["blocker_stop"], "Упор блокиратора откидывания", 1)
        else:
            warnings.append("Для выбранного профиля не указан упор блокиратора откидывания.")
    else:
        warnings.append("Не найден профиль ответных планок.")

    if decor_color in DECOR_KITS:
        add_item(
            items,
            DECOR_KITS[decor_color],
            f"Комплект декоративных накладок, цвет {decor_color}",
            1,
        )

    aggregated = aggregate_items(items)

    log_event(
        "CALC_OK",
        "Расчет завершен",
        items_count=len(aggregated),
        warnings_count=len(warnings),
    )

    return aggregated, warnings


def format_specification(items, warnings):
    text = "Спецификация Internika:\n\n"

    if not items:
        text += "Не удалось сформировать спецификацию.\n"
    else:
        for item in items:
            text += f"{item['sku']} — {item['name']} — {item['qty']} шт.\n"

    if warnings:
        text += "\nПредупреждения:\n"
        for warning in warnings:
            text += f"• {warning}\n"

    return text


# =========================
# XML + SMTP
# =========================

def clean_code(value):
    return str(value).strip().replace(" ", "").replace("\n", "").replace("\r", "")


def build_order_filename(firm_code, warehouse_code):
    firm_code = clean_code(firm_code)
    warehouse_code = clean_code(warehouse_code)
    return f"ORDER_MAIN%firm-{firm_code}{warehouse_code}%(Internika_bot).xml"


def build_order_xml(items, firm_code, warehouse_code):
    log_event(
        "XML_BUILD_START",
        "Начато формирование XML",
        firm_code=firm_code,
        warehouse_code=warehouse_code,
        items_count=len(items),
    )

    if not items:
        raise RuntimeError("Нет товарных позиций для формирования XML")

    root = Element("КоммерческаяИнформация")

    doc_number = f"IB{datetime.now().strftime('%Y%m%d%H%M%S')}"

    doc = SubElement(
        root,
        "Документ",
        {
            "Дата": datetime.now().strftime("%d.%m.%Y"),
            "Комментарий": f"Заявка сформирована ботом Internika. ШИФР={firm_code}; Склад={warehouse_code}",
            "Номер": doc_number,
            "ХозОперация": "Order",
        },
    )

    for item in items:
        sku = str(item["sku"]).strip()
        qty = str(int(item["qty"]))
        name = str(item["name"]).strip()

        SubElement(
            doc,
            "ТоварнаяПозиция",
            {
                "Единица": "шт",
                "Количество": qty,
                "Товар": sku,
                "Описание": name,
            },
        )

    rough_xml = tostring(root, encoding="utf-8")
    parsed = minidom.parseString(rough_xml)
    xml_bytes = parsed.toprettyxml(indent="\t", encoding="UTF-8")

    log_event(
        "XML_BUILD_OK",
        "XML сформирован",
        doc_number=doc_number,
        xml_size_bytes=len(xml_bytes),
    )

    return xml_bytes, doc_number


def save_xml_file(filename, xml_bytes):
    log_event("XML_SAVE_START", "Начато сохранение XML", filename=filename)

    with open(filename, "wb") as file:
        file.write(xml_bytes)

    file_size = os.path.getsize(filename)

    log_event(
        "XML_SAVE_OK",
        "XML сохранен",
        filename=filename,
        file_size_bytes=file_size,
    )

    return file_size


def check_smtp_env():
    missing = []

    if not SMTP_HOST:
        missing.append("SMTP_HOST")

    if not SMTP_PORT:
        missing.append("SMTP_PORT")

    if not SMTP_USER:
        missing.append("SMTP_USER")

    if not SMTP_PASSWORD:
        missing.append("SMTP_PASSWORD")

    if not ORDER_EMAIL_TO:
        missing.append("ORDER_EMAIL_TO")

    if missing:
        raise RuntimeError(f"Не заданы SMTP-переменные: {', '.join(missing)}")


def send_email_with_xml(filename, xml_bytes, firm_code, warehouse_code, doc_number):
    check_smtp_env()

    log_event(
        "SMTP_START",
        "Начата отправка письма",
        smtp_host=SMTP_HOST,
        smtp_port=SMTP_PORT,
        smtp_user=SMTP_USER,
        order_email_to=ORDER_EMAIL_TO,
        filename=filename,
        doc_number=doc_number,
    )

    msg = EmailMessage()
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
    msg["To"] = ORDER_EMAIL_TO
    msg["Subject"] = f"Заявка Internika bot: {filename}"

    msg.set_content(
        "Во вложении XML-файл заявки, сформированный ботом Internika.\n\n"
        f"ШИФР фирмы: {firm_code}\n"
        f"Код склада: {warehouse_code}\n"
        f"Номер документа: {doc_number}\n"
        f"Файл: {filename}\n"
    )

    msg.add_attachment(
        xml_bytes,
        maintype="application",
        subtype="xml",
        filename=filename,
    )

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=300) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

        log_event(
            "SMTP_OK",
            "Письмо успешно отправлено",
            filename=filename,
            order_email_to=ORDER_EMAIL_TO,
            doc_number=doc_number,
        )

    except smtplib.SMTPAuthenticationError as exc:
        log_error(
            "SMTP_AUTH_ERROR",
            "Ошибка авторизации SMTP. Проверь SMTP_USER и SMTP_PASSWORD / пароль приложения Gmail",
            exc=exc,
            smtp_user=SMTP_USER,
        )
        raise

    except smtplib.SMTPConnectError as exc:
        log_error(
            "SMTP_CONNECT_ERROR",
            "Ошибка подключения к SMTP-серверу",
            exc=exc,
            smtp_host=SMTP_HOST,
            smtp_port=SMTP_PORT,
        )
        raise

    except smtplib.SMTPException as exc:
        log_error(
            "SMTP_ERROR",
            "SMTP-ошибка при отправке письма",
            exc=exc,
            smtp_host=SMTP_HOST,
            smtp_port=SMTP_PORT,
        )
        raise


# =========================
# Telegram Bot
# =========================

class CalcStates(StatesGroup):
    shf = State()
    vsf = State()
    side = State()
    system = State()
    response_profile = State()
    decor_color = State()
    after_calc = State()
    firm_code = State()
    warehouse_code = State()


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


def kb(items):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=item)] for item in items],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()

    log_event(
        "TG_START",
        "Пользователь начал расчет",
        user_id=message.from_user.id,
        username=message.from_user.username,
    )

    await message.answer(
        "Калькулятор фурнитуры Internika.\n\n"
        "Введите ШСФ — ширину створки по фальцу, мм.\n"
        "Например: 800"
    )

    await state.set_state(CalcStates.shf)


@dp.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Расчет отменен. Для нового расчета нажмите /start")


@dp.message(CalcStates.shf)
async def get_shf(message: Message, state: FSMContext):
    try:
        shf = int(message.text.strip())
    except ValueError:
        await message.answer("Введите число, например 800")
        return

    await state.update_data(shf=shf)

    await message.answer(
        "Введите ВСФ — высоту створки по фальцу, мм.\n"
        "Например: 1200"
    )

    await state.set_state(CalcStates.vsf)


@dp.message(CalcStates.vsf)
async def get_vsf(message: Message, state: FSMContext):
    try:
        vsf = int(message.text.strip())
    except ValueError:
        await message.answer("Введите число, например 1200")
        return

    await state.update_data(vsf=vsf)

    await message.answer(
        "Выберите направление открывания:",
        reply_markup=kb(["Правое", "Левое"]),
    )

    await state.set_state(CalcStates.side)


@dp.message(CalcStates.side)
async def get_side(message: Message, state: FSMContext):
    if message.text not in ["Правое", "Левое"]:
        await message.answer("Выберите значение кнопкой.")
        return

    await state.update_data(side=message.text)

    await message.answer(
        "Выберите систему ножниц на раме:",
        reply_markup=kb(["12/20-9", "12/20-13", "12/22-13"]),
    )

    await state.set_state(CalcStates.system)


@dp.message(CalcStates.system)
async def get_system(message: Message, state: FSMContext):
    if message.text not in ["12/20-9", "12/20-13", "12/22-13"]:
        await message.answer("Выберите значение кнопкой.")
        return

    await state.update_data(system=message.text)

    await message.answer(
        "Выберите профиль ответных планок:",
        reply_markup=kb(list(RESPONSE_PLATE_PROFILES.keys())),
    )

    await state.set_state(CalcStates.response_profile)


@dp.message(CalcStates.response_profile)
async def get_response_profile(message: Message, state: FSMContext):
    if message.text not in RESPONSE_PLATE_PROFILES:
        await message.answer("Выберите значение кнопкой.")
        return

    await state.update_data(response_profile=message.text)

    await message.answer(
        "Выберите декоративные накладки:",
        reply_markup=kb(["белый", "темно-коричневый", "без накладок"]),
    )

    await state.set_state(CalcStates.decor_color)


@dp.message(CalcStates.decor_color)
async def get_decor_color(message: Message, state: FSMContext):
    if message.text not in ["белый", "темно-коричневый", "без накладок"]:
        await message.answer("Выберите значение кнопкой.")
        return

    data = await state.get_data()

    decor_color = message.text
    if decor_color == "без накладок":
        decor_color = ""

    try:
        items, warnings = calculate_internika(
            shf=data["shf"],
            vsf=data["vsf"],
            side=data["side"],
            system=data["system"],
            response_profile=data["response_profile"],
            decor_color=decor_color,
        )

        result_text = format_specification(items, warnings)

        await state.update_data(
            decor_color=decor_color,
            last_items=items,
            last_warnings=warnings,
        )

        await message.answer(result_text)

        await message.answer(
            "Что сделать дальше?",
            reply_markup=kb(["Отправить заявку", "Новый расчет"]),
        )

        await state.set_state(CalcStates.after_calc)

    except Exception as exc:
        log_error(
            "CALC_ERROR",
            "Ошибка при расчете",
            exc=exc,
            user_id=message.from_user.id,
        )
        await message.answer(
            "Ошибка при расчете. Подробности смотри в Render Logs или /logs."
        )


@dp.message(CalcStates.after_calc)
async def after_calc_action(message: Message, state: FSMContext):
    if message.text == "Новый расчет":
        await state.clear()
        await message.answer("Для нового расчета нажмите /start")
        return

    if message.text == "Отправить заявку":
        data = await state.get_data()
        items = data.get("last_items", [])

        if not items:
            await message.answer("Не найден последний расчет. Сначала выполните расчет заново через /start")
            await state.clear()
            return

        await message.answer(
            "Введите ШИФР фирмы.\n"
            "Например: 1000000"
        )

        await state.set_state(CalcStates.firm_code)
        return

    await message.answer("Выберите действие кнопкой.")


@dp.message(CalcStates.firm_code)
async def get_firm_code(message: Message, state: FSMContext):
    firm_code = clean_code(message.text)

    if not firm_code:
        await message.answer("ШИФР фирмы не должен быть пустым.")
        return

    await state.update_data(firm_code=firm_code)

    await message.answer(
        "Введите код склада.\n"
        "Например: 4290"
    )

    await state.set_state(CalcStates.warehouse_code)


@dp.message(CalcStates.warehouse_code)
async def get_warehouse_code(message: Message, state: FSMContext):
    warehouse_code = clean_code(message.text)

    if not warehouse_code:
        await message.answer("Код склада не должен быть пустым.")
        return

    data = await state.get_data()

    firm_code = data.get("firm_code")
    items = data.get("last_items", [])

    operation_id = str(uuid.uuid4())[:8]

    log_event(
        "ORDER_START",
        "Начато создание заявки",
        operation_id=operation_id,
        user_id=message.from_user.id,
        firm_code=firm_code,
        warehouse_code=warehouse_code,
        items_count=len(items),
    )

    await message.answer("Формирую XML и отправляю заявку на почту...")

    try:
        filename = build_order_filename(firm_code, warehouse_code)
        xml_bytes, doc_number = build_order_xml(items, firm_code, warehouse_code)

        save_xml_file(filename, xml_bytes)

        send_email_with_xml(
            filename=filename,
            xml_bytes=xml_bytes,
            firm_code=firm_code,
            warehouse_code=warehouse_code,
            doc_number=doc_number,
        )

        log_event(
            "ORDER_OK",
            "Заявка успешно сформирована и отправлена",
            operation_id=operation_id,
            filename=filename,
            doc_number=doc_number,
        )

        await message.answer(
            "Заявка успешно сформирована и отправлена.\n\n"
            f"Файл: {filename}\n"
            f"Номер документа: {doc_number}"
        )

        await message.answer("Для нового расчета нажмите /start")
        await state.clear()

    except Exception as exc:
        log_error(
            "ORDER_ERROR",
            "Ошибка при создании или отправке заявки",
            exc=exc,
            operation_id=operation_id,
            firm_code=firm_code,
            warehouse_code=warehouse_code,
        )

        await message.answer(
            "Ошибка при формировании или отправке заявки.\n\n"
            f"ID операции: {operation_id}\n"
            "Проверь Render Logs или страницу /logs."
        )


# =========================
# Webhook server
# =========================

async def healthcheck(request):
    return web.Response(text="Internika Telegram Bot is running")


async def logs_view(request):
    key = request.query.get("key")

    if key != LOG_SECRET:
        return web.Response(status=403, text="Forbidden")

    try:
        if not os.path.exists(LOG_FILE):
            return web.Response(text="Лог-файл пока не создан.")

        with open(LOG_FILE, "r", encoding="utf-8") as file:
            lines = file.readlines()

        last_lines = lines[-300:]

        return web.Response(
            text="".join(last_lines),
            content_type="text/plain",
            charset="utf-8",
        )

    except Exception as exc:
        return web.Response(status=500, text=f"Ошибка чтения логов: {exc}")


async def telegram_webhook(request):
    try:
        data = await request.json()
        update = Update.model_validate(data, context={"bot": bot})
        await dp.feed_update(bot, update)

    except Exception as exc:
        log_error("WEBHOOK_ERROR", "Ошибка обработки webhook", exc=exc)

    return web.Response(text="OK")


async def on_startup(app):
    webhook_full_url = f"{WEBHOOK_URL}{WEBHOOK_PATH}"

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(
        url=webhook_full_url,
        drop_pending_updates=True,
    )

    log_event("WEBHOOK_SET", "Webhook установлен", webhook_url=webhook_full_url)


async def on_shutdown(app):
    await bot.session.close()
    log_event("BOT_SHUTDOWN", "Сессия бота закрыта")


def create_app():
    app = web.Application()

    app.router.add_get("/", healthcheck)
    app.router.add_get("/health", healthcheck)
    app.router.add_get("/logs", logs_view)
    app.router.add_post(WEBHOOK_PATH, telegram_webhook)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    return app


if __name__ == "__main__":
    log_event("APP_START", "Запуск приложения", port=PORT)
    web.run_app(
        create_app(),
        host="0.0.0.0",
        port=PORT,
    )

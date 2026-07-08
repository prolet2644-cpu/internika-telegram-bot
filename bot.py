!pip install -q -U aiogram nest_asyncio pandas

import asyncio
import nest_asyncio
import pandas as pd
from getpass import getpass

from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage


nest_asyncio.apply()

BOT_TOKEN = os.getenv("8862946438:AAFzsdld7LfxisEX7kOlxsn1_ue_iroKxyc")


# =========================
# Справочники Internika
# MVP: поворотно-откидная створка, ручка средняя/переменная
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
    {
        "system": "12/20-9",
        "shf_min": 325,
        "shf_max": 610,
        "side": "Левое",
        "sku": "1088661",
        "name": "Ножницы на раме 12/20-9 250 левое",
    },
    {
        "system": "12/20-9",
        "shf_min": 325,
        "shf_max": 610,
        "side": "Правое",
        "sku": "1088662",
        "name": "Ножницы на раме 12/20-9 250 правое",
    },
    {
        "system": "12/20-9",
        "shf_min": 611,
        "shf_max": 810,
        "side": "Левое",
        "sku": "1088663",
        "name": "Ножницы на раме 12/20-9 350 левое",
    },
    {
        "system": "12/20-9",
        "shf_min": 611,
        "shf_max": 810,
        "side": "Правое",
        "sku": "1088664",
        "name": "Ножницы на раме 12/20-9 350 правое",
    },
    {
        "system": "12/20-9",
        "shf_min": 811,
        "shf_max": 1600,
        "side": "Левое",
        "sku": "1088665",
        "name": "Ножницы на раме 12/20-9 500 левое",
    },
    {
        "system": "12/20-9",
        "shf_min": 811,
        "shf_max": 1600,
        "side": "Правое",
        "sku": "1088666",
        "name": "Ножницы на раме 12/20-9 500 правое",
    },

    {
        "system": "12/20-13",
        "shf_min": 325,
        "shf_max": 610,
        "side": "Левое",
        "sku": "1088667",
        "name": "Ножницы на раме 12/20-13 250 левое",
    },
    {
        "system": "12/20-13",
        "shf_min": 325,
        "shf_max": 610,
        "side": "Правое",
        "sku": "1088668",
        "name": "Ножницы на раме 12/20-13 250 правое",
    },
    {
        "system": "12/20-13",
        "shf_min": 611,
        "shf_max": 810,
        "side": "Левое",
        "sku": "1088669",
        "name": "Ножницы на раме 12/20-13 350 левое",
    },
    {
        "system": "12/20-13",
        "shf_min": 611,
        "shf_max": 810,
        "side": "Правое",
        "sku": "1088670",
        "name": "Ножницы на раме 12/20-13 350 правое",
    },
    {
        "system": "12/20-13",
        "shf_min": 811,
        "shf_max": 1600,
        "side": "Левое",
        "sku": "1088671",
        "name": "Ножницы на раме 12/20-13 500 левое",
    },
    {
        "system": "12/20-13",
        "shf_min": 811,
        "shf_max": 1600,
        "side": "Правое",
        "sku": "1088672",
        "name": "Ножницы на раме 12/20-13 500 правое",
    },

    {
        "system": "12/22-13",
        "shf_min": 325,
        "shf_max": 610,
        "side": "Левое",
        "sku": "1088673",
        "name": "Ножницы на раме 12/22-13 250 левое",
    },
    {
        "system": "12/22-13",
        "shf_min": 325,
        "shf_max": 610,
        "side": "Правое",
        "sku": "1088674",
        "name": "Ножницы на раме 12/22-13 250 правое",
    },
    {
        "system": "12/22-13",
        "shf_min": 611,
        "shf_max": 810,
        "side": "Левое",
        "sku": "1088675",
        "name": "Ножницы на раме 12/22-13 350 левое",
    },
    {
        "system": "12/22-13",
        "shf_min": 611,
        "shf_max": 810,
        "side": "Правое",
        "sku": "1088676",
        "name": "Ножницы на раме 12/22-13 350 правое",
    },
    {
        "system": "12/22-13",
        "shf_min": 811,
        "shf_max": 1600,
        "side": "Левое",
        "sku": "1088677",
        "name": "Ножницы на раме 12/22-13 500 левое",
    },
    {
        "system": "12/22-13",
        "shf_min": 811,
        "shf_max": 1600,
        "side": "Правое",
        "sku": "1088678",
        "name": "Ножницы на раме 12/22-13 500 правое",
    },
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
    "12/20 13, +3.3 мм": {
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
    if sku is None:
        return

    if qty is None or int(qty) <= 0:
        return

    items.append(
        {
            "Артикул": str(sku),
            "Наименование": name,
            "Кол-во": int(qty),
        }
    )


def calculate_internika(shf, vsf, side, system, response_profile, decor_color):
    items = []
    warnings = []
    regular_response_qty = 0

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
        add_item(items, DECOR_KITS[decor_color], f"Комплект декоративных накладок, цвет {decor_color}", 1)

    df = pd.DataFrame(items)

    if not df.empty:
        df = (
            df.groupby(["Артикул", "Наименование"], as_index=False)
            .agg({"Кол-во": "sum"})
            .sort_values(["Наименование", "Артикул"])
        )

    text = "Спецификация Internika:\n\n"

    if df.empty:
        text += "Не удалось сформировать спецификацию.\n"
    else:
        for _, row in df.iterrows():
            text += f"{row['Артикул']} — {row['Наименование']} — {row['Кол-во']} шт.\n"

    if warnings:
        text += "\nПредупреждения:\n"
        for warning in warnings:
            text += f"• {warning}\n"

    return text


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
    await message.answer("Введите ВСФ — высоту створки по фальцу, мм.\nНапример: 1200")
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

    result = calculate_internika(
        shf=data["shf"],
        vsf=data["vsf"],
        side=data["side"],
        system=data["system"],
        response_profile=data["response_profile"],
        decor_color=decor_color,
    )

    await message.answer(result)
    await message.answer("Для нового расчета нажмите /start")
    await state.clear()

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

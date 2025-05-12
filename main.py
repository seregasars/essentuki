from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram_sqlite_storage.sqlitestore import SQLStorage  # Импортируем SQLStorage
from aiogram import Router
import asyncio
import logging

# Токен бота
API_TOKEN = "7557198950:AAEfq3XrNKRO-FUtOcEOKdEMc7IS6tRwdWI"

# Инициализация хранилища с SQLite
my_storage = SQLStorage('/data/fsm_storage.db', serializing_method='pickle')  # Вы можете использовать 'json' или 'pickle'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=my_storage)  # Передаем хранилище в диспетчер
router = Router()
dp.include_router(router)

logging.basicConfig(level=logging.INFO)

# Состояния
class Form(StatesGroup):
    choosing_category = State()
    choosing_question = State()

# Категории и вопросы
categories = {
    "Запись на приём": ["Как записаться на приём к мэру?"],
    "Соцвыплаты и льготы": [
        "Как получить земельный участок участникам СВО?",
        "Куда можно обратиться за выплатами участникам СВО?"
    ],
    "Жалобы и обращения": [
        "Как оставить жалобу на работу администрации?",
        "В течение какого срока рассматривается заявление?",
        "Куда обращаться с жалобой на УК?"
    ],
    "Коммунальные услуги": [
        "Отключили электричество?",
        "Отключили газ?",
        "Отсутствует холодное водоснабжение?",
        "Отсутствует горячее водоснабжение или отопление?"
    ]
}

# Ответы
answers = {
    "Как записаться на приём к мэру?": """Запись осуществляется:
с понедельника по пятницу с 09.00 - 18.00 (перерыв 13.00 - 14.00)
по адресу: г. Ессентуки, ул. Вокзальная, 3А, тел. (87934) 6-56-28.
Запись на личный приём к Главе города — по результатам приёмов заместителей.""",

    "Как получить земельный участок участникам СВО?": """Участники СВО, получившие государственные награды, могут подать заявление в администрацию по месту жительства. Перечень документов определяет Правительство края.""",

    "Куда можно обратиться за выплатами участникам СВО?": """Обратиться можно:
- Минтруд Ставропольского края
- Соцзащита по месту жительства
- Соцфонд РФ: sfr.gov.ru
- Фонд "Защитники Отечества", г. Ставрополь, ул. Ленина, 474. Тел: 8 (800) 100-58-71""",

    "Как оставить жалобу на работу администрации?": """На сайте essentuki.gosuslugi.ru.
Тел. приёмной: +7 (87934) 6-08-10.
Email: adm-essentuki@yandex.ru""",

    "В течение какого срока рассматривается заявление?": """Срок — 30 дней со дня регистрации.
В исключительных случаях — до 60 дней с уведомлением гражданина.
См. закон №59-ФЗ от 02.05.2006.""",

    "Куда обращаться с жалобой на УК?": """В жилищную инспекцию Ставропольского края:
Тел. доверия: (8652) 26-99-69
Email: nadzor26@stavregion.ru
Через портал ГИС ЖКХ""",

    "Отключили электричество?": """АО «Ессентукская сетевая компания»:
Тел: 8 (800) 600-55-83
ЕДДС: 112 или (87934) 6-04-00""",

    "Отключили газ?": """АО «Ессентукигоргаз»:
Тел: 7-33-60 или 104 (моб.)""",

    "Отсутствует холодное водоснабжение?": """Ессентукский водоканал:
Тел: +7 (879) 346-06-26
Стан. Ессентукская, ул. Гагарина, 295 — (87961) 5-07-89""",

    "Отсутствует горячее водоснабжение или отопление?": """АО «Энергоресурсы»:
Тел: 8 (87934) 2-91-00
ООО «Объединение котельных курорта»: 6-54-08
Или в свою УК / ТСЖ"""
}

# Команда /start
@router.message(F.text == "/start")
async def start(message: types.Message, state: FSMContext):
    welcome_text = (
        "Привет, я чат-бот города Ессентуки!\n"
        "Я помогу вам найти информацию по различным городским вопросам.\n\n"
        "Выберите категорию:"
    )
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=cat)] for cat in categories.keys()],
        resize_keyboard=True
    )
    await message.answer(welcome_text, reply_markup=kb)
    await state.set_state(Form.choosing_category)

# Выбор категории
@router.message(Form.choosing_category)
async def choose_category(message: types.Message, state: FSMContext):
    selected = message.text
    if selected not in categories:
        await message.answer("Пожалуйста, выберите категорию с клавиатуры.")
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=q)] for q in categories[selected]] + [[KeyboardButton(text="🏠 На главную")]],
        resize_keyboard=True
    )
    await state.update_data(category=selected)
    await message.answer("Выберите вопрос:", reply_markup=kb)
    await state.set_state(Form.choosing_question)

# Выбор вопроса или возврат на главную
@router.message(Form.choosing_question)
async def answer_question(message: types.Message, state: FSMContext):
    if message.text == "🏠 На главную":
        await start(message, state)
        return

    question = message.text
    answer = answers.get(question)

    if not answer:
        await message.answer("Такой вопрос не найден. Попробуйте снова.")
        return

    await message.answer(f"Ответ:\n{answer}")

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=cat)] for cat in categories.keys()],
        resize_keyboard=True
    )
    await message.answer("Хотите задать ещё вопрос? Выберите категорию:", reply_markup=kb)
    await state.set_state(Form.choosing_category)

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

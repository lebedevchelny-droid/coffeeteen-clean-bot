import os
import sqlite3
import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode, ContentType
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем переменные из окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID')

if not BOT_TOKEN or not ADMIN_CHAT_ID:
    logger.error("❌ Не найдены переменные окружения!")
    exit(1)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# База данных
def get_db_connection():
    conn = sqlite3.connect("reports.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT,
        full_name TEXT NOT NULL,
        coffee_shop TEXT NOT NULL,
        photos TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

init_db()

# Полный список всех 36 кофеен
COFFEE_SHOPS = {
    1: "Кофейня №1 (Рахлина, 5)",
    2: "Кофейня №2 (Тукая, 62)",
    3: "Кофейня №3 (Татарстана, 53А)",
    4: "Кофейня №4 (Московская, 22)",
    5: "Кофейня №5 (Мира, 30Б)",
    6: "Кофейня №6 (Калинина, 32)",
    7: "Кофейня №7 (М.Гареева, 9А)",
    8: "Кофейня №8 (Р.Гареева, 96)",
    9: "Кофейня №9 (Гафури, 5)",
    10: "Кофейня №10 (Аббасова, 8)",
    11: "Кофейня №11 (Аббасова, 9)",
    12: "Кофейня №12 (ТЦ МОКИ)",
    13: "Кофейня №13 (ТЦ Горки)",
    14: "Кофейня №14 (ТЦ МЕГА)",
    15: "Кофейня №15 (ТЦ Южный)",
    16: "Кофейня №16 (ТЦ ПаркХаус 1)",
    17: "Кофейня №17 (ТЦ ПаркХаус 2)",
    18: "Кофейня №18 (ТЦ Порт)",
    19: "Кофейня №19 (ТЦ Кольцо)",
    20: "Кофейня №20 (ТЦ Республика)",
    21: "Кофейня №21 (ТЦ Франт)",
    22: "Кофейня №22 (ТЦ XL)",
    23: "Кофейня №23 (Джалиля, 19)",
    24: "Кофейня №24 (Энергетиков, 3)",
    25: "Кофейня №25 (Революционная, 24)",
    26: "Кофейня №26 (Пушкина, 16)",
    27: "Кофейня №27 (Дубравная, 51Г)",
    28: "Кофейня №28 (Декабристов, 85)",
    29: "Кофейня №29 (Мой Ритм)",
    30: "Кофейня №30 (Тэцевская, 4Д)",
    31: "Кофейня №31 (Максимова, 50)",
    32: "Кофейня №32 (Яраткан, 1)",
    33: "Кофейня №33 (ТЦ Радужный, Садовая 9)",
    34: "Кофейня №34 (Зеленодольск, Эссен)",
    35: "Кофейня №35 (Н.Челны, Джумба)",
    36: "Кофейня №36 (Запасная)"
}

class ReportStates(StatesGroup):
    selecting_shop = State()
    confirmation = State()
    uploading_photos = State()

async def send_to_admin(chat_id: int, message: str, photos: list = None):
    try:
        await bot.send_message(chat_id, message, parse_mode=ParseMode.HTML)
        if photos:
            media = [types.InputMediaPhoto(media=photo) for photo in photos]
            await bot.send_media_group(chat_id, media)
        return True
    except Exception as e:
        logger.error(f"Ошибка отправки админу: {e}")
        return False

@dp.message(Command("start", "cancel"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    keyboard = [[types.KeyboardButton(text=name)] for name in COFFEE_SHOPS.values()]
    await message.answer(
        "🏠 <b>Выберите кофейню из списка:</b>",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            one_time_keyboard=True
        ),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(ReportStates.selecting_shop)

@dp.message(ReportStates.selecting_shop)
async def process_shop(message: types.Message, state: FSMContext):
    if message.text not in COFFEE_SHOPS.values():
        await message.answer("⚠️ Пожалуйста, выберите кофейню из списка!")
        return

    await state.update_data(shop_name=message.text)
    
    await message.answer(
        "🧹 <b>ИНСТРУКЦИЯ ПО ГЕНКЕ</b>\n\n"
        "‼️ Сделай уборку качественно и внимательно!\n\n"
        "<b>Обязательно проверь:</b>\n"
        "• Все труднодоступные места (углы, за оборудованием)\n"
        "• Туалет (пол, сантехнику, зеркала, дверные ручки)\n"
        "• Полы во всех зонах (залы, кухня, склад)\n"
        "• Рабочие поверхности (столы, стойки, полки)\n"
        "• Оборудование (кофемашина, холодильники, печи)\n"
        "• Кофемолку (внутри и снаружи, лоток)\n"
        "• Кофемашину (группа, поддон, панель)\n"
        "• Холдеры и питчеры (внутри и снаружи)\n"
        "• Мойки и раковины (без налёта и пятен)\n\n"
        "<b>Проверь ВСЕ зоны тщательно!</b>",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="✅ Я прочитал инструкцию")]],
            resize_keyboard=True
        ),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(ReportStates.confirmation)

@dp.message(ReportStates.confirmation)
async def process_confirmation(message: types.Message, state: FSMContext):
    if message.text != "✅ Я прочитал инструкцию":
        await message.answer("Пожалуйста, подтвердите прочтение инструкции")
        return
    
    await state.update_data(photos=[])
    await message.answer(
        "📸 <b>Отправьте 8 фотографий уборки:</b>\n\n"
        "<b>Требования к фото:</b>\n"
        "- Минимальный размер 800px по меньшей стороне\n"
        "- Хорошее освещение и четкость\n"
        "- Должны охватывать все основные зоны уборки\n"
        "- Сделаны сегодня и отражают текущее состояние\n\n"
        "Можно отправлять по одному или несколько сразу",
        reply_markup=types.ReplyKeyboardRemove(),
        parse_mode=ParseMode.HTML
    )
    await state.set_state(ReportStates.uploading_photos)

@dp.message(ReportStates.uploading_photos, lambda msg: msg.content_type == ContentType.PHOTO)
async def process_photos(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_photos = data.get("photos", [])
    
    best_photo = message.photo[-1]
    if best_photo.width < 800 or best_photo.height < 800:
        await message.answer("❌ Фото слишком маленькое. Минимальный размер: 800px с каждой стороны")
        return
    
    current_photos.append(best_photo.file_id)
    await state.update_data(photos=current_photos)
    
    if len(current_photos) >= 8:
        await finish_report(message, state, current_photos[-8:])
    else:
        remaining = 8 - len(current_photos)
        await message.answer(f"✅ Принято фото: {len(current_photos)}/8\nОсталось: {remaining}")

async def finish_report(message: types.Message, state: FSMContext, photos: list):
    data = await state.get_data()
    shop_name = data["shop_name"]
    user = message.from_user

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reports (user_id, username, full_name, coffee_shop, photos) VALUES (?, ?, ?, ?, ?)",
            (user.id, user.username, user.full_name, shop_name, ";".join(photos))
        )
        conn.commit()
        conn.close()
        
        report_msg = f"📋 НОВЫЙ ОТЧЁТ ОБ УБОРКЕ\n\n🏠 Кофейня: {shop_name}\n👤 Сотрудник: {user.full_name}\n📅 Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        
        success = await send_to_admin(int(ADMIN_CHAT_ID), report_msg, photos)
        
        if success:
            await message.answer("🎉 ОТЧЁТ УСПЕШНО ПРИНЯТ! Спасибо за работу! ☕")
        else:
            await message.answer("⚠️ Отчет сохранен, но не отправлен админу. Сообщите руководителю.")
            
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.answer("⚠️ Произошла ошибка! Попробуйте еще раз.")
    finally:
        await state.clear()

async def main():
    logger.info("🚀 Бот запущен!")
    await dp.start_polling(bot, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())

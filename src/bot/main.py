import logging
import os
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.middleware import FSMContextMiddleware
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

load_dotenv()

API_TOKEN = os.getenv('BOT_TOKEN')
API_URL = 'http://localhost:8888/api/v1/products'  # URL вашего API

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Определение состояний
class Form(StatesGroup):
    waiting_for_artikul = State()

# Команда /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Получить информацию о товаре", callback_data='info'))
    builder.add(InlineKeyboardButton(text="Подписаться на товар", callback_data='subscribe'))
    builder.adjust(1)  # Кнопки будут расположены вертикально

    await message.answer("Выберите действие:", reply_markup=builder.as_markup())

# Обработка нажатий кнопок
@dp.callback_query()
async def process_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == 'info':
        await callback.answer("Введите артикул товара:")
        await state.set_state(Form.waiting_for_artikul)
    elif callback.data == 'subscribe':
        await callback.answer()
        await callback.message.answer("Вы подписались на товар!")

# Обработка ввода артикула
@dp.message(Form.waiting_for_artikul)
async def process_artikul(message: types.Message, state: FSMContext):
    artikul = message.text
    await message.answer(f"Запрашиваем данные для артикула: {artikul}")

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, json={"artikul": artikul}) as response:
            if response.status == 200:
                data = await response.json()
                # Предположим, что данные содержат поле 'info' с информацией о товаре
                await message.answer(f"Данные о товаре: {data.get('info', 'Нет информации')}")
            else:
                await message.answer("Не удалось получить данные. Попробуйте еще раз.")

    await state.clear()  # Сбрасываем состояние

async def main():
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())

import logging
import os
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.middleware import FSMContextMiddleware
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
import uvicorn
from pydantic import BaseModel

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Инициализация глобальных переменных
BOT_API_TOKEN = os.getenv('BOT_TOKEN')
API_TOKEN = os.getenv('API_TOKEN')
API_URL = os.getenv('API_URL', 'http://app/api/v1')

logger.info(f"Initialized with API_URL: {API_URL}")
logger.info(f"Bot token present: {'Yes' if BOT_API_TOKEN else 'No'}")
logger.info(f"API token present: {'Yes' if API_TOKEN else 'No'}")

# Настройки запросов
HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': f'Bearer {API_TOKEN}'
}

# Инициализация бота
bot = Bot(token=BOT_API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Инициализация FastAPI
app = FastAPI(title="Telegram Bot API")

@app.on_event("startup")
async def startup_event():
    logger.info("Bot API starting up...")
    try:
        bot_info = await bot.get_me()
        logger.info(f"Bot connected successfully: @{bot_info.username}")
    except Exception as e:
        logger.error(f"Failed to initialize bot: {e}")
        raise

class PriceNotification(BaseModel):
    artikul: str
    old_price: float
    new_price: float
    product_name: str

class QuantityNotification(BaseModel):
    artikul: str
    old_quantity: int
    new_quantity: int
    product_name: str

@app.post("/api/v1/notify/price-change")
async def notify_price_change(notification: PriceNotification):
    """Отправляет уведомления об изменении цены подписчикам"""
    logger.info(f"Received price change notification for artikul {notification.artikul}")
    
    # Получаем список подписчиков через API
    async with aiohttp.ClientSession() as session:
        url = f"{API_URL}/subscriptions/{notification.artikul}/users"
        logger.info(f"Fetching subscribers from: {url}")
        
        async with session.get(url, headers=HEADERS) as response:
            if response.status != 200:
                logger.error(f"Failed to get subscribers: HTTP {response.status}")
                raise HTTPException(status_code=500, detail="Failed to get subscribers")
            
            subscribers = await response.json()
            logger.info(f"Found {len(subscribers)} subscribers")
            
            # Отправляем уведомления каждому подписчику
            notifications_sent = 0
            for subscriber in subscribers:
                try:
                    chat_id = subscriber['chat_id']
                    price_diff = notification.new_price - notification.old_price
                    price_change = "снизилась" if price_diff < 0 else "повысилась"
                    percent_change = abs(price_diff / notification.old_price * 100)
                    
                    message = (
                        f"💰 Изменение цены на {notification.product_name}!\n\n"
                        f"Артикул: {notification.artikul}\n"
                        f"Старая цена: {notification.old_price:,.2f} ₽\n"
                        f"Новая цена: {notification.new_price:,.2f} ₽\n"
                        f"Цена {price_change} на {abs(price_diff):,.2f} ₽ ({percent_change:.1f}%)\n\n"
                        f"🔗 https://www.wildberries.ru/catalog/{notification.artikul}/detail.aspx"
                    )
                    
                    logger.info(f"Sending notification to chat_id: {chat_id}")
                    await bot.send_message(chat_id=chat_id, text=message)
                    notifications_sent += 1
                    logger.info(f"Successfully sent notification to chat_id: {chat_id}")
                except Exception as e:
                    logger.error(f"Failed to send notification to {chat_id}: {str(e)}")
            
            logger.info(f"Successfully sent {notifications_sent} notifications")
            return {"success": True, "notifications_sent": notifications_sent}

@app.post("/api/v1/notify/quantity-change")
async def notify_quantity_change(notification: QuantityNotification):
    """Отправляет уведомления об изменении количества подписчикам"""
    # Получаем список подписчиков через API
    async with aiohttp.ClientSession() as session:
        url = f"{API_URL}/subscriptions/{notification.artikul}/users"
        async with session.get(url, headers=HEADERS) as response:
            if response.status != 200:
                logger.error(f"Failed to get subscribers: HTTP {response.status}")
                raise HTTPException(status_code=500, detail="Failed to get subscribers")
            
            subscribers = await response.json()
            
            # Отправляем уведомления каждому подписчику
            notifications_sent = 0
            for subscriber in subscribers:
                try:
                    chat_id = subscriber['chat_id']
                    quantity_diff = notification.new_quantity - notification.old_quantity
                    quantity_change = "увеличилось" if quantity_diff > 0 else "уменьшилось"
                    percent_change = abs(quantity_diff / notification.old_quantity * 100) if notification.old_quantity > 0 else 100
                    
                    message = (
                        f"📦 Изменение количества товара {notification.product_name}!\n\n"
                        f"Артикул: {notification.artikul}\n"
                        f"Старое количество: {notification.old_quantity:,} шт.\n"
                        f"Новое количество: {notification.new_quantity:,} шт.\n"
                        f"Количество {quantity_change} на {abs(quantity_diff):,} шт. ({percent_change:.1f}%)\n\n"
                        f"🔗 https://www.wildberries.ru/catalog/{notification.artikul}/detail.aspx"
                    )
                    
                    await bot.send_message(chat_id=chat_id, text=message)
                    notifications_sent += 1
                    logger.info(f"Quantity change notification sent to {chat_id}")
                except Exception as e:
                    logger.error(f"Failed to send notification to {chat_id}: {e}")
            
            return {"success": True, "notifications_sent": notifications_sent}

# Определение состояний
class Form(StatesGroup):
    waiting_for_artikul = State()
    waiting_for_subscription_artikul = State()
    waiting_for_frequency = State()
    waiting_for_unsubscribe = State()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Получить информацию о товаре")],
        [KeyboardButton(text="Подписаться на товар")],
        [KeyboardButton(text="Мои подписки")]
    ],
    resize_keyboard=True
)

frequency_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="1 минута")],
        [KeyboardButton(text="30 минут")],
        [KeyboardButton(text="1 час")],
        [KeyboardButton(text="3 часа")],
        [KeyboardButton(text="6 часов")],
        [KeyboardButton(text="12 часов")],
        [KeyboardButton(text="24 часа")],
        [KeyboardButton(text="Вернуться обратно")]
    ],
    resize_keyboard=True
)

# Команда /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("Выберите действие:", reply_markup=main_keyboard)

# Обработка нажатий кнопок
@dp.message(lambda message: message.text in ["Получить информацию о товаре", "Подписаться на товар", "Мои подписки"])
async def process_buttons(message: types.Message, state: FSMContext):
    logger.info(f"Обработка нажатия кнопки: {message.text}")
    
    if message.text == "Получить информацию о товаре":
        await message.answer("Введите артикул товара:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.waiting_for_artikul)
    elif message.text == "Подписаться на товар":
        await message.answer("Введите артикул товара для подписки:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(Form.waiting_for_subscription_artikul)
    elif message.text == "Мои подписки":
        chat_id = str(message.chat.id)
        logger.info(f"Запрос подписок для chat_id: {chat_id}")
        
        async with aiohttp.ClientSession() as session:
            url = f"{API_URL}/subscriptions/user/{chat_id}"
            logger.info(f"Отправка GET запроса к: {url}")
            
            try:
                async with session.get(url, headers=HEADERS) as response:
                    logger.info(f"Получен ответ со статусом: {response.status}")
                    
                    if response.status != 200:
                        logger.error(f"Ошибка API: {response.status}")
                        await message.answer("Не удалось получить список подписок. Попробуйте позже.")
                        return
                    
                    subscriptions = await response.json()
                    logger.info(f"Получены подписки: {subscriptions}")
                    
                    if not subscriptions:
                        await message.answer("У вас нет активных подписок.")
                        return

                    # Получаем информацию о каждом товаре
                    subscription_info = []
                    for sub in subscriptions:
                        artikul = sub["artikul"]
                        logger.info(f"Запрос информации о товаре: {artikul}")
                        
                        try:
                            async with session.post(
                                f"{API_URL}/products",
                                headers=HEADERS,
                                json={"artikul": artikul}
                            ) as product_response:
                                if product_response.status == 200:
                                    product = await product_response.json()
                                    subscription_info.append(
                                        f"📦 {product.get('name', 'Название недоступно')}\n"
                                        f"📎 Артикул: {artikul}\n"
                                        f"💰 Текущая цена: {product.get('price', 'Н/Д')} ₽\n"
                                        f"📊 Количество: {product.get('total_quantity', 'Н/Д')} шт.\n"
                                        f"🔗 https://www.wildberries.ru/catalog/{artikul}/detail.aspx\n"
                                    )
                                else:
                                    logger.error(f"Ошибка получения информации о товаре {artikul}: {product_response.status}")
                                    subscription_info.append(
                                        f"📦 Товар {artikul}\n"
                                        f"❌ Не удалось получить информацию о товаре\n"
                                    )
                        except Exception as e:
                            logger.error(f"Ошибка при запросе товара {artikul}: {e}")
                            subscription_info.append(
                                f"📦 Товар {artikul}\n"
                                f"❌ Ошибка при получении информации\n"
                            )

                    if subscription_info:
                        message_text = "Ваши активные подписки:\n\n" + "\n".join(subscription_info)
                        message_text += "\n\nДля отмены подписки используйте команду /unsubscribe"
                        await message.answer(message_text)
                    else:
                        await message.answer("Не удалось получить информацию о подписках. Попробуйте позже.")
            except Exception as e:
                logger.error(f"Ошибка при запросе подписок: {e}")
                await message.answer("Произошла ошибка при получении подписок. Попробуйте позже.")

# Обработка ввода артикула
@dp.message(Form.waiting_for_artikul)
async def process_artikul(message: types.Message, state: FSMContext):
    if message.text == "Вернуться обратно":
        await message.answer("Выберите действие:", reply_markup=main_keyboard)
        await state.clear()
        return

    artikul = message.text
    logger.info(f"Запрос информации о товаре: {artikul}")
    await message.answer(f"Запрашиваем данные для артикула: {artikul}")

    async with aiohttp.ClientSession() as session:
        url = f"{API_URL}/products"
        logger.info(f"Отправка POST запроса к: {url}")
        
        try:
            async with session.post(url, headers=HEADERS, json={"artikul": artikul}) as response:
                logger.info(f"Получен ответ со статусом: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Получены данные о товаре: {data}")
                    
                    product_info = (
                        f"📦 Товар: {data.get('name')}\n"
                        f"📎 Артикул: {data.get('artikul')}\n"
                        f"💰 Цена: {data.get('price')} ₽\n"
                        f"⭐️ Рейтинг: {data.get('rating')}\n"
                        f"📊 Количество: {data.get('total_quantity')} шт.\n"
                        f"🔗 Ссылка: https://www.wildberries.ru/catalog/{data.get('artikul')}/detail.aspx"
                    )

                    link = f"https://www.wildberries.ru/catalog/{data.get('artikul')}/detail.aspx"
                    builder = InlineKeyboardBuilder()
                    builder.add(InlineKeyboardButton(
                        text="Перейти на Wildberries",
                        url=link
                    ))

                    await message.answer(product_info, reply_markup=builder.as_markup())
                elif response.status == 404:
                    await message.answer("❌ Товар не найден. Проверьте артикул и попробуйте снова.")
                else:
                    logger.error(f"Ошибка API: {response.status}")
                    await message.answer("Не удалось получить данные. Попробуйте еще раз.")
        except Exception as e:
            logger.error(f"Ошибка при запросе товара: {e}")
            await message.answer("Произошла ошибка при получении данных. Попробуйте позже.")

    await state.clear()
    await message.answer("Выберите действие:", reply_markup=main_keyboard)

# Функция для отправки уведомления об изменении цены
async def send_price_notification(artikul: str, old_price: float, new_price: float, name: str):
    logger.info(f"Отправка уведомлений об изменении цены для товара {artikul}")
    
    async with aiohttp.ClientSession() as session:
        # Получаем список подписчиков
        url = f"{API_URL}/subscriptions/{artikul}/users"
        logger.info(f"Запрос подписчиков: {url}")
        
        try:
            async with session.get(url, headers=HEADERS) as response:
                if response.status != 200:
                    logger.error(f"Не удалось получить список подписчиков для {artikul}: {response.status}")
                    return
                
                subscribers = await response.json()
                logger.info(f"Получено {len(subscribers)} подписчиков")
                
                if not subscribers:
                    logger.info(f"Нет активных подписчиков для товара {artikul}")
                    return
                
                price_diff = new_price - old_price
                price_change = "увеличилась" if price_diff > 0 else "уменьшилась"
                percent_change = abs(price_diff / old_price * 100)

                message = (
                    f"🔔 Изменение цены!\n\n"
                    f"📦 {name}\n"
                    f"📎 Артикул: {artikul}\n"
                    f"💰 Старая цена: {old_price:.2f} ₽\n"
                    f"💰 Новая цена: {new_price:.2f} ₽\n"
                    f"📊 Цена {price_change} на {abs(price_diff):.2f} ₽ ({percent_change:.1f}%)\n\n"
                    f"🔗 https://www.wildberries.ru/catalog/{artikul}/detail.aspx"
                )

                # Отправляем уведомление каждому подписчику
                for subscriber in subscribers:
                    try:
                        chat_id = subscriber["chat_id"]
                        logger.info(f"Отправка уведомления пользователю {chat_id}")
                        await bot.send_message(chat_id=chat_id, text=message)
                        logger.info(f"Уведомление успешно отправлено пользователю {chat_id}")
                    except Exception as e:
                        logger.error(f"Ошибка отправки уведомления пользователю {subscriber['chat_id']}: {e}")
        except Exception as e:
            logger.error(f"Ошибка при обработке уведомлений: {e}")

# Обработка ввода артикула для подписки
@dp.message(Form.waiting_for_subscription_artikul)
async def process_subscription_artikul(message: types.Message, state: FSMContext):
    if message.text == "Вернуться обратно":
        await message.answer("Выберите действие:", reply_markup=main_keyboard)
        await state.clear()
        return

    artikul = message.text
    await state.update_data(artikul=artikul)
    
    # Проверяем существование товара
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/products", headers=HEADERS, json={"artikul": artikul}) as response:
            if response.status == 404:
                await message.answer("❌ Товар не найден. Проверьте артикул и попробуйте снова.")
                await state.clear()
                await message.answer("Выберите действие:", reply_markup=main_keyboard)
                return
            elif response.status != 200:
                await message.answer("Произошла ошибка. Попробуйте позже.")
                await state.clear()
                await message.answer("Выберите действие:", reply_markup=main_keyboard)
                return
            
            data = await response.json()
            await message.answer(
                f"Товар найден:\n"
                f"📦 {data.get('name')}\n\n"
                f"Выберите частоту обновления данных:",
                reply_markup=frequency_keyboard
            )
            await state.set_state(Form.waiting_for_frequency)

# Обработка выбора частоты обновлений
@dp.message(Form.waiting_for_frequency)
async def process_frequency(message: types.Message, state: FSMContext):
    if message.text == "Вернуться обратно":
        await message.answer("Выберите действие:", reply_markup=main_keyboard)
        await state.clear()
        return

    # Преобразование текста в минуты
    frequency_map = {
        "1 минута": 1,
        "30 минут": 30,
        "1 час": 60,
        "3 часа": 180,
        "6 часов": 360,
        "12 часов": 720,
        "24 часа": 1440
    }

    if message.text not in frequency_map:
        await message.answer("Пожалуйста, выберите частоту из предложенных вариантов.")
        return

    frequency = frequency_map[message.text]
    data = await state.get_data()
    artikul = data.get("artikul")
    chat_id = str(message.chat.id)

    # Создаем подписку
    async with aiohttp.ClientSession() as session:
        # Создаем подписку для пользователя
        async with session.post(
            f"{API_URL}/subscriptions",
            headers=HEADERS,
            json={
                "artikul": artikul,
                "chat_id": chat_id,
                "frequency_minutes": frequency
            }
        ) as response:
            if response.status != 200:
                await message.answer("Не удалось создать подписку. Попробуйте позже.")
                await state.clear()
                await message.answer("Выберите действие:", reply_markup=main_keyboard)
                return

            await message.answer(
                f"✅ Подписка успешно создана!\n"
                f"📦 Артикул: {artikul}\n"
                f"⏰ Частота обновления: {message.text}\n\n"
                f"Вы будете получать уведомления об изменении цены и наличия товара."
            )

    await state.clear()
    await message.answer("Выберите действие:", reply_markup=main_keyboard)

# Команда для отмены подписки
@dp.message(Command("unsubscribe"))
async def unsubscribe_command(message: types.Message):
    async with aiohttp.ClientSession() as session:
        # Получаем список подписок пользователя
        chat_id = str(message.chat.id)
        async with session.get(f"{API_URL}/subscriptions/user/{chat_id}", headers=HEADERS) as response:
            if response.status != 200:
                await message.answer("Не удалось получить список подписок. Попробуйте позже.")
                return
            
            subscriptions = await response.json()
            if not subscriptions:
                await message.answer("У вас нет активных подписок.")
                return

            # Создаем клавиатуру с артикулами для отмены подписки
            keyboard = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text=f"Отписаться от {sub['artikul']}")] for sub in subscriptions
                ] + [[KeyboardButton(text="Вернуться обратно")]],
                resize_keyboard=True
            )
            
            await message.answer("Выберите подписку для отмены:", reply_markup=keyboard)
            await state.set_state(Form.waiting_for_unsubscribe)

# Обработка выбора подписки для отмены
@dp.message(Form.waiting_for_unsubscribe)
async def process_unsubscribe(message: types.Message, state: FSMContext):
    if message.text == "Вернуться обратно":
        await message.answer("Выберите действие:", reply_markup=main_keyboard)
        await state.clear()
        return

    # Извлекаем артикул из текста кнопки
    if not message.text.startswith("Отписаться от "):
        await message.answer("Пожалуйста, выберите подписку из списка.")
        return

    artikul = message.text.replace("Отписаться от ", "")
    chat_id = str(message.chat.id)

    async with aiohttp.ClientSession() as session:
        async with session.delete(
            f"{API_URL}/subscriptions/{artikul}/users/{chat_id}",
            headers=HEADERS
        ) as response:
            if response.status == 200:
                await message.answer(
                    f"✅ Вы успешно отписались от уведомлений о товаре с артикулом {artikul}.",
                    reply_markup=main_keyboard
                )
            else:
                await message.answer(
                    "Не удалось отменить подписку. Попробуйте позже.",
                    reply_markup=main_keyboard
                )

    await state.clear()

async def main():
    # Запускаем бота и FastAPI сервер
    import asyncio
    from hypercorn.asyncio import serve
    from hypercorn.config import Config

    config = Config()
    config.bind = ["0.0.0.0:8889"]
    
    await asyncio.gather(
        serve(app, config),
        dp.start_polling(bot, skip_updates=True)
    )

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())

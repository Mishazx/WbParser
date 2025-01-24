import aiohttp
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton

from config import API_URL, HEADERS, logger
from keyboards import main_keyboard, frequency_keyboard, back_to_menu_keyboard

class Form(StatesGroup):
    waiting_for_artikul = State()
    waiting_for_subscription_artikul = State()
    waiting_for_frequency = State()
    waiting_for_unsubscribe = State()

async def show_main_menu(message: types.Message, text: str = "Выберите действие:"):
    """Показывает главное меню с заданным текстом"""
    await message.answer(text, reply_markup=main_keyboard)

async def menu_command(message: types.Message):
    """Показывает главное меню"""
    await show_main_menu(message, "📱 Главное меню:")

async def send_welcome(message: types.Message):
    """Начало работы с ботом"""
    await show_main_menu(message, "👋 Добро пожаловать! Выберите действие:")

async def help_command(message: types.Message):
    """Показывает справку по командам"""
    help_text = """
🤖 Доступные команды:

/start - Начать работу с ботом
/menu - Показать главное меню
/help - Показать это сообщение
/unsubscribe - Отменить подписку на товар

📱 Кнопки меню:
• 📦 Получить информацию о товаре - Узнать текущую цену и наличие
• 🔔 Подписаться на товар - Получать уведомления об изменениях
• 📋 Мои подписки - Просмотр и управление подписками
• ❓ Помощь - Показать это сообщение

ℹ️ Для возврата в главное меню используйте кнопку "↩️ Вернуться в меню"
"""
    await message.answer(help_text, reply_markup=main_keyboard)

async def process_buttons(message: types.Message, state: FSMContext):
    """Обработка нажатий основных кнопок меню"""
    logger.info(f"Обработка нажатия кнопки: {message.text}")
    
    if message.text == "📦 Получить информацию о товаре":
        await message.answer("Введите артикул товара:", reply_markup=back_to_menu_keyboard)
        await state.set_state(Form.waiting_for_artikul)
    elif message.text == "🔔 Подписаться на товар":
        await message.answer("Введите артикул товара для подписки:", reply_markup=back_to_menu_keyboard)
        await state.set_state(Form.waiting_for_subscription_artikul)
    elif message.text == "📋 Мои подписки":
        await process_my_subscriptions(message)

async def process_my_subscriptions(message: types.Message):
    """Обработка запроса списка подписок"""
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
                    await show_main_menu(message)
                    return
                
                subscriptions = await response.json()
                logger.info(f"Получены подписки: {subscriptions}")
                
                if not subscriptions:
                    await message.answer("У вас нет активных подписок.")
                    await show_main_menu(message)
                    return

                subscription_info = []
                for sub in subscriptions:
                    artikul = sub["artikul"]
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
                
                await show_main_menu(message)
        except Exception as e:
            logger.error(f"Ошибка при запросе подписок: {e}")
            await message.answer("Произошла ошибка при получении подписок. Попробуйте позже.")
            await show_main_menu(message)

async def return_to_menu(message: types.Message, state: FSMContext):
    """Возврат в главное меню из любого состояния"""
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
    await show_main_menu(message)

async def process_artikul(message: types.Message, state: FSMContext):
    """Обработка ввода артикула товара"""
    if message.text == "↩️ Вернуться в меню":
        await return_to_menu(message, state)
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

    await return_to_menu(message, state)

async def process_subscription_artikul(message: types.Message, state: FSMContext):
    """Обработка ввода артикула для подписки"""
    if message.text == "↩️ Вернуться в меню":
        await return_to_menu(message, state)
        return

    artikul = message.text
    await state.update_data(artikul=artikul)
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/products", headers=HEADERS, json={"artikul": artikul}) as response:
            if response.status == 404:
                await message.answer("❌ Товар не найден. Проверьте артикул и попробуйте снова.")
                await state.clear()
                await show_main_menu(message)
                return
            elif response.status != 200:
                await message.answer("Произошла ошибка. Попробуйте позже.")
                await state.clear()
                await show_main_menu(message)
                return
            
            data = await response.json()
            await message.answer(
                f"Товар найден:\n"
                f"📦 {data.get('name')}\n\n"
                f"Выберите частоту обновления данных:",
                reply_markup=frequency_keyboard
            )
            await state.set_state(Form.waiting_for_frequency)

async def process_frequency(message: types.Message, state: FSMContext):
    """Обработка выбора частоты обновлений"""
    if message.text == "↩️ Вернуться в меню":
        await return_to_menu(message, state)
        return

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

    async with aiohttp.ClientSession() as session:
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
                await show_main_menu(message)
                return

            await message.answer(
                f"✅ Подписка успешно создана!\n"
                f"📦 Артикул: {artikul}\n"
                f"⏰ Частота обновления: {message.text}\n\n"
                f"Вы будете получать уведомления об изменении цены и наличия товара."
            )

    await state.clear()
    await show_main_menu(message)

async def unsubscribe_command(message: types.Message, state: FSMContext):
    """Обработка команды отмены подписки"""
    async with aiohttp.ClientSession() as session:
        chat_id = str(message.chat.id)
        async with session.get(f"{API_URL}/subscriptions/user/{chat_id}", headers=HEADERS) as response:
            if response.status != 200:
                await message.answer("Не удалось получить список подписок. Попробуйте позже.")
                await show_main_menu(message)
                return
            
            subscriptions = await response.json()
            if not subscriptions:
                await message.answer("У вас нет активных подписок.")
                await show_main_menu(message)
                return

            keyboard = types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text=f"Отписаться от {sub['artikul']}")] for sub in subscriptions
                ] + [[types.KeyboardButton(text="↩️ Вернуться в меню")]],
                resize_keyboard=True
            )
            
            await message.answer("Выберите подписку для отмены:", reply_markup=keyboard)
            await state.set_state(Form.waiting_for_unsubscribe)

async def process_unsubscribe(message: types.Message, state: FSMContext):
    """Обработка выбора подписки для отмены"""
    if message.text == "↩️ Вернуться в меню":
        await return_to_menu(message, state)
        return

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
                await message.answer(f"✅ Вы успешно отписались от уведомлений о товаре с артикулом {artikul}.")
            else:
                await message.answer("Не удалось отменить подписку. Попробуйте позже.")

    await state.clear()
    await show_main_menu(message) 
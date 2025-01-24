import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from fastapi import FastAPI
from hypercorn.asyncio import serve
from hypercorn.config import Config

from config import BOT_API_TOKEN, logger
from handlers import (
    send_welcome, menu_command, help_command, process_buttons,
    process_artikul, process_subscription_artikul, process_frequency,
    unsubscribe_command, process_unsubscribe, return_to_menu, Form
)
from router import router, set_bot

# Инициализация бота и FastAPI
bot = Bot(token=BOT_API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
app = FastAPI(
    title="Telegram Bot API",
    description="""
    API для отправки уведомлений через Telegram бота.
    
    ## Функциональность
    
    * Отправка уведомлений об изменении цены товара
    * Отправка уведомлений об изменении количества товара
    * Управление подписками пользователей
    
    ## Авторизация
    
    Все запросы должны содержать заголовок авторизации:
    ```
    Authorization: Bearer your-api-token
    ```
    """,
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Установка экземпляра бота для маршрутов
set_bot(bot)

# Регистрация маршрутов API
app.include_router(router)

# Регистрация обработчиков команд
dp.message.register(send_welcome, Command("start"))
dp.message.register(menu_command, Command("menu"))
dp.message.register(help_command, Command("help"))
dp.message.register(help_command, lambda message: message.text == "❓ Помощь")
dp.message.register(unsubscribe_command, Command("unsubscribe"))

# Регистрация обработчиков кнопок и состояний
dp.message.register(process_buttons, lambda message: message.text in [
    "📦 Получить информацию о товаре",
    "🔔 Подписаться на товар",
    "📋 Мои подписки"
])
dp.message.register(return_to_menu, lambda message: message.text == "↩️ Вернуться в меню")
dp.message.register(process_artikul, Form.waiting_for_artikul)
dp.message.register(process_subscription_artikul, Form.waiting_for_subscription_artikul)
dp.message.register(process_frequency, Form.waiting_for_frequency)
dp.message.register(process_unsubscribe, Form.waiting_for_unsubscribe)

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске приложения"""
    logger.info("Bot API starting up...")
    try:
        bot_info = await bot.get_me()
        logger.info(f"Bot connected successfully: @{bot_info.username}")
    except Exception as e:
        logger.error(f"Failed to initialize bot: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка ресурсов при остановке приложения"""
    logger.info("Bot API shutting down...")
    try:
        session = await bot.get_session()
        await session.close()
        logger.info("Bot session closed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

async def main():
    """Основная функция запуска приложения"""
    config = Config()
    config.bind = ["0.0.0.0:8889"]
    
    logger.info("Starting bot and FastAPI server...")
    try:
        await asyncio.gather(
            serve(app, config),
            dp.start_polling(bot, skip_updates=True)
        )
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    finally:
        logger.info("Application shutdown complete")

if __name__ == '__main__':
    asyncio.run(main())

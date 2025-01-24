from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Главное меню
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📦 Получить информацию о товаре")],
        [KeyboardButton(text="🔔 Подписаться на товар")],
        [
            KeyboardButton(text="📋 Мои подписки"),
            KeyboardButton(text="❓ Помощь")
        ]
    ],
    resize_keyboard=True,
    is_persistent=True
)

# Клавиатура выбора частоты обновлений
frequency_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="1 минута")],
        [KeyboardButton(text="30 минут")],
        [KeyboardButton(text="1 час")],
        [KeyboardButton(text="3 часа")],
        [KeyboardButton(text="6 часов")],
        [KeyboardButton(text="12 часов")],
        [KeyboardButton(text="24 часа")],
        [KeyboardButton(text="↩️ Вернуться в меню")]
    ],
    resize_keyboard=True
)

# Клавиатура возврата в меню
back_to_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="↩️ Вернуться в меню")]],
    resize_keyboard=True
) 
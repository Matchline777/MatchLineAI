from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🔴 LIVE матчи"),
            KeyboardButton(text="🔍 Анализ"),
        ],
        [
            KeyboardButton(text="⭐ Сигналы"),
            KeyboardButton(text="📈 Статистика"),
        ],
        [
            KeyboardButton(text="⚙️ Настройки"),
        ],
    ],
    resize_keyboard=True,
)
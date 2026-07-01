from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def match_keyboard(fixture_id):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Статистика",
                    callback_data=f"stats_{fixture_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⚽ События",
                    callback_data=f"events_{fixture_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🤖 AI Анализ",
                    callback_data=f"ai_{fixture_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅ Назад",
                    callback_data="back_live"
                )
            ]
        ]
    )

    return keyboard
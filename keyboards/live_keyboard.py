from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def live_keyboard(matches):

    buttons = []

    for match in matches[:10]:

        fixture_id = match["fixture"]["id"]

        home = match["teams"]["home"]["name"]
        away = match["teams"]["away"]["name"]

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"⚽ {home} — {away}",
                    callback_data=f"match_{fixture_id}"
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)
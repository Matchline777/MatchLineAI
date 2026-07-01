from aiogram import Router
from aiogram.types import CallbackQuery

from services.football_api import get_statistics

router = Router()


@router.callback_query(lambda c: c.data.startswith("stats_"))
async def show_statistics(callback: CallbackQuery):

    fixture_id = callback.data.split("_")[1]

    data = get_statistics(fixture_id)

    if not data:
        await callback.message.answer("❌ Не удалось получить статистику.")
        await callback.answer()
        return

    statistics = data["response"]

    if len(statistics) == 0:
        await callback.message.answer("Статистика пока недоступна.")
        await callback.answer()
        return

    home = statistics[0]
    away = statistics[1]

    text = (
        f"📊 Статистика матча\n\n"
        f"🏠 {home['team']['name']}\n"
        f"🛫 {away['team']['name']}\n\n"
    )

    for i in range(len(home["statistics"])):

        stat_name = home["statistics"][i]["type"]

        home_value = home["statistics"][i]["value"]
        away_value = away["statistics"][i]["value"]

        if home_value is None:
            home_value = "-"

        if away_value is None:
            away_value = "-"

        text += f"{stat_name}\n{home_value} : {away_value}\n\n"

    await callback.message.answer(text)

    await callback.answer()
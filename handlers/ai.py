from aiogram import Router
from aiogram.types import CallbackQuery

from services.football_api import get_statistics

router = Router()


def to_number(value):

    if value is None:
        return 0

    if isinstance(value, int):
        return value

    value = str(value)

    value = value.replace("%", "")

    try:
        return float(value)
    except:
        return 0


@router.callback_query(lambda c: c.data.startswith("ai_"))
async def ai_analysis(callback: CallbackQuery):

    fixture_id = callback.data.split("_")[1]

    data = get_statistics(fixture_id)

    if not data:
        await callback.message.answer("Ошибка получения статистики.")
        await callback.answer()
        return

    if len(data["response"]) == 0:
        await callback.message.answer("Статистика пока недоступна.")
        await callback.answer()
        return

    home = data["response"][0]
    away = data["response"][1]

    stats = {}

    for i in range(len(home["statistics"])):

        stat = home["statistics"][i]["type"]

        stats[stat] = (
            home["statistics"][i]["value"],
            away["statistics"][i]["value"]
        )

    home_shots = to_number(stats.get("Total Shots", (0, 0))[0])
    away_shots = to_number(stats.get("Total Shots", (0, 0))[1])

    home_on = to_number(stats.get("Shots on Goal", (0, 0))[0])
    away_on = to_number(stats.get("Shots on Goal", (0, 0))[1])

    home_pos = to_number(stats.get("Ball Possession", (0, 0))[0])
    away_pos = to_number(stats.get("Ball Possession", (0, 0))[1])

    home_corner = to_number(stats.get("Corner Kicks", (0, 0))[0])
    away_corner = to_number(stats.get("Corner Kicks", (0, 0))[1])

    pressure_home = (
        home_shots * 2
        + home_on * 5
        + home_corner * 3
        + home_pos * 0.3
    )

    pressure_away = (
        away_shots * 2
        + away_on * 5
        + away_corner * 3
        + away_pos * 0.3
    )

    text = (
        "🤖 MATCHLINE AI\n\n"

        f"🏠 {home['team']['name']}\n"
        f"✈ {away['team']['name']}\n\n"

        f"🔥 Давление хозяев: {round(pressure_home,1)}\n"
        f"🔥 Давление гостей: {round(pressure_away,1)}\n\n"
    )

    if pressure_home > pressure_away:

        text += (
            "📈 Преимущество у хозяев.\n"
            "Вероятность следующего опасного момента выше."
        )

    elif pressure_away > pressure_home:

        text += (
            "📈 Преимущество у гостей.\n"
            "Они выглядят опаснее."
        )

    else:

        text += "Матч проходит примерно на равных."

    await callback.message.answer(text)

    await callback.answer()
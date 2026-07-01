from aiogram import Router
from aiogram.types import Message, CallbackQuery

from services.football_api import get_live_matches, get_match
from keyboards.live_keyboard import live_keyboard
from keyboards.match_keyboard import match_keyboard

router = Router()


@router.message(lambda message: message.text == "🔴 LIVE матчи")
async def live_matches(message: Message):

    await message.answer("🔍 Загружаю матчи...")

    data = get_live_matches()

    if not data:
        await message.answer("❌ Ошибка получения данных")
        return

    matches = data["response"]

    if len(matches) == 0:
        await message.answer("Сегодня матчей нет.")
        return

    text = "⚽ Матчи сегодня\n\n"

    for match in matches[:20]:

        home = match["teams"]["home"]["name"]
        away = match["teams"]["away"]["name"]

        league = match["league"]["name"]

        goals_home = match["goals"]["home"]
        goals_away = match["goals"]["away"]

        status = match["fixture"]["status"]["short"]

        if goals_home is None:
            goals_home = "-"

        if goals_away is None:
            goals_away = "-"

        text += (
            f"🏆 {league}\n"
            f"{home} {goals_home}:{goals_away} {away}\n"
            f"Статус: {status}\n\n"
        )

    await message.answer(
        text,
        reply_markup=live_keyboard(matches)
    )


@router.callback_query(lambda c: c.data.startswith("match_"))
async def open_match(callback: CallbackQuery):

    fixture_id = callback.data.split("_")[1]

    data = get_match(fixture_id)

    if not data:
        await callback.message.answer("❌ Ошибка получения данных.")
        await callback.answer()
        return

    match = data["response"][0]

    league = match["league"]["name"]
    country = match["league"]["country"]

    home = match["teams"]["home"]["name"]
    away = match["teams"]["away"]["name"]

    goals_home = match["goals"]["home"]
    goals_away = match["goals"]["away"]

    status = match["fixture"]["status"]["long"]

    stadium = match["fixture"]["venue"]["name"]
    date = match["fixture"]["date"][:10]

    if goals_home is None:
        goals_home = "-"

    if goals_away is None:
        goals_away = "-"

    if stadium is None:
        stadium = "Не указан"

    text = (
        f"🏆 {league}\n\n"
        f"⚽ {home} {goals_home}:{goals_away} {away}\n\n"
        f"📌 Статус: {status}\n"
        f"📅 Дата: {date}\n"
        f"🌍 Страна: {country}\n"
        f"🏟 Стадион: {stadium}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👇 Выберите действие"
    )

    await callback.message.answer(
        text,
        reply_markup=match_keyboard(fixture_id)
    )

    await callback.answer()
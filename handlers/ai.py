from aiogram import Router
from aiogram.types import CallbackQuery

from analysis.engine import analyze, recommend_match
from services.football_api import get_statistics

router = Router()


def statistics_to_dict(team_statistics):
    stats = {}

    for item in team_statistics:
        stats[item["type"]] = item["value"]

    return stats


@router.callback_query(lambda c: c.data.startswith("ai_"))
async def ai_analysis(callback: CallbackQuery):
    fixture_id = callback.data.split("_")[1]

    data = get_statistics(fixture_id)

    if not data:
        await callback.message.answer("Ошибка получения статистики.")
        await callback.answer()
        return

    if len(data["response"]) < 2:
        await callback.message.answer("Статистика пока недоступна.")
        await callback.answer()
        return

    home = data["response"][0]
    away = data["response"][1]

    home_stats = statistics_to_dict(home["statistics"])
    away_stats = statistics_to_dict(away["statistics"])

    home_result = analyze(home_stats, away_stats, side="home")
    away_result = analyze(away_stats, home_stats, side="away")
    recommendation = recommend_match(home_result, away_result)

    text = (
        "🤖 MATCHLINE AI\n\n"
        f"🏠 Home: {home['team']['name']}\n"
        f"✈️ Away: {away['team']['name']}\n\n"
        "🔥 Pressure:\n"
        f"Home: {home_result.pressure}\n"
        f"Away: {away_result.pressure}\n\n"
        "⚡ Momentum:\n"
        f"Home: {home_result.momentum}\n"
        f"Away: {away_result.momentum}\n\n"
        "🎯 Goal probability:\n"
        f"Home: {home_result.goal_probability}%\n"
        f"Away: {away_result.goal_probability}%\n\n"
        "⭐ AI Score:\n"
        f"Home: {home_result.final_score}\n"
        f"Away: {away_result.final_score}\n\n"
        "🎯 Следующий гол:\n"
        f"Home: {home_result.next_goal_probability}%\n"
        f"Away: {away_result.next_goal_probability}%\n\n"
        "📈 ТБ 2.5:\n"
        f"Home: {home_result.over25_probability}%\n"
        f"Away: {away_result.over25_probability}%\n\n"
        "📈 ТБ 3.5:\n"
        f"Home: {home_result.over35_probability}%\n"
        f"Away: {away_result.over35_probability}%\n\n"
        "💎 Сила сигнала:\n"
        f"Home: {home_result.bet_score}\n"
        f"Away: {away_result.bet_score}\n\n"
        "📌 Рейтинг:\n"
        f"Home: {home_result.bet_rating}\n"
        f"Away: {away_result.bet_rating}\n\n"
        "Recommendation:\n"
        f"{recommendation}"
    )

    await callback.message.answer(text)
    await callback.answer()

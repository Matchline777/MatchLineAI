from aiogram import Router


router = Router()


def format_signal(
    match_name,
    next_goal_probability,
    over25_probability,
    bet_score,
    bet_rating,
):
    text = (
        "🚨 MATCHLINE SIGNAL\n\n"
        f"⚽ Матч: {match_name}\n\n"
        f"🎯 Следующий гол: {next_goal_probability}%\n"
        f"📈 ТБ 2.5: {over25_probability}%\n"
        f"💎 Сила сигнала: {bet_score}\n"
        f"📌 Рейтинг: {bet_rating}"
    )

    if bet_score >= 80:
        signal_status = "🔥 Сильный сигнал"
    elif bet_score >= 70:
        signal_status = "⚠️ Средний сигнал"
    else:
        signal_status = "⏳ Ждем усиления"

    return f"{text}\n\n{signal_status}"

from aiogram import Router
from aiogram.types import CallbackQuery

from analysis.engine import analyze, recommend_match
from analysis.team_form import TeamForm
from services.football_api import (
    get_head_to_head,
    get_match,
    get_odds,
    get_statistics,
    get_team_last_matches,
)

router = Router()


def statistics_to_dict(team_statistics):
    stats = {}

    for item in team_statistics:
        stats[item["type"]] = item["value"]

    return stats


def stat_number(stats, *keys, default=0):
    for key in keys:
        value = stats.get(key)
        if value is None:
            continue

        if isinstance(value, (int, float)):
            return value

        try:
            return float(str(value).replace("%", "").strip())
        except ValueError:
            continue

    return default


def build_match_context(match, home_stats, away_stats):
    fixture = match.get("fixture", {}) if match else {}
    status = fixture.get("status", {}) if fixture else {}
    goals = match.get("goals", {}) if match else {}

    minute = status.get("elapsed") or 0
    home_score = goals.get("home")
    away_score = goals.get("away")

    return {
        "minute": int(minute or 0),
        "home_score": int(home_score or 0),
        "away_score": int(away_score or 0),
        "home_red_cards": int(stat_number(home_stats, "Red Cards", "red_cards", default=0)),
        "away_red_cards": int(stat_number(away_stats, "Red Cards", "red_cards", default=0)),
        "home_yellow_cards": int(stat_number(home_stats, "Yellow Cards", "yellow_cards", default=0)),
        "away_yellow_cards": int(stat_number(away_stats, "Yellow Cards", "yellow_cards", default=0)),
        "home_previous_pressure": stat_number(home_stats, "Pressure", "pressure", default=0),
        "away_previous_pressure": stat_number(away_stats, "Pressure", "pressure", default=0),
        "home_previous_shots": int(stat_number(home_stats, "Total Shots", "shots", default=0)),
        "away_previous_shots": int(stat_number(away_stats, "Total Shots", "shots", default=0)),
    }


def calculate_team_form(team_id, last=5):
    data = get_team_last_matches(team_id, last)

    if not data or not data.get("response"):
        return TeamForm(0, 0, 0, 0, 0)

    wins = 0
    draws = 0
    losses = 0
    goals_scored = 0
    goals_conceded = 0

    for match in data["response"]:
        teams = match.get("teams", {})
        goals = match.get("goals", {})
        home_team = teams.get("home", {})
        away_team = teams.get("away", {})
        home_goals = goals.get("home") or 0
        away_goals = goals.get("away") or 0

        if home_team.get("id") == team_id:
            own_goals = home_goals
            opponent_goals = away_goals
        elif away_team.get("id") == team_id:
            own_goals = away_goals
            opponent_goals = home_goals
        else:
            continue

        goals_scored += own_goals
        goals_conceded += opponent_goals

        if own_goals > opponent_goals:
            wins += 1
        elif own_goals == opponent_goals:
            draws += 1
        else:
            losses += 1

    return TeamForm(wins, draws, losses, goals_scored, goals_conceded)


def extract_match_odds(fixture_id):
    data = get_odds(fixture_id)

    if not data or not data.get("response"):
        return 2.0, 2.0

    for item in data["response"]:
        for bookmaker in item.get("bookmakers", []):
            for bet in bookmaker.get("bets", []):
                if bet.get("name") not in ("Match Winner", "Winner"):
                    continue

                home_odds = 2.0
                away_odds = 2.0

                for value in bet.get("values", []):
                    label = value.get("value")
                    odd = value.get("odd")

                    try:
                        odd = float(odd)
                    except (TypeError, ValueError):
                        continue

                    if label == "Home":
                        home_odds = odd
                    elif label == "Away":
                        away_odds = odd

                return home_odds, away_odds

    return 2.0, 2.0


def calculate_h2h_scores(team1_id, team2_id, last=5):
    data = get_head_to_head(team1_id, team2_id, last)

    if not data or not data.get("response"):
        return 50, 50

    home_points = 0
    away_points = 0
    matches_count = 0

    for match in data["response"]:
        teams = match.get("teams", {})
        goals = match.get("goals", {})
        home_team = teams.get("home", {})
        away_team = teams.get("away", {})
        fixture_home_goals = goals.get("home") or 0
        fixture_away_goals = goals.get("away") or 0

        if home_team.get("id") == team1_id:
            team1_goals = fixture_home_goals
            team2_goals = fixture_away_goals
        elif away_team.get("id") == team1_id:
            team1_goals = fixture_away_goals
            team2_goals = fixture_home_goals
        else:
            continue

        matches_count += 1

        if team1_goals > team2_goals:
            home_points += 3
        elif team1_goals < team2_goals:
            away_points += 3
        else:
            home_points += 1
            away_points += 1

    if matches_count == 0:
        return 50, 50

    max_points = matches_count * 3
    home_h2h_score = round((home_points / max_points) * 100, 1)
    away_h2h_score = round((away_points / max_points) * 100, 1)

    return home_h2h_score, away_h2h_score


@router.callback_query(lambda c: c.data.startswith("ai_"))
async def ai_analysis(callback: CallbackQuery):
    fixture_id = callback.data.split("_")[1]

    data = get_statistics(fixture_id)
    match_data = get_match(fixture_id)

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
    match = {}

    if match_data and match_data.get("response"):
        match = match_data["response"][0]

    match_context = build_match_context(match, home_stats, away_stats)
    home_team_id = home["team"].get("id")
    away_team_id = away["team"].get("id")
    home_form = calculate_team_form(home_team_id) if home_team_id else TeamForm(0, 0, 0, 0, 0)
    away_form = calculate_team_form(away_team_id) if away_team_id else TeamForm(0, 0, 0, 0, 0)
    match_context["home_form_score"] = home_form.form_score()
    match_context["away_form_score"] = away_form.form_score()
    home_odds, away_odds = extract_match_odds(fixture_id)
    match_context["home_odds"] = home_odds
    match_context["away_odds"] = away_odds
    home_h2h_score = 50
    away_h2h_score = 50

    if home_team_id and away_team_id:
        home_h2h_score, away_h2h_score = calculate_h2h_scores(home_team_id, away_team_id)

    match_context["home_h2h_score"] = home_h2h_score
    match_context["away_h2h_score"] = away_h2h_score

    home_result = analyze(home_stats, away_stats, match_context=match_context, side="home")
    away_result = analyze(away_stats, home_stats, match_context=match_context, side="away")
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

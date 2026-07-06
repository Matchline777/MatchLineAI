import asyncio
import csv
import os
from datetime import datetime

from analysis.engine import analyze
from handlers.ai import build_match_context, stat_number, statistics_to_dict
from handlers.signals import format_signal
from services.football_api import get_live_matches, get_statistics


async def scan_live_matches(bot, chat_id):
    sent_signals = {}
    pending_signals = {}
    checked_fixtures = {}

    while True:
        try:
            data = get_live_matches()
            candidate_signals = []

            if data and data.get("response"):
                for match in data["response"][:5]:
                    fixture_id = match.get("fixture", {}).get("id")
                    home_team = match.get("teams", {}).get("home", {}).get("name")
                    away_team = match.get("teams", {}).get("away", {}).get("name")
                    now = asyncio.get_event_loop().time()

                    for sent_fixture_id, sent_at in list(sent_signals.items()):
                        if now - sent_at >= 20 * 60:
                            sent_signals.pop(sent_fixture_id, None)

                    if fixture_id in sent_signals and now - sent_signals[fixture_id] < 20 * 60:
                        continue

                    status = match.get("fixture", {}).get("status", {}).get("short", "")

                    if status not in ("1H", "HT", "2H", "ET"):
                        pending_signals.pop(fixture_id, None)
                        continue

                    minute = match.get("fixture", {}).get("status", {}).get("elapsed") or 0

                    if minute < 15:
                        pending_signals.pop(fixture_id, None)
                        continue

                    if 46 <= minute <= 54:
                        pending_signals.pop(fixture_id, None)
                        continue

                    home_goals = match.get("goals", {}).get("home") or 0
                    away_goals = match.get("goals", {}).get("away") or 0

                    if home_goals + away_goals >= 5:
                        pending_signals.pop(fixture_id, None)
                        print("SKIP HIGH SCORE:", fixture_id, home_goals, away_goals)
                        continue

                    if abs(home_goals - away_goals) >= 3:
                        pending_signals.pop(fixture_id, None)
                        continue

                    if minute > 92 and abs(home_goals - away_goals) >= 2:
                        pending_signals.pop(fixture_id, None)
                        print("SKIP LATE:", fixture_id, minute)
                        continue

                    now = asyncio.get_event_loop().time()

                    if (
                        fixture_id not in pending_signals
                        and fixture_id in checked_fixtures
                        and now - checked_fixtures[fixture_id] < 90
                    ):
                        continue

                    checked_fixtures[fixture_id] = now

                    league_name = match.get("league", {}).get("name", "")

                    if "Friendly" in league_name or "Friendlies" in league_name:
                        pending_signals.pop(fixture_id, None)
                        print("SKIP FRIENDLY:", fixture_id, league_name)
                        continue

                    statistics = get_statistics(fixture_id)

                    if not statistics or len(statistics.get("response", [])) < 2:
                        pending_signals.pop(fixture_id, None)
                        continue

                    home_stats = statistics_to_dict(statistics["response"][0]["statistics"])
                    away_stats = statistics_to_dict(statistics["response"][1]["statistics"])
                    total_shots = stat_number(home_stats, "Total Shots", "Shots total", default=0)
                    total_shots += stat_number(away_stats, "Total Shots", "Shots total", default=0)
                    shots_on_target = stat_number(home_stats, "Shots on Goal", "Shots on Target", default=0)
                    shots_on_target += stat_number(
                        away_stats,
                        "Shots on Goal",
                        "Shots on Target",
                        default=0,
                    )
                    corner_kicks = stat_number(home_stats, "Corner Kicks", "Corners", default=0)
                    corner_kicks += stat_number(away_stats, "Corner Kicks", "Corners", default=0)

                    if total_shots < 8 or shots_on_target < 3:
                        pending_signals.pop(fixture_id, None)
                        print(
                            "SKIP WEAK:",
                            fixture_id,
                            home_team,
                            away_team,
                            total_shots,
                            shots_on_target,
                            corner_kicks,
                        )
                        continue

                    if total_shots > 0 and shots_on_target / total_shots < 0.25:
                        pending_signals.pop(fixture_id, None)
                        print(
                            "SKIP EFFICIENCY:",
                            fixture_id,
                            home_team,
                            away_team,
                            shots_on_target,
                            total_shots,
                        )
                        continue

                    if corner_kicks < 5:
                        pending_signals.pop(fixture_id, None)
                        print(
                            "SKIP WEAK:",
                            fixture_id,
                            home_team,
                            away_team,
                            total_shots,
                            shots_on_target,
                            corner_kicks,
                        )
                        continue

                    home_possession = stat_number(home_stats, "Ball Possession", "Possession", default=50)
                    away_possession = stat_number(away_stats, "Ball Possession", "Possession", default=50)

                    if abs(home_possession - away_possession) < 10:
                        pending_signals.pop(fixture_id, None)
                        print("SKIP BALANCED:", fixture_id, home_team, away_team)
                        continue

                    home_dangerous = stat_number(home_stats, "Dangerous Attacks", "Dangerous attacks", default=0)
                    away_dangerous = stat_number(away_stats, "Dangerous Attacks", "Dangerous attacks", default=0)

                    if home_dangerous + away_dangerous < 35:
                        pending_signals.pop(fixture_id, None)
                        print(
                            "SKIP LOW DANGER:",
                            fixture_id,
                            home_team,
                            away_team,
                            home_dangerous,
                            away_dangerous,
                        )
                        continue

                    attacks = (
                        stat_number(home_stats, "Attacks", "Attacks", default=0)
                        + stat_number(away_stats, "Attacks", "Attacks", default=0)
                    )

                    if attacks < 80:
                        pending_signals.pop(fixture_id, None)
                        print(
                            "SKIP ATTACKS:",
                            fixture_id,
                            home_team,
                            away_team,
                            attacks,
                        )
                        continue

                    home_xg = stat_number(home_stats, "Expected Goals", "xG", default=0)
                    away_xg = stat_number(away_stats, "Expected Goals", "xG", default=0)
                    total_xg = home_xg + away_xg

                    if total_xg > 0 and total_xg < 1.20:
                        pending_signals.pop(fixture_id, None)
                        print(
                            "SKIP XG:",
                            fixture_id,
                            home_team,
                            away_team,
                            total_xg,
                        )
                        continue

                    yellow_cards = (
                        stat_number(home_stats, "Yellow Cards", default=0)
                        + stat_number(away_stats, "Yellow Cards", default=0)
                    )
                    red_cards = (
                        stat_number(home_stats, "Red Cards", default=0)
                        + stat_number(away_stats, "Red Cards", default=0)
                    )

                    if yellow_cards >= 8 or red_cards >= 2:
                        pending_signals.pop(fixture_id, None)
                        print(
                            "SKIP CARDS:",
                            fixture_id,
                            home_team,
                            away_team,
                            yellow_cards,
                            red_cards,
                        )
                        continue

                    shot_difference = abs(
                        stat_number(home_stats, "Total Shots", "Shots total", default=0)
                        - stat_number(away_stats, "Total Shots", "Shots total", default=0)
                    )

                    if shot_difference < 4:
                        pending_signals.pop(fixture_id, None)
                        print(
                            "SKIP SHOTS:",
                            fixture_id,
                            home_team,
                            away_team,
                            shot_difference,
                        )
                        continue

                    target_difference = abs(
                        stat_number(home_stats, "Shots on Goal", "Shots on Target", default=0)
                        - stat_number(away_stats, "Shots on Goal", "Shots on Target", default=0)
                    )

                    if target_difference < 2:
                        pending_signals.pop(fixture_id, None)
                        print(
                            "SKIP TARGET:",
                            fixture_id,
                            home_team,
                            away_team,
                            target_difference,
                        )
                        continue

                    corner_difference = abs(
                        stat_number(home_stats, "Corner Kicks", "Corners", default=0)
                        - stat_number(away_stats, "Corner Kicks", "Corners", default=0)
                    )

                    if corner_difference < 2:
                        pending_signals.pop(fixture_id, None)
                        print(
                            "SKIP CORNERS:",
                            fixture_id,
                            home_team,
                            away_team,
                            corner_difference,
                        )
                        continue

                    possession_difference = abs(
                        stat_number(home_stats, "Ball Possession", "Possession", default=50)
                        - stat_number(away_stats, "Ball Possession", "Possession", default=50)
                    )

                    if possession_difference < 15:
                        pending_signals.pop(fixture_id, None)
                        print(
                            "SKIP POSSESSION:",
                            fixture_id,
                            home_team,
                            away_team,
                            possession_difference,
                        )
                        continue

                    match_context = build_match_context(match, home_stats, away_stats)
                    home_result = analyze(home_stats, away_stats, match_context=match_context, side="home")
                    away_result = analyze(away_stats, home_stats, match_context=match_context, side="away")

                    next_goal_probability = max(
                        home_result.next_goal_probability,
                        away_result.next_goal_probability,
                    )
                    over25_probability = max(
                        home_result.over25_probability,
                        away_result.over25_probability,
                    )
                    bet_score = max(
                        home_result.bet_score,
                        away_result.bet_score,
                    )

                    if next_goal_probability < 60 or over25_probability < 55 or bet_score < 10:
                        pending_signals.pop(fixture_id, None)
                        print(
                            "SKIP LOW SCORE:",
                            fixture_id,
                            home_team,
                            away_team,
                            next_goal_probability,
                            over25_probability,
                            bet_score,
                        )
                        continue

                    signal_text = format_signal(
                        match_name=f"{home_team} - {away_team}",
                        next_goal_probability=next_goal_probability,
                        over25_probability=over25_probability,
                        bet_score=bet_score,
                        bet_rating=(
                            home_result.bet_rating
                            if home_result.bet_score >= away_result.bet_score
                            else away_result.bet_rating
                        ),
                    )

                    if fixture_id not in pending_signals:
                        pending_signals[fixture_id] = signal_text
                        print("PENDING SIGNAL:", fixture_id, home_team, away_team)
                        continue

                    late_bonus = 0

                    if minute >= 70:
                        late_bonus += 5

                    if minute >= 80:
                        late_bonus += 5

                    if minute >= 85:
                        late_bonus += 5

                    score_bonus = 0

                    if abs(home_goals - away_goals) == 1:
                        score_bonus += 8

                    elif home_goals == away_goals:
                        score_bonus += 5

                    ranking_score = (
                        bet_score * 0.35
                        + next_goal_probability * 0.25
                        + over25_probability * 0.15
                        + shots_on_target * 2.5
                        + corner_kicks * 1.0
                        + home_dangerous * 0.10
                        + away_dangerous * 0.10
                        + late_bonus
                        + score_bonus
                    )

                    candidate_signals.append(
                        {
                            "fixture_id": fixture_id,
                            "signal_text": signal_text,
                            "bet_score": bet_score,
                            "next_goal_probability": next_goal_probability,
                            "over25_probability": over25_probability,
                            "ranking_score": ranking_score,
                            "home_team": home_team,
                            "away_team": away_team,
                        }
                    )
                    print(
                        "CANDIDATE:",
                        fixture_id,
                        ranking_score,
                        bet_score,
                        next_goal_probability,
                        over25_probability,
                    )

                print(
                    "SCAN SUMMARY:",
                    "matches=", len(data.get("response", [])),
                    "candidates=", len(candidate_signals),
                )

                if not candidate_signals:
                    print(
                        "NO CANDIDATES THIS SCAN"
                    )

                if candidate_signals:
                    candidate_signals.sort(
                        key=lambda signal: signal["ranking_score"],
                        reverse=True,
                    )
                    best_signal = candidate_signals[0]
                    print(
                        "BEST SIGNAL:",
                        best_signal["fixture_id"],
                        best_signal["ranking_score"],
                        best_signal["bet_score"],
                        best_signal["next_goal_probability"],
                        best_signal["over25_probability"],
                    )

                    if best_signal["ranking_score"] < 45:
                        print(
                            "NO STRONG SIGNAL:",
                            best_signal["fixture_id"],
                            best_signal["ranking_score"],
                        )
                        continue

                    if chat_id is not None:
                        await bot.send_message(chat_id, best_signal["signal_text"])

                    os.makedirs("logs", exist_ok=True)
                    with open("logs/signals.csv", "a", newline="", encoding="utf-8") as signals_file:
                        writer = csv.writer(signals_file)
                        writer.writerow(
                            [
                                datetime.now().isoformat(),
                                best_signal["fixture_id"],
                                best_signal["home_team"],
                                best_signal["away_team"],
                                best_signal["ranking_score"],
                                best_signal["bet_score"],
                                best_signal["next_goal_probability"],
                                best_signal["over25_probability"],
                            ]
                        )

                    print(
                        "SENT SIGNAL:",
                        best_signal["fixture_id"],
                        best_signal["home_team"],
                        best_signal["away_team"],
                    )
                    pending_signals.pop(best_signal["fixture_id"], None)
                    sent_signals[best_signal["fixture_id"]] = asyncio.get_event_loop().time()

        except Exception as error:
            print("LIVE SCANNER ERROR:", error)

        await asyncio.sleep(120)

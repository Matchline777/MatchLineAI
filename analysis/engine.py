from dataclasses import asdict, dataclass

from analysis.attack_trend import AttackTrend
from analysis.corner_pressure import CornerPressure
from analysis.dangerous_attacks import DangerousAttacks
from analysis.fatigue import Fatigue
from analysis.foul_impact import FoulImpact
from analysis.goal_signal import GoalSignal
from analysis.match_context import MatchContext
from analysis.match_phase import MatchPhase
from analysis.match_tempo import MatchTempo
from analysis.next_goal_model import NextGoalModel
from analysis.over_model import OverModel
from analysis.red_card import RedCardImpact
from analysis.team_strength import TeamStrength
from analysis.yellow_card import YellowCardImpact
from analysis.bet_strength import BetStrength
from analysis.xg_model import ExpectedGoals


@dataclass(frozen=True)
class AnalysisInput:
    shots: float = 0.0
    shots_on_target: float = 0.0
    possession: float = 0.0
    corners: float = 0.0
    attacks: float = 0.0
    dangerous_attacks: float = 0.0
    red_cards: float = 0.0
    yellow_cards: float = 0.0
    minute: float = 0.0
    team_score: float = 0.0
    opponent_score: float = 0.0


@dataclass(frozen=True)
class AnalysisResult:
    pressure: float
    momentum: float
    goal_probability: float
    total_goals_probability: float
    home_goal_probability: float
    away_goal_probability: float
    attack_rating: float
    recommendation: str
    final_score: float
    next_goal_probability: float
    over25_probability: float
    over35_probability: float
    bet_score: float
    bet_rating: str
    bet_confidence: str

    def to_dict(self):
        return asdict(self)


def analyze(stats, opponent_stats=None, match_context=None, side="home"):
    team = _normalize(stats, match_context, side)
    opponent = _normalize(opponent_stats or {}, match_context, _opposite_side(side))
    context = MatchContext(
        minute=int(team.minute),
        home_score=int(team.team_score if side == "home" else team.opponent_score),
        away_score=int(team.opponent_score if side == "home" else team.team_score),
        home_red_cards=int(team.red_cards if side == "home" else opponent.red_cards),
        away_red_cards=int(opponent.red_cards if side == "home" else team.red_cards),
    )
    is_losing = context.is_losing(side)
    goal_difference = context.goal_difference(side)
    if is_losing:
        motivation_multiplier = 1.05
    else:
        motivation_multiplier = 1.00
    phase = MatchPhase(int(team.minute))

    components = _build_components(team)
    opponent_components = _build_components(opponent)

    pressure = _weighted_average(
        (
            (components["shooting"], 0.25),
            (components["attack_volume"], 0.22),
            (components["danger"], 0.18),
            (components["possession"], 0.12),
            (components["corners"], 0.10),
            (components["discipline"], 0.07),
            (components["match_state"], 0.06),
        )
    )
    attack_rating = _weighted_average(
        (
            (components["shooting"], 0.30),
            (components["danger"], 0.25),
            (components["attack_volume"], 0.20),
            (components["corners"], 0.12),
            (components["possession"], 0.08),
            (components["discipline"], 0.05),
        )
    )
    momentum = _weighted_average(
        (
            (pressure, 0.30),
            (attack_rating, 0.25),
            (components["shooting"], 0.15),
            (components["danger"], 0.12),
            (components["time"], 0.08),
            (components["match_state"], 0.06),
            (components["discipline"], 0.04),
        )
    )
    goal_probability = _goal_probability(
        pressure,
        momentum,
        attack_rating,
        components["time"],
        components["match_state"],
    )
    goal_probability = goal_probability * (phase.time_pressure() / 100)
    goal_probability = goal_probability * motivation_multiplier
    goal_probability = _clamp(goal_probability)
    red_card_bonus = RedCardImpact(
        int(team.red_cards),
        int(opponent.red_cards)
    ).impact_score()
    yellow_card_bonus = YellowCardImpact(
        int(team.yellow_cards),
        int(opponent.yellow_cards)
    ).impact_score()
    foul_bonus = FoulImpact(
        int(_first_value(stats, "Fouls", "fouls", default=0)),
        int(_first_value(opponent_stats or {}, "Fouls", "fouls", default=0)),
    ).impact_score()
    cards_multiplier = 1 + ((red_card_bonus + yellow_card_bonus + foul_bonus) / 1000)
    goal_probability = goal_probability * cards_multiplier
    goal_probability = _clamp(goal_probability)
    trend_bonus = AttackTrend(
        _context_number(
            match_context,
            f"{side}_previous_pressure",
            "previous_pressure",
            pressure,
        ),
        pressure,
    ).trend_bonus()
    trend_multiplier = 1 + (trend_bonus / 1000)
    goal_probability = goal_probability * trend_multiplier
    goal_probability = _clamp(goal_probability)
    fatigue_bonus = Fatigue(
        int(team.minute),
        team.possession,
        int(team.shots),
    ).fatigue_score()
    fatigue_multiplier = 1 + (fatigue_bonus / 1000)
    goal_probability = goal_probability * fatigue_multiplier
    goal_probability = _clamp(goal_probability)
    team_strength_bonus = TeamStrength(
        _context_number(
            match_context,
            f"{side}_pre_match_probability",
            "pre_match_probability",
            goal_probability,
        ),
        _context_number(match_context, f"{side}_elo_rating", "elo_rating", 1600.0),
        int(_context_number(match_context, f"{side}_league_position", "league_position", 11)),
        _context_number(match_context, f"{side}_market_value", "market_value", 500000000.0),
    ).strength_score()
    team_strength_multiplier = 1 + (team_strength_bonus / 2000)
    goal_probability = goal_probability * team_strength_multiplier
    goal_probability = _clamp(goal_probability)
    form_bonus = _context_number(
        match_context,
        f"{side}_form_score",
        "form_score",
        50,
    )
    form_multiplier = 1 + (form_bonus / 3000)
    goal_probability = goal_probability * form_multiplier
    goal_probability = _clamp(goal_probability)
    odds = _context_number(
        match_context,
        f"{side}_odds",
        "odds",
        2.0,
    )

    if odds > 0:
        odds_multiplier = 1 + ((2.5 - min(odds, 2.5)) / 20)
    else:
        odds_multiplier = 1.0

    goal_probability = goal_probability * odds_multiplier
    goal_probability = _clamp(goal_probability)
    h2h_bonus = _context_number(
        match_context,
        f"{side}_h2h_score",
        "h2h_score",
        50,
    )
    h2h_multiplier = 1 + ((h2h_bonus - 50) / 1000)
    goal_probability = goal_probability * h2h_multiplier
    goal_probability = _clamp(goal_probability)
    if match_context.get("recent_goal", False):
        goal_probability *= 0.96
        goal_probability = _clamp(goal_probability)
    if match_context.get("recent_red_card", False):
        goal_probability *= 1.05
        goal_probability = _clamp(goal_probability)
    if match_context.get("recent_substitution", False):
        goal_probability *= 1.02
        goal_probability = _clamp(goal_probability)
    home_score = match_context.get("home_score", 0)
    away_score = match_context.get("away_score", 0)
    if side == "home":
        if home_score < away_score:
            goal_probability *= 1.08
            goal_probability = _clamp(goal_probability)
        elif home_score > away_score:
            goal_probability *= 0.97
            goal_probability = _clamp(goal_probability)
    if side == "away":
        if away_score < home_score:
            goal_probability *= 1.08
            goal_probability = _clamp(goal_probability)
        elif away_score > home_score:
            goal_probability *= 0.97
            goal_probability = _clamp(goal_probability)
    minute = int(match_context.get("minute", 0))
    if minute >= 75:
        if side == "home" and home_score < away_score:
            goal_probability *= 1.05
            goal_probability = _clamp(goal_probability)
        if side == "away" and away_score < home_score:
            goal_probability *= 1.05
            goal_probability = _clamp(goal_probability)
    if minute >= 85:
        if side == "home" and home_score < away_score:
            goal_probability *= 1.05
            goal_probability = _clamp(goal_probability)
        if side == "away" and away_score < home_score:
            goal_probability *= 1.05
            goal_probability = _clamp(goal_probability)
    corners = int(_first_value(stats, "Corner Kicks", "Corners", default=0))
    opponent_corners = int(_first_value(opponent_stats or {}, "Corner Kicks", "Corners", default=0))
    corner_difference = corners - opponent_corners
    if minute >= 70:
        if corner_difference >= 3:
            goal_probability *= 1.03
            goal_probability = _clamp(goal_probability)
        if corner_difference >= 5:
            goal_probability *= 1.03
            goal_probability = _clamp(goal_probability)
    shots_on_target = int(_first_value(stats, "Shots on Goal", "Shots on Target", default=0))
    opponent_shots_on_target = int(
        _first_value(opponent_stats or {}, "Shots on Goal", "Shots on Target", default=0)
    )
    shot_difference = shots_on_target - opponent_shots_on_target
    if shot_difference >= 2:
        goal_probability *= 1.04
        goal_probability = _clamp(goal_probability)
    if shot_difference >= 4:
        goal_probability *= 1.04
        goal_probability = _clamp(goal_probability)
    total_shots = int(_first_value(stats, "Total Shots", "Shots total", default=0))
    opponent_total_shots = int(
        _first_value(opponent_stats or {}, "Total Shots", "Shots total", default=0)
    )
    total_shot_difference = total_shots - opponent_total_shots
    if total_shot_difference >= 5:
        goal_probability *= 1.03
        goal_probability = _clamp(goal_probability)
    if total_shot_difference >= 10:
        goal_probability *= 1.03
        goal_probability = _clamp(goal_probability)
    possession = float(_first_value(stats, "Ball Possession", "Possession", default=50))
    opponent_possession = float(
        _first_value(opponent_stats or {}, "Ball Possession", "Possession", default=50)
    )
    possession_difference = possession - opponent_possession
    if minute >= 60:
        if possession_difference >= 15:
            goal_probability *= 1.02
            goal_probability = _clamp(goal_probability)
        if possession_difference >= 25:
            goal_probability *= 1.02
            goal_probability = _clamp(goal_probability)
    if minute >= 80 and home_score == away_score:
        goal_probability *= 1.04
        goal_probability = _clamp(goal_probability)
    goal_difference = abs(home_score - away_score)
    if minute >= 70 and goal_difference >= 2:
        goal_probability *= 0.97
        goal_probability = _clamp(goal_probability)
    if minute >= 85:
        if goal_probability >= 70:
            goal_probability *= 1.02
            goal_probability = _clamp(goal_probability)
        elif goal_probability <= 30:
            goal_probability *= 0.98
            goal_probability = _clamp(goal_probability)
    goal_signal = GoalSignal(
        pressure,
        momentum,
        attack_rating,
        trend_bonus,
        motivation_multiplier * 100 - 100,
        fatigue_bonus,
        red_card_bonus + yellow_card_bonus,
    ).signal_strength()
    goal_signal_multiplier = 1 + (goal_signal / 5000)
    goal_probability = goal_probability * goal_signal_multiplier
    goal_probability = _clamp(goal_probability)
    xg_bonus = ExpectedGoals(
        _first_value(stats, "Expected Goals", "xG", "expected_goals", default=0),
        _first_value(opponent_stats or {}, "Expected Goals", "xG", "expected_goals", default=0),
    ).goal_probability_bonus()
    xg_multiplier = 1 + (xg_bonus / 1000)
    goal_probability = goal_probability * xg_multiplier
    goal_probability = _clamp(goal_probability)
    dangerous_bonus = DangerousAttacks(
        int(_first_value(stats, "Dangerous Attacks", "Dangerous attacks", default=0)),
        int(_first_value(opponent_stats or {}, "Dangerous Attacks", "Dangerous attacks", default=0)),
    ).goal_probability_bonus()
    if minute >= 60:
        attack_ratio = max(0.1, (shots_on_target + dangerous_bonus / 10))

        if attack_ratio >= 8:
            goal_probability *= 1.03
            goal_probability = _clamp(goal_probability)

        if attack_ratio >= 12:
            goal_probability *= 1.03
            goal_probability = _clamp(goal_probability)
    dangerous_multiplier = 1 + (dangerous_bonus / 1000)
    goal_probability = goal_probability * dangerous_multiplier
    goal_probability = _clamp(goal_probability)
    tempo_bonus = MatchTempo(
        _context_number(
            match_context,
            f"{side}_previous_pressure",
            "previous_pressure",
            pressure,
        ),
        pressure,
        int(
            _context_number(
                match_context,
                f"{side}_previous_shots",
                "previous_shots",
                team.shots,
            )
        ),
        int(team.shots),
    ).tempo_bonus()
    tempo_multiplier = 1 + (tempo_bonus / 1000)
    goal_probability = goal_probability * tempo_multiplier
    goal_probability = _clamp(goal_probability)
    corner_bonus = CornerPressure(
        int(_first_value(stats, "Corner Kicks", "Corners", default=0)),
        int(_first_value(opponent_stats or {}, "Corner Kicks", "Corners", default=0)),
        int(team.minute),
    ).goal_probability_bonus()
    corner_multiplier = 1 + (corner_bonus / 1000)
    goal_probability = goal_probability * corner_multiplier
    goal_probability = _clamp(goal_probability)
    fouls = int(_first_value(opponent_stats or {}, "Fouls", "Fouls committed", default=0))
    if minute >= 60:
        if fouls >= 12:
            goal_probability *= 1.02
            goal_probability = _clamp(goal_probability)
        if fouls >= 18:
            goal_probability *= 1.02
            goal_probability = _clamp(goal_probability)

    offsides = int(_first_value(stats, "Offsides", "Offsides", default=0))
    if minute >= 60:
        if offsides >= 3:
            goal_probability *= 0.99
            goal_probability = _clamp(goal_probability)
        if offsides >= 5:
            goal_probability *= 0.98
            goal_probability = _clamp(goal_probability)

    if minute >= 90:
        goal_probability *= 0.99
        goal_probability = _clamp(goal_probability)

    if minute >= 90 and goal_difference == 1:
        goal_probability *= 1.02
        goal_probability = _clamp(goal_probability)

    next_goal_probability = NextGoalModel(
        goal_signal,
        team_strength_bonus,
        motivation_multiplier * 100 - 100,
        trend_bonus,
        red_card_bonus + yellow_card_bonus,
        fatigue_bonus,
        phase.time_pressure(),
    ).next_goal_probability()

    if minute >= 75 and match_context.get("recent_goal", False):
        next_goal_probability *= 0.98
        next_goal_probability = _clamp(next_goal_probability)

    if minute >= 75 and match_context.get("recent_red_card", False):
        next_goal_probability *= 1.03
        next_goal_probability = _clamp(next_goal_probability)

    over_model = OverModel(
        next_goal_probability,
        int(team.minute),
        int(team.team_score + team.opponent_score),
    )
    over25_probability = over_model.over25_probability()

    if minute >= 80 and over25_probability >= 70:
        over25_probability *= 1.02
        over25_probability = _clamp(over25_probability)

    if minute >= 80 and over25_probability <= 30:
        over25_probability *= 0.98
        over25_probability = _clamp(over25_probability)

    over35_probability = over_model.over35_probability()
    bet_score, bet_rating, bet_confidence = BetStrength(
        next_goal_probability,
        over25_probability,
        over35_probability,
    ).strength()

    opponent_pressure = _weighted_average(
        (
            (opponent_components["shooting"], 0.25),
            (opponent_components["attack_volume"], 0.22),
            (opponent_components["danger"], 0.18),
            (opponent_components["possession"], 0.12),
            (opponent_components["corners"], 0.10),
            (opponent_components["discipline"], 0.07),
            (opponent_components["match_state"], 0.06),
        )
    )
    opponent_goal_probability = _goal_probability(
        opponent_pressure,
        opponent_pressure,
        opponent_pressure,
        opponent_components["time"],
        opponent_components["match_state"],
    )
    total_goals_probability = _total_goals_probability(
        goal_probability,
        opponent_goal_probability,
        team.minute,
        team.team_score + team.opponent_score,
    )

    if side == "away":
        home_goal_probability = opponent_goal_probability
        away_goal_probability = goal_probability
    else:
        home_goal_probability = goal_probability
        away_goal_probability = opponent_goal_probability

    final_score = _weighted_average(
        (
            (pressure, 0.20),
            (momentum, 0.18),
            (goal_probability, 0.20),
            (total_goals_probability, 0.12),
            (attack_rating, 0.15),
            (components["discipline"], 0.06),
            (components["match_state"], 0.05),
            (components["time"], 0.04),
        )
    )

    debug_factors = {
        "pressure": pressure,
        "momentum": momentum,
        "goal_probability": goal_probability,
        "next_goal_probability": next_goal_probability,
        "over25_probability": over25_probability,
        "over35_probability": over35_probability,
        "bet_score": bet_score,
        "bet_rating": bet_rating,
    }
    print("AI DEBUG:", debug_factors)

    return AnalysisResult(
        pressure=round(pressure, 1),
        momentum=round(momentum, 1),
        goal_probability=round(goal_probability, 1),
        total_goals_probability=round(total_goals_probability, 1),
        home_goal_probability=round(home_goal_probability, 1),
        away_goal_probability=round(away_goal_probability, 1),
        attack_rating=round(attack_rating, 1),
        recommendation=_recommend(final_score, goal_probability, momentum),
        final_score=round(final_score, 1),
        next_goal_probability=round(next_goal_probability, 1),
        over25_probability=round(over25_probability, 1),
        over35_probability=round(over35_probability, 1),
        bet_score=round(bet_score, 1),
        bet_rating=bet_rating,
        bet_confidence=bet_confidence,
    )


def recommend_match(home_result, away_result):
    if home_result.final_score > away_result.final_score:
        return f"{home_result.recommendation} Advantage: home team."

    if away_result.final_score > home_result.final_score:
        return f"{away_result.recommendation} Advantage: away team."

    return "Both teams are close. No clear AI advantage yet."


def _normalize(stats, match_context=None, side="home"):
    if isinstance(stats, AnalysisInput):
        return stats

    stats = stats if isinstance(stats, dict) else {}
    match_context = match_context if isinstance(match_context, dict) else {}
    team_prefix = f"{side}_"
    opponent_prefix = f"{_opposite_side(side)}_"

    return AnalysisInput(
        shots=_number(_first_value(stats, "shots", "total_shots", "Total Shots")),
        shots_on_target=_number(
            _first_value(stats, "shots_on_target", "shots_on_goal", "Shots on Goal")
        ),
        possession=_number(_first_value(stats, "possession", "Ball Possession")),
        corners=_number(_first_value(stats, "corners", "Corner Kicks")),
        attacks=_number(_first_value(stats, "attacks", "Attacks")),
        dangerous_attacks=_number(
            _first_value(stats, "dangerous_attacks", "Dangerous Attacks")
        ),
        red_cards=_number(
            _first_value(
                stats,
                "red_cards",
                "Red Cards",
                default=match_context.get(f"{team_prefix}red_cards", 0),
            )
        ),
        yellow_cards=_number(
            _first_value(
                stats,
                "yellow_cards",
                "Yellow Cards",
                default=match_context.get(f"{team_prefix}yellow_cards", 0),
            )
        ),
        minute=_number(match_context.get("minute", stats.get("minute", 0))),
        team_score=_number(
            match_context.get(f"{team_prefix}score", stats.get("team_score", 0))
        ),
        opponent_score=_number(
            match_context.get(
                f"{opponent_prefix}score",
                stats.get("opponent_score", 0),
            )
        ),
    )


def _build_components(data):
    shooting = _score_shooting(data.shots, data.shots_on_target)
    attack_volume = _score_attack_volume(data.attacks)
    danger = _score_dangerous_attacks(data.dangerous_attacks)
    possession = _score_possession(data.possession)
    corners = _score_corners(data.corners)
    discipline = _score_discipline(data.red_cards, data.yellow_cards)
    match_state = _score_match_state(
        data.team_score,
        data.opponent_score,
        data.minute,
    )
    time = _score_time_pressure(data.minute)

    return {
        "shooting": shooting,
        "attack_volume": attack_volume,
        "danger": danger,
        "possession": possession,
        "corners": corners,
        "discipline": discipline,
        "match_state": match_state,
        "time": time,
    }


def _first_value(stats, *keys, default=0):
    for key in keys:
        if key in stats:
            return stats[key]

    return default


def _number(value):
    if value is None:
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    try:
        return float(str(value).replace("%", "").strip())
    except ValueError:
        return 0.0


def _context_number(match_context, *keys):
    default = keys[-1]
    lookup_keys = keys[:-1]

    if isinstance(match_context, dict):
        for key in lookup_keys:
            if key in match_context:
                return _number(match_context[key])

    for key in lookup_keys:
        if hasattr(match_context, key):
            return _number(getattr(match_context, key))

    return _number(default)


def _clamp(value):
    return max(0.0, min(100.0, value))


def _weighted_average(weighted_values):
    return _clamp(sum(value * weight for value, weight in weighted_values))


def _score_shooting(shots, shots_on_target):
    accuracy_bonus = 0.0
    if shots > 0:
        accuracy_bonus = (shots_on_target / shots) * 25.0

    return _clamp(shots * 3.4 + shots_on_target * 8.0 + accuracy_bonus)


def _score_attack_volume(attacks):
    return _clamp(attacks * 0.55)


def _score_dangerous_attacks(dangerous_attacks):
    return _clamp(dangerous_attacks * 1.25)


def _score_possession(possession):
    if possession <= 50:
        return _clamp(possession * 0.65)

    return _clamp(32.5 + (possession - 50.0) * 1.35)


def _score_corners(corners):
    return _clamp(corners * 11.5)


def _score_discipline(red_cards, yellow_cards):
    return _clamp(100.0 - red_cards * 30.0 - yellow_cards * 5.0)


def _score_match_state(team_score, opponent_score, minute):
    score_diff = team_score - opponent_score

    if score_diff < 0:
        return _clamp(58.0 + abs(score_diff) * 10.0 + minute * 0.08)

    if score_diff == 0:
        return _clamp(52.0 + minute * 0.05)

    return _clamp(48.0 - score_diff * 6.0 + minute * 0.04)


def _score_time_pressure(minute):
    if minute <= 0:
        return 50.0

    if minute < 30:
        return _clamp(42.0 + minute * 0.45)

    if minute < 75:
        return _clamp(56.0 + (minute - 30.0) * 0.32)

    return _clamp(72.0 + (minute - 75.0) * 0.6)


def _goal_probability(pressure, momentum, attack_rating, time_pressure, match_state):
    return _clamp(
        pressure * 0.30
        + momentum * 0.22
        + attack_rating * 0.27
        + match_state * 0.11
        + time_pressure * 0.10
    )


def _total_goals_probability(
    team_goal_probability,
    opponent_goal_probability,
    minute,
    current_goals,
):
    match_openness = (team_goal_probability + opponent_goal_probability) / 2.0
    score_bonus = min(current_goals * 6.0, 18.0)
    time_bonus = _score_time_pressure(minute) * 0.12

    return _clamp(match_openness * 0.76 + score_bonus + time_bonus)


def _opposite_side(side):
    return "away" if side == "home" else "home"


def _recommend(final_score, goal_probability, momentum):
    if final_score >= 78 and goal_probability >= 72:
        return "Strong attacking signal. Goal threat is high."

    if final_score >= 64 and momentum >= 62:
        return "Positive pressure. Watch this team closely."

    if final_score >= 48:
        return "Moderate activity. Wait for stronger confirmation."

    return "Low attacking signal. No clear pressure advantage."

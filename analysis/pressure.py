def clamp(value, minimum=0.0, maximum=100.0):
    return max(minimum, min(maximum, value))


def to_number(value, default=0.0):
    if value is None:
        return default

    if isinstance(value, (int, float)):
        return float(value)

    try:
        return float(str(value).replace("%", "").strip())
    except ValueError:
        return default


def attack_pressure(total_shots, shots_on_goal, dangerous_attacks):
    total_shots = to_number(total_shots)
    shots_on_goal = to_number(shots_on_goal)
    dangerous_attacks = to_number(dangerous_attacks)

    score = (
        total_shots * 3.0
        + shots_on_goal * 6.0
        + dangerous_attacks * 0.65
    )

    return clamp(score)


def shots_pressure(total_shots, shots_on_goal):
    total_shots = to_number(total_shots)
    shots_on_goal = to_number(shots_on_goal)

    accuracy_bonus = 0.0
    if total_shots > 0:
        accuracy_bonus = (shots_on_goal / total_shots) * 25.0

    score = total_shots * 4.0 + shots_on_goal * 8.0 + accuracy_bonus
    return clamp(score)


def possession_pressure(possession):
    possession = to_number(possession)

    if possession <= 50:
        return clamp(possession * 0.7)

    score = 35.0 + (possession - 50.0) * 1.3
    return clamp(score)


def corners_pressure(corners):
    corners = to_number(corners)
    return clamp(corners * 12.0)


def dangerous_attacks_score(dangerous_attacks):
    dangerous_attacks = to_number(dangerous_attacks)
    return clamp(dangerous_attacks * 1.4)

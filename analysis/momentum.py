from analysis.pressure import clamp


def momentum_score(
    attack_pressure_score,
    shots_pressure_score,
    possession_pressure_score,
    corners_pressure_score,
    dangerous_attacks_score,
):
    base_score = (
        attack_pressure_score * 0.28
        + shots_pressure_score * 0.24
        + possession_pressure_score * 0.14
        + corners_pressure_score * 0.14
        + dangerous_attacks_score * 0.20
    )

    pressure_spike = max(
        attack_pressure_score,
        shots_pressure_score,
        dangerous_attacks_score,
    )

    if pressure_spike >= 80:
        base_score += 8
    elif pressure_spike >= 65:
        base_score += 4

    return clamp(base_score)

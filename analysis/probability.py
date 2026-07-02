from analysis.pressure import clamp


def goal_probability(
    attack_pressure_score,
    shots_pressure_score,
    possession_pressure_score,
    corners_pressure_score,
    dangerous_attacks_score,
):
    score = (
        attack_pressure_score * 0.30
        + shots_pressure_score * 0.25
        + possession_pressure_score * 0.12
        + corners_pressure_score * 0.13
        + dangerous_attacks_score * 0.20
    )

    return clamp(score)

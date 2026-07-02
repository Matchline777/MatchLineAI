from dataclasses import dataclass


@dataclass(frozen=True)
class NextGoalModel:
    goal_signal: float
    team_strength: float
    motivation: float
    trend: float
    red_card_impact: float
    fatigue: float
    phase_pressure: float

    def next_goal_probability(self) -> float:
        score = (
            self.goal_signal * 0.35
            + self.team_strength * 0.20
            + self.motivation * 0.15
            + self.trend * 0.10
            + self.red_card_impact * 0.05
            + self.fatigue * 0.05
            + self.phase_pressure * 0.10
        )

        return max(0.0, min(100.0, score))

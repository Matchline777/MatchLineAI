from dataclasses import dataclass


@dataclass(frozen=True)
class GoalSignal:
    pressure: float
    momentum: float
    attack_rating: float
    trend_bonus: float
    motivation_bonus: float
    fatigue_score: float
    red_card_bonus: float

    def signal_strength(self) -> float:
        score = (
            self.pressure * 0.25
            + self.momentum * 0.20
            + self.attack_rating * 0.20
            + self.trend_bonus * 0.10
            + self.motivation_bonus * 0.10
            + self.fatigue_score * 0.10
            + self.red_card_bonus * 0.05
        )

        return max(0.0, min(100.0, score))

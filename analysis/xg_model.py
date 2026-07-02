from dataclasses import dataclass


@dataclass(frozen=True)
class ExpectedGoals:
    own_xg: float
    opponent_xg: float

    def advantage(self) -> float:
        return self.own_xg - self.opponent_xg

    def goal_probability_bonus(self) -> float:
        difference = self.advantage()

        if difference <= -1.5:
            bonus = -20.0
        elif difference <= -0.5:
            bonus = -10.0
        elif difference >= 1.5:
            bonus = 20.0
        elif difference >= 0.5:
            bonus = 10.0
        else:
            bonus = 0.0

        return max(-100.0, min(100.0, bonus))

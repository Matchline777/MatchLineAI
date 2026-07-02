from dataclasses import dataclass


@dataclass(frozen=True)
class CornerPressure:
    own_corners: int
    opponent_corners: int
    minute: int

    def advantage(self) -> int:
        return self.own_corners - self.opponent_corners

    def goal_probability_bonus(self) -> float:
        bonus = 0.0
        advantage = self.advantage()

        if advantage >= 2:
            bonus += 5.0

        if advantage >= 4:
            bonus += 10.0

        if self.minute >= 75:
            bonus *= 1.5

        return max(-100.0, min(100.0, bonus))

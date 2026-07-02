from dataclasses import dataclass


@dataclass(frozen=True)
class DangerousAttacks:
    own_dangerous_attacks: int
    opponent_dangerous_attacks: int

    def advantage(self) -> int:
        return self.own_dangerous_attacks - self.opponent_dangerous_attacks

    def goal_probability_bonus(self) -> float:
        difference = self.advantage()

        if difference <= -20:
            bonus = -20.0
        elif difference <= -10:
            bonus = -10.0
        elif difference >= 20:
            bonus = 20.0
        elif difference >= 10:
            bonus = 10.0
        else:
            bonus = 0.0

        return max(-100.0, min(100.0, bonus))

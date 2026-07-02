from dataclasses import dataclass


@dataclass(frozen=True)
class OverModel:
    next_goal_probability: float
    minute: int
    current_total_goals: int

    def over25_probability(self) -> float:
        if self.current_total_goals >= 3:
            return 100.0

        probability = self.next_goal_probability * (0.60 + self.minute / 200)
        return max(0.0, min(100.0, probability))

    def over35_probability(self) -> float:
        if self.current_total_goals >= 4:
            return 100.0

        probability = self.over25_probability() * 0.75
        return max(0.0, min(100.0, probability))

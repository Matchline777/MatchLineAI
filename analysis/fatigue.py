from dataclasses import dataclass


@dataclass(frozen=True)
class Fatigue:
    minute: int
    possession: float
    total_shots: int

    def fatigue_score(self) -> float:
        score = 0.0

        if self.minute >= 60:
            score += 10.0

        if self.minute >= 75:
            score += 20.0

        if self.minute >= 85:
            score += 30.0

        if self.possession >= 60:
            score += 10.0

        if self.total_shots >= 15:
            score += 10.0

        return max(0.0, min(100.0, score))

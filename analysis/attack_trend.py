from dataclasses import dataclass


@dataclass(frozen=True)
class AttackTrend:
    previous_pressure: float
    current_pressure: float

    def is_increasing(self):
        return self.current_pressure > self.previous_pressure

    def is_decreasing(self):
        return self.current_pressure < self.previous_pressure

    def trend_bonus(self) -> float:
        change = self.current_pressure - self.previous_pressure

        if change >= 10.0:
            return 20.0

        if change >= 5.0:
            return 10.0

        if change <= -10.0:
            return -20.0

        if change <= -5.0:
            return -10.0

        return 0.0

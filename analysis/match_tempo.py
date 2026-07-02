from dataclasses import dataclass


@dataclass(frozen=True)
class MatchTempo:
    previous_pressure: float
    current_pressure: float
    previous_shots: int
    current_shots: int

    def pressure_change(self) -> float:
        return self.current_pressure - self.previous_pressure

    def shots_change(self) -> int:
        return self.current_shots - self.previous_shots

    def tempo_bonus(self) -> float:
        bonus = 0.0

        if self.pressure_change() >= 10:
            bonus += 10.0

        if self.pressure_change() >= 20:
            bonus += 20.0

        if self.shots_change() >= 2:
            bonus += 5.0

        if self.shots_change() >= 4:
            bonus += 10.0

        return max(0.0, min(100.0, bonus))

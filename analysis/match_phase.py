from dataclasses import dataclass


@dataclass(frozen=True)
class MatchPhase:
    minute: int

    def is_early_game(self):
        return 0 <= self.minute <= 15

    def is_first_half(self):
        return 0 <= self.minute <= 45

    def is_second_half(self):
        return self.minute >= 46

    def is_late_game(self):
        return self.minute >= 76

    def time_pressure(self):
        if self.minute <= 15:
            return 10.0

        if self.minute <= 30:
            return 30.0

        if self.minute <= 60:
            return 50.0

        if self.minute <= 75:
            return 75.0

        return 100.0

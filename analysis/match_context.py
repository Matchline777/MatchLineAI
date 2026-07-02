from dataclasses import dataclass


@dataclass(frozen=True)
class MatchContext:
    minute: int = 0
    home_score: int = 0
    away_score: int = 0
    home_red_cards: int = 0
    away_red_cards: int = 0

    def goal_difference(self, side):
        if side == "home":
            return self.home_score - self.away_score

        if side == "away":
            return self.away_score - self.home_score

        raise ValueError("side must be 'home' or 'away'")

    def is_losing(self, side):
        return self.goal_difference(side) < 0

    def is_winning(self, side):
        return self.goal_difference(side) > 0

    def is_draw(self):
        return self.home_score == self.away_score

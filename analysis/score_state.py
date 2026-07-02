from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreState:
    own_score: int
    opponent_score: int

    def is_winning(self):
        return self.own_score > self.opponent_score

    def is_drawing(self):
        return self.own_score == self.opponent_score

    def is_losing(self):
        return self.own_score < self.opponent_score

    def goal_difference(self):
        return self.own_score - self.opponent_score

    def motivation_bonus(self) -> float:
        if self.is_winning():
            return -10.0

        if self.is_drawing():
            return 0.0

        if self.goal_difference() == -1:
            return 20.0

        return 35.0

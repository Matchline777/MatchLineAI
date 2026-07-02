from dataclasses import dataclass


@dataclass(frozen=True)
class TeamForm:
    wins: int
    draws: int
    losses: int
    goals_scored: int
    goals_conceded: int

    def points(self) -> int:
        return self.wins * 3 + self.draws

    def goal_difference(self) -> int:
        return self.goals_scored - self.goals_conceded

    def form_score(self) -> float:
        score = self.points() * 5 + self.goal_difference()
        return max(0.0, min(100.0, score))

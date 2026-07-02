from dataclasses import dataclass


@dataclass(frozen=True)
class FoulImpact:
    own_fouls: int
    opponent_fouls: int

    def impact_score(self) -> float:
        score = self.own_fouls * -1.5 + self.opponent_fouls * 1.2
        return max(-100.0, min(100.0, score))

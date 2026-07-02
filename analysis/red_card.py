from dataclasses import dataclass


@dataclass(frozen=True)
class RedCardImpact:
    own_red_cards: int
    opponent_red_cards: int

    def impact_score(self) -> float:
        score = self.own_red_cards * -25.0 + self.opponent_red_cards * 20.0
        return max(-100.0, min(100.0, score))

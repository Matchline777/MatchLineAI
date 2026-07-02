from dataclasses import dataclass


@dataclass(frozen=True)
class YellowCardImpact:
    own_yellow_cards: int
    opponent_yellow_cards: int

    def impact_score(self) -> float:
        score = self.own_yellow_cards * -4 + self.opponent_yellow_cards * 3
        return max(-100.0, min(100.0, score))

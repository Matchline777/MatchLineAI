from dataclasses import dataclass


@dataclass(frozen=True)
class TeamStrength:
    pre_match_probability: float
    elo_rating: float
    league_position: int
    market_value: float

    def strength_score(self) -> float:
        pre_match_score = self._clamp(self.pre_match_probability)
        elo_score = self._clamp((self.elo_rating - 1000.0) / 1200.0 * 100.0)
        position_score = self._clamp((21.0 - self.league_position) / 20.0 * 100.0)
        market_score = self._clamp(self.market_value / 1_000_000_000.0 * 100.0)

        return round(
            pre_match_score * 0.50
            + elo_score * 0.25
            + position_score * 0.15
            + market_score * 0.10,
            1,
        )

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(100.0, value))

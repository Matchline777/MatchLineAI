from dataclasses import dataclass


@dataclass(frozen=True)
class ConfidenceBreakdown:
    pressure: float
    momentum: float
    team_strength: float
    trend: float
    fatigue: float
    discipline: float
    motivation: float

    def confidence(self) -> tuple[float, dict]:
        breakdown = {
            "Pressure": self.pressure * 0.25,
            "Momentum": self.momentum * 0.15,
            "Team Strength": self.team_strength * 0.20,
            "Trend": self.trend * 0.10,
            "Fatigue": self.fatigue * 0.10,
            "Discipline": self.discipline * 0.10,
            "Motivation": self.motivation * 0.10,
        }
        final_confidence = sum(breakdown.values())

        return final_confidence, breakdown


@dataclass(frozen=True)
class BetStrength:
    next_goal_probability: float
    over25_probability: float
    over35_probability: float

    def strength(self) -> tuple[float, str, str]:
        score = (
            self.next_goal_probability * 0.50
            + self.over25_probability * 0.30
            + self.over35_probability * 0.20
        )
        score = max(0.0, min(100.0, score))

        if score >= 90:
            rating = "ELITE"
            confidence = "95%"
        elif score >= 80:
            rating = "STRONG"
            confidence = "85%"
        elif score >= 70:
            rating = "GOOD"
            confidence = "75%"
        elif score >= 60:
            rating = "MEDIUM"
            confidence = "65%"
        else:
            rating = "WEAK"
            confidence = "50%"

        return score, rating, confidence

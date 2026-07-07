"""Fallback Flashscore parser for matches without API-Football live statistics."""


def get_flashscore_statistics(match_url):
    """Return fallback statistics when API-Football returns no live statistics."""
    return {
        "available": False,
        "source": "flashscore",
        "statistics": {},
    }

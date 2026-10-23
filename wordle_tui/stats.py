"""Wordle statistics manager and persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

STATS_DIR = Path.home() / ".local" / "share" / "wordle-tui"
STATS_PATH = STATS_DIR / "stats.json"


class WordleStats:
    """Tracks game statistics globally and by word length."""

    def __init__(self) -> None:
        self.stats: Dict[str, Any] = self._load()

    def _default_stats(self) -> Dict[str, Any]:
        return {
            "total_played": 0,
            "total_won": 0,
            "current_streak": 0,
            "max_streak": 0,
            "guess_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0},
            "by_length": {},
            "last_played": None,
        }

    def _load(self) -> Dict[str, Any]:
        if STATS_PATH.exists():
            try:
                with open(STATS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Merge with default structure
                    defaults = self._default_stats()
                    for k, v in defaults.items():
                        if k not in data:
                            data[k] = v
                    return data
            except Exception:
                pass
        return self._default_stats()

    def save(self) -> None:
        STATS_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATS_PATH, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2)

    def record_game(self, word_length: int, won: bool, attempts: int, word: str) -> None:
        """Record outcome of completed game."""
        self.stats["total_played"] += 1
        if won:
            self.stats["total_won"] += 1
            self.stats["current_streak"] += 1
            if self.stats["current_streak"] > self.stats["max_streak"]:
                self.stats["max_streak"] = self.stats["current_streak"]
            att_key = str(min(attempts, 6))
            self.stats["guess_distribution"][att_key] = (
                self.stats["guess_distribution"].get(att_key, 0) + 1
            )
        else:
            self.stats["current_streak"] = 0

        # Update per-length stats
        len_key = str(word_length)
        if len_key not in self.stats["by_length"]:
            self.stats["by_length"][len_key] = {
                "played": 0,
                "won": 0,
                "current_streak": 0,
                "max_streak": 0,
                "guess_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0},
            }

        len_stats = self.stats["by_length"][len_key]
        len_stats["played"] += 1
        if won:
            len_stats["won"] += 1
            len_stats["current_streak"] += 1
            if len_stats["current_streak"] > len_stats["max_streak"]:
                len_stats["max_streak"] = len_stats["current_streak"]
            att_key = str(min(attempts, 6))
            len_stats["guess_distribution"][att_key] = (
                len_stats["guess_distribution"].get(att_key, 0) + 1
            )
        else:
            len_stats["current_streak"] = 0

        self.stats["last_played"] = {
            "length": word_length,
            "won": won,
            "attempts": attempts,
            "word": word,
        }

        self.save()

    @property
    def total_played(self) -> int:
        return self.stats.get("total_played", 0)

    @property
    def total_won(self) -> int:
        return self.stats.get("total_won", 0)

    @property
    def win_percentage(self) -> int:
        if self.total_played == 0:
            return 0
        return int(round((self.total_won / self.total_played) * 100))

    @property
    def current_streak(self) -> int:
        return self.stats.get("current_streak", 0)

    @property
    def max_streak(self) -> int:
        return self.stats.get("max_streak", 0)

    @property
    def guess_distribution(self) -> Dict[str, int]:
        return self.stats.get("guess_distribution", {})

    def get_length_stats(self, length: int) -> Dict[str, Any]:
        return self.stats.get("by_length", {}).get(str(length), {
            "played": 0,
            "won": 0,
            "current_streak": 0,
            "max_streak": 0,
            "guess_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0},
        })

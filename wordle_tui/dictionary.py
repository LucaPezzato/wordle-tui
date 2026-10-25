"""Dictionary manager for Italian Wordle TUI."""

from __future__ import annotations

import gzip
import json
import os
import random
import unicodedata
import urllib.request
from pathlib import Path
from typing import Dict, List, Set, Tuple

CACHE_DIR = Path.home() / ".local" / "share" / "wordle-tui"
BUNDLED_DICT_PATH = Path(__file__).parent / "data" / "dictionary.json.gz"
CACHED_DICT_PATH = CACHE_DIR / "dictionary.json.gz"




def normalize_word(word: str) -> str:
    """Normalize word to uppercase ASCII letters (A-Z), removing accents."""
    w = unicodedata.normalize("NFD", word.strip().lower())
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return w.upper()


class WordleDictionary:
    """Loads, validates and serves Italian word candidates and guesses."""

    _instance: WordleDictionary | None = None

    def __init__(self) -> None:
        self.targets_by_len: Dict[int, List[str]] = {}
        self.guesses_by_len: Dict[int, Set[str]] = {}
        self.loaded = False
        self._load()

    @classmethod
    def get_instance(cls) -> WordleDictionary:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_active_path(self) -> Path:
        if CACHED_DICT_PATH.exists():
            return CACHED_DICT_PATH
        return BUNDLED_DICT_PATH

    def _load(self) -> None:
        path = self._get_active_path()
        if not path.exists():
            raise FileNotFoundError(f"Vocabolario italiano non trovato in {path}")

        with gzip.open(path, "rt", encoding="utf-8") as f:
            data = json.load(f)

        raw_targets = data.get("targets", {})
        raw_guesses = data.get("guesses", {})

        self.targets_by_len = {
            int(k): list(v) for k, v in raw_targets.items()
        }
        self.guesses_by_len = {
            int(k): set(v) for k, v in raw_guesses.items()
        }
        self.loaded = True

    def get_available_lengths(self) -> List[int]:
        """Return supported word lengths (sorted)."""
        return sorted(self.targets_by_len.keys())

    def get_random_target(self, length: int) -> str:
        """Return a random target word of the given length."""
        words = self.targets_by_len.get(length)
        if not words:
            # Fallback to guesses if targets empty
            guesses = list(self.guesses_by_len.get(length, []))
            if not guesses:
                raise ValueError(f"Nessuna parola trovata per lunghezza {length}")
            return random.choice(guesses)
        return random.choice(words)

    def is_valid_guess(self, word: str, length: int) -> bool:
        """Check if guess is in valid Italian words set."""
        clean = normalize_word(word)
        if len(clean) != length:
            return False
        valid_set = self.guesses_by_len.get(length)
        if not valid_set:
            return False
        return clean in valid_set

    def get_counts(self, length: int) -> Tuple[int, int]:
        """Return (targets_count, valid_guesses_count) for length."""
        targets = len(self.targets_by_len.get(length, []))
        guesses = len(self.guesses_by_len.get(length, []))
        return targets, guesses

    @classmethod
    def update_from_upstream(cls, callback=None) -> Tuple[int, int]:
        """Download latest Italian wordlists and rebuild cached dictionary."""
        from wordle_tui.build_dict import build_clean_dictionary

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        tot_targets, tot_guesses = build_clean_dictionary(
            CACHED_DICT_PATH, callback=callback
        )

        # Reload singleton
        cls._instance = cls()
        return tot_targets, tot_guesses

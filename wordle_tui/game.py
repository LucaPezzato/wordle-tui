"""Wordle game logic and letter evaluation rules."""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Tuple


class LetterState(Enum):
    UNKNOWN = "unknown"
    ABSENT = "absent"      # Grigiastro/Scuro - Non presente
    PRESENT = "present"    # Giallo Dracula - Posizione errata
    CORRECT = "correct"    # Verde Dracula - Posizione corretta

    @property
    def emoji(self) -> str:
        if self == LetterState.CORRECT:
            return "🟩"
        if self == LetterState.PRESENT:
            return "🟨"
        return "⬛"


class GameStatus(Enum):
    PLAYING = "playing"
    WON = "won"
    LOST = "lost"


def evaluate_guess(guess: str, target: str) -> List[LetterState]:
    """Evaluate guess against target respecting standard duplicate letter rules."""
    length = len(guess)
    result = [LetterState.ABSENT] * length
    target_chars: List[Optional[str]] = list(target)

    # Passo 1: Individua le lettere corrette (posizione esatta)
    for i in range(length):
        if guess[i] == target[i]:
            result[i] = LetterState.CORRECT
            target_chars[i] = None

    # Passo 2: Individua lettere presenti ma in posizione errata
    for i in range(length):
        if result[i] != LetterState.CORRECT:
            g = guess[i]
            if g in target_chars:
                result[i] = LetterState.PRESENT
                idx = target_chars.index(g)
                target_chars[idx] = None

    return result


class WordleGame:
    """Manages active Wordle session."""

    def __init__(self, target_word: str, max_attempts: int = 6) -> None:
        self.target: str = target_word.upper()
        self.word_length: int = len(self.target)
        self.max_attempts: int = max_attempts

        self.guesses: List[str] = []
        self.evaluations: List[List[LetterState]] = []
        self.current_input: str = ""
        self.status: GameStatus = GameStatus.PLAYING

        self.keyboard_states: Dict[str, LetterState] = {
            chr(c): LetterState.UNKNOWN for c in range(ord("A"), ord("Z") + 1)
        }

    @property
    def attempt_count(self) -> int:
        return len(self.guesses)

    @property
    def remaining_attempts(self) -> int:
        return max(0, self.max_attempts - self.attempt_count)

    def add_letter(self, char: str) -> bool:
        """Add uppercase letter to current row if space permits."""
        if self.status != GameStatus.PLAYING:
            return False
        char = char.upper()
        if len(self.current_input) < self.word_length and char.isalpha() and char.isascii():
            self.current_input += char
            return True
        return False

    def remove_letter(self) -> bool:
        """Remove last typed letter."""
        if self.status != GameStatus.PLAYING:
            return False
        if self.current_input:
            self.current_input = self.current_input[:-1]
            return True
        return False

    def clear_current_input(self) -> None:
        if self.status == GameStatus.PLAYING:
            self.current_input = ""

    def submit_guess(self) -> Tuple[bool, str]:
        """Submit current input as a guess. Returns (success, message)."""
        if self.status != GameStatus.PLAYING:
            return False, "La partita è già terminata."

        if len(self.current_input) != self.word_length:
            return False, f"La parola deve avere {self.word_length} lettere."

        guess = self.current_input
        evaluation = evaluate_guess(guess, self.target)

        self.guesses.append(guess)
        self.evaluations.append(evaluation)
        self.current_input = ""

        # Update keyboard states
        for char, state in zip(guess, evaluation):
            current = self.keyboard_states[char]
            # Priority: CORRECT > PRESENT > ABSENT > UNKNOWN
            if state == LetterState.CORRECT:
                self.keyboard_states[char] = LetterState.CORRECT
            elif state == LetterState.PRESENT:
                if current != LetterState.CORRECT:
                    self.keyboard_states[char] = LetterState.PRESENT
            elif state == LetterState.ABSENT:
                if current == LetterState.UNKNOWN:
                    self.keyboard_states[char] = LetterState.ABSENT

        # Check win/loss
        if guess == self.target:
            self.status = GameStatus.WON
            return True, f"Bravissimo! Hai indovinato in {self.attempt_count}/{self.max_attempts} tentativi!"

        if self.attempt_count >= self.max_attempts:
            self.status = GameStatus.LOST
            return True, f"Peccato! La parola era: {self.target}"

        return True, "Tentativo registrato."

    def surrender(self) -> str:
        """Surrender the game and reveal secret word."""
        if self.status == GameStatus.PLAYING:
            self.status = GameStatus.LOST
        return self.target

    def get_share_grid(self) -> str:
        """Generate shareable emoji grid."""
        lines = [f"Wordle-TUI ({self.word_length}L) {self.attempt_count if self.status == GameStatus.WON else 'X'}/{self.max_attempts}"]
        for ev in self.evaluations:
            lines.append("".join(s.emoji for s in ev))
        return "\n".join(lines)

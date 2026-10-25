"""Unit tests for Wordle TUI."""

import unittest
from wordle_tui.dictionary import WordleDictionary, normalize_word
from wordle_tui.game import GameStatus, LetterState, WordleGame, evaluate_guess
from wordle_tui.stats import WordleStats


class TestWordleLogic(unittest.TestCase):

    def test_evaluate_guess_exact(self):
        result = evaluate_guess("CASAE", "CASAE")
        self.assertEqual(result, [LetterState.CORRECT] * 5)

    def test_evaluate_guess_all_absent(self):
        result = evaluate_guess("PUPPO", "AMICA")
        self.assertEqual(result, [LetterState.ABSENT] * 5)

    def test_evaluate_guess_duplicates_priority(self):
        # Target: ISOLA (one O)
        # Guess:  COLOR (first O is pos 1, second O is pos 3)
        # In ISOLA, O is at pos 2. Neither match exact position, so only FIRST 'O' in guess is PRESENT, second is ABSENT.
        result = evaluate_guess("COLOR", "ISOLA")
        # C (ABSENT), O (PRESENT), L (PRESENT), O (ABSENT), R (ABSENT)
        self.assertEqual(result[0], LetterState.ABSENT)   # C
        self.assertEqual(result[1], LetterState.PRESENT)  # 1st O
        self.assertEqual(result[2], LetterState.PRESENT)  # L
        self.assertEqual(result[3], LetterState.ABSENT)   # 2nd O (already consumed)
        self.assertEqual(result[4], LetterState.ABSENT)   # R

    def test_evaluate_guess_correct_takes_priority_over_present(self):
        # Target: BOSCO (two O's: pos 1 and pos 4)
        # Guess:  COLOR (two O's: pos 1 and pos 3)
        # Pos 1 in guess matches pos 1 in target -> CORRECT.
        # Target pos 4 has 'O'. Guess pos 3 has 'O' -> PRESENT.
        result = evaluate_guess("COLOR", "BOSCO")
        self.assertEqual(result[1], LetterState.CORRECT)
        self.assertEqual(result[3], LetterState.PRESENT)

    def test_variable_lengths(self):
        for length in (4, 5, 6, 7, 8):
            target = "A" * length
            guess = "A" * length
            res = evaluate_guess(guess, target)
            self.assertEqual(len(res), length)
            self.assertTrue(all(s == LetterState.CORRECT for s in res))


class TestDictionary(unittest.TestCase):

    def setUp(self):
        self.dict_manager = WordleDictionary.get_instance()

    def test_available_lengths(self):
        lengths = self.dict_manager.get_available_lengths()
        for expected in (4, 5, 6, 7, 8):
            self.assertIn(expected, lengths)

    def test_random_target(self):
        for l in (4, 5, 6, 7, 8):
            target = self.dict_manager.get_random_target(l)
            self.assertEqual(len(target), l)
            self.assertTrue(target.isalpha())
            self.assertTrue(target.isupper())

    def test_is_valid_guess(self):
        # "PIZZA" is 5 letters and valid
        self.assertTrue(self.dict_manager.is_valid_guess("pizza", 5))
        self.assertTrue(self.dict_manager.is_valid_guess("PIZZA", 5))
        # "CANE" is 4 letters
        self.assertTrue(self.dict_manager.is_valid_guess("cane", 4))
        # Invalid / nonsense
        self.assertFalse(self.dict_manager.is_valid_guess("XYZQQ", 5))
        # Wrong length
        self.assertFalse(self.dict_manager.is_valid_guess("CANE", 5))

    def test_no_broken_stems(self):
        # Verbal and nominal broken stems must NOT exist in targets or guesses
        broken_stems = [
            "SERR", "NAVIG", "SGOBB", "OLEZZ", "TRARR", "NOVIT", "NUDIT",
            "REALT", "PARL", "PENS", "PORT", "NUOT", "OCCUP", "ODIER"
        ]
        for stem in broken_stems:
            length = len(stem)
            targets = self.dict_manager.targets_by_len.get(length, [])
            guesses = self.dict_manager.guesses_by_len.get(length, set())
            self.assertNotIn(stem, targets, f"{stem} should not be a target word!")
            self.assertNotIn(stem, guesses, f"{stem} should not be a valid guess!")

    def test_no_roman_numerals(self):
        # Roman numerals must not be targets or guesses
        romans = ["CCCII", "CDVII", "LXIII", "XXVII", "MCXII", "CCCLI"]
        for r in romans:
            length = len(r)
            targets = self.dict_manager.targets_by_len.get(length, [])
            guesses = self.dict_manager.guesses_by_len.get(length, set())
            self.assertNotIn(r, targets, f"Roman numeral {r} should not be a target!")
            self.assertNotIn(r, guesses, f"Roman numeral {r} should not be a guess!")

    def test_no_clitic_compounds_in_targets(self):
        # Clitic imperatives and contractions should not be target secret words
        clitics = ["DAMMI", "DARCI", "DARLA", "DIRMI", "FAMMI", "FARLO", "DACCI", "FAGLI", "AMALA"]
        for c in clitics:
            length = len(c)
            targets = self.dict_manager.targets_by_len.get(length, [])
            self.assertNotIn(c, targets, f"Clitic compound {c} should not be a target word!")

    def test_common_everyday_words_present(self):
        # Target list must contain staple common words
        common_words = {
            4: ["CASA", "MARE", "SOLE", "PANE", "VINO", "LUNA", "LUPO", "ROSA"],
            5: ["PIZZA", "TEMPO", "MONDO", "FESTA", "NOTTE", "TRENO", "AMORE", "GATTO"],
            6: ["STRADA", "TAVOLO", "LAVORO", "FOGLIA", "GIORNO"],
            7: ["BAMBINO", "ALBERGO", "MERCATO", "DOMANDA", "RAGAZZO"],
            8: ["STUDENTE", "GIORNALE", "STAZIONE", "FAMIGLIA", "FINESTRA"],
        }
        for length, words in common_words.items():
            targets = set(self.dict_manager.targets_by_len.get(length, []))
            for w in words:
                self.assertIn(w, targets, f"Common word {w} should be in targets[{length}]!")


class TestWordleGameSession(unittest.TestCase):

    def test_game_flow(self):
        game = WordleGame("PIZZA", max_attempts=6)
        self.assertEqual(game.status, GameStatus.PLAYING)
        self.assertEqual(game.word_length, 5)

        # Typing
        game.add_letter("c")
        game.add_letter("a")
        game.add_letter("s")
        game.add_letter("t")
        game.add_letter("o")
        self.assertEqual(game.current_input, "CASTO")

        success, _ = game.submit_guess()
        self.assertTrue(success)
        self.assertEqual(game.attempt_count, 1)
        self.assertEqual(game.current_input, "")

        # Now guess correctly
        for char in "PIZZA":
            game.add_letter(char)
        success, _ = game.submit_guess()
        self.assertTrue(success)
        self.assertEqual(game.status, GameStatus.WON)
        self.assertIn("🟩", game.get_share_grid())

    def test_surrender(self):
        game = WordleGame("BOSCO")
        self.assertEqual(game.status, GameStatus.PLAYING)
        revealed = game.surrender()
        self.assertEqual(revealed, "BOSCO")
        self.assertEqual(game.status, GameStatus.LOST)


if __name__ == "__main__":
    unittest.main()

import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nytbee_solver import solver


class TestWordlistLoading(unittest.TestCase):
    def test_load_words_from_plain_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "words.txt"
            path.write_text("Alpha\nBeta\n123\n")
            words = solver.load_words(path)
        self.assertEqual(words, ["alpha", "beta"])

    def test_load_words_from_dict_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "words.txt"
            path.write_text("{'Alpha': 1, 'beta': 2, '123': 3}")
            words = solver.load_words(path)
        self.assertEqual(words, ["alpha", "beta"])


class TestSolverLogic(unittest.TestCase):
    def test_normalize_letters_requires_seven_unique(self) -> None:
        required, letters = solver.normalize_letters("aBCdefg")
        self.assertEqual(required, "a")
        self.assertEqual(letters, "abcdefg")
        with self.assertRaises(ValueError):
            solver.normalize_letters("abc")

    def test_format_spelling_bee_grid(self) -> None:
        words = ["alpha", "able", "baker", "badge", "bead"]
        grid = solver._format_spelling_bee_grid(words)
        self.assertIn("5", grid)
        self.assertIn("4", grid)
        self.assertIn("A", grid)
        self.assertIn("B", grid)
        self.assertIn("Total", grid)

    def test_get_todays_puzzle_letters_from_answers(self) -> None:
        html = """
        <div id="main-answer-list">
          <ul>
            <li>bag</li>
            <li>cafe</li>
            <li>dad</li>
          </ul>
        </div>
        """
        with patch.object(solver, "fetch_html", return_value=html):
            letters = solver.get_todays_puzzle_letters(base_url="https://example.com/Bee_{date}.html")
        self.assertEqual(letters, "abgcfed")

    def test_solve_spelling_bee_filters_words(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "words.txt"
            path.write_text("facet\nface\nfeed\ndecafbag\nbead\n")
            words, pangrams, letters, required = solver.solve_spelling_bee(
                "abgcfed", wordlist_path=path
            )
        self.assertEqual(required, "a")
        self.assertEqual(letters, "abgcfed")
        self.assertIn("face", words)
        self.assertIn("bead", words)
        self.assertNotIn("feed", words)
        self.assertEqual(pangrams, ["decafbag"])

    def test_print_hint_page_from_todays_letters(self) -> None:
        html = """
        <div id="main-answer-list">
          <ul>
            <li>bag</li>
            <li>cafe</li>
            <li>dad</li>
          </ul>
        </div>
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "words.txt"
            path.write_text("bag\ncafe\ndad\nabed\nface\n")
            with patch.object(solver, "fetch_html", return_value=html):
                letters = solver.get_todays_puzzle_letters(
                    base_url="https://example.com/Bee_{date}.html"
                )
            words, pangrams, cleaned_letters, required = solver.solve_spelling_bee(
                letters, wordlist_path=path
            )

        buffer = io.StringIO()
        with patch("sys.stdout", new=buffer):
            solver.print_hint_page(words, pangrams, cleaned_letters, required)

        output = buffer.getvalue()
        self.assertIn("NYT Spelling Bee Hint Page", output)
        self.assertIn("Letters:", output)
        self.assertIn("Total words:", output)
        self.assertIn("Pangrams:", output)
        self.assertIn("Spelling Bee Grid:", output)


if __name__ == "__main__":
    unittest.main()

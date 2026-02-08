import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nytbee_solver import encoding, solver


class TestEncodingRoundTrips(unittest.TestCase):
    def setUp(self) -> None:
        self.wordlist_path = ROOT / "nytbee_dict.txt"
        self.letters = "abgcfed"
        self.required = "a"
        self.words, _, _, _ = solver.solve_spelling_bee(
            self.letters, wordlist_path=self.wordlist_path
        )

    def test_length_prefixed_round_trip(self) -> None:
        encoded = encoding.encode_length_prefixed(self.words, self.letters, self.required)
        decoded = encoding.decode_length_prefixed(encoded, self.letters, self.required)
        self.assertEqual(decoded, self.words)

    def test_front_coded_round_trip(self) -> None:
        encoded = encoding.encode_front_coded(self.words, self.letters, self.required)
        decoded = encoding.decode_front_coded(encoded, self.letters, self.required)
        self.assertEqual(decoded, sorted(self.words))

    def test_terminated_round_trip(self) -> None:
        encoded = encoding.encode_terminated(self.words, self.letters, self.required)
        decoded = encoding.decode_terminated(encoded, self.letters, self.required)
        self.assertEqual(decoded, self.words)

    def test_random_letters_round_trips(self) -> None:
        random.seed(19)
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        for _ in range(3):
            letters = "".join(random.sample(alphabet, 7))
            required = letters[0]
            words, _, _, _ = solver.solve_spelling_bee(
                letters, wordlist_path=self.wordlist_path
            )
            encoded = encoding.encode_terminated(words, letters, required)
            decoded = encoding.decode_terminated(encoded, letters, required)
            self.assertEqual(decoded, words)


class TestEncodingEvaluation(unittest.TestCase):
    def test_evaluate_encodings_returns_stats(self) -> None:
        stats = encoding.evaluate_encodings(
            ROOT / "nytbee_dict.txt", sample_count=2, seed=7
        )
        self.assertEqual({stat.method for stat in stats}, {"length_prefixed", "front_coded", "terminated"})


if __name__ == "__main__":
    unittest.main()

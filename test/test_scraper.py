import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nytbee_scrapper import scraper


class TestScraperParsing(unittest.TestCase):
    def test_extract_answer_list_parses_main_list(self) -> None:
        html = """
        <html>
          <head>
            <style>.ignored {color: red;}</style>
            <script>console.log('ignore');</script>
          </head>
          <body>
            <div id="main-answer-list">
              <ul>
                <li>Apple</li>
                <li>Banana</li>
              </ul>
            </div>
          </body>
        </html>
        """
        items = scraper.extract_answer_list(html)
        self.assertEqual(items, ["Apple", "Banana"])

    def test_normalize_answer_handles_pangram_suffix(self) -> None:
        self.assertEqual(scraper.normalize_answer("Mango Perfect Pangram"), "mango")
        self.assertEqual(scraper.normalize_answer("Berry pangram"), "berry")
        self.assertEqual(scraper.normalize_answer("  Mixed\rCase  "), "mixedcase")


class TestScraperCollectCounts(unittest.TestCase):
    def test_collect_word_counts_tracks_failures(self) -> None:
        starting_date = date(2024, 1, 2)
        base_url = "https://example.com/Bee_{date}.html"

        html_with_answers = """
        <div id="main-answer-list">
          <ul>
            <li>Alpha</li>
            <li>Beta</li>
            <li>Gamma Perfect Pangram</li>
          </ul>
        </div>
        """

        def fake_fetch(url: str, timeout: int = 20) -> str:
            if url.endswith("20240102.html"):
                return html_with_answers
            return "<div id=\"main-answer-list\"></div>"

        with patch.object(scraper, "fetch_html", side_effect=fake_fetch):
            counts, scraped, failures = scraper.collect_word_counts(
                starting_date,
                2,
                base_url=base_url,
            )

        self.assertEqual(counts["alpha"], 1)
        self.assertEqual(counts["beta"], 1)
        self.assertEqual(counts["gamma"], 1)
        self.assertIn(base_url.format(date="20240102"), scraped)
        self.assertEqual(len(failures), 1)
        self.assertIn("No answers extracted", failures[0][1])

    def test_collect_word_counts_rejects_negative_days(self) -> None:
        with self.assertRaises(ValueError):
            scraper.collect_word_counts(date(2024, 1, 1), -1)


if __name__ == "__main__":
    unittest.main()

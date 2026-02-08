from __future__ import annotations

import argparse
from datetime import date
import sys

from .scraper import collect_word_counts


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the scraper CLI."""
    parser = argparse.ArgumentParser(
        description="Scrape NYTBee answer lists and summarize word counts."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to scrape, counting backwards from today (default: 30).",
    )
    return parser


def main() -> None:
    """Run the scraper CLI to collect answer lists from recent days."""
    parser = build_parser()
    args = parser.parse_args()

    def render_progress(target_date: date, current: int, total: int) -> None:
        """Render the progress bar for the current scrape day."""
        if total <= 0:
            return
        bar_width = 30
        completed = int(bar_width * current / total)
        bar = "#" * completed + "-" * (bar_width - completed)
        message = (
            f"\r[{bar}] {current}/{total} "
            f"Processing {target_date.isoformat()}"
        )
        sys.stdout.write(message)
        sys.stdout.flush()
        if current == total:
            sys.stdout.write("\n")

    word_counts, scraped_urls, failed_urls = collect_word_counts(
        starting_date=date.today(),
        days_to_collect=args.days,
        progress_callback=render_progress,
    )

    print(f"Scraped {len(scraped_urls)} days.")
    print(f"Collected {len(word_counts)} unique words.")
    if failed_urls:
        print("Failed URLs:")
        for url, error in failed_urls:
            print(f"- {url}: {error}")


if __name__ == "__main__":
    main()

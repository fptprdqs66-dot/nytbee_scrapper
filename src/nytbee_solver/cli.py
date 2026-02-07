from __future__ import annotations

import argparse
from pathlib import Path

from .solver import get_todays_puzzle_letters, print_hint_page, solve_spelling_bee


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the solver CLI."""
    parser = argparse.ArgumentParser(
        description="Solve NYT Spelling Bee puzzles and print a hint page summary."
    )
    parser.add_argument(
        "letters",
        nargs="?",
        help=(
            "Seven letters with the required letter first. "
            "When omitted, the solver uses today's NYTBee puzzle."
        ),
    )
    parser.add_argument(
        "--wordlist",
        type=Path,
        default=None,
        help="Path to the wordlist file to use instead of the default cache.",
    )
    return parser


def main() -> None:
    """Run the solver CLI and print the Spelling Bee hint page."""
    parser = build_parser()
    args = parser.parse_args()

    letters = args.letters or get_todays_puzzle_letters()
    words, pangrams, cleaned_letters, required = solve_spelling_bee(
        letters, wordlist_path=args.wordlist
    )
    print_hint_page(words, pangrams, cleaned_letters, required)


if __name__ == "__main__":
    main()

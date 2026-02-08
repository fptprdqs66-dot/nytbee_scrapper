from __future__ import annotations

import argparse
import io
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path

from nytbee_solver.encoding import encode_terminated
from nytbee_solver.solver import print_hint_page, solve_spelling_bee
from nytbee_solver.solver import get_todays_puzzle_letters


def _solve_daily_puzzle(
    puzzle_date: date | None = None,
) -> tuple[date, str, list[str], list[str], str, str]:
    resolved_date = puzzle_date or date.today()
    letters = get_todays_puzzle_letters()
    words, pangrams, cleaned_letters, required = solve_spelling_bee(letters)
    return resolved_date, letters, words, pangrams, cleaned_letters, required


def _render_hint_page(words: list[str], pangrams: list[str], letters: str, required: str) -> str:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        print_hint_page(words, pangrams, letters, required)
    return buffer.getvalue()


def generate_daily_results(output_dir: Path, puzzle_date: date | None = None) -> tuple[Path, Path]:
    """Generate today's Spelling Bee results and write them to dated files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    resolved_date, letters, words, pangrams, cleaned_letters, required = _solve_daily_puzzle(
        puzzle_date
    )
    hint_page = _render_hint_page(words, pangrams, cleaned_letters, required)
    output_path = output_dir / f"{resolved_date.isoformat()}.txt"
    output_path.write_text(
        "NYT Spelling Bee Daily Results\n"
        f"Date: {resolved_date.isoformat()}\n"
        f"Letters: {letters}\n\n"
        f"{hint_page}",
        encoding="utf-8",
    )

    encoded_path = output_dir / f"{resolved_date.isoformat()}.encoded.txt"
    encoded_path.write_text(
        encode_terminated(words, cleaned_letters, required),
        encoding="utf-8",
    )
    return output_path, encoded_path


def update_latest_files(output_dir: Path, output_path: Path, encoded_path: Path) -> tuple[Path, Path]:
    """Write latest copies of the hint page and encoded output."""
    latest_hint_path = output_dir / "latest.txt"
    latest_encoded_path = output_dir / "latest.encoded.txt"
    latest_hint_path.write_text(output_path.read_text(encoding="utf-8"), encoding="utf-8")
    latest_encoded_path.write_text(
        encoded_path.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return latest_hint_path, latest_encoded_path


def main() -> None:
    """Generate daily NYT Spelling Bee results for automated workflows."""
    parser = argparse.ArgumentParser(description="Publish daily NYT Spelling Bee results.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results"),
        help="Directory to write daily results files into.",
    )
    args = parser.parse_args()

    output_path, encoded_path = generate_daily_results(args.output_dir)
    update_latest_files(args.output_dir, output_path, encoded_path)
    print(f"Wrote results to {output_path}")
    print(f"Wrote encoded results to {encoded_path}")


if __name__ == "__main__":
    main()

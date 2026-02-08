from __future__ import annotations

import argparse
import io
from contextlib import redirect_stdout
from datetime import date, datetime
from pathlib import Path

from nytbee_solver.solver import print_hint_page, solve_spelling_bee
from nytbee_solver.solver import get_todays_puzzle_letters


def generate_daily_results(output_dir: Path, puzzle_date: date | None = None) -> Path:
    """Generate today's Spelling Bee results and write them to a dated file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    resolved_date = puzzle_date or date.today()
    letters = get_todays_puzzle_letters()
    words, pangrams, cleaned_letters, required = solve_spelling_bee(letters)

    buffer = io.StringIO()
    with redirect_stdout(buffer):
        print_hint_page(words, pangrams, cleaned_letters, required)

    output_path = output_dir / f"{resolved_date.isoformat()}.txt"
    output_path.write_text(
        "NYT Spelling Bee Daily Results\n"
        f"Date: {resolved_date.isoformat()}\n"
        f"Letters: {letters}\n\n"
        f"{buffer.getvalue()}",
        encoding="utf-8",
    )
    return output_path


def update_latest_summary(output_dir: Path, output_path: Path) -> Path:
    """Write a short latest summary markdown file that points to the dated results."""
    latest_path = output_dir / "latest.md"
    relative_path = output_path.name
    latest_path.write_text(
        "# Latest Spelling Bee Results\n\n"
        f"- Updated: {datetime.utcnow().isoformat(timespec='seconds')}Z\n"
        f"- Results file: `{relative_path}`\n",
        encoding="utf-8",
    )
    return latest_path


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

    output_path = generate_daily_results(args.output_dir)
    update_latest_summary(args.output_dir, output_path)
    print(f"Wrote results to {output_path}")


if __name__ == "__main__":
    main()

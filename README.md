# nytbee-scrapper

Scrappy little utilities for scraping and solving the NYT Spelling Bee puzzle.

## Features

- **Scraper utilities**: fetch daily answer lists from NYTBee and build word frequency data.
- **Solver utilities**: load a wordlist, normalize puzzle letters, and generate valid words/pangrams.
- **Notebooks included**: exploratory notebooks for scraping and testing live data.

## Project layout

```
.
├── src/
│   ├── nytbee_scrapper/
│   │   └── scraper.py
│   └── nytbee_solver/
│       └── solver.py
├── nytbee_dict.txt
├── notebooks (*.ipynb)
└── pyproject.toml
```

## Installation

This project uses a standard Python package layout. Install in editable mode:

```bash
python -m pip install -e .
```

## CLI usage

After installation, two console scripts are available: `nytbee-scraper` and `nytbee-solver`.

### `nytbee-scraper`

Scrape recent NYTBee answer lists and print a summary of collected words.

```bash
nytbee-scraper --days 14
```

Arguments:

- `--days`: number of days to scrape counting backwards from today (default: 30).

### `nytbee-solver`

Solve a puzzle from provided letters (required letter first) and print a hint page summary.

```bash
nytbee-solver aregntp
```

If you omit letters, the solver uses today's NYTBee puzzle letters:

```bash
nytbee-solver
```

Use a custom wordlist instead of the default cache:

```bash
nytbee-solver aregntp --wordlist /path/to/wordlist.txt
```

## Scraper usage

The scraper collects answers from `nytbee.com` pages and can build word counts across multiple days.

```python
from datetime import date
from nytbee_scrapper.scraper import collect_word_counts

word_counts, scraped_urls, failed_urls = collect_word_counts(
    starting_date=date.today(),
    days_to_collect=7,
)

print(f"Collected {len(word_counts)} unique words")
print(f"Failed URLs: {failed_urls}")
```

## Solver usage

The solver loads a wordlist and finds valid Spelling Bee words for a set of letters.
The required letter should be first in the input string.

```python
from nytbee_solver.solver import solve_spelling_bee

words, pangrams, letters, required = solve_spelling_bee("aregntp")
print(f"Required letter: {required}")
print(f"Total words: {len(words)}")
print(f"Pangrams: {pangrams}")
```

To infer today's puzzle letters from the NYTBee answer list:

```python
from nytbee_solver.solver import get_todays_puzzle_letters

letters = get_todays_puzzle_letters()
print(letters)
```

## Solving today's puzzle end-to-end

Use the solver to fetch today's letters, solve the puzzle, and print the hint page.

```python
from nytbee_solver.solver import run_today_hint_page

letters = run_today_hint_page()
print(f"Letters: {letters}")
```

## Wordlist notes

The solver defaults to a cached wordlist at `~/.cache/nytbee_solver/nytbee_dict.txt`.
If the file does not exist, it downloads the canonical wordlist from the repository.
You can pass a custom wordlist path to `solve_spelling_bee` when needed.

## Development

- Python 3.9+ recommended.
- Notebooks in the repository showcase scraping experiments and validation checks.

## License

MIT

## JavaScript browser shortcut (auto-type today's answers)

Use `shortcuts/nytbee-autotype-shortcut.js` as a console snippet or bookmarklet helper.

### How to run

1. Open the NYT Spelling Bee game in your browser.
2. Click into the word input so it has focus.
3. Paste the script into the browser DevTools console and run it.

The shortcut fetches today's answer page from `nytbee.com`, extracts the main answer list,
and types each answer followed by Enter into the focused input.

### Typing speed

- Typing is intentionally fast.
- Keystrokes are delayed by `10 ms` between characters and submissions so the game can register input.

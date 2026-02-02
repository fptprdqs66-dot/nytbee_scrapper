from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from urllib.request import urlopen

WORDLIST_URL = (
    "https://raw.githubusercontent.com/fptprdqs66-dot/nytbee_scrapper/refs/heads/main/nytbee_dict.txt"
)


def get_default_wordlist_path() -> Path:
    return Path.home() / ".cache" / "nytbee_solver" / "nytbee_dict.txt"


def ensure_wordlist(path: Path) -> None:
    if path.exists():
        return
    print(f"Wordlist not found at {path}. Downloading from {WORDLIST_URL}...")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urlopen(WORDLIST_URL) as response:
            content = response.read().decode("utf-8")
    except Exception as exc:
        raise FileNotFoundError(
            f"Unable to download wordlist from {WORDLIST_URL}"
        ) from exc
    path.write_text(content)


def load_words(path: Path) -> list[str]:
    ensure_wordlist(path)
    contents = path.read_text().strip()
    if not contents:
        return []
    if contents.lstrip().startswith("{"):
        from ast import literal_eval

        try:
            loaded = literal_eval(contents)
        except (ValueError, SyntaxError):
            loaded = None
        if isinstance(loaded, dict):
            words = [str(key).strip().lower() for key in loaded]
            return [word for word in words if word.isalpha()]

    words = [line.strip().lower() for line in contents.splitlines()]
    return [word for word in words if word.isalpha()]


def normalize_letters(raw_letters: str) -> tuple[str, str]:
    cleaned = [char for char in raw_letters.lower() if char.isalpha()]
    if not cleaned:
        raise ValueError("Please provide the seven Spelling Bee letters.")

    required = cleaned[0]
    unique_letters = []
    seen = set()
    for char in cleaned:
        if char not in seen:
            seen.add(char)
            unique_letters.append(char)

    if len(unique_letters) < 7:
        raise ValueError("Please provide seven unique letters (required letter first).")

    return required, "".join(unique_letters)


def solve_spelling_bee(
    letters: str, wordlist_path: Path | None = None
) -> tuple[list[str], list[str], str, str]:
    required, cleaned_letters = normalize_letters(letters)
    allowed = set(cleaned_letters)

    if wordlist_path is None:
        wordlist_path = get_default_wordlist_path()

    words = [
        word
        for word in load_words(wordlist_path)
        if len(word) >= 4 and required in word and set(word) <= allowed
    ]
    pangrams = [word for word in words if set(cleaned_letters) <= set(word)]
    return sorted(words), sorted(pangrams), cleaned_letters, required


def print_hint_page(words: list[str], pangrams: list[str], letters: str, required: str) -> None:
    print("NYT Spelling Bee Hint Page")
    print("-" * 30)
    print(f"Letters: {', '.join(letters)} (required: {required})")
    print(f"Total words: {len(words)}")
    print(f"Pangrams ({len(pangrams)}): {', '.join(pangrams) if pangrams else 'None'}")

    grouped: dict[int, list[str]] = defaultdict(list)
    for word in words:
        grouped[len(word)].append(word)

    print("\nBy length:")
    for length in sorted(grouped):
        word_list = ", ".join(sorted(grouped[length]))
        print(f"{length} letters ({len(grouped[length])}): {word_list}")

    print("\nAlphabetical:")
    sorted_words = sorted(words)
    if not sorted_words:
        return

    columns = 3
    rows = (len(sorted_words) + columns - 1) // columns
    column_words = [
        sorted_words[start : start + rows]
        for start in range(0, len(sorted_words), rows)
    ]
    while len(column_words) < columns:
        column_words.append([])

    column_widths = [
        max((len(word) for word in column), default=0) for column in column_words
    ]

    for row_index in range(rows):
        row_entries = []
        for col_index in range(columns):
            column = column_words[col_index]
            word = column[row_index] if row_index < len(column) else ""
            padding = column_widths[col_index]
            row_entries.append(word.ljust(padding))
        print("  ".join(entry for entry in row_entries).rstrip())

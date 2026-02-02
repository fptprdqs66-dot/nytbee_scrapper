from __future__ import annotations

from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_BASE_URL = "https://nytbee.com/Bee_{date}.html"
USER_AGENT = "Mozilla/5.0 (compatible; NYTBeeScraper/1.0)"


class MainAnswerListParser(HTMLParser):
    """Extract list items from the main answer list."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._div_depth = 0
        self._target_div_depth: Optional[int] = None
        self._ul_depth = 0
        self._li_stack: list[list[str]] = []
        self._items: list[str] = []
        self._skip_depth = 0

    @property
    def items(self) -> list[str]:
        return self._items

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag in {"script", "style"}:
            self._skip_depth += 1
            return
        if tag == "div":
            self._div_depth += 1
            if self._target_div_depth is None and dict(attrs).get("id") == "main-answer-list":
                self._target_div_depth = self._div_depth
            return
        if self._target_div_depth is None or self._div_depth < self._target_div_depth:
            return
        if tag == "ul":
            self._ul_depth += 1
            return
        if tag == "li" and self._ul_depth:
            self._li_stack.append([])

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if tag == "li" and self._li_stack:
            text = "".join(self._li_stack.pop()).strip()
            if text:
                self._items.append(text)
            return
        if tag == "ul" and self._ul_depth:
            self._ul_depth -= 1
            return
        if tag == "div":
            if self._target_div_depth is not None and self._div_depth == self._target_div_depth:
                self._target_div_depth = None
            if self._div_depth:
                self._div_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth or not self._li_stack:
            return
        self._li_stack[-1].append(data)


def fetch_html(url: str, timeout: int = 20) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def extract_answer_list(html: str) -> list[str]:
    parser = MainAnswerListParser()
    parser.feed(html)
    return [item.replace("\r", "") for item in parser.items]


def normalize_word(item: str) -> str:
    normalized = item.replace("\r", "").strip().lower()
    return "".join(ch for ch in normalized if ch.isalpha())


def load_word_counts(dict_path: Path) -> dict[str, int]:
    word_counts: dict[str, int] = {}
    try:
        contents = dict_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return word_counts

    if not contents:
        return word_counts

    if contents.lstrip().startswith("{"):
        from ast import literal_eval

        try:
            loaded = literal_eval(contents)
        except (ValueError, SyntaxError):
            loaded = None
        if isinstance(loaded, dict):
            return {str(key): int(value) for key, value in loaded.items()}

    words = [line.strip().lower() for line in contents.splitlines()]
    return {word: 1 for word in words if word}


def load_scraped_urls(log_path: Path) -> set[str]:
    try:
        return {line.strip() for line in log_path.read_text(encoding="utf-8").splitlines() if line}
    except FileNotFoundError:
        return set()


def collect_word_counts(
    *,
    starting_date: date,
    days_to_collect: int,
    dict_path: Path,
    log_path: Path,
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = 20,
    progress: bool = True,
) -> tuple[dict[str, int], list[tuple[str, object]]]:
    if days_to_collect < 0:
        raise ValueError("days_to_collect must be non-negative")

    word_counts = load_word_counts(dict_path)
    scraped_urls = load_scraped_urls(log_path)
    failed_urls: list[tuple[str, object]] = []

    iterator = range(days_to_collect)
    if progress:
        try:
            from tqdm import tqdm

            iterator = tqdm(iterator, desc="Collecting", unit="day")
        except ImportError:
            pass

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as log_handle:
        for offset in iterator:
            target_date = starting_date - timedelta(days=offset)
            url = base_url.format(date=target_date.strftime("%Y%m%d"))

            if url in scraped_urls:
                if hasattr(iterator, "set_postfix"):
                    iterator.set_postfix({"status": "skipped", "url": url})
                continue

            if hasattr(iterator, "set_postfix"):
                iterator.set_postfix({"status": "collecting", "url": url})
            try:
                html = fetch_html(url, timeout=timeout)
            except (HTTPError, URLError) as exc:
                failed_urls.append((url, exc))
                if hasattr(iterator, "set_postfix"):
                    iterator.set_postfix({"status": f"failed: {exc}", "url": url})
                continue

            items = extract_answer_list(html)
            if not items:
                failed_urls.append((url, "No answers extracted"))
                if hasattr(iterator, "set_postfix"):
                    iterator.set_postfix({"status": "failed: no answers", "url": url})
                continue

            for item in items:
                word = normalize_word(item)
                if word:
                    word_counts[word] = word_counts.get(word, 0) + 1
            scraped_urls.add(url)
            log_handle.write(f"{url}\n")
            log_handle.flush()
            if hasattr(iterator, "set_postfix"):
                iterator.set_postfix({"status": f"collected {len(items)}", "url": url})

    return word_counts, failed_urls

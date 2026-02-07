from __future__ import annotations

from datetime import date, timedelta
from html.parser import HTMLParser
import re
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = "https://nytbee.com/Bee_{date}.html"
DEFAULT_URL = "https://nytbee.com/Bee_20260130.html"
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


def fetch_html(url: str, timeout: int = 20, user_agent: str = USER_AGENT) -> str:
    request = Request(url, headers={"User-Agent": user_agent})
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def extract_answer_list(html: str) -> list[str]:
    parser = MainAnswerListParser()
    parser.feed(html)
    return [item.replace("\r", "") for item in parser.items]


def normalize_answer(answer: str) -> str:
    """Normalize an answer list entry into a single word string."""
    normalized = answer.replace("\r", "").strip().lower()
    tokens = re.findall(r"[a-z]+", normalized)
    if len(tokens) > 1 and "pangram" in tokens[1:]:
        pangram_index = tokens.index("pangram")
        end_index = pangram_index
        if end_index > 0 and tokens[end_index - 1] == "perfect":
            end_index -= 1
        tokens = tokens[:end_index]
    return "".join(tokens)


def collect_word_counts(
    starting_date: date,
    days_to_collect: int,
    *,
    base_url: str = BASE_URL,
    timeout: int = 20,
    existing_word_counts: Optional[dict[str, int]] = None,
    existing_scraped_urls: Optional[set[str]] = None,
) -> tuple[dict[str, int], set[str], list[tuple[str, object]]]:
    if days_to_collect < 0:
        raise ValueError("days_to_collect must be non-negative")
    word_counts = dict(existing_word_counts or {})
    scraped_urls = set(existing_scraped_urls or set())
    failed_urls: list[tuple[str, object]] = []

    for offset in range(days_to_collect):
        target_date = starting_date - timedelta(days=offset)
        url = base_url.format(date=target_date.strftime("%Y%m%d"))

        if url in scraped_urls:
            continue

        try:
            html = fetch_html(url, timeout=timeout)
        except (HTTPError, URLError) as exc:
            failed_urls.append((url, exc))
            continue

        items = extract_answer_list(html)
        if not items:
            failed_urls.append((url, "No answers extracted"))
            continue

        for item in items:
            word = normalize_answer(item)
            if word:
                word_counts[word] = word_counts.get(word, 0) + 1
        scraped_urls.add(url)

    return word_counts, scraped_urls, failed_urls

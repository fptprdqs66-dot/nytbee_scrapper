#!/usr/bin/env python3
"""Scrape and output content from a NYTBee page."""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_URL = "https://nytbee.com/Bee_20260130.html"
USER_AGENT = "Mozilla/5.0 (compatible; NYTBeeScraper/1.0)"


class TagTextExtractor(HTMLParser):
    """Extract visible text from a specific tag."""

    def __init__(self, tag: str) -> None:
        super().__init__(convert_charrefs=True)
        self.tag = tag
        self.depth = 0
        self._texts: list[str] = []
        self._skip_depth = 0

    @property
    def text(self) -> str:
        lines = [line.strip() for line in "\n".join(self._texts).splitlines()]
        return "\n".join([line for line in lines if line])

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag in {"script", "style"}:
            self._skip_depth += 1
            return
        if tag == self.tag:
            self.depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._skip_depth:
            self._skip_depth -= 1
            return
        if tag == self.tag and self.depth:
            self.depth -= 1

    def handle_data(self, data: str) -> None:
        if self.depth and not self._skip_depth:
            self._texts.append(data)


def fetch_html(url: str, timeout: int = 20) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def extract_content(html: str) -> str:
    for tag in ("main", "body"):
        extractor = TagTextExtractor(tag)
        extractor.feed(html)
        content = extractor.text
        if content:
            return content
    return ""


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape and print page content from NYTBee."
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help="NYTBee page URL to scrape",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="Request timeout in seconds",
    )
    parser.add_argument(
        "--output",
        help="Optional output file path to write extracted text",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    try:
        html = fetch_html(args.url, timeout=args.timeout)
    except HTTPError as exc:
        print(f"HTTP error fetching {args.url}: {exc}")
        return 1
    except URLError as exc:
        print(f"URL error fetching {args.url}: {exc}")
        return 1

    content = extract_content(html)
    if not content:
        print("No content extracted from the page.")
        return 1

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.write("\n")
    else:
        print(content)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import base64
import bz2
import lzma
import random
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from . import solver


class BitWriter:
    """Accumulate values into a packed bit stream."""

    def __init__(self) -> None:
        self._buffer = 0
        self._buffer_bits = 0
        self._bytes = bytearray()

    def write(self, value: int, bits: int) -> None:
        """Write a value using the requested number of bits."""
        if bits <= 0:
            raise ValueError("Bit length must be positive.")
        if value >= (1 << bits) or value < 0:
            raise ValueError("Value out of range for bit length.")
        self._buffer = (self._buffer << bits) | value
        self._buffer_bits += bits
        while self._buffer_bits >= 8:
            shift = self._buffer_bits - 8
            self._bytes.append((self._buffer >> shift) & 0xFF)
            self._buffer_bits -= 8
            self._buffer &= (1 << shift) - 1 if shift else 0

    def finish(self) -> bytes:
        """Flush any remaining bits into the byte stream."""
        if self._buffer_bits:
            self._bytes.append(self._buffer << (8 - self._buffer_bits))
            self._buffer = 0
            self._buffer_bits = 0
        return bytes(self._bytes)


class BitReader:
    """Read values from a packed bit stream."""

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._position = 0
        self._buffer = 0
        self._buffer_bits = 0

    def read(self, bits: int) -> int:
        """Read the next value with the requested bit length."""
        if bits <= 0:
            raise ValueError("Bit length must be positive.")
        while self._buffer_bits < bits:
            if self._position >= len(self._data):
                raise EOFError("Not enough data to read the requested bits.")
            self._buffer = (self._buffer << 8) | self._data[self._position]
            self._buffer_bits += 8
            self._position += 1
        shift = self._buffer_bits - bits
        value = (self._buffer >> shift) & ((1 << bits) - 1)
        self._buffer_bits -= bits
        self._buffer &= (1 << shift) - 1 if shift else 0
        return value


def _b64encode(data: bytes) -> str:
    encoded = base64.urlsafe_b64encode(data).decode("ascii")
    return encoded.rstrip("=")


def _b64decode(data: str) -> bytes:
    padding = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _build_letter_map(letters: str) -> dict[str, int]:
    return {letter: index for index, letter in enumerate(letters)}


def _validate_words(words: Iterable[str], letters: str, required: str) -> list[str]:
    allowed = set(letters)
    cleaned = []
    for word in words:
        normalized = word.strip().lower()
        if len(normalized) < 4:
            raise ValueError("Words must be at least 4 letters long.")
        if required not in normalized:
            raise ValueError("Words must include the required letter.")
        if not normalized.isalpha():
            raise ValueError("Words must use letters a-z only.")
        if set(normalized) - allowed:
            raise ValueError("Words must only use the puzzle letters.")
        cleaned.append(normalized)
    return cleaned


def encode_length_prefixed(words: Iterable[str], letters: str, required: str) -> str:
    """Encode words with length prefixes and 3-bit letter packing."""
    cleaned = _validate_words(words, letters, required)
    letter_map = _build_letter_map(letters)
    writer = BitWriter()
    writer.write(len(cleaned), 12)
    for word in cleaned:
        length = len(word)
        if length < 4 or length > 35:
            raise ValueError("Word length out of supported range (4-35).")
        writer.write(length - 4, 5)
        for char in word:
            writer.write(letter_map[char], 3)
    return _b64encode(writer.finish())


def decode_length_prefixed(payload: str, letters: str, required: str) -> list[str]:
    """Decode length-prefixed words packed with 3-bit letters."""
    reader = BitReader(_b64decode(payload))
    total = reader.read(12)
    words = []
    for _ in range(total):
        length = reader.read(5) + 4
        chars = [letters[reader.read(3)] for _ in range(length)]
        word = "".join(chars)
        words.append(word)
    return _validate_words(words, letters, required)


def encode_front_coded(words: Iterable[str], letters: str, required: str) -> str:
    """Encode words using front coding against the previous entry."""
    cleaned = sorted(_validate_words(words, letters, required))
    letter_map = _build_letter_map(letters)
    writer = BitWriter()
    writer.write(len(cleaned), 12)
    previous = ""
    for word in cleaned:
        common = 0
        for a, b in zip(previous, word):
            if a != b:
                break
            common += 1
        common = min(common, 15)
        suffix = word[common:]
        if len(suffix) > 31:
            raise ValueError("Suffix too long for front-coded encoding.")
        writer.write(common, 4)
        writer.write(len(suffix), 5)
        for char in suffix:
            writer.write(letter_map[char], 3)
        previous = word
    return _b64encode(writer.finish())


def decode_front_coded(payload: str, letters: str, required: str) -> list[str]:
    """Decode front-coded words packed with 3-bit letters."""
    reader = BitReader(_b64decode(payload))
    total = reader.read(12)
    words: list[str] = []
    previous = ""
    for _ in range(total):
        common = reader.read(4)
        suffix_length = reader.read(5)
        suffix = [letters[reader.read(3)] for _ in range(suffix_length)]
        word = previous[:common] + "".join(suffix)
        words.append(word)
        previous = word
    return _validate_words(words, letters, required)


def encode_terminated(words: Iterable[str], letters: str, required: str) -> str:
    """Encode words as 3-bit letters with a terminator symbol."""
    return _b64encode(_encode_terminated_bytes(words, letters, required))


def encode_terminated_lzma(words: Iterable[str], letters: str, required: str) -> str:
    """Encode words with terminators and LZMA-compress the payload."""
    raw_bytes = _encode_terminated_bytes(words, letters, required)
    compressed = lzma.compress(raw_bytes)
    return _b64encode(compressed)


def decode_terminated(payload: str, letters: str, required: str) -> list[str]:
    """Decode words packed with 3-bit letters plus a terminator symbol."""
    reader = BitReader(_b64decode(payload))
    total = reader.read(12)
    words = []
    current: list[str] = []
    while len(words) < total:
        value = reader.read(3)
        if value == 7:
            word = "".join(current)
            words.append(word)
            current = []
        else:
            current.append(letters[value])
    return _validate_words(words, letters, required)


def decode_terminated_lzma(payload: str, letters: str, required: str) -> list[str]:
    """Decode LZMA-compressed, terminated word payloads."""
    compressed = _b64decode(payload)
    raw_bytes = lzma.decompress(compressed)
    reader = BitReader(raw_bytes)
    total = reader.read(12)
    words = []
    current: list[str] = []
    while len(words) < total:
        value = reader.read(3)
        if value == 7:
            word = "".join(current)
            words.append(word)
            current = []
        else:
            current.append(letters[value])
    return _validate_words(words, letters, required)


def _encode_terminated_bytes(words: Iterable[str], letters: str, required: str) -> bytes:
    cleaned = _validate_words(words, letters, required)
    letter_map = _build_letter_map(letters)
    writer = BitWriter()
    writer.write(len(cleaned), 12)
    for word in cleaned:
        for char in word:
            writer.write(letter_map[char], 3)
        writer.write(7, 3)
    return writer.finish()


@dataclass
class EncodingStats:
    """Capture size statistics for encoding approaches."""

    method: str
    average_chars: float
    average_ratio: float


@dataclass
class CompressionStats:
    """Capture size statistics for compression approaches."""

    method: str
    average_chars: float
    average_ratio: float


def evaluate_encodings(
    wordlist_path: Path,
    sample_count: int = 50,
    seed: int = 1337,
) -> list[EncodingStats]:
    """Compare encoding sizes across random puzzles using the solver routine."""
    random.seed(seed)
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    methods = [
        ("length_prefixed", encode_length_prefixed),
        ("front_coded", encode_front_coded),
        ("terminated", encode_terminated),
    ]
    totals = {name: 0 for name, _ in methods}
    ratios = {name: 0.0 for name, _ in methods}

    for _ in range(sample_count):
        letters = "".join(random.sample(alphabet, 7))
        required = letters[0]
        words, _, _, _ = solver.solve_spelling_bee(letters, wordlist_path=wordlist_path)
        raw_payload = ",".join(words)
        raw_length = max(len(raw_payload), 1)
        for name, encoder in methods:
            encoded = encoder(words, letters, required)
            totals[name] += len(encoded)
            ratios[name] += len(encoded) / raw_length

    stats = []
    for name, _ in methods:
        stats.append(
            EncodingStats(
                method=name,
                average_chars=totals[name] / sample_count,
                average_ratio=ratios[name] / sample_count,
            )
        )
    return stats


def evaluate_terminated_compression(
    wordlist_path: Path,
    sample_count: int = 50,
    seed: int = 1337,
) -> list[CompressionStats]:
    """Compare compressing terminated payloads with simple compressors."""
    random.seed(seed)
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    compressors = [
        ("terminated", lambda data: data),
        ("terminated+zlib", zlib.compress),
        ("terminated+bz2", bz2.compress),
        ("terminated+lzma", lzma.compress),
    ]
    totals = {name: 0 for name, _ in compressors}
    ratios = {name: 0.0 for name, _ in compressors}

    for _ in range(sample_count):
        letters = "".join(random.sample(alphabet, 7))
        required = letters[0]
        words, _, _, _ = solver.solve_spelling_bee(letters, wordlist_path=wordlist_path)
        raw_bytes = _encode_terminated_bytes(words, letters, required)
        raw_length = len(_b64encode(raw_bytes)) or 1
        for name, compressor in compressors:
            compressed = compressor(raw_bytes)
            encoded = _b64encode(compressed)
            totals[name] += len(encoded)
            ratios[name] += len(encoded) / raw_length

    stats = []
    for name, _ in compressors:
        stats.append(
            CompressionStats(
                method=name,
                average_chars=totals[name] / sample_count,
                average_ratio=ratios[name] / sample_count,
            )
        )
    return stats

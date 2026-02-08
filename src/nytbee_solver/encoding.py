from __future__ import annotations

import base64
from typing import Iterable


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


def encode_terminated(words: Iterable[str], letters: str, required: str) -> str:
    """Encode words as 3-bit letters with a terminator symbol."""
    return _b64encode(_encode_terminated_bytes(words, letters, required))


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

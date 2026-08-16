"""A readable Recursive Character Splitter implementation for learning."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RecursiveSplitter:
    chunk_size: int = 512
    overlap: int = 128
    separators: tuple[str, ...] = ("\n\n", "\n", "。", "！", "？", "；", "，", " ", "")

    def __post_init__(self) -> None:
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.overlap < 0 or self.overlap >= self.chunk_size:
            raise ValueError("overlap must be in [0, chunk_size)")
        if not self.separators or self.separators[-1] != "":
            raise ValueError("separators must end with an empty string")

    def split(self, text: str) -> list[str]:
        normalized = "\n".join(line.rstrip() for line in text.strip().splitlines()).strip()
        if not normalized:
            return []
        units = self._recursive_units(normalized, 0)
        return self._pack_with_overlap(units)

    def _recursive_units(self, text: str, separator_index: int) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]

        separator = self.separators[separator_index]
        if separator == "":
            return [text[start : start + self.chunk_size] for start in range(0, len(text), self.chunk_size)]

        pieces = self._split_preserving_separator(text, separator)
        if len(pieces) == 1:
            return self._recursive_units(text, separator_index + 1)

        units: list[str] = []
        next_index = min(separator_index + 1, len(self.separators) - 1)
        for piece in pieces:
            if len(piece) <= self.chunk_size:
                units.append(piece)
            else:
                units.extend(self._recursive_units(piece, next_index))
        return units

    @staticmethod
    def _split_preserving_separator(text: str, separator: str) -> list[str]:
        pieces: list[str] = []
        start = 0
        while True:
            position = text.find(separator, start)
            if position < 0:
                if start < len(text):
                    pieces.append(text[start:])
                break
            end = position + len(separator)
            pieces.append(text[start:end])
            start = end
        return pieces

    def _pack_with_overlap(self, units: list[str]) -> list[str]:
        base_chunks: list[str] = []
        current = ""
        for unit in units:
            if len(unit) > self.chunk_size:
                if current:
                    base_chunks.append(current)
                    current = ""
                base_chunks.extend(
                    unit[start : start + self.chunk_size]
                    for start in range(0, len(unit), self.chunk_size)
                )
                continue

            if current and len(current) + len(unit) > self.chunk_size:
                base_chunks.append(current)
                current = ""
            current += unit

        if current:
            base_chunks.append(current)

        # Add context only after base chunks are stable. Trimming the tail when
        # needed guarantees that overlap can never violate chunk_size.
        chunks: list[str] = []
        for index, chunk in enumerate(base_chunks):
            prefix = base_chunks[index - 1][-self.overlap :] if index and self.overlap else ""
            available = max(0, self.chunk_size - len(chunk))
            prefix = prefix[-available:] if available else ""
            chunks.append((prefix + chunk).strip())
        return [chunk for chunk in chunks if chunk]

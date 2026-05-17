from __future__ import annotations

from typing import Optional

import numpy as np

TT_DTYPE = np.dtype(
    [
        ("depth", np.uint8),
        (
            "score",
            np.int16,
        ),
        ("flag", np.uint8),
    ]
)

FLAG_EXACT = np.uint8(0)
FLAG_LOWER = np.uint8(1)
FLAG_UPPER = np.uint8(2)


class TranspositionTable:
    def __init__(self) -> None:
        self._table: dict[int, np.void] = {}

    def probe(
        self,
        key: int,
        depth: int,
        alpha: int,
        beta: int,
    ) -> Optional[int]:
        """
        Return a cached score if we have a sufficiently deep entry, else None.

        depth  - the depth we are about to search to
        alpha  - current lower bound
        beta   - current upper bound
        """
        entry = self._table.get(key)
        if entry is None or int(entry["depth"]) < depth:
            return None

        if int(entry["flag"]) == FLAG_EXACT:
            return int(entry["score"])

        if int(entry["flag"]) == FLAG_LOWER and int(entry["score"]) >= beta:
            return int(entry["score"])  # real score >= beta -> cut off

        if int(entry["flag"]) == FLAG_UPPER and int(entry["score"]) <= alpha:
            return int(entry["score"])  # real score <= alpha -> cut off

        return None

    def store(self, key: int, depth: int, score: int, flag: int | np.uint8) -> None:
        existing = self._table.get(key)
        if existing is not None and int(existing["depth"]) > depth:
            return  # keep the deeper entry

        entry = np.zeros(1, dtype=TT_DTYPE)[0]
        entry["depth"] = depth
        entry["flag"] = flag
        entry["score"] = score
        self._table[key] = entry

    def clear(self) -> None:
        self._table.clear()

    def __len__(self) -> int:
        return len(self._table)

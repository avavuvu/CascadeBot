from __future__ import annotations

from typing import Optional

import numpy as np

from ..actions.generator import ACTION_DTYPE

# Each entry stores the search result plus the best move that produced it.
# has_move=0 means no move is stored (e.g. an all-node / FLAG_UPPER entry).
TT_DTYPE = np.dtype(
    [
        ("depth", np.uint8),
        ("score", np.int16),
        ("flag", np.uint8),
        ("has_move", np.uint8),
        ("move_type", np.uint8),
        ("move_coord", np.int8),
        ("move_direction", np.int8),
        ("move_source", np.int8),
        ("move_dest_count", np.uint8),
    ]
)

FLAG_EXACT = np.uint8(0)
FLAG_LOWER = np.uint8(1)  # score is a lower bound  (cut-node / beta cutoff)
FLAG_UPPER = np.uint8(2)  # score is an upper bound (all-node  / no improvement)


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

    def get_best_move(self, key: int) -> Optional[np.void]:
        """Return the best move stored for this position, or None.

        The returned value is an np.void with ACTION_DTYPE fields so it can be
        compared directly against entries in a generated action array.
        """
        entry = self._table.get(key)
        if entry is None or not int(entry["has_move"]):
            return None

        move = np.zeros(1, dtype=ACTION_DTYPE)[0]
        move["type"] = entry["move_type"]
        move["coord"] = entry["move_coord"]
        move["direction"] = entry["move_direction"]
        move["source"] = entry["move_source"]
        move["dest_count"] = entry["move_dest_count"]
        return move

    def store(
        self,
        key: int,
        depth: int,
        score: int,
        flag: int | np.uint8,
        best_move: Optional[np.void] = None,
    ) -> None:
        existing = self._table.get(key)
        if existing is not None and int(existing["depth"]) > depth:
            return  # keep the deeper entry

        entry = np.zeros(1, dtype=TT_DTYPE)[0]
        entry["depth"] = depth
        entry["flag"] = flag
        entry["score"] = score

        if best_move is not None:
            entry["has_move"] = np.uint8(1)
            entry["move_type"] = best_move["type"]
            entry["move_coord"] = best_move["coord"]
            entry["move_direction"] = best_move["direction"]
            entry["move_source"] = best_move["source"]
            entry["move_dest_count"] = best_move["dest_count"]

        self._table[key] = entry

    def clear(self) -> None:
        self._table.clear()

    def __len__(self) -> int:
        return len(self._table)

from dataclasses import dataclass
from enum import Enum, auto

from referee.game import Action


class TTFlag(Enum):
    EXACT = auto()
    LOWERBOUND = auto()
    UPPERBOUND = auto()


@dataclass(slots=True)
class TTEntry:
    depth: int
    value: float
    flag: TTFlag
    best_action: Action | None  # move that produced this value (move-ordering hint)


class TranspositionTable:
    """Fast dict-backed transposition table.

    Entries are replaced only when the new search depth is >= the stored
    depth, keeping the highest-quality (deepest) information.
    """

    def __init__(self) -> None:
        self._data: dict[int, TTEntry] = {}

    def __len__(self) -> int:
        return len(self._data)

    def probe(
        self,
        h: int,
        depth: int,
        alpha: float,
        beta: float,
    ) -> tuple[float | None, Action | None]:
        """Look up hash *h*.

        Returns ``(value, best_action)`` where:
          - *value* is non-None only when the entry is deep enough **and** its
            flag lets us use the value as a definitive answer in the current
            alpha/beta window.
          - *best_action* is always returned when the entry exists so the caller
            can prioritise that move even when the value itself cannot be used.

        Note: if the hash hit came from a D4-symmetric board, best_action will
        be in the wrong coordinate frame and simply won't appear in the legal
        moves list — it is silently ignored by _order_moves_enhanced.
        """
        entry = self._data.get(h)
        if entry is None:
            return None, None

        best_action = entry.best_action

        if entry.depth < depth:
            # Shallower result — usable only as a move-ordering hint
            return None, best_action

        if entry.flag is TTFlag.EXACT:
            return entry.value, best_action
        if entry.flag is TTFlag.LOWERBOUND and entry.value >= beta:
            return entry.value, best_action
        if entry.flag is TTFlag.UPPERBOUND and entry.value <= alpha:
            return entry.value, best_action

        return None, best_action

    def store(
        self,
        h: int,
        depth: int,
        value: float,
        flag: TTFlag,
        best_action: Action | None = None,
    ) -> None:
        """Store or replace an entry.

        Deeper entries take precedence — we never overwrite a high-quality
        result with a shallower one.
        """
        existing = self._data.get(h)
        if existing is None or existing.depth <= depth:
            self._data[h] = TTEntry(depth, value, flag, best_action)

    def clear(self) -> None:
        self._data.clear()

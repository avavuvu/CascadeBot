"""
Zobrist random number table.

Kept in its own module so that board.py can import it without creating a
circular dependency (board ← keys, zobrist ← board + keys is fine).

Layout:  TABLE[square, color_index, height]
  square      : 0-63
  color_index : 0 = RED (piece byte & 0x10), 1 = BLUE (piece byte & 0x20)
  height      : 0-15  (bits 0-3 of the piece byte)
"""

import numpy as np

_rng = np.random.default_rng(seed=12345678)

TABLE: np.ndarray = _rng.integers(
    low=0, high=np.iinfo(np.int64).max, size=(64, 2, 16), dtype=np.int64
)

# XOR this in whenever it is BLUE's turn to move.
SIDE_KEY: int = int(_rng.integers(0, np.iinfo(np.int64).max, dtype=np.int64))

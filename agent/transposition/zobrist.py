import numpy as np

from ..player_color import PlayerColor
from .keys import SIDE_KEY, TABLE


def piece_key(square: int, piece: int) -> int:
    """Return the Zobrist contribution of a single piece on a single square."""
    color_idx = 0 if (piece & PlayerColor.RED.value) else 1
    height = piece & 0x0F
    return int(TABLE[square, color_idx, height])


def calculate_zobrist(board: np.ndarray, color: PlayerColor) -> int:
    """Compute the Zobrist hash for a board position from scratch."""
    key = np.int64(0)
    for pos in np.flatnonzero(board != 0):
        key ^= TABLE[
            pos,
            0 if (board[pos] & PlayerColor.RED.value) else 1,
            board[pos] & 0x0F,
        ]
    if color == PlayerColor.BLUE:
        key ^= SIDE_KEY
    return int(key)

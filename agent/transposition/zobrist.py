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


# def calculate_zobrist(board: np.ndarray, color: PlayerColor):
#     def flip_h(a):
#         return np.fliplr(a.reshape(8, 8)).ravel()

#     def flip_v(a):
#         return np.flipud(a.reshape(8, 8)).ravel()

#     def rot90_cw(a):
#         return np.rot90(a.reshape(8, 8), k=-1).ravel()

#     def rot90_ccw(a):
#         return np.rot90(a.reshape(8, 8), k=1).ravel()

#     def rot180(a):
#         return np.rot90(a.reshape(8, 8), k=2).ravel()

#     def transpose(a):
#         return a.reshape(8, 8).T.ravel()

#     def anti_transpose(a):
#         return np.rot90(a.reshape(8, 8), k=2).T.ravel()

#     transpositions = [
#         _calculate_individual_zobrist(b, color)
#         for b in [
#             board,
#             flip_h(board),
#             flip_v(board),
#             rot90_cw(board),
#             rot90_ccw(board),
#             rot180(board),
#             transpose(board),
#             anti_transpose(board),
#         ]
#     ]

#     return min(transpositions)

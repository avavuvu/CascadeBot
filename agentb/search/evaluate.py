import numpy as np

from ..board import Board
from ..player_color import PlayerColor

_MAX_DIST = 14
_MAX_EDGE_DIST = 3


def evaluate(board: Board, color: PlayerColor) -> int:
    our_material = _count_material(board, color)
    opp_material = _count_material(board, color.opponent())
    material_eval = our_material - opp_material

    pieces = int(np.sum(board.board & np.uint8(0x0F)))
    if pieces == 0:
        return material_eval * 10

    # Scales from 0 (all pieces on board) → 1 (pieces have been taken)
    endgame_weight = 1.0 - pieces / 24.0

    positional = _winning_eval(board, color)
    # if material_eval > 0:
    # else:
    #     positional = _losing_eval(board, color)

    return material_eval * 10 + int(positional * endgame_weight)


def _count_material(board: Board, color: PlayerColor) -> int:
    color_mask = np.uint8(color.value)
    my_squares = np.flatnonzero(board.board & color_mask)
    return int(np.sum(board.board[my_squares] & np.uint8(0x0F)))


def _winning_eval(board: Board, color: PlayerColor) -> float:

    our_mask = np.uint8(color.value)
    opp_mask = np.uint8(color.opponent().value)

    our_squares = np.flatnonzero(board.board & our_mask)
    opp_squares = np.flatnonzero(board.board & opp_mask)

    if len(our_squares) == 0 or len(opp_squares) == 0:
        return 0.0

    our_heights = (board.board[our_squares] & np.uint8(0x0F)).astype(np.float32)
    opp_heights = (board.board[opp_squares] & np.uint8(0x0F)).astype(np.float32)

    our_rows, our_cols = np.divmod(our_squares, 8)
    opp_rows, opp_cols = np.divmod(opp_squares, 8)

    dist = np.abs(our_rows[:, None] - opp_rows[None, :]) + np.abs(
        our_cols[:, None] - opp_cols[None, :]
    )

    can_eat = our_heights[:, None] > opp_heights[None, :]

    eat_dist = np.where(can_eat, dist, _MAX_DIST + 1).min(axis=1)
    gen_dist = dist.min(axis=1)
    has_target = can_eat.any(axis=1)

    target_dist = np.where(has_target, eat_dist, gen_dist).clip(0, _MAX_DIST)

    scores = (_MAX_DIST - target_dist) * our_heights
    return float(scores.sum()) / float(our_heights.sum())


def _losing_eval(board: Board, color: PlayerColor) -> float:

    our_mask = np.uint8(color.value)
    our_squares = np.flatnonzero(board.board & our_mask)

    if len(our_squares) > 1:
        return _consolidate_eval(board, our_squares)
    else:
        return _edge_pressure_eval(board, color)


def _consolidate_eval(board: Board, our_squares: np.ndarray) -> float:

    n = len(our_squares)
    if n <= 1:
        return 0.0

    our_heights = (board.board[our_squares] & np.uint8(0x0F)).astype(np.float32)
    our_rows, our_cols = np.divmod(our_squares, 8)

    dist = (
        np.abs(our_rows[:, None] - our_rows[None, :])
        + np.abs(our_cols[:, None] - our_cols[None, :])
    ).astype(np.float32)

    proximity = (_MAX_DIST - dist) * our_heights[:, None] * our_heights[None, :]
    np.fill_diagonal(proximity, 0.0)  # exclude self-pairs

    total_h_sq = float(our_heights.sum()) ** 2
    if total_h_sq == 0:
        return 0.0
    return float(proximity.sum()) / total_h_sq


def _edge_pressure_eval(board: Board, color: PlayerColor) -> float:
    opp_mask = np.uint8(color.opponent().value)
    opp_squares = np.flatnonzero(board.board & opp_mask)

    if len(opp_squares) == 0:
        return 0.0

    opp_heights = (board.board[opp_squares] & np.uint8(0x0F)).astype(np.float32)
    opp_rows, opp_cols = np.divmod(opp_squares, 8)

    edge_dist = np.minimum(
        np.minimum(opp_rows, 7 - opp_rows),
        np.minimum(opp_cols, 7 - opp_cols),
    ).astype(np.float32)

    scores = (_MAX_EDGE_DIST - edge_dist) * opp_heights
    raw = float(scores.sum()) / float(opp_heights.sum())  # [0, MAX_EDGE_DIST]

    return raw * (_MAX_DIST / _MAX_EDGE_DIST)

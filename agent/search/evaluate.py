import numpy as np

from ..board import Board
from ..piece import Piece
from ..player_color import PlayerColor


def evaluate(board: Board, color: PlayerColor) -> int:
    red_eval = _count_material(board, color)
    blue_eval = _count_material(board, color.opponent())

    eval = red_eval - blue_eval

    pieces = int(np.sum(board.board & np.uint8(0x0F)))
    percentage = 24 / pieces

    endgame_weight = 1 - percentage

    engame_eval = int(_endgame_distance_eval(board, color) * endgame_weight)

    return (eval * (-1 if color == PlayerColor.BLUE else 1)) + engame_eval


def _count_material(board: Board, color: PlayerColor) -> int:
    color_mask = np.uint8(color.value)

    my_squares = np.flatnonzero(board.board & color_mask)
    heights = board.board & np.uint8(0x0F)
    my_heights = heights[my_squares]

    return int(np.sum(my_heights))


def _endgame_distance_eval(board: Board, color: PlayerColor):
    color_mask = np.uint8(color.opponent().value)

    opp_squares = np.flatnonzero(board.board & color_mask)
    distances = []
    for i in opp_squares:
        height = Piece.get_height(board.board[i])
        row, col = divmod(int(i), 8)

        distToCenterRow = max(3 - row, row - 4)
        distToCenterCol = max(3 - col, col - 4)
        distance = distToCenterCol + distToCenterRow

        distances.append(distance / height)

    return sum(distances)

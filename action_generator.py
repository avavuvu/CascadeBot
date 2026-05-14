import numpy as np

from agent.actions.generator import (
    # decode_action,
    # format_action,
    generate_legal_actions,
)

# from agent.actions.types import CASCADE_ACTION, EAT_ACTION, MOVE_ACTION
from agent.board import Board
from agent.piece import Piece
from agent.player_color import PlayerColor

board = Board()
board.board[25] = Piece.BLUE.of_height(4)
board.board[26] = Piece.RED.of_height(4)
board.board[26 + 8] = Piece.RED.of_height(4)


def action_generator(depth=6, color=PlayerColor.RED):
    if depth == 0:
        return 1

    actions = generate_legal_actions(board, color)

    positions = 0

    for i in actions:
        board.make_move(i, color)
        positions += action_generator(depth - 1, color.opponent())
        board.unmake_move()

    return positions


print(action_generator())

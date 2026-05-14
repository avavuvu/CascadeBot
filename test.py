import math
import time

from agent.actions.generator import format_action
from agent.board import Board
from agent.piece import Piece
from agent.player_color import PlayerColor
from agent.search.search import get_best_move


def test():
    board = Board()

    board.board[4] = Piece.of(4, PlayerColor.BLUE)
    board.board[5] = Piece.of(4, PlayerColor.BLUE)
    board.board[32] = Piece.of(4, PlayerColor.BLUE)
    board.board[56] = Piece.of(4, PlayerColor.BLUE)

    board.board[2] = Piece.of(4, PlayerColor.RED)
    board.board[19] = Piece.of(4, PlayerColor.RED)
    board.board[33] = Piece.of(4, PlayerColor.RED)
    board.board[56] = Piece.of(4, PlayerColor.RED)

    start = time.perf_counter()
    move = get_best_move(board, PlayerColor.BLUE, 6)
    elapsed = time.perf_counter() - start

    if move is None:
        print("move is None, likely error")
        return

    print(board)
    print(format_action(move))
    print(f"Time: {elapsed:.3f}s")


test()

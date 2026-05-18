import time

import numpy as np

from agent.actions.generator import format_action
from agent.board import Board
from agent.player_color import PlayerColor
from agent.search.search import get_best_move
from agent.transposition.table import TranspositionTable


def parse_board(path: str) -> Board:
    """Parse a board text file into a Board object.

    Format (8x8, space-separated tokens):
        R6  →  RED  piece of height 6  (encoded as 0x10 | 6)
        B3  →  BLUE piece of height 3  (encoded as 0x20 | 3)
        .   →  empty square            (encoded as 0)
    """
    board = Board()

    with open(path) as f:
        lines = [l.strip() for l in f if l.strip()]

    if len(lines) != 8:
        raise ValueError(f"Expected 8 rows, got {len(lines)} in {path!r}")

    for row, line in enumerate(lines):
        tokens = line.split()
        if len(tokens) != 8:
            raise ValueError(f"Expected 8 columns on row {row}, got {len(tokens)}")

        for col, token in enumerate(tokens):
            idx = row * 8 + col
            if token == ".":
                board.board[idx] = np.uint8(0)
            elif token[0] in ("R", "B") and token[1:].isdigit():
                color_bit = 0x10 if token[0] == "R" else 0x20
                height = int(token[1:])
                board.board[idx] = np.uint8(color_bit | height)
            else:
                raise ValueError(f"Unrecognised token {token!r} at ({row},{col})")

    # Mark the board as being in the move phase (past all place turns).
    board._turn = Board.PLACE_TURNS

    return board


def test_from_file(path: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"Test: {path}")
    print("=" * 60)

    board = parse_board(path)
    print(board)

    for color in (PlayerColor.RED, PlayerColor.BLUE):
        played_table: dict[int, int] = {}
        trans_table = TranspositionTable()

        start = time.perf_counter()
        action, score = get_best_move(
            board,
            color,
            played_table,
            trans_table,
            time_remaining=5.0,
            max_depth=30,
        )
        elapsed = time.perf_counter() - start

        print(
            f"{color.name:4s}  best={score:+6d}  {format_action(action)}  ({elapsed:.3f}s)"
        )


if __name__ == "__main__":
    test_from_file("agent/tests/1.txt")

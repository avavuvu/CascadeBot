import numpy as np

from agent.actions.types import CASCADE_ACTION, EAT_ACTION, MOVE_ACTION, PLACE_ACTION
from agent.piece import Piece

from .player_color import PlayerColor


def _is_valid_step(pos: int, direction: int) -> bool:
    """Return True if pos + direction stays inside the 8x8 board."""
    if direction == 8:
        return pos < 56  # South: not on last rank
    if direction == -8:
        return pos >= 8  # North: not on first rank
    if direction == 1:
        return pos % 8 < 7  # East:  not on last file
    if direction == -1:
        return pos % 8 > 0  # West:  not on first file
    return False


def _push_stack(board: np.ndarray, pos: int, direction: int) -> None:
    if not _is_valid_step(pos, direction):
        board[pos] = 0
        return
    next_pos = pos + direction
    if board[next_pos] != 0:
        _push_stack(board, next_pos, direction)
    board[next_pos] = board[pos]
    board[pos] = 0


class Board:
    def __init__(self):
        self.board = np.zeros(64, dtype=np.uint8)

        self._history: list[np.ndarray] = []

    def make_move(self, action: np.void, color: PlayerColor):

        self._history.append(self.board.copy())

        if int(action["type"]) == int(CASCADE_ACTION):
            source = int(action["source"])
            direction = int(action["direction"])
            dest_count = int(action["dest_count"])

            self.board[source] = 0

            token = np.uint8(color.value | 1)

            for i in range(1, dest_count + 1):
                dest = source + i * direction
                if self.board[dest] != 0:
                    _push_stack(self.board, dest, direction)
                self.board[dest] = token

        elif int(action["type"]) == int(MOVE_ACTION):
            source = int(action["source"])
            coord = int(action["coord"])

            height = Piece.get_height(self.board[coord]) + Piece.get_height(
                self.board[source]
            )
            self.board[coord] = Piece.of(height, color)
            self.board[source] = 0

        elif int(action["type"]) == int(EAT_ACTION):
            source = int(action["source"])
            coord = int(action["coord"])

            self.board[coord] = self.board[source]
            self.board[source] = 0

        elif int(action["type"]) == int(PLACE_ACTION):
            coord = int(action["coord"])

            self.board[coord] = Piece.of(4, color)

    def unmake_move(self) -> bool:
        if not self._history:
            return False
        self.board[:] = self._history.pop()
        return True

    def is_color(self, index: int, color: PlayerColor) -> bool:
        return self.board[index] & color.value != 0

    def is_occupied(self, index: int) -> bool:
        return self.board[index] != 0

    def __str__(self) -> str:
        output = ""
        for row in range(8):
            for col in range(8):
                cell = self.board[row * 8 + col]
                if cell & PlayerColor.RED.value:
                    output += f"R{cell & 0x0F} ".ljust(4)

                elif cell & PlayerColor.BLUE.value:
                    output += f"B{cell & 0x0F} ".ljust(4)
                else:
                    output += ".   "
            output += "\n"
        return output

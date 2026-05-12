from dataclasses import dataclass

from referee.game import Coord, Direction, PlayerColor

type Board = dict[Coord, CellState]

BOARD_N = 8


@dataclass(frozen=True, slots=True)
class CellState:
    """
    A structure representing the state of a cell on the game board. A cell can
    be empty or contain a stack of tokens of a given player colour and height.
    """

    color: PlayerColor | None = None
    height: int = 0

    def __post_init__(self):
        if self.color is None and self.height != 0:
            raise ValueError("Empty cell cannot have non-zero height")
        if self.color is not None and self.height <= 0:
            raise ValueError("Stack must have positive height")

    @property
    def is_empty(self) -> bool:
        return self.color is None

    @property
    def is_stack(self) -> bool:
        return self.color is not None

    def __str__(self):
        if self.is_empty:
            return "."
        color_char = "R" if self.color == PlayerColor.RED else "B"
        return f"{color_char}{self.height}"

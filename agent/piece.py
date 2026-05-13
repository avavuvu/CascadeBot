from enum import Enum

from .player_color import PlayerColor


class Piece(Enum):
    RED = 0x10  # bit 4
    BLUE = 0x20  # bit 5

    def of_height(self, height: int) -> int:
        return self.value | height

    @staticmethod
    def of(height: int, color: PlayerColor) -> int:
        return color.value | height

    @staticmethod
    def is_equal_color(piece: int, color: PlayerColor) -> bool:
        return piece & color.value != 0

    @staticmethod
    def get_height(piece: int) -> int:
        return piece & 0x0F

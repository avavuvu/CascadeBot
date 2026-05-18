from enum import Enum


class PlayerColor(Enum):
    RED = 0x10  # bit 4
    BLUE = 0x20  # bit 5

    def opponent(self) -> "PlayerColor":
        match self:
            case PlayerColor.RED:
                return PlayerColor.BLUE
            case PlayerColor.BLUE:
                return PlayerColor.RED

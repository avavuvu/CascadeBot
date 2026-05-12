from referee.game import PlayerColor

from ..types import Board


def consolidation(board: Board, player: PlayerColor) -> float:
    """
    (own average stack height) - (opponent average stack height)
    """

    def avg_height(color: PlayerColor) -> float:
        stacks = [s for s in board.values() if s.color == color]
        if not stacks:
            return 0.0
        return sum(s.height for s in stacks) / len(stacks)

    return avg_height(player) - avg_height(player.opponent)

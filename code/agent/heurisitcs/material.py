from referee.game import Action, Coord, Direction, PlayerColor

from ..types import Board, CellState


def material(board: Board, player: PlayerColor) -> float:
    """
    Own total height minus opponent's total height.
    The most fundamental metric: raw material on the board.
    """
    own = sum(s.height for s in board.values() if s.color == player)
    opp = sum(s.height for s in board.values() if s.color == player.opponent)
    return float(own - opp)

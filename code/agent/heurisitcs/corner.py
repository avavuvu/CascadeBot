from referee.game import Action, Coord, Direction, PlayerColor

from ..types import Board, CellState


# For cornering a piece in an endgame
def corner(board: Board, player: PlayerColor) -> float:
    opp = 0.0

    for coord, state in board.items():
        if state.color is None:
            continue
        dist = abs(coord.r - 3.5) + abs(coord.c - 3.5)

        if state.color != player:
            opp += dist

    return opp

from referee.game import Action, Coord, Direction, PlayerColor

from ..types import Board, CellState


def center(board: Board, player: PlayerColor) -> float:
    own = 0.0
    opp = 0.0

    for coord, state in board.items():
        if state.color is None:
            continue
        dist = abs(coord.r - 3.5) + abs(coord.c - 3.5)
        val = (7.0 - dist) * state.height
        if state.color == player:
            own += val
        else:
            opp += val
    return own - opp

from referee.game.actions import (
    Action,
    CascadeAction,
    Coord,
    Direction,
    EatAction,
    MoveAction,
)
from referee.game.player import PlayerColor

from .types import Board, CellState


def get_legal_placements(color: PlayerColor, board: Board):
    legal_placements = list(board.keys())

    ## just get oppposing colors
    for coord, state in board.items():
        if state.color is None:
            continue

        if coord in legal_placements:
            legal_placements.remove(coord)

        if state.color != color:
            for _, neighbor in _neighbors(coord):
                if neighbor in legal_placements:
                    legal_placements.remove(neighbor)

    return legal_placements


def get_legal_moves(color: PlayerColor, board: Board) -> list[Action]:
    actions: list[Action] = []

    same_color_cells = [cell for cell in board.items() if cell[1].color == color]

    for coord, state in same_color_cells:
        actions.extend(_move_eat_actions(board, color, coord, state))
        actions.extend(_cascade_actions(board, color, coord, state))
    return actions


def is_at_edge(coord: Coord, direction: Direction):
    return (direction in (Direction.Up, Direction.Down) and coord.r in (0, 7)) or (
        direction in (Direction.Left, Direction.Right) and coord.c in (0, 7)
    )


def _neighbors(coord: Coord) -> list[tuple[Direction, Coord]]:
    result = []
    for d in [Direction.Left, Direction.Up, Direction.Right, Direction.Down]:
        try:
            result.append((d, coord + d))
        except ValueError:
            pass
    return result


def _move_eat_actions(
    board: Board, color: PlayerColor, coord: Coord, state: CellState
) -> list[Action]:
    actions: list[Action] = []
    for direction, neighbour in _neighbors(coord):
        neighbour_state = board.get(neighbour)
        if neighbour_state is None or neighbour_state.color is None:
            actions.append(MoveAction(coord, direction))

        elif neighbour_state.color != color:
            if state.height >= neighbour_state.height:
                actions.append(EatAction(coord, direction))

        elif neighbour_state.color == color:
            actions.append(MoveAction(coord, direction))

    return actions


def _cascade_actions(
    board: Board, color: PlayerColor, coord: Coord, state: CellState
) -> list[Action]:
    actions: list[Action] = []
    if state.height < 2:
        return actions

    H = state.height
    for direction in (Direction.Up, Direction.Down, Direction.Left, Direction.Right):
        dr = direction.value.r
        dc = direction.value.c

        hits_opponent = False
        knocks_opponent_off = False
        pieces_seen = 0

        for step in range(1, H + 1):
            r = coord.r + dr * step
            c = coord.c + dc * step
            if not (0 <= r < 8 and 0 <= c < 8):
                break

            cell = board.get(Coord(r, c))
            if cell is None or cell.color is None:
                continue  # empty cell — keep scanning

            landing_r = coord.r + dr * (H + 1 + pieces_seen)
            landing_c = coord.c + dc * (H + 1 + pieces_seen)
            off_board = not (0 <= landing_r < 8 and 0 <= landing_c < 8)
            pieces_seen += 1

            if cell.color == color.opponent:
                hits_opponent = True
                if off_board:
                    knocks_opponent_off = True

        if knocks_opponent_off or hits_opponent:
            actions.append(CascadeAction(coord, direction))

    return actions

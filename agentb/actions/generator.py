import numpy as np

from ..board import Board
from ..direction import DIR_STEPS, EDGE_DIST_TABLE, NEIGHBOR_TABLE
from ..player_color import PlayerColor
from .types import (
    CASCADE_ACTION,
    EAT_ACTION,
    MOVE_ACTION,
    PLACE_ACTION,
    Action,
    CascadeAction,
    EatAction,
    MoveAction,
    PlaceAction,
)

ACTION_DTYPE = np.dtype(
    [
        ("type", np.uint8),
        ("coord", np.int8),
        ("direction", np.int8),
        ("source", np.int8),
        ("dest_count", np.uint8),
    ]
)


_DIR_SYMBOLS = {-8: "↑", 8: "↓", 1: "→", -1: "←"}
_DIR_NAMES = {-8: "North", 8: "South", 1: "East", -1: "West"}
_ACTION_NAMES = {0: "MOVE", 1: "EAT", 2: "CASCADE", 3: "PLACE"}


def _square(index: int) -> str:
    row, col = divmod(int(index), 8)
    return f"({row},{col})"


def format_action(action: np.void) -> str:
    t = int(action["type"])
    source = int(action["source"])
    coord = int(action["coord"])
    direction = int(action["direction"])

    type_name = _ACTION_NAMES.get(t, f"UNKNOWN({t})")
    dir_symbol = _DIR_SYMBOLS.get(direction, f"?({direction})")
    dir_name = _DIR_NAMES.get(direction, f"?({direction})")

    if t == PLACE_ACTION:
        return f"PLACE     -> {_square(coord)}"
    elif t == CASCADE_ACTION:
        dests = get_cascade_destinations(action)
        dest_str = " -> ".join(_square(d) for d in dests)
        return f"CASCADE   {_square(source)} {dir_symbol} {dir_name}  [{dest_str}]"
    else:
        return f"{type_name:<8}  {_square(source)} {dir_symbol} {dir_name}  -> {_square(coord)}"


def print_actions(actions: np.ndarray) -> None:
    for i, a in enumerate(actions):
        print(f"[{i:>3}] {format_action(a)}")


def decode_action(row: np.void) -> Action:
    action_type = int(row["type"])
    source = int(row["source"])
    coord = int(row["coord"])
    direction = int(row["direction"])

    if action_type == PLACE_ACTION:
        return PlaceAction(coord=coord)
    elif action_type == MOVE_ACTION:
        return MoveAction(source=source, dest=coord, direction=direction)
    elif action_type == EAT_ACTION:
        return EatAction(source=source, dest=coord, direction=direction)
    elif action_type == CASCADE_ACTION:
        dest_count = int(row["dest_count"])
        dests = tuple(source + i * direction for i in range(1, dest_count + 1))
        return CascadeAction(source=source, direction=direction, destinations=dests)
    else:
        raise ValueError(f"Unknown action type: {action_type}")


def get_cascade_destinations(action: np.void) -> np.ndarray:
    return int(action["source"]) + np.arange(1, int(action["dest_count"]) + 1) * int(
        action["direction"]
    )


def _generate_place_actions(board: Board) -> np.ndarray:
    empty_squares = np.flatnonzero(board.board == 0)
    neighbors = NEIGHBOR_TABLE[empty_squares]

    safe_squares = empty_squares[~np.any(board.board[neighbors] != 0, axis=1)]

    n = len(safe_squares)
    actions = np.empty(n, dtype=ACTION_DTYPE)
    actions["type"] = PLACE_ACTION
    actions["coord"] = safe_squares.astype(np.int8)
    actions["source"] = np.int8(0)
    actions["direction"] = np.int8(0)
    actions["dest_count"] = np.uint8(0)
    return actions


def generate_legal_actions(board: Board, color: PlayerColor) -> np.ndarray:
    if board.is_place_phase:
        return _generate_place_actions(board)

    color_mask = np.uint8(color.value)

    my_squares = np.flatnonzero(board.board & color_mask)
    if len(my_squares) == 0:
        return np.empty(0, dtype=ACTION_DTYPE)

    heights = board.board & np.uint8(0x0F)
    my_heights = heights[my_squares]

    neighbor_index = NEIGHBOR_TABLE[my_squares]
    edge_distance = EDGE_DIST_TABLE[my_squares]

    valid = neighbor_index >= 0

    safe_index = np.where(valid, neighbor_index, np.int8(0))
    neighbor_val = board.board[safe_index]

    empty = (neighbor_val == 0) & valid
    friendly = ((neighbor_val & color_mask) != 0) & valid
    enemy = (~empty) & (~friendly) & valid
    eat_ok = enemy & (my_heights[:, None] >= (neighbor_val & np.uint8(0x0F)))

    move_mask = (empty | friendly) & valid
    eat_mask = eat_ok
    cascade_mask = (my_heights[:, None] > np.uint8(1)) & valid

    move_pi, move_di = np.where(move_mask)
    eat_pi, eat_di = np.where(eat_mask)
    casc_pi, casc_di = np.where(cascade_mask)

    n_move, n_eat, n_casc = len(move_pi), len(eat_pi), len(casc_pi)
    total = n_move + n_eat + n_casc

    actions = np.empty(total, dtype=ACTION_DTYPE)

    # Move actions
    if n_move:
        sl = slice(0, n_move)
        actions["type"][sl] = MOVE_ACTION
        actions["coord"][sl] = neighbor_index[move_pi, move_di]
        actions["direction"][sl] = DIR_STEPS[move_di]
        actions["source"][sl] = my_squares[move_pi]
        actions["dest_count"][sl] = np.uint8(0)

    # Eat actions
    if n_eat:
        sl = slice(n_move, n_move + n_eat)
        actions["type"][sl] = EAT_ACTION
        actions["coord"][sl] = neighbor_index[eat_pi, eat_di]
        actions["direction"][sl] = DIR_STEPS[eat_di]
        actions["source"][sl] = my_squares[eat_pi]
        actions["dest_count"][sl] = np.uint8(0)

    # Cascade actions
    if n_casc:
        sl = slice(n_move + n_eat, total)
        source_edges = edge_distance[casc_pi, casc_di]
        actions["type"][sl] = CASCADE_ACTION
        actions["coord"][sl] = neighbor_index[casc_pi, casc_di]
        actions["direction"][sl] = DIR_STEPS[casc_di]
        actions["source"][sl] = my_squares[casc_pi]
        actions["dest_count"][sl] = np.minimum(source_edges, my_heights[casc_pi])

    return actions

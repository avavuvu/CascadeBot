# COMP30024 Artificial Intelligence, Semester 1 2026
# Project Part B: Game Playing Agent
#
import numpy as np

from referee.game import (
    Action as RAction,
)
from referee.game import (
    CascadeAction as RCascadeAction,
)
from referee.game import (
    Coord as RCoord,
)
from referee.game import (
    Direction as RDirection,
)
from referee.game import (
    EatAction as REatAction,
)
from referee.game import (
    MoveAction as RMoveAction,
)
from referee.game import (
    PlaceAction as RPlaceAction,
)
from referee.game import PlayerColor as RPlayerColor

from .actions.generator import ACTION_DTYPE, format_action
from .actions.types import (
    CASCADE_ACTION,
    EAT_ACTION,
    MOVE_ACTION,
    PLACE_ACTION,
)
from .board import Board
from .direction import EDGE_DIST_TABLE
from .player_color import PlayerColor
from .search.search import get_best_move

# Maps between the referee's Direction enum and the agent's flat-board step ints.
# Agent steps: North=-8, South=+8, East=+1, West=-1 (row-major 8x8 board)
_DIR_TO_INT: dict[RDirection, int] = {
    RDirection.Up: -8,
    RDirection.Down: 8,
    RDirection.Left: -1,
    RDirection.Right: 1,
}
_INT_TO_DIR: dict[int, RDirection] = {v: k for k, v in _DIR_TO_INT.items()}
# Index into DIR_STEPS / EDGE_DIST_TABLE columns: N=0, S=1, E=2, W=3
_DIR_IDX: dict[int, int] = {-8: 0, 8: 1, 1: 2, -1: 3}


class Agent:
    """
    This class is the "entry point" for your agent, providing an interface to
    respond to various Cascade game events.
    """

    def __init__(self, color: RPlayerColor, **referee: dict):
        """
        This constructor method runs when the referee instantiates the agent.
        Any setup and/or precomputation should be done here.
        """
        self._color = PlayerColor.RED if color == RPlayerColor.RED else PlayerColor.BLUE
        self._turn_count = 0
        self._board = Board()

    def action(self, **referee: dict) -> RAction:
        """
        This method is called by the referee each time it is the agent's turn
        to take an action. It must always return an action object.
        """

        action = get_best_move(self._board, self._color, 4)

        if action is None:
            raise Exception("Likely error: Action is none")

        return convert_action_from_agent_to_referee(action)

    def update(self, color: RPlayerColor, action: RAction, **referee: dict):
        """
        This method is called by the referee after a player has taken their
        turn. You should use it to update the agent's internal game state.
        """
        match color:
            case RPlayerColor.BLUE:
                if self._color == PlayerColor.BLUE:
                    self._turn_count += 1
            case RPlayerColor.RED:
                if self._color == PlayerColor.RED:
                    self._turn_count += 1

        action_color = (
            PlayerColor.RED if color == RPlayerColor.RED else PlayerColor.BLUE
        )

        agent_aciton = convert_action_from_referee_to_agent(action, self._board)

        print(format_action(agent_aciton))

        self._board.make_move(agent_aciton, action_color)


def _make_np_action(
    action_type: int | np.unsignedinteger,
    coord: int,
    source: int,
    direction: int,
    dest_count: int,
) -> np.void:
    row = np.zeros(1, dtype=ACTION_DTYPE)
    row["type"] = action_type
    row["coord"] = coord
    row["source"] = source
    row["direction"] = direction
    # fixing bug during grading, not sure if best fix
    row["dest_count"] = max(dest_count, 0)
    return row[0]


def convert_action_from_referee_to_agent(action: RAction, board: Board) -> np.void:
    """Convert a referee action into the agent's internal np.void representation.

    A `board` (before the move is applied) is required so that CascadeAction
    dest_count can be derived from the source piece's height.
    """
    match action:
        case RPlaceAction(coord=coord):
            return _make_np_action(PLACE_ACTION, coord.r * 8 + coord.c, 0, 0, 0)

        case RMoveAction(coord=coord, direction=direction):
            source = coord.r * 8 + coord.c
            dir_int = _DIR_TO_INT[direction]
            return _make_np_action(MOVE_ACTION, source + dir_int, source, dir_int, 0)

        case REatAction(coord=coord, direction=direction):
            source = coord.r * 8 + coord.c
            dir_int = _DIR_TO_INT[direction]
            return _make_np_action(EAT_ACTION, source + dir_int, source, dir_int, 0)

        case RCascadeAction(coord=coord, direction=direction):
            source = coord.r * 8 + coord.c
            dir_int = _DIR_TO_INT[direction]
            height = int(board.board[source] & 0x0F)
            edge_dist = int(EDGE_DIST_TABLE[source, _DIR_IDX[dir_int]])
            dest_count = min(height, edge_dist)
            return _make_np_action(
                CASCADE_ACTION, source + dir_int, source, dir_int, dest_count
            )

        case _:
            raise ValueError(f"Unknown referee action type: {action}")


def convert_action_from_agent_to_referee(action: np.void) -> RAction:
    action_type = int(action["type"])
    source = int(action["source"])
    coord = int(action["coord"])
    direction = int(action["direction"])

    if action_type == PLACE_ACTION:
        return RPlaceAction(coord=RCoord(coord // 8, coord % 8))

    elif action_type == MOVE_ACTION:
        return RMoveAction(
            coord=RCoord(source // 8, source % 8),
            direction=_INT_TO_DIR[direction],
        )

    elif action_type == EAT_ACTION:
        return REatAction(
            coord=RCoord(source // 8, source % 8),
            direction=_INT_TO_DIR[direction],
        )

    elif action_type == CASCADE_ACTION:
        return RCascadeAction(
            coord=RCoord(source // 8, source % 8),
            direction=_INT_TO_DIR[direction],
        )

    raise ValueError(f"Unknown agent action type: {action_type}")

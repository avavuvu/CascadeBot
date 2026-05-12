from referee.game import (
    Action,
    CascadeAction,
    Coord,
    Direction,
    EatAction,
    MoveAction,
    PlaceAction,
    PlayerColor,
)

# from vis.thoughts import format_move, send_thoughts
from .data import get_updated_board
from .distance import manhattan
from .legal_moves import get_legal_moves, get_legal_placements
from .minimax import evaluate_breakdown, get_action, get_action_iterative
from .transposition import TranspositionTable
from .types import Board, CellState


class Agent:
    def __init__(self, color: PlayerColor, **referee: dict):
        self._color = color
        self._turn_count = 0
        self.board_state: Board = {
            Coord(r, c): CellState(None, 0) for r in range(8) for c in range(8)
        }
        self._tt: TranspositionTable | None = None  # persists across turns
        super()

    def action(self, **referee: dict) -> Action:
        if self._turn_count < 4:
            places = get_legal_placements(self._color, self.board_state)
            places.sort(key=lambda a: manhattan(a, Coord(4, 4)))
            # top5 = []
            # for i, p in enumerate(places[:5]):
            #     act = PlaceAction(p)
            #     score = -manhattan(p, Coord(4, 4))
            #     new_board = get_updated_board(self.board_state, self._color, act)
            #     bd = evaluate_breakdown(new_board, self._color)
            #     top5.append(format_move(i + 1, act, score, bd))
            # # send_thoughts(self._color, self._turn_count, top5)
            return PlaceAction(places[0])

        pieces_left = sum(cell.height for cell in self.board_state.values())

        if pieces_left < 10:
            depth = 15
        elif pieces_left < 13:
            depth = 8
        else:
            depth = 5

        best_action, top5_scored = get_action(self._color, self.board_state, depth)
        # thoughts = [
        #     format_move(rank + 1, act, score, bd)
        #     for rank, (act, score, bd) in enumerate(top5_scored)
        # ]
        # send_thoughts(self._color, self._turn_count, thoughts)
        return best_action

    def update(self, color: PlayerColor, action: Action, **referee: dict):
        self.board_state = get_updated_board(self.board_state, color, action)
        if color == self._color:
            self._turn_count += 1


def json_encode(board: Board, color: PlayerColor, action: Action):
    board = get_updated_board(board, color, action)
    match action:
        case PlaceAction(coord):
            print(f"Testing: {color} played PLACE action at {coord}")
        case MoveAction(coord, direction):
            print(f"Testing: {color} played MOVE action:")
            print(f"  Coord: {coord}")
            print(f"  Direction: {direction}")
        case EatAction(coord, direction):
            print(f"Testing: {color} played EAT action:")
            print(f"  Coord: {coord}")
            print(f"  Direction: {direction}")
        case CascadeAction(coord, direction):
            print(f"Testing: {color} played CASCADE action:")
            print(f"  Coord: {coord}")
            print(f"  Direction: {direction}")
        case _:
            raise ValueError(f"Unknown action type: {action}")

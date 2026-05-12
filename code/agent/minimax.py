import math
import time

from referee.game import Action, Coord, Direction, PlayerColor
from referee.game.actions import CascadeAction, EatAction

from .data import get_updated_board, is_winner
from .heurisitcs.center import center
from .heurisitcs.consolidation import consolidation
from .heurisitcs.corner import corner
from .heurisitcs.material import material
from .legal_moves import get_legal_moves
from .transposition import TranspositionTable, TTFlag
from .types import Board
from .zobrist import board_hash

DEBUG = False


class _SearchTimeout(Exception):
    """Raised internally when the search deadline is exceeded."""


def _debug(*args):
    if DEBUG:
        print(*args)


def _neighbors(coord: Coord) -> list[tuple[Direction, Coord]]:
    result = []
    for d in (Direction.Left, Direction.Up, Direction.Right, Direction.Down):
        try:
            result.append((d, coord + d))
        except ValueError:
            pass
    return result


def _pieces_on_board(board: Board) -> tuple[int, int]:
    stacks = [s for s in board.items() if s[1].color is not None]
    pieces = sum(state.height for _, state in stacks)
    return len(stacks), pieces


def _components(board: Board, player: PlayerColor) -> dict[str, float]:
    """
    All evaluation components from `player`'s perspective.
    Every value follows the convention: positive = good for player.
    """
    return {
        "material": material(board, player),
        "center": center(board, player),
        "consolidation": consolidation(board, player),
        "corner": corner(board, player),
    }


_WEIGHTS_NORMAL: dict[str, float] = {
    "material": 10.0,
    "center": 0.05,
    "consolidation": 0.5,
    "corner": 0.0,
}

_WEIGHTS_ENDGAME: dict[str, float] = {
    "material": 10.0,
    "center": 0.0,
    "consolidation": 0.0,
    "corner": 2.0,
}


def evaluate_breakdown(board: Board, player: PlayerColor) -> dict[str, float]:
    """Round each component for visualiser display."""
    return {k: round(v, 2) for k, v in _components(board, player).items()}


def _interpolate_weights(endgame_percent: float) -> dict[str, float]:
    t = 1.0 - endgame_percent
    return {
        k: _WEIGHTS_NORMAL[k] + t * (_WEIGHTS_ENDGAME[k] - _WEIGHTS_NORMAL[k])
        for k in _WEIGHTS_NORMAL
    }


def _evaluate(board: Board, player: PlayerColor) -> float:
    stacks, pieces = _pieces_on_board(board)
    endgame_percent = pieces / 24
    w = _interpolate_weights(endgame_percent)
    c = _components(board, player)
    return sum(w[k] * c[k] for k in w)


def _order_moves(moves: list[Action]) -> list[Action]:
    """Basic structural ordering: Eat > Cascade > others."""

    def priority(action: Action) -> int:
        if isinstance(action, EatAction):
            return 0
        if isinstance(action, CascadeAction):
            return 1
        return 2

    return sorted(moves, key=priority)


def _order_moves_enhanced(
    moves: list[Action],
    killers: list[Action | None],
    history: dict[str, int],
    tt_move: Action | None = None,
) -> list[Action]:
    """
    Order moves using TT hint, type priority, killer moves, and history.

    Priority (ascending = tried first):
      -1  TT move (best move from a previous search of this node)
       0  EatAction (captures)
       1  CascadeAction
       2  Killer moves
       3  Quiet moves, sorted by history score (descending)

    If tt_move is from a D4-symmetric board it won't match any legal move and
    is silently ignored by the sort.
    """

    def priority(action: Action) -> tuple[int, int]:
        if action == tt_move:
            return (-1, 0)
        if isinstance(action, EatAction):
            return (0, 0)
        if isinstance(action, CascadeAction):
            return (1, 0)
        if action in killers:
            return (2, 0)
        return (3, -history.get(str(action), 0))

    return sorted(moves, key=priority)


def _record_cutoff(
    action: Action,
    depth: int,
    killers: list[list[Action | None]] | None,
    history: dict[str, int] | None,
) -> None:
    """Update the killer table and history heuristic when a cutoff occurs."""
    if killers is not None and depth < len(killers):
        if not isinstance(action, EatAction) and action != killers[depth][0]:
            killers[depth][1] = killers[depth][0]
            killers[depth][0] = action
    if history is not None:
        key = str(action)
        history[key] = history.get(key, 0) + depth * depth


def _alphabeta(
    board: Board,
    h: int,
    maximizing_player: PlayerColor,
    current_player: PlayerColor,
    alpha: float,
    beta: float,
    depth: int,
    deadline: float | None = None,
    killers: list[list[Action | None]] | None = None,
    history: dict[str, int] | None = None,
    tt: TranspositionTable | None = None,
) -> float:
    # ── Time check ────────────────────────────────────────────────────────────
    if deadline is not None and time.monotonic() > deadline:
        raise _SearchTimeout()

    # ── Terminal checks ───────────────────────────────────────────────────────
    winner = is_winner(board)
    if winner is not None:
        return 100.0 if winner == maximizing_player else -100.0

    moves = get_legal_moves(current_player, board)
    if depth == 0 or not moves:
        return _evaluate(board, maximizing_player)

    # ── Transposition table probe ─────────────────────────────────────────────
    original_alpha = alpha
    tt_move: Action | None = None
    if tt is not None:
        tt_value, tt_move = tt.probe(h, depth, alpha, beta)
        if tt_value is not None:
            _debug(f"[TT HIT] depth={depth} value={tt_value:.2f}")
            return tt_value

    # ── Move ordering ─────────────────────────────────────────────────────────
    if killers is not None and history is not None:
        depth_killers: list[Action | None] = (
            killers[depth] if depth < len(killers) else [None, None]
        )
        moves = _order_moves_enhanced(moves, depth_killers, history, tt_move)
    else:
        moves = _order_moves(moves)

    best_action: Action | None = None

    if current_player == maximizing_player:
        # ── MAX node ──────────────────────────────────────────────────────────
        value = -math.inf
        for action in moves:
            new_board = get_updated_board(board, current_player, action)
            child_h = board_hash(new_board, current_player.opponent)
            child_val = _alphabeta(
                new_board,
                child_h,
                maximizing_player,
                current_player.opponent,
                alpha,
                beta,
                depth - 1,
                deadline,
                killers,
                history,
                tt,
            )
            _debug(
                f"[MAX] depth={depth} child={child_val:.2f} a={alpha:.2f} b={beta:.2f}"
            )
            if child_val > value:
                value = child_val
                best_action = action
            alpha = max(alpha, value)
            if alpha >= beta:
                _record_cutoff(action, depth, killers, history)
                break  # beta cutoff

    else:
        # ── MIN node ──────────────────────────────────────────────────────────
        value = math.inf
        for action in moves:
            new_board = get_updated_board(board, current_player, action)
            child_h = board_hash(new_board, current_player.opponent)
            child_val = _alphabeta(
                new_board,
                child_h,
                maximizing_player,
                current_player.opponent,
                alpha,
                beta,
                depth - 1,
                deadline,
                killers,
                history,
                tt,
            )
            _debug(
                f"[MIN] depth={depth} child={child_val:.2f} a={alpha:.2f} b={beta:.2f}"
            )
            if child_val < value:
                value = child_val
                best_action = action
            beta = min(beta, value)
            if beta <= alpha:
                _record_cutoff(action, depth, killers, history)
                break  # alpha cutoff

    # ── Transposition table store ─────────────────────────────────────────────
    if tt is not None:
        if value <= original_alpha:
            flag = TTFlag.UPPERBOUND
        elif value >= beta:
            flag = TTFlag.LOWERBOUND
        else:
            flag = TTFlag.EXACT
        tt.store(h, depth, value, flag, best_action)

    return value


def _get_action_at_depth(
    current_player: PlayerColor,
    board: Board,
    h: int,
    depth: int,
    deadline: float,
    moves: list[Action],
    killers: list[list[Action | None]],
    history: dict[str, int],
    tt: TranspositionTable,
) -> tuple[Action, list[tuple[Action, float, dict[str, float]]]]:
    """
    Single alpha-beta pass at a fixed depth.
    Raises _SearchTimeout if the deadline is hit mid-search — the caller
    should discard these partial results and keep the previous depth's answer.
    """
    best_action: Action | None = None
    best_value = -math.inf
    alpha = -math.inf
    scored: list[tuple[Action, float, dict[str, float]]] = []

    # TT move hint at root: value can't be used (open window) but move is gold
    _, tt_move = tt.probe(h, depth, alpha, math.inf)
    if tt_move is not None and tt_move in moves:
        moves = [tt_move] + [m for m in moves if m != tt_move]

    for action in moves:
        new_board = get_updated_board(board, current_player, action)
        child_h = board_hash(new_board, current_player.opponent)
        value = _alphabeta(
            new_board,
            child_h,
            current_player,
            current_player.opponent,
            alpha,
            math.inf,
            depth - 1,
            deadline,
            killers,
            history,
            tt,
        )
        _debug(f"[ROOT d={depth}] value={value:.2f} action={action}")
        scored.append((action, value, evaluate_breakdown(new_board, current_player)))
        if value > best_value:
            best_value = value
            best_action = action
        alpha = max(alpha, best_value)

    # Root always gets EXACT — it searched the full window
    if best_action is not None:
        tt.store(h, depth, best_value, TTFlag.EXACT, best_action)

    top5 = sorted(scored, key=lambda x: x[1], reverse=True)[:5]
    return best_action or moves[0], top5


def get_action_iterative(
    current_player: PlayerColor,
    board: Board,
    time_limit: float = 20.0,
    max_depth: int = 15,
    tt: TranspositionTable | None = None,
) -> tuple[Action, list[tuple[Action, float, dict[str, float]]], TranspositionTable]:
    moves = _order_moves(get_legal_moves(current_player, board))
    if not moves:
        raise ValueError("No legal moves available")

    if tt is None:
        tt = TranspositionTable()

    h = board_hash(board, current_player)
    best_action: Action = moves[0]
    best_top5: list[tuple[Action, float, dict[str, float]]] = []
    deadline = time.monotonic() + time_limit

    # History persists across iterations for cumulative signal
    history: dict[str, int] = {}

    for depth in range(1, max_depth + 1):
        if time.monotonic() >= deadline:
            break

        # Fresh killers each iteration — shallower entries are unreliable deeper
        killers: list[list[Action | None]] = [[None, None] for _ in range(depth + 1)]

        try:
            action, top5 = _get_action_at_depth(
                current_player, board, h, depth, deadline, moves, killers, history, tt
            )
            best_action = action
            best_top5 = top5
            # Promote best move to front for next iteration
            moves = [best_action] + [m for m in moves if m != best_action]
            _debug(
                f"[IDDFS] completed depth={depth} best={best_action} tt_size={len(tt)}"
            )
        except _SearchTimeout:
            _debug(
                f"[IDDFS] timeout at depth={depth}, keeping depth={depth - 1} result"
            )
            break

    return best_action, best_top5, tt


def get_action(
    current_player: PlayerColor, board: Board, depth: int
) -> tuple[Action, list[tuple[Action, float, dict[str, float]]]]:
    """Fixed-depth alpha-beta (fallback / comparison baseline)."""
    moves = _order_moves(get_legal_moves(current_player, board))

    best_action: Action | None = None
    best_value = -math.inf
    alpha = -math.inf
    scored: list[tuple[Action, float, dict[str, float]]] = []

    for action in moves:
        new_board = get_updated_board(board, current_player, action)
        child_h = board_hash(new_board, current_player.opponent)
        value = _alphabeta(
            new_board,
            child_h,
            current_player,
            current_player.opponent,
            alpha,
            math.inf,
            depth - 1,
        )
        _debug(f"[ROOT] value={value:.2f} action={action}")
        scored.append((action, value, evaluate_breakdown(new_board, current_player)))
        if value > best_value:
            best_value = value
            best_action = action
        alpha = max(alpha, best_value)

    top5 = sorted(scored, key=lambda x: x[1], reverse=True)[:5]
    return (best_action or moves[0], top5)

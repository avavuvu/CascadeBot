import time

import numpy as np

from ..actions.generator import generate_legal_actions
from ..board import Board
from ..player_color import PlayerColor
from ..search.order_moves import _order_place_actions, order_moves
from ..transposition.table import (
    FLAG_EXACT,
    FLAG_LOWER,
    FLAG_UPPER,
    TranspositionTable,
)
from ..transposition.zobrist import calculate_zobrist
from .evaluate import evaluate

INF = 30_000


def _prepend_tt_move(actions: np.ndarray, tt_move: np.void) -> np.ndarray:
    if len(actions) == 0:
        return actions

    tt_type = int(tt_move["type"])
    tt_src = int(tt_move["source"])
    tt_coord = int(tt_move["coord"])
    tt_dir = int(tt_move["direction"])

    for idx in range(len(actions)):
        a = actions[idx]
        if (
            int(a["type"]) == tt_type
            and int(a["source"]) == tt_src
            and int(a["coord"]) == tt_coord
            and int(a["direction"]) == tt_dir
        ):
            if idx == 0:
                return actions  # already first, nothing to do
            return np.concatenate(
                [
                    actions[idx : idx + 1],
                    actions[:idx],
                    actions[idx + 1 :],
                ]
            )

    return actions  # TT move not in current legal list – stale entry, ignore


def get_best_move(
    board: Board,
    color: PlayerColor,
    played_table: dict[int, int],
    trans_table: TranspositionTable,
    time_remaining: float = 60.0,
    max_depth: int = 30,
) -> tuple[np.void, int]:
    actions = generate_legal_actions(board, color)
    if len(actions) == 0:
        raise Exception("Likely error: Action is none")

    if board.is_place_book:
        place_actions = _order_place_actions(actions, board, color)
        return place_actions[0], 0

    time_budget = max(0.5, min(time_remaining / 5.0, 30.0))
    start = time.monotonic()

    best_action = actions[0]
    best_score = -INF

    depth = 1
    while True:
        iteration_start = time.monotonic()
        iterations_best_action = best_action  # fallback if all moves are skipped
        iterations_best_score = -INF

        for action in actions:
            board.make_move(action, color)

            key = calculate_zobrist(board.board, color)
            times_played_before = played_table.get(key, 0)

            if times_played_before == 2:
                # Avoid threefold repetition LIKE THE PLAGUE
                board.unmake_move()
                continue

            score = -_search(
                board,
                -INF,
                -iterations_best_score,
                key,
                played_table,
                trans_table,
                color.opponent(),
                depth - 1,
            )
            board.unmake_move()

            if score > iterations_best_score:
                iterations_best_score = score
                iterations_best_action = action

        if iterations_best_score > best_score:
            best_action = iterations_best_action
            best_score = iterations_best_score

        iteration_time = time.monotonic() - iteration_start
        elapsed = time.monotonic() - start

        if depth >= max_depth:
            break

        if elapsed + iteration_time * 6 > time_budget:
            break

        depth += 1

    return best_action, best_score


def _search(
    board: Board,
    alpha: int,
    beta: int,
    node_key: int,
    played_table: dict[int, int],
    trans_table: TranspositionTable,
    color: PlayerColor = PlayerColor.RED,
    depth: int = 6,
) -> int:
    original_alpha = alpha

    cached = trans_table.probe(node_key, depth, alpha, beta)
    if cached is not None:
        return cached

    if depth == 0:
        return evaluate(board, color)

    opp_mask = np.uint8(color.opponent().value)
    opp_squares = np.flatnonzero(board.board & opp_mask)
    if len(opp_squares) == 0:
        return INF if color == PlayerColor.RED else -INF

    actions = generate_legal_actions(board, color)
    sorted_actions = order_moves(actions, board, color)

    tt_move = trans_table.get_best_move(node_key)
    if tt_move is not None:
        sorted_actions = _prepend_tt_move(sorted_actions, tt_move)

    best_move_in_node: np.void | None = None

    for i in sorted_actions:
        board.make_move(i, color)
        key = calculate_zobrist(board.board, color)

        times_played_before = played_table.get(key, 0)

        if times_played_before == 2:
            # Avoid threefold repetition LIKE THE PLAGUE
            board.unmake_move()
            continue

        score: int = -_search(
            board,
            -beta,
            -alpha,
            key,
            played_table,
            trans_table,
            color.opponent(),
            depth - 1,
        )
        board.unmake_move()

        if score >= beta:
            trans_table.store(node_key, depth, score, FLAG_LOWER, best_move=i)
            return beta

        if score > alpha:
            alpha = score
            best_move_in_node = i

    flag = FLAG_UPPER if alpha <= original_alpha else FLAG_EXACT
    trans_table.store(node_key, depth, alpha, flag, best_move=best_move_in_node)

    return alpha

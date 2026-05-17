from typing import Optional

import numpy as np

from agent.transposition.table import (
    FLAG_EXACT,
    FLAG_LOWER,
    FLAG_UPPER,
    TranspositionTable,
)
from agent.transposition.zobrist import calculate_zobrist

from ..actions.generator import generate_legal_actions
from ..board import Board
from ..player_color import PlayerColor
from ..search.order_moves import _order_place_actions, order_moves
from .evaluate import evaluate

INF = 30_000


def get_best_move(
    board: Board,
    color: PlayerColor,
    played_table: dict[int, int],
    trans_table: TranspositionTable,
    depth: int = 6,
) -> tuple[np.void, int]:
    actions = generate_legal_actions(board, color)
    if len(actions) == 0:
        raise Exception("Likely error: Action is none")

    if board.is_place_book:
        place_actions = _order_place_actions(actions, board, color)
        return place_actions[0], 0

    ## This is when the game is over and someone thinks they've lost it all
    # Just give in and pick the first move in the list

    best_action = actions[0]
    best_score = -INF

    for action in actions:
        board.make_move(action, color)

        key = calculate_zobrist(board.board, color)
        times_played_before = played_table.get(key) or 0

        if times_played_before == 2:
            ## fully avoid threefold repition
            board.unmake_move()
            print("Skipping move at 2 repeitiotns")
            continue

        score = -_search(
            board,
            -INF,
            -best_score,
            key,
            trans_table,
            color.opponent(),
            depth - 1,
        )
        board.unmake_move()

        if score > best_score:
            best_score = score
            best_action = action

    if best_action == actions[0]:
        print(f"{color.name}: WARNING: Making action[0], no better move found ")

    return best_action, best_score


def _search(
    board: Board,
    alpha: int,
    beta: int,
    node_key: int,
    trans_table: TranspositionTable,
    color=PlayerColor.RED,
    depth=6,
) -> int:
    original_alpha = alpha

    cached = trans_table.probe(node_key, depth, alpha, beta)
    if cached is not None:
        return cached

    if depth == 0:
        return evaluate(board, color)

    actions = generate_legal_actions(board, color)
    sorted_actions = order_moves(actions, board, color)

    for i in sorted_actions:
        board.make_move(i, color)
        key = calculate_zobrist(board.board, color)

        score: int = -_search(
            board,
            -beta,
            -alpha,
            key,
            trans_table,
            color.opponent(),
            depth - 1,
        )
        board.unmake_move()

        if score >= beta:
            trans_table.store(node_key, depth, score, FLAG_LOWER)
            return beta

        alpha = max(alpha, score)

    if trans_table is not None:
        flag = FLAG_UPPER if alpha <= original_alpha else FLAG_EXACT
        trans_table.store(node_key, depth, alpha, flag)

    return alpha

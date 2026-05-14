from typing import Optional

import numpy as np

from ..actions.generator import generate_legal_actions
from ..board import Board
from ..player_color import PlayerColor
from ..search.order_moves import _order_place_actions, order_moves
from .evaluate import evaluate


def get_best_move(
    board: Board,
    color: PlayerColor,
    depth: int = 6,
) -> Optional[np.void]:
    actions = generate_legal_actions(board, color)
    if len(actions) == 0:
        return None

    if board.is_place_book:
        place_actions = _order_place_actions(actions, board, color)
        return place_actions[0]

    ## This is when the game is over and someone thinks they've lost it all
    # Just give in and pick the first move in the list
    best_action = actions[0]
    best_score = -(10**9)

    for action in actions:
        board.make_move(action, color)
        score = -_search(board, -(10**9), -best_score, color.opponent(), depth - 1)
        board.unmake_move()

        if score > best_score:
            best_score = score
            best_action = action

    return best_action


def _search(
    board: Board,
    alpha: int,
    beta: int,
    color=PlayerColor.RED,
    depth=6,
) -> int:
    if depth == 0:
        eval = evaluate(board, color)
        return eval

    actions = generate_legal_actions(board, color)

    sorted_actions = order_moves(actions, board, color)

    for i in sorted_actions:
        board.make_move(i, color)
        eval: int = -_search(
            board,
            -beta,
            -alpha,
            color.opponent(),
            depth - 1,
        )
        board.unmake_move()

        if eval >= beta:
            return beta

        alpha = max(alpha, eval)

    return alpha

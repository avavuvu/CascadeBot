import numpy as np

from ..actions.types import CASCADE_ACTION, EAT_ACTION
from ..board import Board
from ..direction import DIR_STEPS, EDGE_DIST_TABLE, NEIGHBOR_TABLE
from ..player_color import PlayerColor

_sq = np.arange(64)
_CENTRE_DIST = np.abs(_sq // 8 * 2 - 7) + np.abs(_sq % 8 * 2 - 7)


def _has_stronger_enemy_neighbour(
    dest: int, our_height: int, board: np.ndarray, opp_mask: np.uint8
) -> bool:
    for nb in NEIGHBOR_TABLE[dest]:
        if nb >= 0:
            piece = int(board[nb])
            if piece & opp_mask and (piece & 0x0F) > our_height:
                return True
    return False


def _in_dangerous_cascade(
    coord: int, board_arr: np.ndarray, opp_mask: np.uint8
) -> bool:
    for d_idx in range(4):
        if EDGE_DIST_TABLE[coord, d_idx] != 0:
            continue

        opp_d_idx = d_idx ^ 1
        back_step = -int(DIR_STEPS[d_idx])
        sq = coord
        for k in range(1, 8):
            if EDGE_DIST_TABLE[sq, opp_d_idx] == 0:
                break
            sq += back_step
            piece = int(board_arr[sq])
            if piece & opp_mask and (piece & 0x0F) >= k:
                return True

    return False


def _order_place_actions(
    actions: np.ndarray, board: Board, color: PlayerColor
) -> np.ndarray:

    opp_mask = np.uint8(color.opponent().value)
    coords = actions["coord"].astype(np.intp)

    danger = np.array(
        [_in_dangerous_cascade(int(c), board.board, opp_mask) for c in coords],
        dtype=np.int64,
    )
    dist = _CENTRE_DIST[coords]
    combined = danger * (int(_CENTRE_DIST.max()) + 1) + dist

    return actions[np.argsort(combined, kind="stable")]


def order_moves(actions: np.ndarray, board: Board, color: PlayerColor):
    """
    Move phase priority:
    0  destination holds an enemy piece with height <= our height
    1  EAT_ACTION
    2  CASCADE whose path passes through at least one enemy piece
    3  moves out of the path of a dangerous cascade
    4  neutral
    5  in the path of a dangerous cascade
    6  a neighbour of the destination is an enemy with height > our height
       (moving into attack range — deprioritised)
    """
    if board.is_place_phase:
        return _order_place_actions(actions, board, color)

    opp_mask = np.uint8(color.opponent().value)

    n = len(actions)
    keys = np.full(n, 4, dtype=np.int64)  # default: neutral

    for i in range(n):
        action_type = int(actions["type"][i])
        src = int(actions["source"][i])
        dest = int(actions["coord"][i])
        our_height = int(board.board[src] & 0x0F)

        if action_type == EAT_ACTION:
            keys[i] = 1

        elif action_type == CASCADE_ACTION:
            direction = int(actions["direction"][i])
            dest_count = int(actions["dest_count"][i])

            hits_enemy = any(
                board.board[src + step * direction] & opp_mask
                for step in range(1, dest_count + 1)
            )

            if hits_enemy:
                keys[i] = 2
            else:
                src_danger = _in_dangerous_cascade(src, board.board, opp_mask)
                dest_danger = _in_dangerous_cascade(dest, board.board, opp_mask)
                if src_danger and not dest_danger:
                    keys[i] = 3
                elif dest_danger:
                    keys[i] = 5
                elif _has_stronger_enemy_neighbour(
                    dest, our_height, board.board, opp_mask
                ):
                    keys[i] = 6

        else:
            dest_piece = int(board.board[dest])

            if dest_piece & opp_mask and (dest_piece & 0x0F) <= our_height:
                keys[i] = 0
            else:
                src_danger = _in_dangerous_cascade(src, board.board, opp_mask)
                dest_danger = _in_dangerous_cascade(dest, board.board, opp_mask)
                if src_danger and not dest_danger:
                    keys[i] = 3
                elif dest_danger:
                    keys[i] = 5
                elif _has_stronger_enemy_neighbour(
                    dest, our_height, board.board, opp_mask
                ):
                    keys[i] = 6

    sorted_indices = np.argsort(keys, kind="stable")
    return actions[sorted_indices]

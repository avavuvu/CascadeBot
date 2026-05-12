from referee.game.actions import (
    Action,
    CascadeAction,
    Coord,
    EatAction,
    MoveAction,
    PlaceAction,
)

from .types import Board, CellState, PlayerColor

BOARD_N = 8


def _push_stack(board: Board, r: int, c: int, dr: int, dc: int) -> Board:
    """
    Push the stack at (r, c) exactly one cell in direction (dr, dc).
    If the destination also has a stack, push that one first (chain reaction).
    If the destination is off the board, the stack is eliminated.
    """
    coord = Coord(r, c)
    cell = board.get(coord, CellState(None, 0))
    if cell.color is None:
        return board

    dest_r, dest_c = r + dr, c + dc

    if not (0 <= dest_r < BOARD_N and 0 <= dest_c < BOARD_N):
        # Pushed off the board — eliminated
        board[coord] = CellState(None, 0)
        return board

    dest = Coord(dest_r, dest_c)
    if board.get(dest, CellState(None, 0)).color is not None:
        # Recursively push whatever is at the destination first
        board = _push_stack(board, dest_r, dest_c, dr, dc)

    board[dest] = cell
    board[coord] = CellState(None, 0)
    return board


def is_winner(board: Board) -> PlayerColor | None:
    any_red = any(state.color == PlayerColor.RED for state in board.values())

    if not any_red:
        return PlayerColor.BLUE

    any_blue = any(state.color == PlayerColor.BLUE for state in board.values())

    if not any_blue:
        return PlayerColor.RED

    return None


def get_updated_board(board: Board, player_color: PlayerColor, action: Action) -> Board:
    # needs to be clone of board
    new_board: Board = dict(board)

    if isinstance(action, PlaceAction):
        new_board[action.coord] = CellState(player_color, 3)

    # is move
    elif isinstance(action, MoveAction):
        source_state = new_board.pop(action.coord)
        new_board[action.coord] = CellState(None, 0)  # leave empty cell behind
        dst = action.coord + action.direction
        dst_state = new_board.get(dst)
        if dst_state is not None and dst_state.color is not None:
            # Merge onto an occupied stack
            new_board[dst] = CellState(
                player_color, source_state.height + dst_state.height
            )
        else:
            new_board[dst] = source_state

    # is eat
    elif isinstance(action, EatAction):
        source_state = new_board[action.coord]
        new_board[action.coord] = CellState(None, 0)  # source cell is now empty
        dst = action.coord + action.direction
        new_board[dst] = CellState(player_color, source_state.height)

    # is cascade
    elif isinstance(action, CascadeAction):
        source_state = new_board[action.coord]
        new_board[action.coord] = CellState(None, 0)  # remove original stack

        dr = action.direction.value.r
        dc = action.direction.value.c
        height = source_state.height

        for i in range(1, height + 1):
            target_r = action.coord.r + dr * i
            target_c = action.coord.c + dc * i

            if not (0 <= target_r < BOARD_N and 0 <= target_c < BOARD_N):
                continue  # this token falls off the board — discard it

            target = Coord(target_r, target_c)

            if new_board.get(target, CellState(None, 0)).color is not None:
                # A stack is in the way — push it one cell further before
                # placing the cascade token
                new_board = _push_stack(new_board, target_r, target_c, dr, dc)

            new_board[target] = CellState(player_color, 1)

    return new_board

import random

from referee.game import PlayerColor

from .types import BOARD_N, Board

# ── Constants ─────────────────────────────────────────────────────────────────

N = BOARD_N  # 8
MAX_HEIGHT = 24  # maximum possible stack height on the board


# ── D4 symmetry group acting on (r, c) in [0, N-1]^2 ─────────────────────────
#
# Each function maps a cell coordinate to its image under one of the 8 elements
# of the dihedral group D4.


def _r0(r: int, c: int) -> tuple[int, int]:
    return (r, c)  # identity


def _r1(r: int, c: int) -> tuple[int, int]:
    return (c, N - 1 - r)  # 90 CW


def _r2(r: int, c: int) -> tuple[int, int]:
    return (N - 1 - r, N - 1 - c)  # 180


def _r3(r: int, c: int) -> tuple[int, int]:
    return (N - 1 - c, r)  # 270 CW


def _fh(r: int, c: int) -> tuple[int, int]:
    return (N - 1 - r, c)  # flip horizontal axis


def _fv(r: int, c: int) -> tuple[int, int]:
    return (r, N - 1 - c)  # flip vertical axis


def _fd(r: int, c: int) -> tuple[int, int]:
    return (c, r)  # flip main diagonal


def _fa(r: int, c: int) -> tuple[int, int]:
    return (N - 1 - c, N - 1 - r)  # flip anti-diagonal


_SYMMETRIES = (_r0, _r1, _r2, _r3, _fh, _fv, _fd, _fa)


# ── Orbit representative ──────────────────────────────────────────────────────


def _orbit_rep(r: int, c: int) -> tuple[int, int]:
    """Lex-min cell in the D4 orbit of (r, c) — canonical representative."""
    return min(f(r, c) for f in _SYMMETRIES)


# ── Zobrist table construction ────────────────────────────────────────────────


def _build_table() -> list[list[dict[tuple[int, int], int]]]:
    """
    Build _TABLE[r][c][(color_idx, height)] -> random 64-bit int.

    All cells in the same D4 orbit point to the *same* inner dict, so XORing
    a board position and any of its 8 symmetric equivalents always produces the
    same aggregate hash.
    """
    rng = random.Random(0xABCD_1234_5678_EF00)  # fixed seed for reproducibility

    orbit_randoms: dict[tuple[int, int], dict[tuple[int, int], int]] = {}
    for r in range(N):
        for c in range(N):
            rep = _orbit_rep(r, c)
            if rep not in orbit_randoms:
                orbit_randoms[rep] = {
                    (ci, h): rng.getrandbits(64)
                    for ci in range(2)
                    for h in range(1, MAX_HEIGHT + 1)
                }

    # Every cell points directly at its orbit representative's dict
    return [[orbit_randoms[_orbit_rep(r, c)] for c in range(N)] for r in range(N)]


_TABLE = _build_table()

# Side-to-move: include whose turn it is so that the same board with a different
# active player hashes differently (they are genuinely distinct positions).
_rng_side = random.Random(0xFEDC_BA98_7654_3210)
_SIDE_HASH: dict[PlayerColor, int] = {p: _rng_side.getrandbits(64) for p in PlayerColor}


# ── Public API ────────────────────────────────────────────────────────────────


def board_hash(board: Board, current_player: PlayerColor) -> int:
    """Canonical Zobrist hash of *board* with *current_player* to move.

    Any D4-symmetric equivalent of *board* produces the same hash value,
    so no separate canonicalisation step is ever needed.
    """
    h = _SIDE_HASH[current_player]
    for coord, state in board.items():
        if state.color is not None:
            ci = 0 if state.color == PlayerColor.RED else 1
            h ^= _TABLE[coord.r][coord.c][(ci, state.height)]
    return h

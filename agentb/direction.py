from enum import Enum

import numpy as np


class Direction1D(Enum):
    North = -8
    South = 8
    East = 1
    West = -1

    def __str__(self) -> str:
        return {
            Direction1D.South: "[↓]",
            Direction1D.North: "[↑]",
            Direction1D.West: "[←]",
            Direction1D.East: "[→]",
        }[self]


DIRECTIONS = [Direction1D.North, Direction1D.South, Direction1D.East, Direction1D.West]

# Direction index mapping
#   0 = North (step -8)   1 = South (step +8)
#   2 = East  (step +1)   3 = West  (step -1)

DIR_STEPS = np.array([-8, 8, 1, -1], dtype=np.int8)

NEIGHBOR_TABLE = np.full((64, 4), -1, dtype=np.int8)
EDGE_DIST_TABLE = np.zeros((64, 4), dtype=np.uint8)

for _sq in range(64):
    _row, _col = divmod(_sq, 8)
    _dists = [_row, 7 - _row, 7 - _col, _col]
    for _d, (_step, _dist) in enumerate(zip([-8, 8, 1, -1], _dists)):
        EDGE_DIST_TABLE[_sq, _d] = _dist
        if _dist > 0:
            NEIGHBOR_TABLE[_sq, _d] = _sq + _step

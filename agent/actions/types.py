from dataclasses import dataclass

import numpy as np

MOVE_ACTION = np.uint8(0)
EAT_ACTION = np.uint8(1)
CASCADE_ACTION = np.uint8(2)
PLACE_ACTION = np.uint8(3)


@dataclass(frozen=True, slots=True)
class MoveAction:
    source: int
    dest: int
    direction: int


@dataclass(frozen=True, slots=True)
class EatAction:
    source: int
    dest: int
    direction: int


@dataclass(frozen=True, slots=True)
class CascadeAction:
    source: int
    direction: int
    destinations: tuple[int, ...]


Action = MoveAction | EatAction | CascadeAction

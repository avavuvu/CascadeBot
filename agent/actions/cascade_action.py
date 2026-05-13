from dataclasses import dataclass
from typing import List

from ..coord import index_to_coord
from ..direction import Direction1D


@dataclass(frozen=True, slots=True)
class CascadeAction1D:
    coord: int
    direction: Direction1D
    destinations: List[int]

    def __str__(self) -> str:
        return f"CASCADE\t{index_to_coord(self.coord)}\t{self.direction}"

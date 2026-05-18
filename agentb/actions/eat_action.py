from dataclasses import dataclass

from ..coord import index_to_coord
from ..direction import Direction1D


@dataclass(frozen=True, slots=True)
class EatAction1D:
    coord: int
    direction: Direction1D

    def __str__(self) -> str:
        return f"EAT\t{index_to_coord(self.coord)}\t{self.direction}"

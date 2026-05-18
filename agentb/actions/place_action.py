from dataclasses import dataclass

from ..coord import index_to_coord


@dataclass(frozen=True, slots=True)
class PlaceAction1D:
    coord: int

    def __str__(self) -> str:
        return f"PLACE\t{index_to_coord(self.coord)}"

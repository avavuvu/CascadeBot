def index_to_coord(index: int) -> tuple[int, int]:
    return divmod(index, 8)

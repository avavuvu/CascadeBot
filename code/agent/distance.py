from referee.game.coord import Coord

def manhattan(a: Coord, b: Coord):
    return abs(a.r - b.r) + abs(a.c - b.c)
    
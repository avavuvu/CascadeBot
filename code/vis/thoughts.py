"""
Visualiser thought client.

Formats agent move candidates and POSTs them to the thought server so the
Svelte visualiser can display them alongside the game.

Kept separate from agent logic so the agent works fine even when the
visualiser is not running.
"""

import json
import urllib.request

from referee.game import (
    Action,
    CascadeAction,
    EatAction,
    MoveAction,
    PlaceAction,
    PlayerColor,
)

THOUGHT_SERVER = "http://host.docker.internal:8767"

_DIR_ARROW: dict[str, str] = {
    "Up": "↑",
    "Down": "↓",
    "Left": "←",
    "Right": "→",
    "UpLeft": "↖",
    "UpRight": "↗",
    "DownLeft": "↙",
    "DownRight": "↘",
}


def format_move(
    rank: int, action: Action, score: float, breakdown: dict[str, float] | None = None
) -> dict:
    """
    Serialise a single candidate move into the JSON shape the visualiser
    expects:
        { rank, score, type, label, coord, direction }

    `coord` is [row, col].  `direction` is the enum name (e.g. "Up") or None.
    """
    base: dict = {"rank": rank, "score": round(score, 2)}
    if breakdown is not None:
        base["breakdown"] = breakdown
    match action:
        case PlaceAction(coord):
            return {
                **base,
                "type": "PlaceAction",
                "label": f"Place ({coord.r},{coord.c})",
                "coord": [coord.r, coord.c],
                "direction": None,
            }
        case MoveAction(coord, direction):
            return {
                **base,
                "type": "MoveAction",
                "label": f"Move ({coord.r},{coord.c}) {_DIR_ARROW.get(direction.name, '?')}",
                "coord": [coord.r, coord.c],
                "direction": direction.name,
            }
        case EatAction(coord, direction):
            return {
                **base,
                "type": "EatAction",
                "label": f"Eat ({coord.r},{coord.c}) {_DIR_ARROW.get(direction.name, '?')}",
                "coord": [coord.r, coord.c],
                "direction": direction.name,
            }
        case CascadeAction(coord, direction):
            return {
                **base,
                "type": "CascadeAction",
                "label": f"Cascade ({coord.r},{coord.c}) {_DIR_ARROW.get(direction.name, '?')}",
                "coord": [coord.r, coord.c],
                "direction": direction.name,
            }
    return {**base, "type": "Unknown", "label": "?", "coord": [0, 0], "direction": None}


def send_thoughts(player: PlayerColor, turn: int, moves: list[dict]) -> None:
    """
    POST the top-N candidate moves to the visualiser's thought server.

    `moves` should be a list of dicts produced by `format_move`.

    Fails silently — the agent works fine even if the visualiser isn't running.
    """
    payload = json.dumps(
        {"player": str(player), "turn": turn, "thoughts": moves}
    ).encode()
    try:
        req = urllib.request.Request(
            f"{THOUGHT_SERVER}/thoughts",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=0.5)
    except Exception:
        pass  # Visualiser not running — that's fine

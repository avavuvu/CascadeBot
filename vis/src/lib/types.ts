export type Player = 1 | -1
export type Phase = "PLAY"

export type Coord = [number, number]
export type Direction = [number, number]

export interface Cell {
    color: Player
    height: number
}

export type Board = Cell[][]

export interface PlaceAction {
    type: "PlaceAction"
    coord: Coord
}

export interface MoveAction {
    type: "MoveAction"
    coord: Coord
    direction: Direction
}

export type Action = PlaceAction | MoveAction

export interface Ping {
    type: "<ping>"
    id: null
}

export interface GameMetadata {
    type: "GameMetadata"
    players: string[]
    id: null
}

export interface TurnBegin {
    type: "GameUpdate:TurnBegin"
    turnId: number
    player: Player
    id: number
}

export interface TurnEnd {
    type: "GameUpdate:TurnEnd"
    turnId: number
    player: Player
    action: Action
    id: number
}

export interface BoardUpdate {
    type: "GameUpdate:BoardUpdate"
    board: Board
    phase: Phase
    id: number
}

export interface PlayerError {
    type: "GameUpdate:PlayerError"
    id: number
}

export interface GameEnd {
    type: "GameUpdate:GameEnd"
    winner: Player
    id: number
}

export type GameUpdate =
    | TurnBegin
    | TurnEnd
    | BoardUpdate
    | PlayerError
    | GameEnd
    | Ping
    | GameMetadata

export type ActionType =
    | "PlaceAction"
    | "MoveAction"
    | "EatAction"
    | "CascadeAction"

export interface RankedMove {
    rank: number
    score: number
    type: ActionType
    label: string
    coord: [number, number] // [row, col]
    direction: string | null // e.g. "Up", "Down", "Left", "Right", or null
    breakdown?: EvalBreakdown
}

/** Per-heuristic component values from _components() in minimax.py.
 *  Keys and values mirror that dict exactly — add/remove features there
 *  and the display updates automatically.
 *  All values: positive = good for the player.
 */
export type EvalBreakdown = Record<string, number>

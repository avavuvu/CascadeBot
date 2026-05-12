import type { Board, GameUpdate, RankedMove } from "./types"

const THOUGHT_SERVER = "http://localhost:8767"

export interface ThoughtPayload {
    player: string
    turn: number
    thoughts: RankedMove[]
}

class GameManager {
    ws!: WebSocket
    updateMessages: GameUpdate[] = $state([])
    id: number = $state(1)
    boardState: Board = $state([])
    thoughts: ThoughtPayload[] = $state([])
    isAuto = $state(false)
    isSteppingToMove = $state(false)

    init = async () => {
        this.ws = new WebSocket("ws://localhost:8766")

        this.ws.onopen = () => {
            console.log("connected")
            this.ws.send(
                JSON.stringify({
                    type: "<ack>",
                    id: null,
                })
            )
        }

        this.ws.onmessage = this.listen
    }

    sendAck = () => {
        this.ws.send(
            JSON.stringify({
                type: "<ack>",
                id: this.id,
            })
        )
    }

    auto = () => {
        this.isAuto = true
        this.sendAck()
    }

    nextMove = () => {
        this.isSteppingToMove = true
        this.sendAck()
    }

    fetchLatestThoughts = async () => {
        try {
            const res = await fetch(`${THOUGHT_SERVER}/thoughts`)
            if (!res.ok) return
            const data: ThoughtPayload[] = await res.json()
            this.thoughts = data
        } catch {
            // thought server not running — silently ignore
        }
    }

    listen = (ev: MessageEvent<any>) => {
        console.log(ev.data)
        const messageData: GameUpdate = JSON.parse(ev.data)

        if (messageData.type === "<ping>") {
            return
        }

        if (messageData.type === "GameMetadata") {
            this.ws.send(
                JSON.stringify({
                    type: "<ack>",
                    id: 0,
                })
            )

            this.thoughts = []
            return
        }

        this.updateMessages.push(messageData)
        this.id = messageData.id

        if (messageData.type === "GameUpdate:BoardUpdate") {
            this.boardState = messageData.board
        }

        // Fetch thoughts only at TurnEnd: by that point the agent has finished
        // action() and posted its candidates, but the board hasn't changed yet.
        // Fetching at BoardUpdate would be one event too late — the overlay would
        // show the move that just happened rather than the upcoming candidates.
        if (messageData.type === "GameUpdate:TurnEnd") {
            this.fetchLatestThoughts()
        }

        // nextMove auto-acks through BoardUpdate and TurnBegin, then stops at
        // TurnEnd.  At that point the board reflects the last completed move and
        // thoughts reflect the upcoming player's candidates for exactly this state.
        const isTurnEnd = messageData.type === "GameUpdate:TurnEnd"
        if (this.isSteppingToMove && isTurnEnd) {
            this.isSteppingToMove = false
        }

        const shouldAutoAck =
            this.isAuto || (this.isSteppingToMove && !isTurnEnd)

        if (shouldAutoAck) {
            this.sendAck()
        }
    }
}

export const gameManager = new GameManager()

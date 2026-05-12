<script lang="ts">
    import { gameManager, type ThoughtPayload } from "$lib/GameManager.svelte"
    import type { Player, RankedMove } from "$lib/types"
    import type { ActionType } from "$lib/types"
    import TopMoves from "$lib/TopMoves.svelte"

    const colorMap: Record<Player, string> = {
        "1": "red",
        "-1": "blue",
    }

    const TYPE_COLOR: Record<ActionType, string> = {
        PlaceAction: "#22c55e",
        MoveAction: "#3b82f6",
        EatAction: "#f97316",
        CascadeAction: "#a855f7",
    }

    // coord is [row, col]; SVG x = col, y = row
    // "Up" means row decreases → SVG y decreases
    const DIR_VEC: Record<string, [number, number]> = {
        Up: [0, -1],
        Down: [0, 1],
        Left: [-1, 0],
        Right: [1, 0],
    }

    const latestThought = $derived(gameManager.thoughts.at(-1) ?? null)
    let currentThought: RankedMove | undefined = $state()

    $effect(() => {
        if (latestThought) {
            currentThought = latestThought.thoughts.at(0)
        }
    })

    const updateRankedMove = (index: number) => {
        if (latestThought) {
            currentThought = latestThought.thoughts[index]
        }
    }
</script>

<button onclick={async () => await gameManager.init()}> connect </button>

<div class="max-w-6xl grid grid-cols-[1fr_15em_18em]">
    <!-- Board -->
    <div>
        <button onclick={() => gameManager.sendAck()}> next </button>
        <button onclick={() => gameManager.nextMove()}> next move </button>
        <button
            onclick={() => gameManager.auto()}
            disabled={gameManager.isAuto}
        >
            {gameManager.isAuto ? "autoplaying…" : "autoplay"}
        </button>
        {#if gameManager.isAuto}
            <button onclick={() => (gameManager.isAuto = false)}> stop </button>
        {/if}

        <svg viewBox="0 0 8 8">
            {#each gameManager.boardState as rows, y}
                {#each rows as cell, x}
                    <g transform="translate({x} {y})">
                        <rect
                            width="1"
                            height="1"
                            fill="white"
                            stroke="black"
                            stroke-width="0.02"
                        >
                        </rect>
                        {#if cell.color}
                            <rect
                                width=".8"
                                height=".8"
                                transform="translate(0.1 0.1)"
                                fill={colorMap[cell.color]}
                                stroke="white"
                                stroke-width="0.02"
                            >
                            </rect>
                            <text
                                transform="translate(0.4 0.6)"
                                font-size="0.02rem"
                                fill="white"
                            >
                                {cell.height}
                            </text>
                        {/if}

                        <text
                            transform="translate(0.1 0.2)"
                            fill="black"
                            font-size="0.009rem"
                        >
                            {x},{y}
                        </text>
                    </g>
                {/each}
            {/each}

            {#if currentThought}
                {@const [row, col] = currentThought.coord}
                <!-- {@const opacity = 0.55 - i * 0.08} -->
                {@const color = TYPE_COLOR[currentThought.type]}
                {@const dirVec =
                    currentThought.direction !== null
                        ? DIR_VEC[currentThought.direction]
                        : null}
                <g transform="translate({col} {row})">
                    <!-- Colored cell overlay -->
                    <rect width="1" height="1" fill={color} opacity="0.5" />

                    <!-- Direction arrow line -->
                    {#if dirVec}
                        {@const [dx, dy] = dirVec}
                        {@const angle = (Math.atan2(dy, dx) * 180) / Math.PI}
                        <polygon
                            points="0.88,0.5 0.62,0.38 0.62,0.62"
                            fill="white"
                            transform="rotate({angle}, 0.5, 0.5)"
                        />
                    {/if}

                    <!-- Rank label -->
                    <!-- <text
                            x="0.5"
                            y="0.62"
                            font-size="0.35"
                            fill="white"
                            font-weight="bold"
                            text-anchor="middle"
                            dominant-baseline="middle"
                        >
                            {move.rank}
                        </text> -->
                </g>
            {/if}
        </svg>
    </div>

    <!-- Agent thoughts panel -->
    <div class="overflow-y-scroll max-h-[60vh] border-l pl-2">
        <TopMoves
            payload={latestThought}
            history={gameManager.thoughts}
            {updateRankedMove}
        />
    </div>
</div>

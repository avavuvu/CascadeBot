<script lang="ts">
    import type { ThoughtPayload } from "$lib/GameManager.svelte"
    import type { ActionType, RankedMove } from "$lib/types"

    interface Props {
        payload: ThoughtPayload | null
        history?: ThoughtPayload[]
        updateRankedMove: (index: number) => void
    }

    let { payload, history = [], updateRankedMove }: Props = $props()

    const TYPE_COLOR: Record<ActionType, string> = {
        PlaceAction: "#22c55e",
        MoveAction: "#3b82f6",
        EatAction: "#f97316",
        CascadeAction: "#a855f7",
    }

    const TYPE_SHORT: Record<ActionType, string> = {
        PlaceAction: "Place",
        MoveAction: "Move",
        EatAction: "Eat",
        CascadeAction: "Cascade",
    }

    function scoreBarWidth(moves: RankedMove[], move: RankedMove): number {
        const scores = moves.map((m) => m.score)
        const max = Math.max(...scores)
        const min = Math.min(...scores)
        if (max === min) return 100
        return ((move.score - min) / (max - min)) * 100
    }
</script>

<!-- Latest thoughts -->
{#if payload === null}
    <p class="text-xs text-gray-400 italic">No thoughts yet.</p>
{:else}
    <h3 class="font-bold text-sm mb-2">
        Turn {payload.turn} · <span class="font-normal">{payload.player}</span>
    </h3>

    <ol class="space-y-1 mb-3">
        {#each payload.thoughts as move, i}
            {@const barWidth = scoreBarWidth(payload.thoughts, move)}
            {@const color = TYPE_COLOR[move.type]}
            <li
                class="rounded overflow-hidden border border-gray-200"
                style="border-left: 3px solid {color}"
            >
                <button
                    onclick={() => updateRankedMove(i)}
                    class="cursor-pointer"
                >
                    <div class="flex items-center gap-1 px-2 pt-1 pb-0.5">
                        <!-- Rank -->
                        <span class="text-gray-400 text-xs w-5 shrink-0"
                            >#{move.rank}</span
                        >

                        <!-- Type badge -->
                        <span
                            class="text-white text-[10px] font-semibold px-1 rounded shrink-0"
                            style="background-color: {color}"
                        >
                            {TYPE_SHORT[move.type]}
                        </span>

                        <!-- Label -->
                        <span class="font-mono text-xs truncate flex-1 min-w-0"
                            >{move.label}</span
                        >

                        <!-- Score -->
                        <span
                            class="font-mono text-xs text-right shrink-0 ml-1"
                        >
                            {move.score.toFixed(1)}
                        </span>
                    </div>

                    <!-- Score bar -->
                    <div
                        class="h-1 bg-gray-100 mx-2 mb-1 rounded-full overflow-hidden"
                    >
                        <div
                            class="h-full rounded-full"
                            style="width: {barWidth}%; background-color: {color}; opacity: 0.7"
                        ></div>
                    </div>

                    {#if move.breakdown}
                        <div
                            class="flex gap-x-3 gap-y-0.5 flex-wrap px-2 pb-1.5 pt-0.5"
                        >
                            {#each Object.entries(move.breakdown) as [key, val]}
                                <span
                                    class="font-mono text-[9px] tabular-nums {val >
                                    0
                                        ? 'text-green-600'
                                        : val < 0
                                          ? 'text-red-500'
                                          : 'text-gray-400'}"
                                >
                                    {key}:{val >= 0 ? "+" : ""}{val.toFixed(1)}
                                </span>
                            {/each}
                        </div>
                    {/if}
                </button>
            </li>
        {/each}
    </ol>
{/if}

<!-- History accordion -->
{#if history.length > 1}
    {@const pastEntries = history.toReversed().slice(1)}
    <details class="text-xs">
        <summary
            class="cursor-pointer font-semibold text-gray-500 hover:text-gray-700 select-none"
        >
            history ({pastEntries.length} earlier {pastEntries.length === 1
                ? "turn"
                : "turns"})
        </summary>

        <ol class="mt-1 space-y-1">
            {#each pastEntries as past}
                {@const top = past.thoughts[0]}
                <li>
                    <details
                        class="border border-gray-200 rounded overflow-hidden"
                    >
                        <summary
                            class="font-mono cursor-pointer px-2 py-1 bg-gray-50 hover:bg-gray-100 select-none"
                        >
                            turn {past.turn} · {past.player}
                            {#if top}
                                — #{top.rank} {top.label}
                            {/if}
                        </summary>

                        <ol class="divide-y divide-gray-100">
                            {#each past.thoughts as move}
                                <li
                                    class="flex items-center gap-2 px-2 py-0.5 font-mono"
                                >
                                    <span class="text-gray-400 w-5 shrink-0"
                                        >#{move.rank}</span
                                    >
                                    <span
                                        class="text-white text-[10px] font-semibold px-1 rounded shrink-0"
                                        style="background-color: {TYPE_COLOR[
                                            move.type
                                        ]}"
                                    >
                                        {TYPE_SHORT[move.type]}
                                    </span>
                                    <span class="truncate flex-1 min-w-0"
                                        >{move.label}</span
                                    >
                                    <span class="shrink-0 text-gray-500"
                                        >{move.score.toFixed(1)}</span
                                    >
                                </li>
                            {/each}
                        </ol>
                    </details>
                </li>
            {/each}
        </ol>
    </details>
{/if}

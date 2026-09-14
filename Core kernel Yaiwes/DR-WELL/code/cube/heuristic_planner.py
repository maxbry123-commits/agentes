"""
Heuristic Multiagent Planner
============================
Generate cooperative plans for all agents to deliver blocks by repeatedly
selecting the block closest to the goal (right-most column) and assigning
all agents to: MoveToBlock -> Rendezvous -> Push.

Plans are emitted as strings compatible with BaseAgent.parse_step and the
SymbolicController used in main.
"""

from __future__ import annotations
from typing import Dict, List, Tuple

from .env import CoopBlockPush, Block


def _distance_to_goal(env: CoopBlockPush, block: Block) -> int:
    """Horizontal cells the block must move for any cell to reach the goal column."""
    # rightmost column occupied by this block
    right_edge_col = block.c + block.weight - 1
    # goal at col K-1
    return max(0, env.K - 1 - right_edge_col)

def _sorted_blocks_by_goal_proximity(env: CoopBlockPush) -> List[Block]:
    """Return blocks sorted by (distance to goal asc, weight desc)"""
    # return sorted(
    #     list(env._blocks),
    #     key=lambda b: (_distance_to_goal(env, b), -b.weight, b.id),
    # )

    return sorted(list(env._blocks), key=lambda b: (_distance_to_goal(b), -b.weight, b.id))
    # parts = [f"{b.id}@({b.r},{b.c}) w={b.weight} d={dist_to_goal(b)}" for b in blocks_sorted]
    # closest_id = blocks_sorted[0].id if blocks_sorted else "none"
    # return f"[ {', '.join(parts)} ] (closest: {closest_id})"


def _push_steps_needed(env: CoopBlockPush, block: Block) -> int:
    """Minimal horizontal steps to touch the goal strip (no buffer)."""
    return max(1, _distance_to_goal(env, block))


def generate_multiagent_heuristic_plans(
    env: CoopBlockPush,
    rendezvous_timeout: int = 5,
    side: str = "left",
    debug: bool = False,
    tie_break: str = "none",
) -> Dict[str, List[str]]:
    """
    Create per-agent plans so that all agents cooperate on the block closest
    to the goal, push it to the goal, then repeat for the next-closest block
    until all blocks are planned.

    - side: use "left" so agents align on the left face to push right toward the goal.

    Returns:
        Dict[agent_id, List[str]]
    """
    agent_ids = list(env.agents)
    if not agent_ids:
        return {}

    # Determine rendezvous threshold
    def rendezvous_need(block: Block) -> int:
        return max(1, min(block.weight, len(agent_ids)))

    # Find the single closest block to goal
    def sort_key(b: Block):
        dist = _distance_to_goal(env, b)
        if tie_break == "weight_asc":
            return (dist, b.weight, b.id)
        if tie_break == "none":
            return (dist, b.id)
        # default: heavier first
        return (dist, -b.weight, b.id)

    if not env._blocks:
        return {aid: [] for aid in agent_ids}
    
    ordered = sorted(list(env._blocks), key=sort_key)
    closest_block = ordered[0]
    
    if debug:
        # Emit a concise planning order explanation
        dist = _distance_to_goal(env, closest_block)
        print(f"[HeuristicPlanner] Targeting closest block: {closest_block.id}(w={closest_block.weight},d={dist}) (key: distance asc, tie_break={tie_break})")
    
    # Generate plan for only the closest block
    block_id = closest_block.id
    push_steps = _push_steps_needed(env, closest_block)
    need = rendezvous_need(closest_block)

    print(f"[HeuristicPlanner] Generating plans for block: {block_id} (need: {need}, push_steps: {push_steps})")
    # Create plan for each agent: MoveToBlock -> Rendezvous -> Push
    plans: Dict[str, List[str]] = {aid: [] for aid in agent_ids}
    for aid in agent_ids:
        side = "left"
        plans[aid].append(f"MoveToBlock {block_id} {side}")
        plans[aid].append(f"Rendezvous {block_id} {side} {need} {rendezvous_timeout}")
        plans[aid].append(f"Push {block_id} {push_steps}")

    return plans


__all__ = [
    "generate_multiagent_heuristic_plans",
]

# symbolic_concepts.py
"""
Essential utilities and geometric helpers for symbolic reasoning in the block-pushing environment.
Contains only functions used by symbolic_actions.py.
"""
from __future__ import annotations
from typing import Dict, List, Tuple, Optional
from collections import deque
from numba import njit
import numpy as np
from .env import CoopBlockPush, Block


# ==========================
# Block and Environment Utilities
# ==========================

def get_block(env: CoopBlockPush, block_id: int) -> Optional[Block]:
    """Find a block by ID in the environment."""
    for b in env._blocks:
        if b.id == block_id:
            return b
    return None


# ==========================
# Geometric and Spatial Calculations
# ==========================

def face_cells_outside(env: CoopBlockPush, b: Block, side: str) -> List[Tuple[int, int]]:
    """Get cells immediately outside a block's face where agents can stand."""
    # Handle case where block_id (int) is passed instead of Block object
    if isinstance(b, int):
        b = get_block(env, b)
        if b is None:
            return []  # Block doesn't exist (delivered/removed)
    
    r, c, w, K = b.r, b.c, b.weight, env.K
    
    if side == "left":
        cells = [(r + dr, c - 1) for dr in range(w)]
    elif side == "right":
        cells = [(r + dr, c + w) for dr in range(w)]
    elif side == "up":
        cells = [(r - 1, c + dc) for dc in range(w)]
    elif side == "down":
        cells = [(r + w, c + dc) for dc in range(w)]
    else:
        return []
    
    # Filter to in-bounds cells that are not block cells
    return [(rr, cc) for rr, cc in cells 
            if 0 <= rr < K and 0 <= cc < K and env._occupied[rr, cc] != 2]


def manhattan_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
    """Calculate Manhattan distance between two positions."""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def closest_free_cell(env: CoopBlockPush, from_pos: Tuple[int, int], 
                     candidates: List[Tuple[int, int]]) -> Tuple[int, int]:
    """Choose nearest candidate cell, preferring cells not currently occupied by agents."""
    if not candidates:
        return from_pos
    
    occupied_by_agents = set(env._agent_positions.values())
    free_candidates = [p for p in candidates if p not in occupied_by_agents]
    pool = free_candidates if free_candidates else candidates
    
    return min(pool, key=lambda p: manhattan_distance(from_pos, p))

import numpy as np
from numba import njit

# ------- constants (same semantics as your code) -------
ACTION_CODES = {"stay": 0, "up": 1, "down": 2, "left": 3, "right": 4}
ACTION_STAY  = 0
ACTION_UP    = 1
ACTION_DOWN  = 2
ACTION_LEFT  = 3
ACTION_RIGHT = 4

# 4-neighborhood (row, col deltas)
_DIRS = np.array([[-1, 0, ACTION_UP],
                  [ 1, 0, ACTION_DOWN],
                  [ 0,-1, ACTION_LEFT],
                  [ 0, 1, ACTION_RIGHT]], dtype=np.int32)

@njit(cache=True)
def _bfs_next_action_numba(occupied: np.ndarray,
                           K: int,
                           start_r: int, start_c: int,
                           goals_rc: np.ndarray,   # shape (G, 2) int32
                           avoid_agents: bool) -> int:
    """
    Numba-compiled BFS that mirrors the Python version's behavior.

    occupied: int array (K,K) with semantics:
        0 = free, 1 = agent, 2 = wall/blocked (same as your env._occupied)
    K: grid size
    start_r, start_c: start cell
    goals_rc: (G,2) array of goal cells (r,c). If G==0 -> stay.
    avoid_agents: if True, treat occupied==1 as blocked; otherwise only occupied==2 is blocked.
    """
    # Early outs
    if goals_rc.shape[0] == 0:
        return ACTION_STAY

    # Flatten helpers
    def idx(r, c):
        return r * K + c

    def rc(i):
        return i // K, i % K

    # Mark goals in a boolean mask over flattened grid
    N = K * K
    goal_mask = np.zeros(N, dtype=np.uint8)
    for g in range(goals_rc.shape[0]):
        gr = goals_rc[g, 0]
        gc = goals_rc[g, 1]
        if 0 <= gr < K and 0 <= gc < K:
            goal_mask[idx(gr, gc)] = 1

    start_idx = idx(start_r, start_c)
    if goal_mask[start_idx] == 1:
        return ACTION_STAY

    # BFS structures
    visited = np.zeros(N, dtype=np.uint8)
    parent  = np.full(N, -1, dtype=np.int32)
    queue   = np.empty(N, dtype=np.int32)
    qh = 0  # head
    qt = 0  # tail

    # enqueue start if it's not hard-blocked
    if occupied[start_r, start_c] == 2:
        return ACTION_STAY
    visited[start_idx] = 1
    queue[qt] = start_idx
    qt += 1

    found_goal = -1

    while qh < qt:
        cur = queue[qh]
        qh += 1

        cr, cc = rc(cur)
        # goal check
        if goal_mask[cur] == 1:
            found_goal = cur
            break

        # neighbors
        for d in range(_DIRS.shape[0]):
            dr = _DIRS[d, 0]
            dc = _DIRS[d, 1]
            nr = cr + dr
            nc = cc + dc
            if nr < 0 or nr >= K or nc < 0 or nc >= K:
                continue

            # blocking rules
            cell = occupied[nr, nc]
            if cell == 2:
                continue
            if avoid_agents and cell == 1:
                continue

            ni = idx(nr, nc)
            if visited[ni] == 0:
                visited[ni] = 1
                parent[ni] = cur
                queue[qt] = ni
                qt += 1

    if found_goal == -1:
        return ACTION_STAY

    # Reconstruct just enough to get the first move from start:
    # walk back from goal until the parent is start (or we hit start)
    child = found_goal
    while parent[child] != -1 and parent[child] != start_idx:
        child = parent[child]

    # If the goal is adjacent to start, 'child' is that neighbor.
    if parent[child] == start_idx:
        nr, nc = rc(child)
        r, c = start_r, start_c
        if nr == r - 1 and nc == c:
            return ACTION_UP
        if nr == r + 1 and nc == c:
            return ACTION_DOWN
        if nr == r and nc == c - 1:
            return ACTION_LEFT
        if nr == r and nc == c + 1:
            return ACTION_RIGHT

    # Otherwise either we're on the start or couldn't find a valid step.
    return ACTION_STAY


def bfs_next_action(env, start, goals, *, avoid_agents: bool = True) -> int:
    """
    Same signature and behavior as your original bfs_next_action, but fast via Numba.

    - Pulls `K` and `_occupied` off the env and forwards to the compiled kernel.
    - Accepts: start: (r,c) tuple; goals: list of (r,c) tuples.
    """
    K = env.K
    occupied = np.asarray(env._occupied)  # expected int-like, shape (K,K)
    start_r, start_c = int(start[0]), int(start[1])
    if len(goals) == 0:
        return ACTION_CODES["stay"]
    goals_rc = np.asarray(goals, dtype=np.int32)
    return int(_bfs_next_action_numba(occupied, int(K), start_r, start_c, goals_rc, bool(avoid_agents)))

# # ==========================
# # Constants
# # ==========================

ACTION_CODES = {"stay": 0, "up": 1, "down": 2, "left": 3, "right": 4}
SIDE_TO_DIR = {"left": "right", "right": "left", "up": "down", "down": "up"}
DIR_TO_SIDE = {"right": "left", "left": "right", "down": "up", "up": "down"}
# # for numba type inference
# ACTION_STAY  = 0
# ACTION_UP    = 1
# ACTION_DOWN  = 2
# ACTION_LEFT  = 3
# ACTION_RIGHT = 4

# # 4-neighborhood as a typed numpy array (also Numba-friendly)
# DIRS = np.array([[-1, 0],
#                  [ 1, 0],
#                  [ 0,-1],
#                  [ 0, 1]], dtype=np.int32)

# # ==========================
# # Pathfinding
# # ==========================

# def neighbors_free(env: CoopBlockPush, r: int, c: int):
#     """Get free neighboring cells and their corresponding actions."""
#     K = env.K
#     for dr, dc, action in [(-1, 0, ACTION_CODES["up"]), (1, 0, ACTION_CODES["down"]),
#                           (0, -1, ACTION_CODES["left"]), (0, 1, ACTION_CODES["right"])]:
#         nr, nc = r + dr, c + dc
#         if 0 <= nr < K and 0 <= nc < K and env._occupied[nr, nc] != 2:
#             yield (nr, nc), action



# def bfs_next_action(env: CoopBlockPush, start: Tuple[int, int], 
#                    goals: List[Tuple[int, int]], *, avoid_agents: bool = True) -> int:
#     """BFS pathfinding to return the next action to approach the nearest goal.
#     When avoid_agents is True (default), treat agent-occupied cells as blocked.
#     """
#     if not goals or start in goals:
#         return ACTION_CODES["stay"]
    
#     queue = deque([start])
#     parent = {start: None}
    
#     while queue:
#         current = queue.popleft()
#         if current in goals:
#             # Reconstruct path
#             path = [current]
#             while parent[current] is not None:
#                 current = parent[current]
#                 path.append(current)
#             path.reverse()
            
#             if len(path) >= 2:
#                 (r, c), (nr, nc) = path[0], path[1]
#                 if nr == r - 1 and nc == c:
#                     return ACTION_CODES["up"]
#                 if nr == r + 1 and nc == c:
#                     return ACTION_CODES["down"]
#                 if nr == r and nc == c - 1:
#                     return ACTION_CODES["left"]
#                 if nr == r and nc == c + 1:
#                     return ACTION_CODES["right"]
#             return ACTION_CODES["stay"]
        
#         for neighbor, action in neighbors_free(env, *current):
#             nr, nc = neighbor
#             # Skip agent-occupied cells if requested
#             if avoid_agents and env._occupied[nr, nc] == 1:
#                 continue
#             if neighbor not in parent:
#                 parent[neighbor] = current
#                 queue.append(neighbor)
    
#     return ACTION_CODES["stay"]


# ==========================
# Agent-Block Alignment
# ==========================

def is_aligned_with_block(env: CoopBlockPush, agent: str, block: Block, side: str) -> bool:
    """Check if agent is aligned with the specified block face (including chain formations)."""
    pos = env._agent_positions.get(agent)
    if pos is None:
        return False
    
    # Get cells immediately adjacent to the block face
    face_cells = face_cells_outside(env, block, side)
    if not face_cells:
        return False
    
    # Direct adjacency check
    if pos in face_cells:
        return True
    
    # Extended alignment check for chain formations
    if side == "left":
        away_dr, away_dc = 0, -1
    elif side == "right":
        away_dr, away_dc = 0, 1
    elif side == "up":
        away_dr, away_dc = -1, 0
    elif side == "down":
        away_dr, away_dc = 1, 0
    else:
        return False
    
    agent_r, agent_c = pos
    
    # Check if agent is in a line extending from any face cell
    for face_r, face_c in face_cells:
        if _is_in_line_from_face(agent_r, agent_c, face_r, face_c, away_dr, away_dc):
            if _has_continuous_chain(env, agent_r, agent_c, face_r, face_c, -away_dr, -away_dc):
                return True
    
    return False


def _is_in_line_from_face(agent_r: int, agent_c: int, face_r: int, face_c: int, away_dr: int, away_dc: int) -> bool:
    """Check if agent is in the line extending from the face cell in the away direction."""
    if away_dr == 0:  # horizontal line
        if agent_r != face_r:
            return False
        if away_dc > 0:  # extending right
            return agent_c > face_c
        else:  # extending left
            return agent_c < face_c
    elif away_dc == 0:  # vertical line
        if agent_c != face_c:
            return False
        if away_dr > 0:  # extending down
            return agent_r > face_r
        else:  # extending up
            return agent_r < face_r
    else:
        return False


def _has_continuous_chain(env: CoopBlockPush, start_r: int, start_c: int, 
                         end_r: int, end_c: int, step_dr: int, step_dc: int) -> bool:
    """Check if there's a continuous chain of agents from start to end."""
    current_r, current_c = start_r, start_c
    
    # Verify there's an agent at the face cell
    if (end_r, end_c) not in env._agent_positions.values():
        return False
    
    while (current_r, current_c) != (end_r, end_c):
        if (current_r, current_c) not in env._agent_positions.values():
            return False
        
        current_r += step_dr
        current_c += step_dc
        
        if not (0 <= current_r < env.K and 0 <= current_c < env.K):
            return False
            
        # Prevent infinite loops
        distance = abs(start_r - current_r) + abs(start_c - current_c)
        if distance > 10:
            return False
    
    return True


def count_aligned_agents(env: CoopBlockPush, block: Block, side: str) -> int:
    """Count how many agents are aligned with the specified block face."""
    return sum(1 for agent in env._agent_positions.keys() 
               if is_aligned_with_block(env, agent, block, side))


def all_aligned_positions(env: CoopBlockPush, block: Block, side: str) -> List[Tuple[int, int]]:
    """Get all valid aligned positions for the specified block and side."""
    # Get the immediate face cells
    face_cells = face_cells_outside(env, block, side)
    if not face_cells:
        return []
    
    aligned_positions = set(face_cells)
    
    # Determine the direction away from the block
    if side == "left":
        away_dr, away_dc = 0, -1
    elif side == "right":
        away_dr, away_dc = 0, 1
    elif side == "up":
        away_dr, away_dc = -1, 0
    elif side == "down":
        away_dr, away_dc = 1, 0
    else:
        return list(aligned_positions)
    
    # Extend from each face cell to find chain positions
    for face_r, face_c in face_cells:
        current_r, current_c = face_r + away_dr, face_c + away_dc
        distance = 1
        
        while (0 <= current_r < env.K and 0 <= current_c < env.K and 
               env._occupied[current_r, current_c] != 2 and distance <= 10):
            aligned_positions.add((current_r, current_c))
            current_r += away_dr
            current_c += away_dc
            distance += 1
    
    # Sort by distance from block center
    block_center = (block.r + block.weight // 2, block.c + block.weight // 2)
    return sorted(aligned_positions, key=lambda pos: manhattan_distance(pos, block_center))


# ==========================
# Action Inference
# ==========================

def infer_push_direction_from_alignment(env: CoopBlockPush, agent: str, 
                                       block_id: int) -> int:
    """Infer push direction from agent's current alignment to block face."""
    b = get_block(env, block_id)
    if b is None:
        return ACTION_CODES["stay"]
    
    pos = env._agent_positions.get(agent)
    if pos is None:
        return ACTION_CODES["stay"]
    
    # Map sides to push actions
    side_to_push = {"left": ACTION_CODES["right"], "right": ACTION_CODES["left"], 
                   "up": ACTION_CODES["down"], "down": ACTION_CODES["up"]}
    
    # Check if agent is on a known face
    for side in side_to_push:
        if pos in face_cells_outside(env, b, side):
            return side_to_push[side]
    
    # Default to pushing right toward goal
    return ACTION_CODES["right"]

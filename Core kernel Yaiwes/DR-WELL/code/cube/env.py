from __future__ import annotations
import random
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

import numpy as np
from gymnasium import spaces
from pettingzoo.utils.env import ParallelEnv
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
from numba import njit
import time

# ==========================
# Colors
# ==========================
PALETTE = {
    "bg":        (0,0,0),   # near-white canvas
    "goal":      (157, 212, 177),   # #98c1d9
    "agent":     (152, 193, 217),     # muted maroon (readable on light bg)
    "block_min": (212, 196, 188) ,           # base gray (we'll shade by weight)
    "block_max": (190, 188, 172),
    "grid":      (0, 0, 0),         # black grid, but very low alpha later
    "outline":   (90, 90, 90),      # soft outline
    "id_text":   (20, 20, 25),
}

def _set_matplotlib_defaults():
    import matplotlib as mpl
    mpl.rcParams.update({
        "figure.dpi": 200,
        "font.size": 9.5,
        "axes.facecolor": (1,1,1,0),
        "savefig.facecolor": (1,1,1,0),
        "mathtext.fontset": "cm",   # Computer Modern for subscripts
        "mathtext.rm": "cm",
    })

from dataclasses import dataclass
from typing import List, Tuple, Iterator
import numpy as np

@njit(cache=True)
def _collect_push_chain_numba(block_r, block_c, block_w, occupied, block_at, start_idx, direction, K):
    """
    Find the chain of blocks that must move with start_idx in the given direction.
    Returns (chain_indices, can_move).
    - block_r, block_c, block_w: int32 arrays of shape (B,)
    - occupied:  int8  (K,K): 0 empty, 1 agent, 2 block, 3 goal
    - block_at:  int32 (K,K): index of block at cell, or -1 if none
    - start_idx: int32
    - direction: 1=UP, 2=DOWN, 3=LEFT, 4=RIGHT
    - K: grid size
    """
    # dir mapping: 1:UP, 2:DOWN, 3:LEFT, 4:RIGHT
    dr = 0
    dc = 0
    if direction == 1:
        dr, dc = -1, 0
    elif direction == 2:
        dr, dc = 1, 0
    elif direction == 3:
        dr, dc = 0, -1
    elif direction == 4:
        dr, dc = 0, 1

    B = block_r.shape[0]
    chain = np.empty(B, dtype=np.int32)
    chain_len = 1
    chain[0] = start_idx

    seen = np.zeros(B, dtype=np.uint8)
    seen[start_idx] = 1

    while True:
        front = chain[chain_len - 1]
        fr, fc, fw = block_r[front], block_c[front], block_w[front]
        nr = fr + dr
        nc = fc + dc

        # scan the destination footprint of 'front'
        next_block = -1

        # Iterate cells in the front's destination square
        for r_off in range(fw):
            rr = nr + r_off
            if rr < 0 or rr >= K:
                return chain[:chain_len], False
            for c_off in range(fw):
                cc = nc + c_off
                if cc < 0 or cc >= K:
                    return chain[:chain_len], False

                occ = occupied[rr, cc]
                if occ == 1:
                    # agent blocks the movement
                    return chain[:chain_len], False
                elif occ == 2:
                    # another block; see if it's a *new* block directly in front (touching + overlapping span)
                    b2 = block_at[rr, cc]
                    if b2 != -1 and seen[b2] == 0:
                        br, bc, bw = block_r[b2], block_c[b2], block_w[b2]

                        if direction == 3 or direction == 4:
                            # left/right: must overlap rows and be column-adjacent
                            same_row_span = not (br + bw - 1 < fr or br > fr + fw - 1)
                            touching = ((direction == 4 and bc == fc + fw) or
                                        (direction == 3 and bc + bw == fc))
                            if same_row_span and touching:
                                next_block = b2
                                break
                        else:
                            # up/down: must overlap columns and be row-adjacent
                            same_col_span = not (bc + bw - 1 < fc or bc > fc + fw - 1)
                            touching = ((direction == 2 and br == fr + fw) or
                                        (direction == 1 and br + bw == fr))
                            if same_col_span and touching:
                                next_block = b2
                                break
            if next_block != -1:
                break

        if next_block != -1:
            chain[chain_len] = next_block
            chain_len += 1
            seen[next_block] = 1
            # continue while: check what's ahead of new front
            continue

        # in-bounds, agent-free, no new block ahead → can move
        return chain[:chain_len], True

@njit(cache=True)
def _core_occupied(occ, r, c, w):
    # Return True if any cell in the w×w core is occupied
    for rr in range(r, r + w):
        for cc in range(c, c + w):
            if occ[rr, cc]:
                return True
    return False

@njit(cache=True)
def _moat_clear(occ, r, c, w):
    # Check the 1-cell moat around the block: window [r-1..r+w], [c-1..c+w], clamped to bounds
    K = occ.shape[0]
    r0 = r - 1
    c0 = c - 1
    r1 = r + w
    c1 = c + w
    if r0 < 0: r0 = 0
    if c0 < 0: c0 = 0
    if r1 >= K: r1 = K - 1
    if c1 >= K: c1 = K - 1
    # We already ensure core is empty separately, so *any* True here means moat violation.
    for rr in range(r0, r1 + 1):
        for cc in range(c0, c1 + 1):
            if occ[rr, cc]:
                return False
    return True

@njit(cache=True)
def _write_block(occ, r, c, w):
    for rr in range(r, r + w):
        for cc in range(c, c + w):
            occ[rr, cc] = True

@njit(cache=True)
def first_fit_place(occ, candidates_rc, w):
    """
    occ:        (K,K) boolean array, modified in-place
    candidates: (N,2) int32 array of [r,c] top-left positions (already legal wrt walls/goal)
    w:          int block size

    Returns: index in candidates_rc if placed, else -1
    """
    N = candidates_rc.shape[0]
    for i in range(N):
        r = candidates_rc[i, 0]
        c = candidates_rc[i, 1]
        # Quick reject: core already taken
        if _core_occupied(occ, r, c, w):
            continue
        # Moat must be clear
        if not _moat_clear(occ, r, c, w):
            continue
        # Reserve cells and return success
        _write_block(occ, r, c, w)
        return i
    return -1

@dataclass
class Block:
    id: int
    weight: int  # also the square side length in cells
    # top-left coordinate of the square (row, col)
    r: int
    c: int

    # def cells(self) -> List[Tuple[int, int]]:
    #     return [(self.r + dr, self.c + dc) for dr in range(self.weight) for dc in range(self.weight)]

    # NEW: fast, allocation-free iterator over block cells
    def iter_cells(self) -> Iterator[Tuple[int, int]]:
        """
        Yields (r, c) for each cell in the block without building a list.
        Use this in hot loops instead of `cells()` to avoid per-call list allocations.
        """
        r0, c0, w = self.r, self.c, self.weight
        for dr in range(w):
            rr = r0 + dr
            for dc in range(w):
                yield rr, c0 + dc

    # NEW: vectorized row/col arrays for NumPy ops
    def rc_arrays(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns two 1D int32 arrays (rs, cs) listing all block cell coordinates.
        Useful for vectorized writes like: arr[rs, cs] = value
        """
        w = self.weight
        rs = np.repeat(np.arange(self.r, self.r + w, dtype=np.int32), w)
        cs = np.tile(np.arange(self.c, self.c + w, dtype=np.int32), w)
        return rs, cs

    def border_facing(self, direction: int) -> List[Tuple[int, int]]:
        """Return the list of *block* cells that form the face from which force is applied.
        Directions: 1=UP, 2=DOWN, 3=LEFT, 4=RIGHT (0=STAY).

        This returns the face on the *incoming* side of the push (opposite of motion), so
        that pusher agents stand in the adjacent cells outside the block.
        """
        if direction == 1:  # pushing up -> force comes from below -> bottom row of the block
            return [(self.r + self.weight - 1, self.c + dc) for dc in range(self.weight)]
        if direction == 2:  # pushing down -> force comes from above -> top row of the block
            return [(self.r, self.c + dc) for dc in range(self.weight)]
        if direction == 3:  # pushing left -> force comes from the right -> right column
            return [(self.r + dr, self.c + self.weight - 1) for dr in range(self.weight)]
        if direction == 4:  # pushing right -> force comes from the left -> left column
            return [(self.r + dr, self.c) for dr in range(self.weight)]
        return []

    def next_pos(self, direction: int) -> Tuple[int, int]:
        if direction == 1:  # up
            return (self.r - 1, self.c)
        if direction == 2:  # down
            return (self.r + 1, self.c)
        if direction == 3:  # left
            return (self.r, self.c - 1)
        if direction == 4:  # right
            return (self.r, self.c + 1)
        return (self.r, self.c)


# ==========================
# Environment
# ==========================
class CoopBlockPush(ParallelEnv):
    """
    Cooperative block-pushing environment (grid-based) compatible with PettingZoo Parallel API.

    Key mechanics:
      - Grid is K x K with a goal strip on the rightmost column (col = K-1).
      - Blocks are squares of side length equal to their weight.
      - Agents apply unit force (1) when moving in a direction. A block of weight W
        requires W total *simultaneous* force in the same direction along a straight line
        of adjacent agents to move it 1 cell.
      - Agents can push other agents who push the block (force chains). If the block moves,
        the pushing line of agents also shift forward by 1 cell.
      - When any cell of a block enters the goal column, the block is immediately removed and
        a team reward is granted.

    Observation (per agent): (K, K, 3) float32
      - channel 0: agents (1.0 at agent cells, else 0.0)
      - channel 1: blocks (value = weight, else 0.0)
      - channel 2: goal strip (1.0 in goal column, else 0.0)

    Action space (per agent): Discrete(5)
      0 = stay, 1 = up, 2 = down, 3 = left, 4 = right

    Rewards:
      - step penalty: -step_cost each step (default 0.01)
      - delivery bonus: +deliver_reward * weight (shared equally by all agents)

    Termination:
      - all blocks delivered or max_steps reached.
    """

    metadata = {
        "name": "cooperative_block_push_v0",
        "render_modes": ["rgb_array", "human", None],
        "is_parallelizable": True,
    }

    def __init__(
        self,
        n: Optional[int] = None,
        custom_settings: Optional[Dict] = None,
        max_steps: int = 500,
        render_mode: Optional[str] = None,
        step_cost: float = 0.01,
        deliver_reward: float = 1.0,
        seed: Optional[int] = None,
        jupyter_mode: bool = False,
    ):
        # Determine settings based on input
        self.n = n
        if custom_settings is not None:
            # Use custom settings
            grid_size = custom_settings.get('grid_size', 15)
            num_agents = custom_settings.get('num_agents', 3)
            block_specs = custom_settings.get('block_specs', {2: 1, 3: 1})
        elif n is not None:
            # New difficulty-based defaults based on n
            grid_size = int(max(20, n))
            num_agents = n

            block_weight = n // 2 + 1
            num_blocks = 1
            block_specs = {}

            while block_weight >= 1:
                block_specs[int(block_weight)] = num_blocks
                num_blocks += 1
                block_weight /= 2
        else:
            # Original defaults
            grid_size = 15
            num_agents = 3
            block_specs = {1:3, 2: 2, 3: 1}
        
        assert grid_size >= 5, "grid_size must be >= 5"
        self.K = grid_size
        # IMPORTANT: don't assign to self.num_agents directly; use an internal variable.
        self._init_num_agents = int(num_agents)
        self.block_specs = block_specs
        self.max_steps = max_steps
        self.render_mode = render_mode
        self.step_cost = float(step_cost)
        self.deliver_reward = float(deliver_reward)
        self.jupyter_mode = jupyter_mode
        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)

        # PettingZoo API bookkeeping
        self.possible_agents = [f"agent_{i}" for i in range(self._init_num_agents)]
        self.agents = list(self.possible_agents)
        self.agent_name_mapping = {name: i for i, name in enumerate(self.possible_agents)}

        # Spaces
        self.action_spaces = {agent: spaces.Discrete(5) for agent in self.possible_agents}
        obs_space = spaces.Box(low=0.0, high=float(max(10, max(self.block_specs.keys()) + 1)),
                               shape=(self.K, self.K, 5), dtype=np.float32)
        self.observation_spaces = {agent: obs_space for agent in self.possible_agents}

        # State
        self._agent_positions: Dict[str, Tuple[int, int]] = {}
        self._blocks: List[Block] = []
        self._occupied = None  # integer grid occupancy for fast checks
        self._step_count = 0

        # For pyplot rendering
        self._fig = None
        self._ax = None
        self._im = None
        self._text_artists = []  # track overlay texts for cleanup

    # -------------- Helpers --------------
    def _empty_grid(self) -> np.ndarray:
        # 0 empty, 1 agent, 2 block, 3 goal
        return np.zeros((self.K, self.K), dtype=np.int8)
    
    def _rebuild_occupied(self):
        g = self._empty_grid()
        # goal column
        g[:, self.K - 1] = 3
        # blocks
        for b in self._blocks:
            for r, c in b.iter_cells():
                g[r, c] = 2
        # agents
        for pos in self._agent_positions.values():
            r, c = pos
            g[r, c] = 1
        self._occupied = g

    def _place_entities(self):
        start_time = time.time()
        print('=== Building the environment ===')
        self._agent_positions.clear()
        self._blocks.clear()

        K = self.K
        occ = np.zeros((K, K), dtype=np.bool_)

        # -------- parameters (easy to tweak) --------
        edge_band = 2
        big_block_threshold = 3
        center_avoid_radius = max(1, K // 6)
        goal_col = K - 1

        # -------- vectorized candidates per w --------
        # Valid r,c: leave a 1-cell wall margin and a 1-cell goal margin.
        # r in [1, K-w-2], c in [1, K-w-3] (since we also keep c <= K-w-2 explicitly)
        def candidates_for_w(w: int) -> np.ndarray:
            rmax = K - w - 2
            cmax = K - w - 2
            if rmax < 1 or cmax < 1:
                return np.empty((0, 2), dtype=np.int32)
            rs = np.arange(1, rmax + 1, dtype=np.int32)
            cs = np.arange(1, cmax + 1, dtype=np.int32)
            R, C = np.meshgrid(rs, cs, indexing='ij')  # shape (Nr, Nc)
            # keep distance from goal column: top-left c must be <= K - w - 2 (already by cmax)
            rc = np.stack([R.ravel(), C.ravel()], axis=1).astype(np.int32)
            return rc  # (N,2)

        # -------- numeric bias score (vectorized) --------
        # Higher score = better (earlier tried).
        def score_candidates(rc: np.ndarray, w: int) -> np.ndarray:
            if rc.size == 0:
                return np.empty((0,), dtype=np.float32)
            r = rc[:, 0].astype(np.int32)
            c = rc[:, 1].astype(np.int32)

            # distance to nearest "legal" boundary (respect margins)
            # legal r in [1, K-w-2], c in [1, K-w-2]
            top    = r - 1
            left   = c - 1
            bottom = (K - w - 1) - r
            right  = (K - w - 1) - c
            min_edge = np.minimum(np.minimum(top, left), np.minimum(bottom, right))
            edge_bonus = (min_edge <= edge_band).astype(np.float32)

            # center penalty for big blocks
            if w >= big_block_threshold:
                br = r + (w - 1) * 0.5
                bc = c + (w - 1) * 0.5
                gr = (K - 1) * 0.5
                gc = (K - 1) * 0.5
                in_center = ((np.abs(br - gr) <= center_avoid_radius) &
                            (np.abs(bc - gc) <= center_avoid_radius))
                center_penalty = in_center.astype(np.float32)
            else:
                center_penalty = np.zeros_like(edge_bonus)

            # Simple linear score
            return edge_bonus - center_penalty  # ∈ {1, 0, -1}

        # -------- precompute & cache candidates per size --------
        unique_ws = sorted({int(w) for w in self.block_specs.keys()}, reverse=True)
        cand_by_w = {w: candidates_for_w(w) for w in unique_ws}

        # -------- build and sort block list (largest first) --------
        block_list = []
        for w, cnt in self.block_specs.items():
            block_list.extend([int(w)] * int(cnt))
        block_list.sort(reverse=True)

        # Warm-up compile once (cheap)
        if block_list:
            w0 = block_list[0]
            _ = first_fit_place(occ.copy(), np.array([[1, 1]], dtype=np.int32), w0)

        # -------- place blocks --------
        bid = 0
        for w in block_list:
            if not (1 <= w <= K - 2):
                raise RuntimeError(f"Block weight {w} out of bounds for wall margin.")

            base = cand_by_w[w]
            if base.size == 0:
                raise RuntimeError(f"No legal positions for w={w} under moat/wall constraints.")

            # score + order once; light shuffle within equal-score groups for variety
            scores = score_candidates(base, w)
            order = np.argsort(-scores, kind='stable')  # descending by score
            ordered = base[order]

            # Optional small shuffle on ties:
            # find boundaries where score changes; shuffle segments with same score
            if ordered.size:
                s_sorted = scores[order]
                # indices where score changes
                changes = np.nonzero(np.diff(s_sorted))[0] + 1
                segments = np.concatenate(([0], changes, [len(s_sorted)]))
                for i in range(len(segments) - 1):
                    a, b = segments[i], segments[i + 1]
                    if b - a > 1:
                        self.rng.shuffle(ordered[a:b])

            idx = first_fit_place(occ, ordered, w)
            if idx < 0:
                raise RuntimeError(f"Failed to place block size {w}; try larger grid or fewer/lighter blocks.")

            r, c = int(ordered[idx, 0]), int(ordered[idx, 1])
            self._blocks.append(Block(bid, w, r, c))
            bid += 1

        # -------- place agents on left wall (col 0) --------
        # Prefer empty rows; if fewer than needed (shouldn’t happen with wall moat), fallback scans are trivial.
        candidate_rows = np.arange(K, dtype=int)
        self.rng.shuffle(candidate_rows)
        need = self._init_num_agents
        if need > K:
            raise RuntimeError("Not enough distinct rows on the left wall for all agents.")

        taken = 0
        for agent in self.possible_agents:
            # find next row with col0 free
            while taken < K and occ[candidate_rows[taken], 0]:
                taken += 1
            if taken >= K:
                # fallback linear scan
                found = np.where(~occ[:, 0])[0]
                if found.size == 0:
                    raise RuntimeError("Failed to place agents on the left wall without collision.")
                r = int(found[0])
            else:
                r = int(candidate_rows[taken])
                taken += 1
            occ[r, 0] = True
            self._agent_positions[agent] = (r, 0)

        print(f'=== Done building the environment in {time.time() - start_time:.2f} seconds ===')
        self._rebuild_occupied()

    def _entities_info(self) -> dict:
        return {
            "agents": [
                {
                    "name": agent,
                    "id": self.agent_name_mapping[agent],
                    "pos": tuple(self._agent_positions[agent]),
                }
                for agent in self.possible_agents
                if agent in self._agent_positions
            ],
            "blocks": [
                {
                    "id": b.id,
                    "weight": b.weight,
                    "pos": (b.r, b.c),  # top-left of the square
                }
                for b in self._blocks
            ],
        }

    def _obs(self) -> Dict[str, np.ndarray]:
        # channels: 0=agents mask, 1=blocks weight, 2=goal, 3=agent_id(+1), 4=block_id(+1)
        obs = np.zeros((self.K, self.K, 5), dtype=np.float32)

        # goal strip
        obs[:, self.K - 1, 2] = 1.0

        # blocks: weight (ch1) and id+1 (ch4)
        for b in self._blocks:
            for r, c in b.iter_cells():
                obs[r, c, 1] = float(b.weight)
                obs[r, c, 4] = float(b.id + 1)

        # agents: mask (ch0) and id+1 (ch3)
        for agent, (r, c) in self._agent_positions.items():
            obs[r, c, 0] = 1.0
            obs[r, c, 3] = float(self.agent_name_mapping[agent] + 1)

        # same observation for each live agent (you can customize per-agent later if needed)
        # return {agent: obs.copy() for agent in self.agents}
        return {agent: obs for agent in self.agents}


    def _rgb(self) -> np.ndarray:
        K = self.K
        img = np.zeros((K, K, 3), dtype=np.uint8)
        img[:] = np.array(PALETTE["bg"], np.uint8)

        # goal stripe (right-most column)
        img[:, K - 1, :] = np.array(PALETTE["goal"], np.uint8)

        # blocks: gray shaded by weight (soft ramp)
        for b in self._blocks:
            # shade = int(np.clip(PALETTE["block_min"] - b.weight * 8, 
            #                     PALETTE["block_min"], PALETTE["block_max"]))
            color = np.array(PALETTE["block_min"], np.uint8)
            for r, c in b.iter_cells():
                img[r, c, :] = color

        # agents
        agent_rgb = np.array(PALETTE["agent"], np.uint8)
        for r, c in self._agent_positions.values():
            img[r, c, :] = agent_rgb

        return img

    def _mask_goal_and_blocks(self, ax):
        K = self.K

        # --- goal stripe mask (rightmost column) ---
        goal_rgb = np.array(PALETTE["goal"], dtype=float)/255.0
        ax.add_patch(Rectangle((K-1-0.5, -0.5), 1, K,    # x,y,w,h
                            facecolor=goal_rgb, edgecolor="none", zorder=3))

        # --- block masks (match your shading) ---
        for b in self._blocks:
            rs, cs = b.rc_arrays() # zip(*b.cells())
            r0, c0 = min(rs), min(cs)
            h,  w  = max(rs) - r0 + 1, max(cs) - c0 + 1

            # use your newer, stronger shading:
            shade = int(np.clip(100 + b.weight * 20, 80, 240))
            col = (shade/255.0, shade/255.0, shade/255.0)

            # ax.add_patch(Rectangle((c0-0.5, r0-0.5), w, h,
            #                     facecolor=col, edgecolor=(0,0,0,0.15),
            #                     linewidth=0.5, zorder=3))


    def _draw_grid(self, ax):
        import numpy as np
        K = self.K
        # draw as overlays so they’re visible
        ax.vlines(np.arange(-0.5, K, 1), -0.5, K-0.5, linestyle='-',
                colors=PALETTE['grid'], linewidth=0.6, alpha=0.10, zorder=2)
        ax.hlines(np.arange(-0.5, K, 1), -0.5, K-0.5, linestyle='-',
                colors=PALETTE['grid'], linewidth=0.6, alpha=0.10, zorder=2)

    def _draw_ids_on_axes(self, ax):
        artists = []
        
        # Agent font size: Scale inversely with grid size
        agent_base_font = 256 / self.K
        
        # Agents: scaled text
        for aid, (r, c) in self._agent_positions.items():
            idx = aid.split("_")[-1]
            txt = ax.text(c, r, f"A{idx}", ha="center", va="center",
                          fontsize=agent_base_font, weight="bold", color="white")
            artists.append(txt)
        
        # Blocks: hybrid scaling based on block size
        for b in self._blocks:
            rs, cs = b.rc_arrays()
            r = (min(rs) + max(rs)) / 2
            c = (min(cs) + max(cs)) / 2
            
            block_size = b.weight
            
            # Hybrid scaling: sqrt for small blocks, linear for large blocks
            if block_size <= 4:
                font_multiplier = (block_size ** 0.5)  # sqrt scaling
            else:
                font_multiplier = 2.0 + (block_size - 4) * 0.8  # linear scaling for large blocks
            
            font_multiplier = min(20.0, font_multiplier)
            
            # Calculate font sizes
            block_id_font = max(3, min(150, agent_base_font * font_multiplier))
            block_size_font = max(2, min(120, agent_base_font * font_multiplier * 0.75))
            
            # Text positions scaled with block size
            offset_y1 = 0.15 * block_size
            offset_y2 = 0.2 * block_size
            
            # Block ID
            txt_id = ax.text(c, r - offset_y1,
                             f"B{b.id}",
                             ha="center", va="center",
                             fontsize=block_id_font, weight="bold", color="black")
            artists.append(txt_id)

            # Block size
            txt_size = ax.text(c, r + offset_y2,
                               f"s:{b.weight}",
                               ha="center", va="center",
                               fontsize=block_size_font, color="black")
            artists.append(txt_size)
        return artists

    @staticmethod
    def _dir_to_delta(a: int) -> Tuple[int, int]:
        if a == 1:  # up
            return (-1, 0)
        if a == 2:  # down
            return (1, 0)
        if a == 3:  # left
            return (0, -1)
        if a == 4:  # right
            return (0, 1)
        return (0, 0)  # stay

    # -------------- PettingZoo API --------------
    def reset(self, seed: Optional[int] = None, options: Optional[dict] = None):
        if seed is not None:
            self.rng.seed(seed)
            self.np_rng = np.random.default_rng(seed)
        self.agents = list(self.possible_agents)
        self._step_count = 0
        self._place_entities()
        obs = self._obs()
        entities = self._entities_info()
        infos = {a: entities for a in self.agents}
        return obs, infos
    
    def _block_cells_set(self, b: Block) -> set[tuple[int, int]]:
        """Fast set of cells for a block."""
        return set(b.iter_cells())# set(b.cells())
    
    def _collect_push_chain(self, start_block: "Block", direction: int):
        """
        Thin wrapper around the Numba kernel.
        Builds arrays and a block_at grid, calls the kernel, and returns ([Block], can_move).
        """
        K = self.K
        blocks = self._blocks
        B = len(blocks)

        # Arrays of block geometry
        block_r = np.empty(B, dtype=np.int32)
        block_c = np.empty(B, dtype=np.int32)
        block_w = np.empty(B, dtype=np.int32)
        id_to_idx = {}

        for i, b in enumerate(blocks):
            block_r[i] = b.r
            block_c[i] = b.c
            block_w[i] = b.weight
            id_to_idx[b.id] = i

        start_idx = id_to_idx[start_block.id]

        # Build block_at grid: index of block occupying a cell, else -1
        block_at = np.full((K, K), -1, dtype=np.int32)
        for i, b in enumerate(blocks):
            # use the fast iterator you added
            for rr, cc in b.iter_cells():
                block_at[rr, cc] = i

        # Call numba kernel
        chain_idx, can_move = _collect_push_chain_numba(
            block_r, block_c, block_w,
            self._occupied.astype(np.int8, copy=False),  # 0,1,2,3 encoding
            block_at,
            np.int32(start_idx),
            np.int32(direction),
            np.int32(K)
        )

        # Map indices back to Block objects
        chain_blocks = [blocks[int(i)] for i in chain_idx.tolist()]
        return chain_blocks, bool(can_move)

    def step(self, actions: Dict[str, int]):
        assert set(actions.keys()) == set(self.agents), "Actions must be provided for all live agents"
        self._step_count += 1

        # Clip/validate actions
        for a in self.agents:
            act = int(actions[a])
            if act < 0 or act > 4:
                actions[a] = 0

        # Build quick maps
        pos_to_agent = {pos: agent for agent, pos in self._agent_positions.items()}

        # Track which agents are part of a successful push to avoid double-moving
        moved_agents: set[str] = set()

        # First: resolve block pushes per direction so forces can sum
        # First: resolve block pushes per direction so forces can sum (with chain pushing)
        for direction in [1, 2, 3, 4]:  # up, down, left, right
            dr, dc = self._dir_to_delta(direction)

            # To avoid double-processing blocks that have already been moved in this direction loop
            moved_block_ids: set[int] = set()

            # For each block, collect pushing lines touching its relevant incoming face
            for b in list(self._blocks):
                if b.id in moved_block_ids:
                    continue

                face = b.border_facing(direction)  # incoming face (outside cells will hold pushers)

                # Adjacent cells *outside* the block face (where the pushers stand)
                adj_cells = []
                for r, c in face:
                    rr = r - dr
                    cc = c - dc
                    if 0 <= rr < self.K and 0 <= cc < self.K:
                        adj_cells.append((rr, cc))

                # Build chains of pushing agents per face cell
                pos_to_agent = {pos: agent for agent, pos in self._agent_positions.items()}

                total_force = 0
                lines: List[List[Tuple[int, int]]] = []  # each line is a list of agent positions front->back
                for start_cell in adj_cells:
                    line_positions: List[Tuple[int, int]] = []
                    cur = start_cell
                    while True:
                        if cur in pos_to_agent and actions[pos_to_agent[cur]] == direction:
                            line_positions.append(cur)
                            # extend backwards along -dr,-dc
                            cur = (cur[0] - dr, cur[1] - dc)
                            if not (0 <= cur[0] < self.K and 0 <= cur[1] < self.K):
                                break
                        else:
                            break
                    if line_positions:
                        lines.append(line_positions)
                        total_force += len(line_positions)

                if total_force < b.weight:
                    # Quick fail: not enough force even for the starting block
                    continue

                # Try to collect a push chain (b plus any blocks in front)
                chain, can_move = self._collect_push_chain(b, direction)
                if not can_move:
                    continue

                # Ensure we have enough total force to push the entire chain
                required_force = sum(blk.weight for blk in chain)
                if total_force < required_force:
                    # Not enough pushing power to move all blocks in the chain
                    continue

                # --- Perform the chain move ---
                # Move blocks from front to back to avoid temporary overlaps
                for blk in reversed(chain):
                    nr, nc = blk.next_pos(direction)
                    blk.r, blk.c = nr, nc
                    moved_block_ids.add(blk.id)

                pushing_agent_moves: Dict[str, Tuple[int, int]] = {}
                for line in lines:
                    for pos in line:
                        agent_name = pos_to_agent[pos]
                        nr_a = pos[0] + dr
                        nc_a = pos[1] + dc
                        pushing_agent_moves[agent_name] = (nr_a, nc_a)

                # Resolve collisions by awarding the cell to the smallest-id agent
                targets_to_agents: Dict[Tuple[int, int], List[str]] = {}
                for agent_name, target_pos in pushing_agent_moves.items():
                    targets_to_agents.setdefault(target_pos, []).append(agent_name)

                for target_pos, agents_list in targets_to_agents.items():
                    if not agents_list:
                        continue
                    # smallest numeric id wins (uses agent_name_mapping)
                    winner = min(agents_list, key=lambda a: self.agent_name_mapping[a])
                    # move only the winner
                    self._agent_positions[winner] = target_pos
                    moved_agents.add(winner)
                    # losers are marked processed to avoid double-processing this tick
                    for loser in agents_list:
                        moved_agents.add(loser)
                # After movement, update occupancy (needed before delivery check)
                self._rebuild_occupied()

                # Delivery check for *all* blocks that just moved
                delivered_ids: list[int] = []
                delivered_bonus = 0.0
                for blk in chain:
                    if any(c == self.K - 1 for (_, c) in blk.iter_cells()):
                        delivered_ids.append(blk.id)
                        delivered_bonus += self.deliver_reward * float(blk.weight)

                if delivered_ids:
                    self._blocks = [bx for bx in self._blocks if bx.id not in delivered_ids]
                    self._rebuild_occupied()
                    if delivered_bonus > 0:
                        if not hasattr(self, "_pending_bonus"):
                            self._pending_bonus = 0.0
                        self._pending_bonus += delivered_bonus

        desired: Dict[str, Tuple[int, int]] = {}
        for agent, pos in self._agent_positions.items():
            if agent in moved_agents:
                continue
            act = int(actions[agent])
            dr, dc = self._dir_to_delta(act)
            nr, nc = pos[0] + dr, pos[1] + dc
            if 0 <= nr < self.K and 0 <= nc < self.K:
                # cannot step into blocks
                if self._occupied[nr, nc] == 2:
                    desired[agent] = pos  # stay
                else:
                    desired[agent] = (nr, nc)
            else:
                desired[agent] = pos  # stay

        # Resolve target conflicts: smallest-id agent wins each cell.
        targets_to_agents: Dict[Tuple[int, int], List[str]] = {}
        for agent, target in desired.items():
            if agent in moved_agents:
                continue
            targets_to_agents.setdefault(target, []).append(agent)

        for target, agents_list in targets_to_agents.items():
            # cannot move into blocks or already-occupied-by-block/agent cells
            if self._occupied[target] in (1, 2):
                continue
            # pick winner
            winner = min(agents_list, key=lambda a: self.agent_name_mapping[a])
            # move only the winner; the rest stay
            if winner not in moved_agents:
                self._agent_positions[winner] = target
                moved_agents.add(winner)

        # Rebuild occupancy after all movements
        self._rebuild_occupied()

        # Compute rewards, terminations, truncations
        rewards = {a: -self.step_cost for a in self.agents}
        bonus = getattr(self, "_pending_bonus", 0.0)
        if bonus > 0:
            share = bonus / max(1, len(self.agents))
            for a in rewards:
                rewards[a] += share
            self._pending_bonus = 0.0

        terminated = {a: False for a in self.agents}
        all_delivered = len(self._blocks) == 0
        if all_delivered:
            for a in self.agents:
                terminated[a] = True
        truncated = {a: False for a in self.agents}
        if self._step_count >= self.max_steps:
            for a in self.agents:
                truncated[a] = True

        entities = self._entities_info()
        infos = {a: entities for a in self.agents}

        # If done, clear live agents list per PettingZoo parallel API convention
        if any(terminated.values()) or any(truncated.values()):
            self.agents = []

        obs = self._obs() if self.agents else {}
        return obs, rewards, terminated, truncated, infos
    
    def render(self, return_image=False):
        rgb = self._rgb()
        if self.render_mode == "rgb_array":
            return rgb

        import matplotlib.pyplot as plt
        _set_matplotlib_defaults()

        if self.jupyter_mode:
            try:
                from IPython.display import clear_output
                if not return_image:
                    clear_output(wait=True)
            except Exception:
                pass

        # Reuse figure/axes in non-jupyter mode
        if not self.jupyter_mode and self._fig is not None and self._ax is not None and self._im is not None:
            self._im.set_data(rgb)
            self._ax.set_title(
                f"n: {self.n} | Steps: {self._step_count:02d}",
                pad=1, fontsize=35
            )
            # Remove previous text artists
            for t in getattr(self, "_text_artists", []):
                try:
                    t.remove()
                except Exception:
                    pass
            # Redraw and store new text artists
            self._text_artists = self._draw_ids_on_axes(self._ax)
            self._ax.set_xticks([]); self._ax.set_yticks([])
            self._fig.tight_layout(pad=0)
            self._fig.canvas.draw_idle()
            plt.pause(0.001)
            return rgb

        # Create new figure/axes if needed
        fig, ax = plt.subplots(figsize=(10, 10))
        im = ax.imshow(rgb, interpolation="nearest")   # crisp
        ax.set_title(
            f"n: {self.n} | Steps: {self._step_count:02d}",
            pad=1, fontsize=35
        )
        for s in ax.spines.values():
            s.set_visible(False)

        # self._draw_grid(ax)            # zorder=2  (faint grid everywhere)
        # self._mask_goal_and_blocks(ax) # zorder=3  (covers grid only in those regions)
        self._text_artists = self._draw_ids_on_axes(ax)     # zorder=4  (labels on top)

        ax.set_xticks([])
        ax.set_yticks([])
        fig.tight_layout(pad=0)

        # Save references for future updates
        if not self.jupyter_mode:
            self._fig = fig
            self._ax = ax
            self._im = im

        if return_image:
            return fig, ax
        else:
            plt.show(block=False)

    def close(self):
        if self._fig is not None:
            try:
                plt.close(self._fig)
            except Exception:
                pass
            self._fig, self._ax, self._im = None, None, None
        # Also clear any text artists
        if hasattr(self, "_text_artists"):
            for t in self._text_artists:
                try:
                    t.remove()
                except Exception:
                    pass
            self._text_artists = []

    def __str__(self) -> str:
        """Return a concise string representation of the environment state."""
        block_info = f"{len(self._blocks)} blocks"
        if self._blocks:
            weights = [b.weight for b in self._blocks]
            block_info += f" (weights: {weights})"
        
        agent_info = f"Agents: {dict(self._agent_positions)}"
        step_info = f"Step: {self._step_count}/{self.max_steps}"
        
        return f"Environment: {block_info}, {agent_info}, {step_info}"

    # Optional global state (for MARL algorithms that use it)
    def state(self) -> np.ndarray:
        return self._obs()[self.possible_agents[0]].copy()
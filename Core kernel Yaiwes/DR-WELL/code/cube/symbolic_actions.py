from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

from .env import CoopBlockPush, Block  # do not modify env
from .symbolic_concepts import (
    get_block, face_cells_outside, bfs_next_action,
    ACTION_CODES, SIDE_TO_DIR, DIR_TO_SIDE,
    closest_free_cell, infer_push_direction_from_alignment,
    is_aligned_with_block, count_aligned_agents,
    all_aligned_positions
)

# ==========================
# Symbolic Actions
# ==========================

@dataclass
class MoveToBlock:
    block_id: int
    side: str  # 'left'|'right'|'up'|'down'
    timeout: int = 40

@dataclass
class Rendezvous:
    """Wait for other agents to arrive at the rendezvous point."""
    block_id: int
    side: str
    need: int
    timeout: int = 10

@dataclass
class Push:
    """Push a block. Direction is inferred from agent's current alignment."""
    block_id: int
    steps: int = 1
    timeout: int = 30

@dataclass
class YieldFace:
    """Move away from a block face."""
    block_id: int
    side: str
    steps: int = 2
    timeout: int = 30

@dataclass
class Wait:
    steps: int = 1
    timeout: int = 30

@dataclass
class WaitAgents:
    """Wait until at least `need` agents are available (idle) in the team."""
    need: int
    timeout: int


# ==========================
# Controller: executes symbolic programs
# ==========================

class SymbolicController:
    """Executes per-agent symbolic programs using the CoopBlockPush environment."""
    
    _ACT = ACTION_CODES
    side_to_dir = SIDE_TO_DIR
    dir_to_side = DIR_TO_SIDE

    def __init__(self, env: CoopBlockPush, plans: Dict[str, List[object]], agents = None, wm = None):
        self.env = env
        self.wm = wm
        self.agents = agents
        self.plans = {a: list(p) for a, p in plans.items()}
        self.idx = {a: 0 for a in plans}
        self.rem = {a: 0 for a in plans}
        # Context for tracking current block/side assignments
        self.ctx = {a: {"block_id": None, "side": None} for a in plans}
        
        # Action execution mapping
        self._action_handlers = {
            MoveToBlock: self._exec_MoveToBlock,
            Rendezvous: self._exec_Rendezvous,
            Push: self._exec_Push,
            YieldFace: self._exec_YieldFace,
            Wait: self._exec_Wait,
            WaitAgents: self._exec_WaitAgents,
        }
        # Coordination structures
        self._barriers = {}  # key: (block_id, side, need) -> {"arrived": set(), "release_step": None}
        # Slot claims for MoveToBlock face ordering and deconfliction
        # key: (block_id, side) -> { agent_id: (r, c) }
        self._slot_claims = {}
        # Group push sessions and rendezvous→push handoff groups
        # key: (block_id, side)
        self._push_sessions = {}
        self._next_push_groups = {}


    def _set_state(self, agent: str, machine_state: str, meta: Optional[dict] = None):
        """Update agent state in world model if available."""
        if self.wm is not None and hasattr(self.wm, "set_agent_state"):
            self.wm.set_agent_state(agent, machine_state, meta or {})


    def _exec_MoveToBlock(self, agent: str, instr: MoveToBlock) -> int:
        """Move agent to the specified side of a block, with dynamic re-planning and anti-deadlock coordination."""
        b = get_block(self.env, instr.block_id)
        if b is None:
            # If the block disappeared, finish
            self.idx[agent] += 1
            return self._ACT["stay"]

        timeout_key = f"{agent}_MoveToBlock_{instr.block_id}_{instr.side}_{self.idx[agent]}"
        # Initialize timeout on first entry
        if timeout_key not in self.rem:
            self.rem[timeout_key] = instr.timeout
            self._set_state(agent, "moving", {"block_id": instr.block_id, "side": instr.side})
        # Decrement and check timeout
        self.rem[timeout_key] -= 1
        if self.rem[timeout_key] <= 0:
            # Timeout: abort action
            self.rem.pop(timeout_key, None)
            self.idx[agent] += 1
            self._set_state(agent, "timeout", {"action": "MoveToBlock"})
            return self._ACT["stay"]

        # Current position and alignment status
        pos = self.env._agent_positions[agent]
        is_currently_aligned = is_aligned_with_block(self.env, agent, b, instr.side)

        # Compute the set of face-adjacent target cells on this block side
        face_cells = face_cells_outside(self.env, b, instr.side)
        if not face_cells:
            # No valid face cells (e.g., block against wall) – safely do nothing this tick
            return self._ACT["stay"]

        # Determine movement direction vectors for this side (to go "behind" the face)
        if instr.side == "left":
            dr, dc = 0, -1
        elif instr.side == "right":
            dr, dc = 0, 1
        elif instr.side == "up":
            dr, dc = -1, 0
        else:  # "down"
            dr, dc = 1, 0

        # --- Simple approach: no slot claiming, just go to best available position ---
        # Helper function for distance calculation
        def dist_to_block_rect(cell):
            r, c = cell
            top, left = b.r, b.c
            bottom = b.r + b.weight - 1
            right = b.c + b.weight - 1
            dv = 0 if top <= r <= bottom else (top - r if r < top else r - bottom)
            dh = 0 if left <= c <= right else (left - c if c < left else c - right)
            return dv + dh

        def centrality_score(cell):
            r, c = cell
            if instr.side in ("left", "right"):
                face_center = b.r + (b.weight - 1) / 2.0
                return abs(r - face_center)
            else:  # "up" or "down"
                face_center = b.c + (b.weight - 1) / 2.0
                return abs(c - face_center)
        
        # Current occupied positions
        occupied = set(self.env._agent_positions.values())
        
        # Score face cells by: 1) distance to block, 2) centrality
        def slot_priority(cell):
            dist = dist_to_block_rect(cell)
            cent = centrality_score(cell)
            is_occupied = cell in occupied
            
            # If agent is already aligned, strongly prefer slots that are closer/more central than current position
            if is_currently_aligned:
                current_dist = dist_to_block_rect(pos)
                current_cent = centrality_score(pos)
                # Heavily penalize slots that are worse than current position
                if dist > current_dist or (dist == current_dist and cent > current_cent):
                    return (10, dist, cent)  # High penalty for worse positions
            
            # Lower score = higher priority
            # Prioritize: free > occupied, then distance, then centrality
            availability_penalty = 0 if not is_occupied else 1
            return (availability_penalty, dist, cent)
        
        # Find the best available face cell (first come, first serve)
        available_face_cells = [cell for cell in face_cells if cell not in occupied]
        if available_face_cells:
            sorted_face_cells = sorted(available_face_cells, key=slot_priority)
            target_face = sorted_face_cells[0]
        else:
            # All face cells occupied, pick best overall (may need to wait or chain)
            sorted_face_cells = sorted(face_cells, key=slot_priority)
            target_face = sorted_face_cells[0]

        # --- Check for alignment completion conditions ---
        # Only terminate if agent is aligned AND there's no better position available anywhere on the face
        if is_currently_aligned:
            aligned_positions = all_aligned_positions(self.env, b, instr.side)
            
            # Find ALL free aligned positions (not restricted to claimed lane)
            free_aligned_positions = [p for p in aligned_positions if p not in set(self.env._agent_positions.values())]
            
            # Check if there's a better position available anywhere on this face
            current_dist = dist_to_block_rect(pos)
            current_cent = centrality_score(pos)
            
            has_better_position = False
            if free_aligned_positions:
                for candidate in free_aligned_positions:
                    cand_dist = dist_to_block_rect(candidate)
                    cand_cent = centrality_score(candidate)
                    # Better if: closer to block OR (same distance AND more central)
                    if (cand_dist < current_dist) or (cand_dist == current_dist and cand_cent < current_cent):
                        has_better_position = True
                        break
            
            # Only complete if aligned AND no better position exists anywhere
            if not has_better_position:
                self.ctx[agent]["block_id"] = b.id
                self.ctx[agent]["side"] = instr.side
                self._set_state(agent, "at_face", {"block_id": b.id, "side": instr.side})
                self.rem.pop(timeout_key, None)
                self.idx[agent] += 1
                return self._ACT["stay"]

        # --- Move toward the target or staging position ---
        occupied = set(self.env._agent_positions.values())
        goals = []
        
        # If already aligned, prioritize better aligned positions anywhere on the face
        if is_currently_aligned:
            aligned_positions = all_aligned_positions(self.env, b, instr.side)
            
            # Find better aligned positions (closer to block or more central) anywhere on face
            current_dist = dist_to_block_rect(pos)
            current_cent = centrality_score(pos)
            
            better_aligned_positions = []
            for candidate in aligned_positions:
                if candidate not in occupied:
                    cand_dist = dist_to_block_rect(candidate)
                    cand_cent = centrality_score(candidate)
                    if (cand_dist < current_dist) or (cand_dist == current_dist and cand_cent < current_cent):
                        better_aligned_positions.append(candidate)
            
            # Sort better positions by priority (distance first, then centrality)
            if better_aligned_positions:
                better_aligned_positions.sort(key=lambda p: (dist_to_block_rect(p), centrality_score(p)))
                goals = better_aligned_positions
        
        # If not aligned or no better aligned positions, prioritize target face then fallback
        if not goals:
            if target_face and target_face not in occupied:
                goals = [target_face]
            else:
                # plan to behind the face (one step outward)
                behind_positions = []
                if target_face:
                    nr, nc = target_face[0] + dr, target_face[1] + dc
                    if 0 <= nr < self.env.K and 0 <= nc < self.env.K and self.env._occupied[nr, nc] != 2:
                        behind_positions.append((nr, nc))
                if not behind_positions:
                    # consider behind any face cell on this side
                    for fr, fc in sorted(face_cells, key=lambda rc: (rc[0], rc[1])):
                        nr, nc = fr + dr, fc + dc
                        if 0 <= nr < self.env.K and 0 <= nc < self.env.K and self.env._occupied[nr, nc] != 2:
                            behind_positions.append((nr, nc))
                free_behind = [p for p in behind_positions if p not in occupied]
                goals = free_behind if free_behind else behind_positions

        # === Normal approach: try to step toward face/behind goal(s) first
        if goals:
            target = goals[0]
            avoid_flag = True
            # if target is occupied by an already-aligned teammate, we may allow threading (chain formation)
            if self.env._occupied[target[0], target[1]] == 1:
                for other_agent, other_pos in self.env._agent_positions.items():
                    if other_pos == target and is_aligned_with_block(self.env, other_agent, b, instr.side):
                        avoid_flag = False
                        break
            step = bfs_next_action(self.env, pos, goals, avoid_agents=avoid_flag)
            if step != self._ACT["stay"]:
                return step

        # === Fallback: no path behind → attach at the SIDE of a teammate on my lane
        # This keeps the lane clear and avoids deadlock when the corridor is sealed.
        def neighbors4(rc):
            r, c = rc
            return [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]

        # teammates aligned with this block & side form the lane; attach next to any of them
        lane_teammates = [
            a2 for a2 in self.env._agent_positions
            if a2 != agent and is_aligned_with_block(self.env, a2, b, instr.side)
        ]
        side_attach_candidates = []
        for a2 in lane_teammates:
            p2 = self.env._agent_positions[a2]
            for nb in neighbors4(p2):
                r, c = nb
                if not (0 <= r < self.env.K and 0 <= c < self.env.K):
                    continue
                if self.env._occupied[r, c] == 2:  # not into blocks
                    continue
                if nb in occupied:                 # only free side cells
                    continue
                # Avoid stepping onto the face/behind lane cells themselves to keep the queue clear
                # compute simple lane membership check: same row for left/right, same col for up/down
                on_lane = ((instr.side in ("left", "right") and target_face and nb[0] == target_face[0]) or
                        (instr.side in ("up", "down")   and target_face and nb[1] == target_face[1]))
                if on_lane:
                    continue
                side_attach_candidates.append(nb)

        # deduplicate while preserving order, then try BFS
        if side_attach_candidates:
            seen = set()
            side_attach = []
            for rc in side_attach_candidates:
                if rc not in seen:
                    seen.add(rc)
                    side_attach.append(rc)
            step2 = bfs_next_action(self.env, pos, side_attach, avoid_agents=True)
            if step2 != self._ACT["stay"]:
                return step2

        # Nothing better this tick
        return self._ACT["stay"]

    def _exec_Rendezvous(self, agent: str, instr: Rendezvous) -> int:
        b = get_block(self.env, instr.block_id)
        if b is None:
            self.idx[agent] += 1
            return self._ACT["stay"]

        timeout_key = f"{agent}_Rendezvous_{instr.block_id}_{instr.side}_{instr.need}_{self.idx[agent]}"
        key = (instr.block_id, instr.side, instr.need)
        rec = self._barriers.setdefault(key, {"arrived": set(), "release_step": None})

        # 1) On first entry for this agent, start its timer and mark 'waiting'
        if timeout_key not in self.rem:
            self.rem[timeout_key] = instr.timeout
            self._set_state(agent, "waiting",
                            {"mode": "rendezvous", "block_id": instr.block_id, "side": instr.side})

        # Immediate alignment check - terminate if agent is not aligned with the correct side
        if not is_aligned_with_block(self.env, agent, b, instr.side):
            self.rem.pop(timeout_key, None)
            rec["arrived"].discard(agent)
            self._set_state(agent, "not_aligned", {"action": "Rendezvous", "required_side": instr.side})
            self.idx[agent] += 1
            return self._ACT["stay"]

        # Timeout handling
        self.rem[timeout_key] -= 1
        if self.rem[timeout_key] <= 0:
            self.rem.pop(timeout_key, None)
            rec["arrived"].discard(agent)
            self._set_state(agent, "timeout", {"action": "Rendezvous"})
            self.idx[agent] += 1
            return self._ACT["stay"]

        # 2) If aligned and truly at this same Rendezvous step, register arrival
        step = self.plans[agent][self.idx[agent]]
        if (isinstance(step, Rendezvous) and
            step.block_id == instr.block_id and step.side == instr.side and step.need == instr.need and
            is_aligned_with_block(self.env, agent, b, instr.side)):
            rec["arrived"].add(agent)

        # 3) If quorum reached and no release scheduled, set release to NEXT env step
        if len(rec["arrived"]) >= instr.need and rec["release_step"] is None:
            rec["release_step"] = self.env._step_count + 1  # ensure at least one tick of 'waiting' is recorded

        # 4) On/after release step: atomically advance everyone, clear timers, mark ready
        if rec["release_step"] is not None and self.env._step_count >= rec["release_step"]:
            participants = list(rec["arrived"])
            # Seed a push group for the next step so Push can synchronize the same set
            # Use current side for keying; participants will be released together after push completes
            push_key = (instr.block_id, instr.side)
            self._next_push_groups[push_key] = {
                "participants": set(participants),
                "expiry": self.env._step_count + 3,
            }
            for a in participants:
                tk = f"{a}_Rendezvous_{instr.block_id}_{instr.side}_{instr.need}_{self.idx[a]}"
                if tk in self.rem:
                    self.rem.pop(tk, None)
                self._set_state(a, "rendezvous_ready",
                                {"block_id": instr.block_id, "side": instr.side, "count": len(participants)})
                self.idx[a] += 1
            # reset barrier record so a future Rendezvous can reuse the key safely
            rec["arrived"].clear()
            rec["release_step"] = None
            return self._ACT["stay"]

        # Not released yet; keep everyone waiting
        return self._ACT["stay"]

    def _exec_Push(self, agent: str, instr: Push) -> int:
        """Push as a synchronized group: count steps only when the block moves, then release all together."""
        b = get_block(self.env, instr.block_id)
        if b is None:
            self.idx[agent] += 1
            return self._ACT["stay"]

        # Determine the side we are pushing from (based on prior alignment)
        side = self.ctx.get(agent, {}).get("side")
        if side is None:
            # Fallback: try to infer from current alignment
            # Map push action back to a side (approximate); default to 'left'
            push_act = infer_push_direction_from_alignment(self.env, agent, instr.block_id)
            side = self.dir_to_side.get(push_act, "left")

        key = (instr.block_id, side)

        # Initialize or attach to an existing session
        sess = self._push_sessions.get(key)
        if sess is None:
            # Seed participants from rendezvous handoff if available (and fresh)
            npg = self._next_push_groups.get(key)
            if npg and self.env._step_count <= npg.get("expiry", -1):
                participants = set(a for a in npg["participants"] if a in self.env.agents)
                # Clear the handoff so it doesn't leak into a later unrelated push
                self._next_push_groups.pop(key, None)
            else:
                # Fallback: discover participants at the same Push step for this block and side
                participants = set()
                for a in self.env.agents:
                    if a in self.plans and self.idx.get(a, 0) < len(self.plans[a]):
                        st = self.plans[a][self.idx[a]]
                        if isinstance(st, Push) and st.block_id == instr.block_id and self.ctx.get(a, {}).get("side") == side:
                            participants.add(a)

            # Determine shared remaining based on the max of requested steps among participants
            target = 0
            for a in participants:
                st = self.plans[a][self.idx[a]]
                if isinstance(st, Push) and st.block_id == instr.block_id:
                    target = max(target, getattr(st, "steps", instr.steps))
            sess = {
                "participants": participants,
                "remaining": target if target > 0 else instr.steps,
                "last_block_pos": (b.r, b.c),
                "release_step": None,
            }
            self._push_sessions[key] = sess

        # Standard per-agent timeout handling still applies, but completion is synchronized
        timeout_key = f"{agent}_Push_{instr.block_id}_{side}_{self.idx[agent]}"
        if timeout_key not in self.rem:
            self.rem[timeout_key] = instr.timeout
            self._set_state(agent, "pushing", {"block_id": instr.block_id, "steps": sess["remaining"]})
        self.rem[timeout_key] -= 1
        if self.rem[timeout_key] <= 0:
            # Remove this agent from the session and advance it independently
            self.rem.pop(timeout_key, None)
            if agent in sess["participants"]:
                sess["participants"].discard(agent)
            self.idx[agent] += 1
            self._set_state(agent, "timeout", {"action": "Push"})
            return self._ACT["stay"]

        # If session has no participants left, clean it up
        if not sess["participants"]:
            self._push_sessions.pop(key, None)
            # Continue with agent state; if it was the last one, it's already advanced above on timeout
            # Otherwise keep pushing until it finishes on its own

        # Count a shared push step only when the block actually moves
        current_pos = (b.r, b.c)
        if current_pos != sess["last_block_pos"] and sess["remaining"] > 0:
            sess["remaining"] -= 1
            sess["last_block_pos"] = current_pos
            if sess["remaining"] <= 0 and sess["release_step"] is None:
                sess["release_step"] = self.env._step_count + 1

        # If it's time to release, advance all still-participating agents together
        if sess.get("release_step") is not None and self.env._step_count >= sess["release_step"]:
            participants = list(sess["participants"])  # snapshot
            for a in participants:
                tk = f"{a}_Push_{instr.block_id}_{side}_{self.idx[a]}"
                if tk in self.rem:
                    self.rem.pop(tk, None)
                self._set_state(a, "push_complete", {"block_id": instr.block_id})
                self.idx[a] += 1
            # End the session
            self._push_sessions.pop(key, None)
            return self._ACT["stay"]

        # Otherwise keep pushing
        return infer_push_direction_from_alignment(self.env, agent, instr.block_id)

    def _exec_YieldFace(self, agent: str, instr: YieldFace) -> int:
        """Move away from specified block face."""
        timeout_key = f"{agent}_YieldFace_{instr.block_id}_{instr.side}_{self.idx[agent]}"
        
        # Initialize
        if timeout_key not in self.rem:
            self.rem[timeout_key] = instr.timeout
            self.ctx[agent]["yield_remaining"] = instr.steps
            self._set_state(agent, "yielding", {"block_id": instr.block_id, "side": instr.side})
        
        # Timeout handling
        self.rem[timeout_key] -= 1
        if self.rem[timeout_key] <= 0:
            self.rem.pop(timeout_key, None)
            self.idx[agent] += 1
            self._set_state(agent, "timeout", {"action": "YieldFace"})
            return self._ACT["stay"]
        
        # Check completion
        remaining = self.ctx[agent].get("yield_remaining", 0)
        if remaining <= 0:
            self.rem.pop(timeout_key, None)
            self.idx[agent] += 1
            self._set_state(agent, "yield_complete")
            return self._ACT["stay"]
        
        # Move away from face using direction mapping
        side_to_action = {
            "left": self._ACT["left"],
            "right": self._ACT["right"], 
            "up": self._ACT["up"],
            "down": self._ACT["down"]
        }
        
        away_action = side_to_action.get(instr.side, self._ACT["stay"])
        self.ctx[agent]["yield_remaining"] = remaining - 1
        return away_action

    def _exec_Wait(self, agent: str, instr: Wait) -> int:
        """Wait for specified number of steps."""
        timeout_key = f"{agent}_Wait_{self.idx[agent]}"
        
        if timeout_key not in self.rem:
            self.rem[timeout_key] = instr.steps
            self._set_state(agent, "waiting", {"mode": "time", "steps": instr.steps})
        
        self.rem[timeout_key] -= 1
        if self.rem[timeout_key] <= 0:
            self.rem.pop(timeout_key, None)
            self.idx[agent] += 1
            self._set_state(agent, "wait_complete")
        
        return self._ACT["stay"]

    def _exec_WaitAgents(self, agent: str, instr: WaitAgents) -> int:
        """Wait until enough agents are available."""
        timeout_key = f"{agent}_WaitAgents_{instr.need}_{self.idx[agent]}"
        
        if timeout_key not in self.rem:
            self.rem[timeout_key] = instr.timeout
            self._set_state(agent, "waiting", {"mode": "agents_available", "need": instr.need})
        
        # Check timeout
        self.rem[timeout_key] -= 1
        if self.rem[timeout_key] <= 0:
            self.rem.pop(timeout_key, None)
            self.idx[agent] += 1
            self._set_state(agent, "timeout", {"action": "WaitAgents"})
            return self._ACT["stay"]
        
        # Count available agents (using world model if available)
        if self.wm is not None and hasattr(self.wm, 'agents'):
            available = sum(1 for a, rec in self.wm.agents.items() 
                          if a in self.env.agents and rec.status in ("idle", "waiting"))
        else:
            # Simple fallback: count agents that finished their plans
            available = sum(1 for a in self.env.agents 
                          if self.idx.get(a, 0) >= len(self.plans.get(a, [])))
        
        if available >= instr.need:
            self.rem.pop(timeout_key, None)
            self.idx[agent] += 1
            self._set_state(agent, "agents_ready", {"available": available, "need": instr.need})
        
        return self._ACT["stay"]

    def done(self) -> bool:
        """Check if all agents have completed their plans."""
        return all(self.idx.get(a, 0) >= len(self.plans.get(a, [])) for a in self.env.agents)

    def act(self) -> Dict[str, int]:
        """Execute one step for all agents."""
        actions: Dict[str, int] = {}
        for a in self.env.agents:
            if a not in self.plans or self.idx[a] >= len(self.plans[a]):
                self._set_state(a, "idle")
                actions[a] = self._ACT["stay"]
                continue
            
            step = self.plans[a][self.idx[a]]
            
            # Use action handler mapping for cleaner dispatch
            handler = self._action_handlers.get(type(step))
            if handler:
                actions[a] = handler(a, step)
            else:
                # Unknown step, skip it
                self.idx[a] += 1
                self._set_state(a, "idle")
                actions[a] = self._ACT["stay"]
        return actions
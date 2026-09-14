
#!/usr/bin/env python3
"""
main_learning.py
=================
A learning pipeline that:
1) Runs N episodes (like main_llm), saving a clean JSON trace per episode.
2) Builds/updates a Multiverse "universe" after each episode (JSON + PNG).
3) On subsequent steps, enhances communication & planning with retrieval from the universe graph
   (EnhancedMessageBoard + a plan-revision pass that uses historical insights).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from typing import Dict, List, Optional

# --- Environment / Controllers ---
from cube.env import CoopBlockPush
from cube.symbolic_actions import SymbolicController

# --- Framework pieces from this repo ---
from llm_agent import LLMAgent, LLMConfig, LLMAgentManager, client as azure_client
from communication import EnhancedMessageBoard
from llm_templates import (
    AgentPlan, RevisionOutput, action_to_string,
    PLANNING_SYSTEM_PROMPT, PLANNING_USER_TEMPLATE,
    REVISION_SYSTEM_PROMPT, REVISION_USER_TEMPLATE,
    EnhancedTemplates, create_enhanced_templates
)
from world_model import create_world_model_from_log
from multiverse import Multiverse
from retriever import UniverseRetriever

# ------------------------------
# Small IO helpers
# ------------------------------
def ensure_dir(path: str):
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def write_text(path: str, text: str):
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

# ------------------------------
# Universe manager (persist across episodes)
# ------------------------------
class UniverseStore:
    """Keeps a Multiverse on disk under runs/universe/ and updates it per episode."""
    def __init__(self, root: str = "runs/universe"):
        self.root = root
        os.makedirs(self.root, exist_ok=True)
        self.json_path = os.path.join(self.root, "universe_graph.json")
        self.png_path = os.path.join(self.root, "universe_graph.png")
        self.mv = Multiverse(name="UNIVERSE")

        # If a universe already exists, try to load its episodes back
        # (We don't reconstruct objects per-episode here; we will re-add as episodes appear)
        if os.path.exists(self.json_path):
            try:
                # Rehydrate episodes quickly from stored universe_data episodes
                data = json.load(open(self.json_path, "r", encoding="utf-8"))
                # We don't try to rebuild mv from scratch; we'll just append as we go this run.
            except Exception as e:
                print(f"[UNIVERSE] Could not load existing universe: {e}")

    def update_with_episode_worldmodel(self, episode_world_model_json: str, episode_id: Optional[str] = None):
        """Add a world model JSON to the universe and write updated JSON and PNG."""
        print(f"[UNIVERSE] Adding episode WM: {episode_world_model_json}")
        self.mv.add_world_model(episode_world_model_json, episode_id=episode_id)
        # Build retrieval views (COG/TCG/PDG)
        self.mv.build_views(bucket=10)
        # Save JSON and PNG
        self.mv.export_graph(self.json_path)
        self.mv.visualize(self.png_path, show_plot=False)
        print(f"[UNIVERSE] Updated: {self.json_path} and {self.png_path}")

    def json(self) -> str:
        return self.json_path

# ------------------------------
# Agent construction
# ------------------------------
def build_agents(env, manager: LLMAgentManager, n_agents: int, cfg: LLMConfig) -> Dict[str, LLMAgent]:
    agents: Dict[str, LLMAgent] = {}
    for i in range(n_agents):
        aid = f"agent_{i}"
        a = LLMAgent(aid, env, manager, cfg, plan=[])
        agents[aid] = a
        manager.add_agent(a)
    return agents

# ------------------------------
# Retrieval-enhanced communication
# ------------------------------
def run_enhanced_comm_round(agents: Dict[str, LLMAgent], manager: LLMAgentManager, step: int, universe_json: Optional[str]) -> List[str]:
    """Two-phase comm (proposals -> commitments) using EnhancedMessageBoard with historical insights."""
    participants = [a.id for a in agents.values() if a.should_plan()]
    if not participants:
        print("No agents need to communicate/plan at this step.")
        return []

    board = EnhancedMessageBoard(universe_json_path=universe_json)
    # Proposal phase with context on current session
    board.start_proposal_round(current_timestep=step, num_agents=len(agents))
    for aid in participants:
        agents[aid].propose_task(board)

    # Commitment phase
    board.start_commitment_round()
    for aid in participants:
        agents[aid].commit_to_task(board)
    board.complete_communication()

    # Apply assignments to agents & log once
    assignments = board.get_agent_assignments()
    for aid, d in assignments.items():
        ag = agents[aid]
        ag.assigned_block = d['assigned_block']
        ag.task_name = d['task_name']

    manager.log_communication_round(
        step=step,
        participants=participants,
        communication_type="enhanced_comm",
        result={aid: d['assigned_block'] for aid, d in assignments.items()}
    )
    return participants

# ------------------------------
# Plan + Retrieval-enhanced revision
# ------------------------------
def _fmt_position(p):
    try:
        return f"({p[0]},{p[1]})"
    except Exception:
        return str(p)

def _obs_for(agent: LLMAgent) -> dict:
    return agent.observe()

def _revise_plan_with_history(agent: LLMAgent, env, all_agents: Dict[str, LLMAgent], enhanced_templates: Optional[EnhancedTemplates], shared_file: str):
    """Run agent.plan() (initial), then a revision pass that uses REVISION_* template and writes shared insights."""
    # 1) initial plan (uses LLMAgent's built-in planning flow)
    agent.plan(all_agents=all_agents)
    
    # Clean the initial plan steps to remove steps= and other parameter formats
    if agent.plan_steps:
        cleaned_plan_steps = [clean_action_string(step) for step in agent.plan_steps]
        agent.plan_steps = cleaned_plan_steps

    # 2) revision pass, pulling extra context + historical insights via EnhancedTemplates
    obs = _obs_for(agent)
    previous_plan = "\n".join(agent.plan_steps) if agent.plan_steps else "(none)"
    file_text = read_text(shared_file)
    
    # Print shared file content for debugging
    if file_text.strip():
        print(f"[SHARED_INFO] Using shared insights from {shared_file}:")
        print(f"[SHARED_INFO] Content length: {len(file_text)} characters")
        print(f"[SHARED_INFO] Content preview: {file_text[:200]}...")
    else:
        print(f"[SHARED_INFO] No shared insights available yet")

    # Enhanced planning user template (inject insights) for display to the LLM in revision context
    # Build the standard revision user message, but use enhanced templates if available
    template_kwargs = {
        "agent": obs["agent_id"],
        "my_position": _fmt_position(obs.get("my_position")),
        "target_block": agent.assigned_block,
        "task_name": agent.task_name,
        "team_size": len(all_agents),
        "env_info": f"Grid: {obs.get('grid_size','?')}x{obs.get('grid_size','?')}",
        "blocks_info": "\n".join([f"Block {b.id}: weight={b.weight}, position=({b.r},{b.c})" for b in getattr(env, "_blocks", [])]) if hasattr(env, "_blocks") else "No blocks info",
        "other_agents_state": "\n".join([f"{aid}: Position {pos}" for aid, pos in obs.get("agent_positions", {}).items() if aid != agent.id]) or "No other agent position data available",
        "all_committed_tasks": "\n".join([f"{aid}: {getattr(a, 'task_name', 'No_Task')} (Block {getattr(a,'assigned_block','None')})" for aid,a in all_agents.items()]) or "No other agent commitments available",
        "previous_plan": previous_plan,
        "file_text": file_text or "(empty)"
    }

    # Try to use enhanced templates for historical insights
    if enhanced_templates and enhanced_templates.retriever:
        print(f"\n=== PLANNING REVISION FOR {agent.id} ===")
        print(f"[ENHANCED_REVISION] Using historical insights for {agent.task_name}")
        
        # Get enhanced template with historical insights
        try:
            rev_user = enhanced_templates.get_enhanced_revision_user_template(**template_kwargs)
            print(f"[ENHANCED_REVISION] Historical insights injected for planning revision")
        except Exception as e:
            print(f"[ENHANCED_REVISION] Failed to get enhanced template: {e}")
            rev_user = REVISION_USER_TEMPLATE.format(**template_kwargs)
    else:
        print(f"\n=== PLANNING REVISION FOR {agent.id} ===")
        print(f"[BASIC_REVISION] No historical insights available")
        rev_user = REVISION_USER_TEMPLATE.format(**template_kwargs)

    # Print what we're feeding to the LLM for revision
    print(f"\n[LLM_INPUT] {agent.id} REVISION:")
    print("=" * 60)
    print(rev_user)
    print("=" * 60)

    # Call Azure client with structured output for revision
    try:
        res = azure_client.beta.chat.completions.parse(
            model=agent.cfg.model,
            messages=[
                {"role": "system", "content": REVISION_SYSTEM_PROMPT},
                {"role": "user", "content": rev_user}
            ],
            response_format=RevisionOutput,
            temperature=agent.cfg.temperature,
            max_tokens=agent.cfg.max_tokens
        )
        parsed = res.choices[0].message.parsed if res and res.choices else None
    except Exception as e:
        print(f"[REVISION] LLM revision failed for {agent.id}: {e}")
        parsed = None

    if not parsed:
        return

    # 3) Convert revised actions to strings compatible with controller
    grid_size = obs.get("grid_size", 7)  # default fallback
    try:
        new_steps: List[str] = []
        for act in parsed.plan:
            action_str = action_to_string(act, grid_size)
            # Clean the action string to remove steps= and other parameter formats
            clean_action_str = clean_action_string(action_str)
            new_steps.append(clean_action_str)
        if new_steps:
            agent.plan_steps = new_steps
            agent.plan_index = 0
            # Log reflection to shared file
            reflection = parsed.reflection or ""
            if reflection:
                with open(shared_file, "a", encoding="utf-8") as f:
                    f.write(f"\n{reflection}\n")
            # Record plan update in WM
            agent.world_model.record_plan(agent.id, agent.plan_steps)
            agent.world_model.log_communication(agent.id, "ALL", f"[REVISED PLAN] {'; '.join(agent.plan_steps)}")
    except Exception as e:
        print(f"[REVISION] Failed to apply revision for {agent.id}: {e}")

def clean_action_string(action_str: str) -> str:
    """Clean action strings by removing named parameters and converting to positional format"""
    # Handle MoveToBlock timeout=X -> remove timeout
    if "MoveToBlock" in action_str and "timeout=" in action_str:
        parts = action_str.split()
        clean_parts = [p for p in parts if not p.startswith("timeout=")]
        return " ".join(clean_parts)
    
    # Handle Rendezvous X Y need=Z timeout=W -> Rendezvous X Y Z W
    if "Rendezvous" in action_str:
        parts = action_str.split()
        if "need=" in action_str and "timeout=" in action_str:
            block_id = parts[1]
            side = parts[2]
            need = next(p.split("=")[1] for p in parts if p.startswith("need="))
            timeout = next(p.split("=")[1] for p in parts if p.startswith("timeout="))
            return f"Rendezvous {block_id} {side} {need} {timeout}"
    
    # Handle Push X steps=Y timeout=Z -> Push X Y (convert steps= format to positional)
    if "Push" in action_str:
        parts = action_str.split()
        if any(p.startswith("steps=") for p in parts):
            block_id = parts[1]
            steps = next(p.split("=")[1] for p in parts if p.startswith("steps="))
            return f"Push {block_id} {steps}"
        elif "timeout=" in action_str:
            # Just remove timeout if no steps= format
            clean_parts = [p for p in parts if not p.startswith("timeout=")]
            return " ".join(clean_parts)
    
    # Handle WaitAgents need=X timeout=Y -> WaitAgents X Y
    if "WaitAgents" in action_str:
        parts = action_str.split()
        if "need=" in action_str and "timeout=" in action_str:
            need = next(p.split("=")[1] for p in parts if p.startswith("need="))
            timeout = next(p.split("=")[1] for p in parts if p.startswith("timeout="))
            return f"WaitAgents {need} {timeout}"
    
    # Handle Wait steps=X timeout=Y -> Wait X
    if "Wait" in action_str:
        parts = action_str.split()
        if any(p.startswith("steps=") for p in parts):
            steps = next(p.split("=")[1] for p in parts if p.startswith("steps="))
            return f"Wait {steps}"
        elif "timeout=" in action_str:
            # Just remove timeout if no steps= format
            clean_parts = [p for p in parts if not p.startswith("timeout=")]
            return " ".join(clean_parts)
    
    # Handle YieldFace X Y steps=Z timeout=W -> YieldFace X Y Z
    if "YieldFace" in action_str:
        parts = action_str.split()
        if any(p.startswith("steps=") for p in parts):
            block_id = parts[1]
            side = parts[2]
            steps = next(p.split("=")[1] for p in parts if p.startswith("steps="))
            return f"YieldFace {block_id} {side} {steps}"
        elif "timeout=" in action_str:
            # Just remove timeout if no steps= format
            clean_parts = [p for p in parts if not p.startswith("timeout=")]
            return " ".join(clean_parts)
    
    return action_str

# ------------------------------
# Episode runner
# ------------------------------
def run_episode(ep_num: int, args, universe: UniverseStore) -> Dict:
    print("\n" + "="*60)
    print(f"STARTING EPISODE {ep_num}")
    print("="*60)

    # Folders & files
    ep_root = f"runs/episode_{ep_num:02d}"
    os.makedirs(ep_root, exist_ok=True)
    shared_file = os.path.join(ep_root, "shared_extra_info.md")
    log_file = os.path.join(ep_root, "trace.json")

    # Environment (fixed seed across episodes for comparability)
    import random, numpy as np
    random.seed(args.seed)
    np.random.seed(args.seed)

    env = CoopBlockPush(n=args.n, max_steps=args.max_steps, render_mode='human')
    env.reset(seed=args.seed)

    # Core managers & agents
    manager = LLMAgentManager(env)
    cfg = LLMConfig(model=args.model, temperature=args.temperature, max_tokens=args.max_tokens)
    agents = build_agents(env, manager, args.n, cfg)

    # ===== COMMUNICATION + PLANNING (ENHANCED) =====
    step = 0
    participants = run_enhanced_comm_round(agents, manager, step, universe_json=universe.json() if os.path.exists(universe.json()) else None)

    # Initial planning + revision with retrieval
    enhanced_templates = create_enhanced_templates(universe.json() if os.path.exists(universe.json()) else None)
    for aid in (participants or agents.keys()):
        _revise_plan_with_history(agents[aid], env, agents, enhanced_templates, shared_file)

    # Build controller
    controller = SymbolicController(env, manager.convert_all_agent_plans_to_objects())

    # ===== EXECUTION LOOP (with occasional re-planning) =====
    total_reward = 0.0
    step = 0
    MAX_ITERS = 10
    iter_count = 1

    while step < args.max_steps and iter_count <= MAX_ITERS:
        print(f"\n=== ITERATION {iter_count} ===")
        # Execute until all agents finish plans or blocks delivered
        start_step = step
        while step < args.max_steps:
            # If any agent finished early but blocks remain → re-plan that agent
            if len(getattr(env, "_blocks", [])) > 0:
                need = [aid for aid, a in agents.items() if a.is_finished()]
                if need:
                    print(f"Agents needing replan: {need}")
                    # Reset those agents to planning and do enhanced comm only among them
                    for aid in need:
                        a = agents[aid]
                        a.plan_steps = []
                        a.plan_index = 0
                        a.phase = "planning"
                        if hasattr(a, '_plan_completion_logged'):
                            delattr(a, '_plan_completion_logged')

                    participants = run_enhanced_comm_round({aid: agents[aid] for aid in need}, manager, step, universe_json=universe.json() if os.path.exists(universe.json()) else None)
                    for aid in participants:
                        _revise_plan_with_history(agents[aid], env, agents, enhanced_templates, shared_file)
                    # Update controller for those agents
                    plans_obj = manager.convert_all_agent_plans_to_objects()
                    for aid in participants:
                        if aid in plans_obj:
                            controller.plans[aid] = plans_obj[aid]
                            controller.idx[aid] = 0
                            controller.rem[aid] = 0

            # Act
            actions = controller.act()
            manager.log_timestep(step, actions)
            obs, rewards, dones, truncated, infos = env.step(actions)
            env.render()

            # Sync agent progress with controller
            for aid, a in agents.items():
                if aid in controller.idx and controller.idx[aid] > a.plan_index:
                    a.plan_index = controller.idx[aid]

            # Auto-log plan completion per-agent
            for aid, a in agents.items():
                if a.plan_steps and a.plan_index >= len(a.plan_steps) and not hasattr(a, '_plan_completion_logged'):
                    a._plan_completion_logged = True
                    # simple success heuristic: target block not present
                    target = getattr(a, 'assigned_block', None)
                    block_ids = [b.id for b in getattr(env, "_blocks", [])]
                    plan_successful = (target is not None and target not in block_ids) or target is None
                    manager.log_plan_execution_completed(step, {aid: {
                        'plan_successful': plan_successful,
                        'target_block': target,
                        'committed_task': getattr(a, 'task_name', None)
                    }})

            step += 1
            total_reward += sum(rewards.values())

            # Stop condition
            if all(a.is_finished() for a in agents.values()):
                break

        iter_count += 1
        if len(getattr(env, "_blocks", [])) == 0:
            print("All blocks delivered — episode done.")
            break
        if not any(not a.is_finished() for a in agents.values()):
            # Trigger a final group re-plan if stuck
            participants = run_enhanced_comm_round(agents, manager, step, universe_json=universe.json() if os.path.exists(universe.json()) else None)
            for aid in participants:
                _revise_plan_with_history(agents[aid], env, agents, enhanced_templates, shared_file)
            # refresh controller
            controller = SymbolicController(env, manager.convert_all_agent_plans_to_objects())

    # ===== Save episode log & per-episode artifacts =====
    manager.save_complete_log(log_file)
    print(f"Saved episode log to {os.path.abspath(log_file)}")

    # Generate per-episode WM (json + png) and timeline viz
    # (world_model JSON is saved to the episode folder by create_world_model_from_log)
    try:
        cwd = os.getcwd()
        os.chdir(ep_root)
        wm = create_world_model_from_log(
            log_file="trace.json", show_text=False, show_graph=False, save_graph=True, save_format='json'
        )
        wm.visualize(save_path='world_model_graph.png', show_plot=False)

        # concept graph text
        import io, sys
        old = sys.stdout
        sys.stdout = buf = io.StringIO()
        wm.visualize_text_concept_graph()
        sys.stdout = old
        write_text('world_model_concept_graph.txt', buf.getvalue())
    finally:
        os.chdir(cwd)

    # Timeline viz
    viz_png = os.path.join(ep_root, "log_visualization.png")
    result = subprocess.run([
        "python", "log_visualizer.py", os.path.abspath(log_file), "-o", os.path.abspath(viz_png)
    ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
    if result.returncode != 0:
        print("Log visualizer error:", result.stderr)

    # ===== Update universe (learning) =====
    ep_world_model_json = os.path.join(ep_root, "world_model_graph.json")
    if os.path.exists(ep_world_model_json):
        universe.update_with_episode_worldmodel(ep_world_model_json, episode_id=f"E{ep_num}")
    else:
        print(f"[WARN] Missing {ep_world_model_json}; universe not updated for episode {ep_num}" )

    # Episode summary
    total_steps = len([e for e in manager.activity_log if e.get('event_type') == 'timestep'])
    comm_rounds = len(manager.get_communication_log())
    success = len(getattr(env, "_blocks", [])) == 0
    return {
        'episode_num': ep_num,
        'total_steps': total_steps,
        'total_reward': total_reward,
        'communication_rounds': comm_rounds,
        'success': success,
        'episode_folder': ep_root
    }

# ------------------------------
# CLI
# ------------------------------
def main():
    p = argparse.ArgumentParser("Learning Pipeline (episodes → multiverse → retrieval)")
    p.add_argument("--n", type=int, default=2, help="# agents")
    p.add_argument("--model", type=str, default="gpt-4o", help="Azure OpenAI deployment name")
    p.add_argument("--max_steps", type=int, default=50)
    p.add_argument("--num_episodes", type=int, default=3)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--max_tokens", type=int, default=900)
    args = p.parse_args()

    print(f"Running {args.num_episodes} episodes; agents={args.n}; model={args.model}")
    universe = UniverseStore(root="runs/universe")

    results = []
    for ep in range(1, args.num_episodes+1):
        try:
            r = run_episode(ep, args, universe)
            results.append(r)
            print(f"Episode {ep} → steps={r['total_steps']}, reward={r['total_reward']:.2f}, success={r['success']}")
        except Exception as e:
            print(f"Episode {ep} failed: {e}")
            results.append({'episode_num': ep, 'error': str(e), 'success': False})

    # Save multi-episode summary
    out = {
        'args': vars(args),
        'episodes': results
    }
    ensure_dir("runs/multi_episode_summary.json")
    with open("runs/multi_episode_summary.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("Saved summary to runs/multi_episode_summary.json")
    print("Universe graph at:", universe.json())

if __name__ == "__main__":
    main()


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
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import time
import random
import sys
import io
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

# --- Environment / Controllers ---
from cube.env import CoopBlockPush
from cube.symbolic_actions import SymbolicController

# --- Framework pieces from this repo ---
from llm_agent import LLMConfig, LLMAgentManager, client as azure_client
from llm_agent_enhanced import EnhancedLLMAgent
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
        
        # Main universe files (always current/latest)
        self.json_path = os.path.join(self.root, "universe_graph.json")
        self.png_path = os.path.join(self.root, "universe_graph.png")
        
        # Snapshots directory for historical universe states
        self.snapshots_dir = os.path.join(self.root, "snapshots")
        os.makedirs(self.snapshots_dir, exist_ok=True)
        
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

    def add_episode_data(self, episode_data: Dict, episode_id: str):
        """Add episode data to the universe data structure."""
        print(f"[UNIVERSE] Adding episode data for {episode_id}")
        
        # Load existing universe data
        universe_data = {}
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, 'r') as f:
                    universe_data = json.load(f)
            except Exception as e:
                print(f"[UNIVERSE] Could not load existing universe data: {e}")
                universe_data = {}
        
        # Ensure universe_data structure exists
        if 'universe_data' not in universe_data:
            universe_data['universe_data'] = {}
        if 'episodes' not in universe_data['universe_data']:
            universe_data['universe_data']['episodes'] = {}
        
        # Add episode data
        universe_data['universe_data']['episodes'][episode_id] = episode_data
        
        # Save updated universe data
        with open(self.json_path, 'w') as f:
            json.dump(universe_data, f, indent=2)
        
        print(f"[UNIVERSE] Episode data saved for {episode_id}")

    def update_with_episode_worldmodel(self, episode_world_model_json: str, episode_id: Optional[str] = None):
        """Add a world model JSON to the universe and write updated JSON and PNG."""
        print(f"[UNIVERSE] Adding episode WM: {episode_world_model_json}")
        self.mv.add_world_model(episode_world_model_json, episode_id=episode_id)
        # Build retrieval views (COG/TCG/PDG)
        self.mv.build_views(bucket=10)
        
        # Save main universe files (always current/latest)
        self.mv.export_graph(self.json_path)
        self.mv.visualize(self.png_path, show_plot=False)
        
        # Save snapshot for this episode
        if episode_id:
            snapshot_json = os.path.join(self.snapshots_dir, f"universe_graph_{episode_id}.json")
            snapshot_png = os.path.join(self.snapshots_dir, f"universe_graph_{episode_id}.png")
            
            self.mv.export_graph(snapshot_json)
            self.mv.visualize(snapshot_png, show_plot=False)
            
            print(f"[UNIVERSE] Updated main files: {self.json_path} and {self.png_path}")
            print(f"[UNIVERSE] Saved snapshot: {snapshot_json} and {snapshot_png}")
        else:
            print(f"[UNIVERSE] Updated: {self.json_path} and {self.png_path}")

    def json(self) -> str:
        return self.json_path
        
    def get_snapshot_path(self, episode_id: str) -> str:
        """Get the path to a specific episode's universe snapshot."""
        return os.path.join(self.snapshots_dir, f"universe_graph_{episode_id}.json")
        
    def list_snapshots(self) -> List[str]:
        """List all available universe snapshots."""
        if not os.path.exists(self.snapshots_dir):
            return []
        
        snapshots = []
        for filename in os.listdir(self.snapshots_dir):
            if filename.startswith("universe_graph_") and filename.endswith(".json"):
                episode_id = filename[15:-5]  # Remove "universe_graph_" and ".json"
                snapshots.append(episode_id)
        
        return sorted(snapshots)
    
    def generate_universe_evolution_summary(self, output_dir: str = "runs") -> str:
        """Generate a summary showing how the universe evolved over episodes."""
        snapshots = self.list_snapshots()
        
        if not snapshots:
            print("[UNIVERSE] No snapshots available for evolution summary")
            return ""
        
        summary_path = os.path.join(output_dir, "universe_evolution_summary.txt")
        
        with open(summary_path, 'w') as f:
            f.write("UNIVERSE EVOLUTION SUMMARY\n")
            f.write("=" * 50 + "\n\n")
            
            f.write(f"Total Episodes Processed: {len(snapshots)}\n")
            f.write(f"Universe Snapshots Available: {snapshots}\n\n")
            
            # Analyze growth over time
            episode_sizes = []
            for episode_id in snapshots:
                snapshot_path = self.get_snapshot_path(episode_id)
                try:
                    with open(snapshot_path, 'r') as sf:
                        data = json.load(sf)
                        episodes_count = len(data.get('universe_data', {}).get('episodes', {}))
                        episode_sizes.append((episode_id, episodes_count))
                        f.write(f"After {episode_id}: {episodes_count} episodes in universe\n")
                except Exception as e:
                    f.write(f"After {episode_id}: Error reading snapshot - {e}\n")
            
            f.write(f"\nCurrent Universe State: {self.json_path}\n")
            f.write(f"Snapshots Directory: {self.snapshots_dir}\n")
            
            # Growth analysis
            if len(episode_sizes) > 1:
                f.write(f"\nUniverse Growth:\n")
                for i in range(1, len(episode_sizes)):
                    prev_ep, prev_size = episode_sizes[i-1]
                    curr_ep, curr_size = episode_sizes[i]
                    growth = curr_size - prev_size
                    f.write(f"  {prev_ep} → {curr_ep}: +{growth} episodes\n")
        
        print(f"[UNIVERSE] Evolution summary saved to: {summary_path}")
        return summary_path

# ------------------------------
# Agent construction
# ------------------------------
def build_agents(env, manager: LLMAgentManager, n_agents: int, cfg: LLMConfig, universe_json_path: str = None) -> Dict[str, EnhancedLLMAgent]:
    agents: Dict[str, EnhancedLLMAgent] = {}
    for i in range(n_agents):
        aid = f"agent_{i}"
        a = EnhancedLLMAgent(aid, env, manager, cfg, plan=[], universe_json_path=universe_json_path)
        # Add tracking attributes
        a.planning_count = 0
        a.episode_start_time = time.time()
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
    
    # COMM PHASE - Show retrieved historical info at the top for all agents to see
    print("\n" + "="*60)
    print("COMMUNICATION PHASE - HISTORICAL INSIGHTS")
    print("="*60)
    
    # Proposal phase with context on current session - this displays retrieved historical info
    board.start_proposal_round(current_timestep=step, num_agents=len(agents))
    
    print("="*60)
    print("AGENT PROPOSALS")
    print("="*60)
    
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

def _obs_for(agent: LLMAgent) -> dict:
    return agent.observe()

def _initial_plan_with_history(agent: LLMAgent, env, all_agents: Dict[str, LLMAgent], enhanced_templates: Optional[EnhancedTemplates]):
    """PLANNING PHASE 1: Initial planning with historical insights for each agent"""
    print(f"\n" + "="*60)
    print(f"PLANNING PHASE 1 - INITIAL PLANNING FOR {agent.id}")
    print("="*60)
    
    # Track planning count
    agent.planning_count += 1
    
    # Show retrieved historical insights for this agent's planning phase 1
    if enhanced_templates and enhanced_templates.retriever:
        print(f"[PHASE_1] Retrieving historical planning insights for {agent.task_name}...")
        
        # Get historical insights for this specific task
        try:
            # Get plan prototypes for this task
            if agent.task_name:
                block_name = agent.task_name if 'Block_' in agent.task_name else f"Block_{agent.assigned_block}"
                plan_prototypes = enhanced_templates.retriever.get_plan_prototypes(task_name=block_name)
                prototypes = plan_prototypes.get("plan_prototypes", {})
                
                if prototypes:
                    print(f"[PHASE_1] Historical Plan Prototypes for {block_name}:")
                    for i, (key, data) in enumerate(prototypes.items(), 1):
                        success_rate = data.get("success_rate", 0)
                        symbolic_actions = data.get("symbolic_actions", [])
                        avg_team_size = data.get("avg_team_size", 0)
                        actions_str = " -> ".join(symbolic_actions) if symbolic_actions else "empty_plan"
                        print(f"  {i}. {actions_str}")
                        print(f"     Success: {success_rate:.1%} | Team size: {avg_team_size:.1f}")
                else:
                    print(f"[PHASE_1] No historical prototypes found for {block_name}")
        except Exception as e:
            print(f"[PHASE_1] Error retrieving insights: {e}")
    else:
        print(f"[PHASE_1] No historical insights available")
    
    print("="*60)
    print(f"INITIAL PLANNING FOR {agent.id}")
    print("="*60)
    
    # Run the initial planning (this will show the LLM input with enhanced template if available)
    agent.plan(all_agents=all_agents)
    
    # Clean the initial plan steps to remove steps= and other parameter formats
    if agent.plan_steps:
        cleaned_plan_steps = [clean_action_string(step) for step in agent.plan_steps]
        agent.plan_steps = cleaned_plan_steps

def _revise_plan_with_history(agent: LLMAgent, env, all_agents: Dict[str, LLMAgent], enhanced_templates: Optional[EnhancedTemplates], shared_file: str, args):
    """PLANNING PHASE 2: Revision with shared insights + historical data"""
    print(f"\n" + "="*80)
    print(f"PLANNING PHASE 2 - REVISION WITH SHARED + HISTORICAL INSIGHTS FOR {agent.id}")
    print("="*80)
    
    # Track planning count for revision
    agent.planning_count += 1
    
    # Phase 2 information display
    historical_insights = ""
    shared_insights = ""
    
    if enhanced_templates and enhanced_templates.retriever:
        print(f"[PHASE_2] Retrieving comprehensive insights for {agent.task_name}...")
        
        # Get historical task performance insights for revision
        try:
            if agent.task_name:
                block_name = agent.task_name if 'Block_' in agent.task_name else f"Block_{agent.assigned_block}"
                
                # Use available methods to get task performance data
                general_info = enhanced_templates.retriever.get_general_info()
                task_distribution = general_info.get("task_distribution", {})
                
                if block_name in task_distribution:
                    task_stats = task_distribution[block_name]
                    completion_rate = task_stats.get("completion_rate", 0)
                    total_instances = task_stats.get("total_instances", 0)
                    successful_instances = task_stats.get("successful_instances", 0)
                    episodes_seen = task_stats.get("episodes_seen", 0)
                    
                    print(f"[PHASE_2] Task Performance Analysis for {block_name}:")
                    print(f"  - Success Rate: {completion_rate:.1%} ({total_instances} attempts)")
                    print(f"  - Successful Instances: {successful_instances}")
                    print(f"  - Episodes Seen: {episodes_seen}")
                    
                    historical_insights = f"Historical Performance: {completion_rate:.1%} success rate, {total_instances} attempts"
                else:
                    print(f"[PHASE_2] No historical data found for {block_name}")
                    historical_insights = "No historical data available"
        except Exception as e:
            print(f"[PHASE_2] Error retrieving historical insights: {e}")
    
    # Read shared insights from cross-episode file
    if os.path.exists(shared_file):
        try:
            with open(shared_file, 'r') as f:
                shared_content = f.read()
                if shared_content.strip():
                    print(f"[PHASE_2] Shared Insights from Cross-Episode Learning:")
                    # Show a preview of shared insights
                    lines = shared_content.strip().split('\n')
                    relevant_lines = [line for line in lines if agent.task_name in line or "general" in line.lower()][:3]
                    if relevant_lines:
                        for line in relevant_lines:
                            print(f"  - {line.strip()}")
                    else:
                        # Show first few general insights
                        for line in lines[:3]:
                            if line.strip():
                                print(f"  - {line.strip()}")
                    shared_insights = shared_content[:200] + "..." if len(shared_content) > 200 else shared_content
        except Exception as e:
            print(f"[PHASE_2] Error reading shared insights: {e}")
    
    print("="*80)
    print(f"PLAN REVISION FOR {agent.id}")
    print("="*80)
    
    # 2) revision pass, pulling extra context + historical insights via EnhancedTemplates
    obs = _obs_for(agent)
    previous_plan = "\n".join(agent.plan_steps) if agent.plan_steps else "(none)"
    file_text = read_text(shared_file)
    
    # Print shared file content for debugging
    if file_text.strip():
        print(f"[SHARED_INFO] Using shared insights from {shared_file}:")
        print(f"[SHARED_INFO] Content length: {len(file_text)} characters")
        print(f"[SHARED_INFO] Content preview: \n{file_text[:200]}{'...' if len(file_text) > 200 else ''}\n")

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
            # Log reflection to shared file (cross-episodic knowledge)
            if not args.disable_shared_writing:
                reflection = parsed.reflection or ""
                if reflection:
                    with open(shared_file, "a", encoding="utf-8") as f:
                        f.write(f"\n{reflection}\n")
    except Exception as e:
        print(f"[REVISION] Failed to apply revision for {agent.id}: {e}")

# ------------------------------
# Episode runner
# ------------------------------
def run_episode(ep_num: int, args, universe: UniverseStore) -> Dict:
    print("\n" + "="*60)
    print(f"STARTING EPISODE {ep_num}")
    print("="*60)

    # Timing and tracking initialization
    episode_start_time = time.time()
    block_completion_times = {}  # block_id -> completion_time
    initial_blocks = None
    
    # Agent commitment tracking
    agent_commitments = defaultdict(list)  # agent_id -> [(step, task_name), ...]
    
    # Folders & files
    ep_root = f"runs/episode_{ep_num:02d}"
    os.makedirs(ep_root, exist_ok=True)
    os.makedirs("runs", exist_ok=True)  # Ensure runs directory exists for shared file
    shared_file = "runs/shared_extra_info.md"  # Single shared file across all episodes
    log_file = os.path.join(ep_root, "trace.json")

    # Initialize shared file with header if this is the first episode
    if not args.disable_shared_writing and ep_num == 1 and not os.path.exists(shared_file):
        with open(shared_file, "w", encoding="utf-8") as f:
            f.write("# Shared Learning Insights Across Episodes\n")
            f.write("# This file accumulates actionable guidelines from all agents across episodes\n\n")

    # Environment (fixed seed across episodes for comparability)
    random.seed(args.seed)
    np.random.seed(args.seed)

    env = CoopBlockPush(n=args.n, max_steps=args.max_steps, render_mode='human')
    env.reset(seed=args.seed)
    
    # Track initial blocks for completion timing
    initial_blocks = set([b.id for b in getattr(env, "_blocks", [])])
    print(f"Initial blocks: {initial_blocks}")

    # Core managers & agents
    manager = LLMAgentManager(env)
    cfg = LLMConfig(model=args.model, temperature=args.temperature, max_tokens=args.max_tokens)
    agents = build_agents(env, manager, args.n, cfg, universe_json_path=universe.json() if os.path.exists(universe.json()) else None)
    
    # Set episode start time for all agents
    for agent in agents.values():
        agent.episode_start_time = episode_start_time

    # ===== COMMUNICATION + PLANNING (ENHANCED) =====
    step = 0
    print(f"[DEBUG] Starting communication with agents: {list(agents.keys())}")
    participants = run_enhanced_comm_round(agents, manager, step, universe_json=universe.json() if os.path.exists(universe.json()) else None)
    print(f"[DEBUG] Communication participants: {participants}")
    
    # Ensure all agents participate in planning if participants is empty
    if not participants:
        participants = list(agents.keys())
        print(f"[DEBUG] No participants from comm round, using all agents: {participants}")

    # ===== PLANNING PHASES (ENHANCED 3-PHASE SYSTEM) =====
    enhanced_templates = create_enhanced_templates(universe.json() if os.path.exists(universe.json()) else None)
    
    # PHASE 1: Initial planning with historical insights for each agent
    for aid in participants:
        _initial_plan_with_history(agents[aid], env, agents, enhanced_templates)
    
    # PHASE 2: Revision with shared insights + historical data for each agent
    for aid in participants:
        _revise_plan_with_history(agents[aid], env, agents, enhanced_templates, shared_file, args)

    # Build controller
    print(f"[DEBUG] All agents: {list(agents.keys())}")
    print(f"[DEBUG] Participants: {participants}")
    
    # Convert agent plans to objects
    plans_obj = manager.convert_all_agent_plans_to_objects()
    print(f"[DEBUG] Plans object keys: {list(plans_obj.keys()) if plans_obj else 'None'}")
    
    controller = SymbolicController(env, plans_obj)

    # Print debug info about plans
    for aid, agent in agents.items():
        print(f"[DEBUG] {aid} cleaned plan: {agent.plan_steps}")
        if aid not in plans_obj:
            print(f"[WARNING] {aid} missing from plans_obj!")

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
                    # For mid-episode re-planning, use only Phase 2 (revision with full context)
                    for aid in participants:
                        _revise_plan_with_history(agents[aid], env, agents, enhanced_templates, shared_file, args)
                    # Update controller for those agents
                    plans_obj = manager.convert_all_agent_plans_to_objects()
                    for aid in participants:
                        if aid in plans_obj:
                            controller.plans[aid] = plans_obj[aid]
                            controller.idx[aid] = 0
                            controller.rem[aid] = 0

            # Act
            actions = controller.act()
            print(f"[DEBUG] Step {step}: Actions returned by controller: {actions}")
            print(f"[DEBUG] Step {step}: Expected agents: {list(agents.keys())}")
            print(f"[DEBUG] Step {step}: Environment agents: {env.agents}")
            
            # Check if environment has ended (agents list becomes empty)
            if not env.agents:
                print(f"[DEBUG] Environment agents list is empty - episode has ended")
                # Break out of execution loop since environment has no more agents
                break
            
            # Check if all agents have actions
            missing_agents = [aid for aid in agents.keys() if aid not in actions]
            if missing_agents:
                print(f"[ERROR] Missing actions for agents: {missing_agents}")
                # Provide default actions (stay in place) for missing agents
                for aid in missing_agents:
                    actions[aid] = 0  # 0 = stay action
                print(f"[DEBUG] Actions after filling missing: {actions}")
            
            manager.log_timestep(step, actions)
            obs, rewards, dones, truncated, infos = env.step(actions)
            env.render()
            
            # Track block completions with timing
            current_blocks = set([b.id for b in getattr(env, "_blocks", [])])
            completed_blocks = initial_blocks - current_blocks
            for block_id in completed_blocks:
                if block_id not in block_completion_times:
                    completion_time = time.time() - episode_start_time
                    block_completion_times[block_id] = completion_time
                    print(f"[TIMING] Block {block_id} completed at {completion_time:.2f}s into episode")
            
            # Track agent commitments at each step
            for aid, agent in agents.items():
                current_task = getattr(agent, 'task_name', 'No_Task')
                # Only record if this is a new commitment or step 0
                if not agent_commitments[aid] or agent_commitments[aid][-1][1] != current_task:
                    agent_commitments[aid].append((step, current_task))

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
            # For final re-planning, use only Phase 2 (revision with full context)
            for aid in participants:
                _revise_plan_with_history(agents[aid], env, agents, enhanced_templates, shared_file, args)
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
    episode_id = f"E{ep_num}"
    ep_world_model_json = os.path.join(ep_root, "world_model_graph.json")
    if os.path.exists(ep_world_model_json):
        universe.update_with_episode_worldmodel(ep_world_model_json, episode_id=episode_id)
    else:
        print(f"[WARN] Missing {ep_world_model_json}; universe not updated for episode {ep_num}" )

    # Episode summary data collection
    total_steps = len([e for e in manager.activity_log if e.get('event_type') == 'timestep'])
    comm_rounds = len(manager.get_communication_log())
    success = len(getattr(env, "_blocks", [])) == 0
    episode_duration = time.time() - episode_start_time
    
    # Collect agent planning counts
    agent_planning_counts = {aid: getattr(agent, 'planning_count', 0) for aid, agent in agents.items()}
    
    # Create episode data structure
    episode_data = {
        'episode_num': ep_num,
        'total_steps': total_steps,
        'total_reward': total_reward,
        'communication_rounds': comm_rounds,
        'success': success,
        'episode_duration': episode_duration,
        'block_completion_times': block_completion_times,
        'agent_planning_counts': agent_planning_counts,
        'agent_commitments': dict(agent_commitments),
        'initial_blocks': list(initial_blocks) if initial_blocks else [],
        'completed_blocks': list(block_completion_times.keys()),
        'episode_folder': ep_root
    }
    
    # ALWAYS save episode data to universe regardless of world model generation success
    print(f"[DEBUG] Saving episode data to universe for episode {ep_num}")
    universe.add_episode_data(episode_data, episode_id)
    print(f"[DEBUG] Episode data saved to universe for episode {ep_num}")
    
    return episode_data

# ------------------------------
# CLI
# ------------------------------
def analyze_learning_progress(results: List[Dict], universe: UniverseStore) -> Dict:
    """
    Analyze agent learning progress across episodes and generate comprehensive metrics
    """
    print("\n" + "="*60)
    print("ANALYZING LEARNING PROGRESS")
    print("="*60)
    
    print(f"[DEBUG] Total results received: {len(results)}")
    print(f"[DEBUG] Results with errors: {len([r for r in results if 'error' in r])}")
    
    analysis = {
        'learning_metrics': {},
        'strategy_evolution': {},
        'block_delivery_analysis': {},
        'communication_efficiency': {},
        'coordination_improvement': {},
        'episode_completion_analysis': {}
    }
    
    # 1. Basic Performance Metrics
    episodes = [r for r in results if 'error' not in r]
    print(f"[DEBUG] Valid episodes after error filtering: {len(episodes)}")
    
    if not episodes:
        print("[WARNING] No valid episodes found for analysis")
        return analysis
    
    episode_nums = [r['episode_num'] for r in episodes]
    rewards = [r['total_reward'] for r in episodes]
    steps = [r['total_steps'] for r in episodes]
    comm_rounds = [r.get('communication_rounds', 0) for r in episodes]
    success_rates = [r['success'] for r in episodes]
    
    print(f"[DEBUG] Episode numbers: {episode_nums}")
    print(f"[DEBUG] Sample episode data: {episodes[0] if episodes else 'None'}")
    
    # New metrics
    episode_durations = [r.get('episode_duration', 0) for r in episodes]
    planning_counts = [r.get('agent_planning_counts', {}) for r in episodes]
    block_completions = [r.get('block_completion_times', {}) for r in episodes]
    agent_commitments = [r.get('agent_commitments', {}) for r in episodes]
    
    print(f"[DEBUG] Agent commitments sample: {agent_commitments[0] if agent_commitments else 'None'}")
    
    analysis['learning_metrics'] = {
        'reward_trend': rewards,
        'efficiency_trend': [s for s in steps],  # Lower is better
        'communication_trend': comm_rounds,
        'success_rate_progression': success_rates,
        'episode_duration_trend': episode_durations,
        'planning_counts_per_episode': planning_counts,
        'block_completion_trends': block_completions,
        'agent_commitments_per_episode': agent_commitments,
        'average_reward_improvement': np.mean(rewards[-2:]) - np.mean(rewards[:2]) if len(rewards) >= 4 else 0,
        'step_efficiency_improvement': np.mean(steps[:2]) - np.mean(steps[-2:]) if len(steps) >= 4 else 0
    }
    
    # 2. Process direct episode results for immediate visualization
    # Extract block completion times from our direct episode results
    direct_block_completion_times = defaultdict(list)
    
    # First, collect all unique block IDs across all episodes
    all_block_ids = set()
    for result in episodes:
        block_times = result.get('block_completion_times', {})
        all_block_ids.update(block_times.keys())
    
    # Now build completion times for each block, ensuring each has an entry for every episode
    for block_id in all_block_ids:
        for result in episodes:
            block_times = result.get('block_completion_times', {})
            if block_id in block_times:
                direct_block_completion_times[block_id].append(block_times[block_id])
            else:
                # Block not completed in this episode - use 0
                direct_block_completion_times[block_id].append(0)
    
    print(f"[DEBUG] Direct block completion times: {dict(direct_block_completion_times)}")
    print(f"[DEBUG] Number of episodes: {len(episodes)}, All block IDs: {sorted(all_block_ids)}")
    
    # 3. Analyze Universe Data for Strategy Evolution
    if os.path.exists(universe.json()):
        try:
            with open(universe.json(), 'r') as f:
                universe_data = json.load(f)
            
            episodes_data = universe_data.get('universe_data', {}).get('episodes', {})
            
            # Track strategy diversity
            strategy_diversity = defaultdict(list)
            block_success_rates = defaultdict(list)
            task_completion_times = defaultdict(list)
            
            for ep_id, ep_data in episodes_data.items():
                task_data = ep_data.get('task_data', {})
                
                for task_name, task_info in task_data.items():
                    # Collect plan templates used
                    templates = task_info.get('templates', {})
                    for template_name, template_data in templates.items():
                        instances = template_data.get('instances', [])
                        
                        # Track strategy types
                        strategy_diversity[task_name].append(template_name)
                        
                        # Track success rates per block
                        successes = sum(1 for inst in instances if inst.get('success', False))
                        total = len(instances)
                        if total > 0:
                            block_success_rates[task_name].append(successes / total)
                        
                        # Track completion times
                        for inst in instances:
                            if inst.get('success', False):
                                duration = inst.get('duration', 0)
                                if duration > 0:
                                    task_completion_times[task_name].append(duration)
            
            analysis['strategy_evolution'] = {
                'strategy_diversity_per_task': {task: len(set(strategies)) for task, strategies in strategy_diversity.items()},
                'strategies_tried': dict(strategy_diversity),
                'block_success_evolution': dict(block_success_rates),
                'completion_time_trends': dict(direct_block_completion_times)  # Use direct data from current run
            }
            
            # Track episode completion metrics
            episode_completion_data = []
            episode_completion_times = []
            
            for ep_id, ep_data in episodes_data.items():
                task_data = ep_data.get('task_data', {})
                episode_completions = 0
                episode_avg_completion_time = 0
                completion_times_this_episode = []
                
                for task_name, task_info in task_data.items():
                    templates = task_info.get('templates', {})
                    for template_name, template_data in templates.items():
                        instances = template_data.get('instances', [])
                        
                        # Count successful completions and their times
                        for inst in instances:
                            if inst.get('success', False):
                                episode_completions += 1
                                duration = inst.get('duration', 0)
                                if duration > 0:
                                    completion_times_this_episode.append(duration)
                
                episode_completion_data.append(episode_completions)
                avg_time = np.mean(completion_times_this_episode) if completion_times_this_episode else 0
                episode_completion_times.append(avg_time)
            
            analysis['episode_completion_analysis'] = {
                'blocks_completed_per_episode': episode_completion_data,
                'avg_completion_time_per_episode': episode_completion_times,
                'total_blocks_completed': sum(episode_completion_data),
                'episodes_with_completions': sum(1 for x in episode_completion_data if x > 0),
                'best_episode_completions': max(episode_completion_data) if episode_completion_data else 0,
                'completion_trend': 'improving' if len(episode_completion_data) > 1 and episode_completion_data[-1] > episode_completion_data[0] else 'stable'
            }
            
            # 3. Block Delivery Analysis
            total_blocks_attempted = len(block_success_rates)
            successful_blocks = sum(1 for rates in block_success_rates.values() if any(r > 0 for r in rates))
            
            analysis['block_delivery_analysis'] = {
                'total_blocks_attempted': total_blocks_attempted,
                'blocks_with_successful_deliveries': successful_blocks,
                'overall_block_success_rate': successful_blocks / total_blocks_attempted if total_blocks_attempted > 0 else 0,
                'per_block_performance': {
                    task: {
                        'attempts': len(rates),
                        'best_success_rate': max(rates) if rates else 0,
                        'latest_success_rate': rates[-1] if rates else 0,
                        'improvement': rates[-1] - rates[0] if len(rates) > 1 else 0
                    } for task, rates in block_success_rates.items()
                }
            }
            
        except Exception as e:
            print(f"[WARNING] Could not analyze universe data: {e}")
    
    # Build block success evolution from current episode results (fallback or supplement)
    current_block_success_rates = defaultdict(list)
    for result in episodes:
        block_times = result.get('block_completion_times', {})
        completed_blocks = set(block_times.keys())
        
        # For each block that appeared in any episode, track if it was completed
        for block_id in all_block_ids:
            success_rate = 1.0 if block_id in completed_blocks else 0.0
            current_block_success_rates[f"Block_{block_id}"].append(success_rate)
    
    print(f"[DEBUG] Current block success rates: {dict(current_block_success_rates)}")
    
    # If no universe data exists or universe data is incomplete, use our direct episode data
    if not os.path.exists(universe.json()) or 'strategy_evolution' not in analysis or not analysis['strategy_evolution'].get('block_success_evolution'):
        analysis['strategy_evolution'] = {
            'strategy_diversity_per_task': {},
            'strategies_tried': {},
            'block_success_evolution': dict(current_block_success_rates),
            'completion_time_trends': dict(direct_block_completion_times)
        }
    else:
        # Supplement existing universe data with current results
        existing_evolution = analysis['strategy_evolution'].get('block_success_evolution', {})
        # Update completion time trends with current data
        analysis['strategy_evolution']['completion_time_trends'] = dict(direct_block_completion_times)
        # If block success evolution is empty from universe, use current data
        if not existing_evolution:
            analysis['strategy_evolution']['block_success_evolution'] = dict(current_block_success_rates)
    analysis['communication_efficiency'] = {
        'avg_comm_rounds_early': np.mean(comm_rounds[:len(comm_rounds)//2]) if comm_rounds else 0,
        'avg_comm_rounds_late': np.mean(comm_rounds[len(comm_rounds)//2:]) if comm_rounds else 0,
        'communication_improvement': (np.mean(comm_rounds[:len(comm_rounds)//2]) - np.mean(comm_rounds[len(comm_rounds)//2:])) if len(comm_rounds) > 2 else 0
    }
    
    # 5. Coordination Improvement (based on step efficiency and success)
    coordination_score = []
    for i, (r, s, c) in enumerate(zip(rewards, steps, comm_rounds)):
        # Higher reward, lower steps, fewer comm rounds = better coordination
        score = r / max(s, 1) * (1 / max(c, 1))  # Avoid division by zero
        coordination_score.append(score)
    
    analysis['coordination_improvement'] = {
        'coordination_scores': coordination_score,
        'coordination_trend': 'improving' if len(coordination_score) > 2 and coordination_score[-1] > coordination_score[0] else 'stable',
        'best_coordination_episode': episode_nums[np.argmax(coordination_score)] if coordination_score else 0
    }
    
    return analysis

def generate_learning_visualizations(analysis: Dict, output_dir: str = "runs"):
    """
    Generate comprehensive learning progress visualizations including planning counts and block completion timing
    """
    print("\n" + "="*60)
    print("GENERATING LEARNING VISUALIZATIONS")
    print("="*60)
    
    # Get the actual number of episodes from the current run
    learning_metrics = analysis.get('learning_metrics', {})
    actual_episodes = len(learning_metrics.get('reward_trend', []))
    
    plt.style.use('default')
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    fig.suptitle(f'Agent Learning Progress Analysis ({actual_episodes} Episodes)', fontsize=16, fontweight='bold')
    
    # 1. Agent Planning Activity Over Episodes
    ax1 = axes[0, 0]
    planning_counts = analysis.get('learning_metrics', {}).get('planning_counts_per_episode', [])
    if planning_counts:
        episodes = list(range(1, len(planning_counts) + 1))
        avg_planning_per_episode = [np.mean(list(counts.values())) if counts else 0 for counts in planning_counts]
        total_planning_per_episode = [sum(counts.values()) if counts else 0 for counts in planning_counts]
        
        # Plot both average and total planning counts
        ax1_twin = ax1.twinx()
        
        bars = ax1.bar(episodes, avg_planning_per_episode, alpha=0.7, color='lightcoral', label='Avg Planning/Agent')
        line = ax1_twin.plot(episodes, total_planning_per_episode, 'go-', linewidth=2, markersize=6, label='Total Planning Events')
        
        ax1.set_title('Agent Planning Activity Over Episodes', fontweight='bold')
        ax1.set_xlabel('Episode Number')
        ax1.set_ylabel('Average Planning Events per Agent', color='red')
        ax1.tick_params(axis='y', labelcolor='red')
        ax1_twin.set_ylabel('Total Planning Events', color='green')
        ax1_twin.tick_params(axis='y', labelcolor='green')
        ax1.grid(True, alpha=0.3)
        
        # Add value labels
        for bar, val in zip(bars, avg_planning_per_episode):
            if val > 0:
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, 
                        f'{val:.1f}', ha='center', va='bottom', fontweight='bold')
        
        # Combined legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax1_twin.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    else:
        ax1.text(0.5, 0.5, 'No planning activity data available', ha='center', va='center', transform=ax1.transAxes)
        ax1.set_title('Agent Planning Activity Over Episodes', fontweight='bold')
    
    # 2. Block Completion Timing Across Episodes
    ax2 = axes[0, 1]
    block_completions = analysis.get('learning_metrics', {}).get('block_completion_trends', [])
    if block_completions:
        # Aggregate completion times by episode
        episode_completion_times = []
        episode_block_counts = []
        
        for ep_data in block_completions:
            if ep_data:
                times = list(ep_data.values())
                episode_completion_times.append(np.mean(times) if times else 0)
                episode_block_counts.append(len(times))
            else:
                episode_completion_times.append(0)
                episode_block_counts.append(0)
        
        episodes = list(range(1, len(episode_completion_times) + 1))
        
        # Dual axis: completion time and number of blocks
        ax2_twin = ax2.twinx()
        
        line1 = ax2.plot(episodes, episode_completion_times, 'bo-', linewidth=2, markersize=6, label='Avg Completion Time')
        bars = ax2_twin.bar(episodes, episode_block_counts, alpha=0.3, color='orange', label='Blocks Completed')
        
        ax2.set_title('Block Completion Timing Analysis', fontweight='bold')
        ax2.set_xlabel('Episode Number')
        ax2.set_ylabel('Average Completion Time (seconds)', color='blue')
        ax2.tick_params(axis='y', labelcolor='blue')
        ax2_twin.set_ylabel('Number of Blocks Completed', color='orange')
        ax2_twin.tick_params(axis='y', labelcolor='orange')
        ax2.grid(True, alpha=0.3)
        
        # Combined legend
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_twin.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    else:
        ax2.text(0.5, 0.5, 'No block completion timing data available', ha='center', va='center', transform=ax2.transAxes)
        ax2.set_title('Block Completion Timing Analysis', fontweight='bold')
    
    # 3. Task Diversity Over Time (Agent Strategy Evolution)
    ax3 = axes[0, 2]
    strategy_div = analysis.get('strategy_evolution', {}).get('strategy_diversity_per_task', {})
    if strategy_div:
        tasks = list(strategy_div.keys())
        diversity = list(strategy_div.values())
        bars = ax3.bar(tasks, diversity, color='skyblue', alpha=0.7)
        ax3.set_title('Agent Task Strategy Diversity', fontweight='bold')
        ax3.set_xlabel('Block Task')
        ax3.set_ylabel('Number of Different Strategies Tried')
        ax3.grid(True, alpha=0.3)
        # Add value labels on bars
        for bar, val in zip(bars, diversity):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                    str(val), ha='center', va='bottom', fontweight='bold')
    else:
        ax3.text(0.5, 0.5, 'No strategy diversity data available', ha='center', va='center', transform=ax3.transAxes)
        ax3.set_title('Agent Task Strategy Diversity', fontweight='bold')
    
    # 4. Block Success Rate Heatmap Over Time (Binary: Success/Failure per Episode)
    ax4 = axes[1, 0]
    block_success_evolution = analysis.get('strategy_evolution', {}).get('block_success_evolution', {})
    if block_success_evolution:
        # Prepare data for heatmap - show ALL historical episodes, not just current run
        all_blocks = list(block_success_evolution.keys())
        
        # Find the maximum number of episodes across all blocks (full history)
        max_episodes = max(len(rates) for rates in block_success_evolution.values()) if block_success_evolution else 1
        
        # Create matrix: rows = blocks, columns = episodes (ALL episodes in history)
        success_matrix = np.full((len(all_blocks), max_episodes), np.nan)
        
        for i, block in enumerate(all_blocks):
            rates = block_success_evolution[block]
            # Use ALL rates, not just recent ones - show full history
            for j, rate in enumerate(rates):
                if j < max_episodes:
                    success_matrix[i, j] = rate
        
        # Create heatmap with binary colormap (0 = failure/red, 1 = success/green)
        im = ax4.imshow(success_matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
        
        # Set labels
        ax4.set_title(f'Block Success Rate Over All Episodes (Binary: ✓/✗)', fontweight='bold')
        ax4.set_xlabel('Episode Number')
        ax4.set_ylabel('Block Task')
        ax4.set_yticks(range(len(all_blocks)))
        ax4.set_yticklabels(all_blocks)
        ax4.set_xticks(range(max_episodes))
        
        # Label ALL episodes in sequence, not relative to current run
        ax4.set_xticklabels([f'Ep{i+1}' for i in range(max_episodes)])
        
        # Add colorbar with binary labels
        cbar = plt.colorbar(im, ax=ax4, fraction=0.046, pad=0.04)
        cbar.set_label('Success (1=✓, 0=✗)', rotation=270, labelpad=15)
        cbar.set_ticks([0, 1])
        cbar.set_ticklabels(['Failed', 'Success'])
        
        # Add text annotations for binary values
        for i in range(len(all_blocks)):
            for j in range(max_episodes):
                if not np.isnan(success_matrix[i, j]):
                    # Show checkmark or X for binary success
                    symbol = '✓' if success_matrix[i, j] == 1.0 else '✗'
                    color = "white" if success_matrix[i, j] == 1.0 else "black"
                    text = ax4.text(j, i, symbol,
                                   ha="center", va="center", color=color,
                                   fontsize=10, fontweight='bold')
    else:
        ax4.text(0.5, 0.5, 'No block success data available', ha='center', va='center', transform=ax4.transAxes)
        ax4.set_title('Block Success Rate Over Episodes', fontweight='bold')
    
    # 5. Block Completion Times Over All Episodes (Bar Plot)
    ax5 = axes[1, 1]
    completion_times = analysis.get('strategy_evolution', {}).get('completion_time_trends', {})
    if completion_times:
        # Prepare data for grouped bar plot - show ALL historical episodes
        blocks = list(completion_times.keys())
        colors = plt.cm.Set3(np.linspace(0, 1, len(blocks)))
        
        # Find the maximum number of episodes across all blocks (full history)
        max_episodes_completion = max(len(times) for times in completion_times.values()) if completion_times else 1
        
        # Calculate bar positions for ALL episodes
        bar_width = 0.8 / len(blocks) if blocks else 0.8
        episode_positions = np.arange(1, max_episodes_completion + 1)
        
        for i, (block, times) in enumerate(completion_times.items()):
            if times:  # Only plot if we have completion data
                # Use ALL historical data, not just recent episodes
                plot_times = list(times)  # Show full history
                
                # Pad with zeros if this block has fewer episodes than others
                while len(plot_times) < max_episodes_completion:
                    plot_times.append(0)
                
                print(f"[DEBUG] Block {block}: Showing {len(plot_times)} episodes (full history)")
                
                # Calculate bar positions for this block
                bar_positions = episode_positions + (i - len(blocks)/2 + 0.5) * bar_width
                
                bars = ax5.bar(bar_positions, plot_times, width=bar_width, 
                             color=colors[i], alpha=0.7, label=block)
                
                # Add value labels on bars (only for non-zero values)
                for bar, val in zip(bars, plot_times):
                    if val > 0:
                        ax5.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                                f'{val:.1f}', ha='center', va='bottom', fontsize=8)
        
        ax5.set_title(f'Block Completion Times Over All Episodes (Full History)', fontweight='bold')
        ax5.set_xlabel('Episode Number')
        ax5.set_ylabel('Completion Time (seconds)')
        ax5.set_xticks(episode_positions)
        ax5.set_xticklabels([f'Ep{i}' for i in episode_positions])
        ax5.grid(True, alpha=0.3, axis='y')
        ax5.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
    else:
        ax5.text(0.5, 0.5, 'No completion time data available', ha='center', va='center', transform=ax5.transAxes)
        ax5.set_title('Block Completion Times Over All Episodes (Full History)', fontweight='bold')
    
    # 6. Agent Commitment Heatmap Across All Episodes
    ax6 = axes[1, 2]
    agent_commitments = analysis.get('learning_metrics', {}).get('agent_commitments_per_episode', [])
    if agent_commitments:  # Show all historical episodes, not limited to actual_episodes
        # Build comprehensive agent commitment matrix
        all_agents = set()
        max_steps = 0
        
        # Collect all agents and find max steps across episodes
        for ep_commitments in agent_commitments:
            for agent_id, commitments in ep_commitments.items():
                all_agents.add(agent_id)
                if commitments:
                    max_step = max(step for step, task in commitments)
                    max_steps = max(max_steps, max_step)
        
        if all_agents and max_steps > 0:
            all_agents = sorted(list(all_agents))
            
            # Create matrix: rows = (episode, agent), columns = timesteps
            y_labels = []
            commitment_matrix = []
            
            # Collect unique task names for color mapping
            all_tasks = set(['No_Task'])
            for ep_commitments in agent_commitments:
                for agent_id, commitments in ep_commitments.items():
                    for step, task in commitments:
                        all_tasks.add(task)
            
            all_tasks = sorted(list(all_tasks))
            task_to_num = {task: i for i, task in enumerate(all_tasks)}
            
            for ep_idx, ep_commitments in enumerate(agent_commitments):
                for agent_id in all_agents:
                    y_labels.append(f"E{ep_idx+1}_{agent_id}")
                    
                    # Build commitment row for this agent in this episode
                    row = [task_to_num['No_Task']] * (max_steps + 1)  # Default to No_Task
                    
                    if agent_id in ep_commitments:
                        commitments = ep_commitments[agent_id]
                        # Fill in actual commitments
                        for i, (step, task) in enumerate(commitments):
                            if step <= max_steps:
                                # Fill from this step to next commitment or end
                                end_step = max_steps
                                if i + 1 < len(commitments):
                                    end_step = min(commitments[i + 1][0] - 1, max_steps)
                                
                                for s in range(step, end_step + 1):
                                    if s < len(row):
                                        row[s] = task_to_num.get(task, task_to_num['No_Task'])
                    
                    commitment_matrix.append(row)
            
            if commitment_matrix:
                commitment_matrix = np.array(commitment_matrix)
                
                # Create heatmap
                im = ax6.imshow(commitment_matrix, cmap='tab20', aspect='auto', 
                               vmin=0, vmax=len(all_tasks)-1)
                
                # Set labels
                ax6.set_title('Agent Task Commitments Across Episodes', fontweight='bold')
                ax6.set_xlabel('Timestep')
                ax6.set_ylabel('Episode_Agent')
                
                # Set y-axis labels (episode_agent)
                ax6.set_yticks(range(len(y_labels)))
                ax6.set_yticklabels(y_labels, fontsize=8)
                
                # Set x-axis labels (timesteps) - show every 10th step
                step_ticks = list(range(0, max_steps + 1, max(1, max_steps // 10)))
                ax6.set_xticks(step_ticks)
                ax6.set_xticklabels(step_ticks)
                
                # Add colorbar with task names
                cbar = plt.colorbar(im, ax=ax6, fraction=0.046, pad=0.04)
                cbar.set_label('Task Assignment', rotation=270, labelpad=15)
                
                # Set colorbar ticks to task names
                if len(all_tasks) <= 10:  # Only show labels if not too many tasks
                    cbar.set_ticks(range(len(all_tasks)))
                    cbar.set_ticklabels(all_tasks, fontsize=8)
        else:
            ax6.text(0.5, 0.5, 'No agent commitment data', ha='center', va='center', transform=ax6.transAxes)
    else:
        ax6.text(0.5, 0.5, 'No agent commitment data available', ha='center', va='center', transform=ax6.transAxes)
        ax6.set_title('Agent Task Commitments Across Episodes', fontweight='bold')
    
    plt.tight_layout()
    
    # Save the plot
    plot_path = os.path.join(output_dir, 'learning_progress_analysis.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"Learning progress visualization saved to: {plot_path}")
    
    # Create a summary text report focused on the key metrics
    report_path = os.path.join(output_dir, 'learning_analysis_report.txt')
    with open(report_path, 'w') as f:
        f.write("AGENT LEARNING PROGRESS ANALYSIS REPORT\n")
        f.write("="*50 + "\n\n")
        
        # Task strategy diversity
        f.write("1. AGENT TASK STRATEGY DIVERSITY:\n")
        strategy_div = analysis.get('strategy_evolution', {}).get('strategy_diversity_per_task', {})
        total_strategies = sum(strategy_div.values()) if strategy_div else 0
        f.write(f"   - Total unique strategies explored: {total_strategies}\n")
        for task, diversity in strategy_div.items():
            f.write(f"   - {task}: {diversity} different strategies tried\n")
        f.write("\n")
        
        # Episode completion analysis
        f.write("2. EPISODE COMPLETION PROGRESS:\n")
        episode_completion = analysis.get('episode_completion_analysis', {})
        total_completed = episode_completion.get('total_blocks_completed', 0)
        episodes_with_completions = episode_completion.get('episodes_with_completions', 0)
        best_episode = episode_completion.get('best_episode_completions', 0)
        completion_trend = episode_completion.get('completion_trend', 'unknown')
        
        f.write(f"   - Total blocks completed across all episodes: {total_completed}\n")
        f.write(f"   - Episodes with successful completions: {episodes_with_completions}\n")
        f.write(f"   - Best episode completion count: {best_episode}\n")
        f.write(f"   - Overall completion trend: {completion_trend}\n")
        
        blocks_per_episode = episode_completion.get('blocks_completed_per_episode', [])
        if blocks_per_episode:
            f.write(f"   - Episode-by-episode completions: {blocks_per_episode}\n")
        f.write("\n")
        
        # Block success rate evolution
        f.write("3. BLOCK SUCCESS RATE EVOLUTION:\n")
        block_success_evolution = analysis.get('strategy_evolution', {}).get('block_success_evolution', {})
        for block, rates in block_success_evolution.items():
            if rates:
                first_rate = rates[0]
                last_rate = rates[-1]
                best_rate = max(rates)
                improvement = last_rate - first_rate
                f.write(f"   {block}:\n")
                f.write(f"     - First attempt: {first_rate:.1%}\n")
                f.write(f"     - Latest attempt: {last_rate:.1%}\n")
                f.write(f"     - Best achieved: {best_rate:.1%}\n")
                f.write(f"     - Overall improvement: {improvement:+.1%}\n")
        f.write("\n")
        
        # Block completion time trends
        f.write("4. BLOCK COMPLETION TIME TRENDS:\n")
        completion_times = analysis.get('strategy_evolution', {}).get('completion_time_trends', {})
        for block, times in completion_times.items():
            if times:
                avg_time = np.mean(times)
                if len(times) > 1:
                    first_time = times[0]
                    last_time = times[-1]
                    time_improvement = first_time - last_time
                    f.write(f"   {block}:\n")
                    f.write(f"     - Average completion time: {avg_time:.1f} steps\n")
                    f.write(f"     - First completion: {first_time:.1f} steps\n")
                    f.write(f"     - Latest completion: {last_time:.1f} steps\n")
                    f.write(f"     - Time improvement: {time_improvement:+.1f} steps\n")
                else:
                    f.write(f"   {block}: Single completion in {times[0]:.1f} steps\n")
    
    print(f"Learning analysis report saved to: {report_path}")
    
    return plot_path, report_path

def export_detailed_csv(results: List[Dict], analysis: Dict, output_dir: str = "runs") -> str:
    """
    Export comprehensive learning data to CSV files for detailed analysis
    """
    print("\n" + "="*60)
    print("EXPORTING DETAILED CSV DATA")
    print("="*60)
    
    # 1. Episode Summary CSV
    episode_data = []
    for result in results:
        if 'error' not in result:
            row = {
                'episode_num': result['episode_num'],
                'total_steps': result['total_steps'],
                'total_reward': result['total_reward'],
                'communication_rounds': result.get('communication_rounds', 0),
                'success': result['success'],
                'episode_duration': result.get('episode_duration', 0),
                'blocks_completed': len(result.get('completed_blocks', [])),
                'initial_blocks_count': len(result.get('initial_blocks', []))
            }
            
            # Add planning counts per agent
            planning_counts = result.get('agent_planning_counts', {})
            for agent_id, count in planning_counts.items():
                row[f'planning_count_{agent_id}'] = count
            
            # Add average planning count
            if planning_counts:
                row['avg_planning_count'] = np.mean(list(planning_counts.values()))
                row['total_planning_events'] = sum(planning_counts.values())
            
            episode_data.append(row)
    
    episode_df = pd.DataFrame(episode_data)
    episode_csv = os.path.join(output_dir, 'episode_summary.csv')
    episode_df.to_csv(episode_csv, index=False)
    print(f"Episode summary CSV saved to: {episode_csv}")
    
    # 2. Block Completion Timing CSV
    block_timing_data = []
    for result in results:
        if 'error' not in result and 'block_completion_times' in result:
            episode_num = result['episode_num']
            for block_id, completion_time in result['block_completion_times'].items():
                block_timing_data.append({
                    'episode_num': episode_num,
                    'block_id': block_id,
                    'completion_time_seconds': completion_time,
                    'episode_total_steps': result['total_steps'],
                    'episode_success': result['success']
                })
    
    if block_timing_data:
        block_timing_df = pd.DataFrame(block_timing_data)
        block_timing_csv = os.path.join(output_dir, 'block_completion_timing.csv')
        block_timing_df.to_csv(block_timing_csv, index=False)
        print(f"Block completion timing CSV saved to: {block_timing_csv}")
    
    # 3. Agent Planning Activity CSV
    planning_data = []
    for result in results:
        if 'error' not in result and 'agent_planning_counts' in result:
            episode_num = result['episode_num']
            for agent_id, planning_count in result['agent_planning_counts'].items():
                planning_data.append({
                    'episode_num': episode_num,
                    'agent_id': agent_id,
                    'planning_count': planning_count,
                    'episode_success': result['success'],
                    'episode_steps': result['total_steps'],
                    'blocks_completed': len(result.get('completed_blocks', []))
                })
    
    if planning_data:
        planning_df = pd.DataFrame(planning_data)
        planning_csv = os.path.join(output_dir, 'agent_planning_activity.csv')
        planning_df.to_csv(planning_csv, index=False)
        print(f"Agent planning activity CSV saved to: {planning_csv}")
    
    # 4. Learning Progress Summary CSV
    learning_metrics = analysis.get('learning_metrics', {})
    if learning_metrics:
        progress_data = []
        
        for i, ep_num in enumerate(learning_metrics.get('reward_trend', [])):
            row = {
                'episode_num': i + 1,
                'reward': learning_metrics['reward_trend'][i] if i < len(learning_metrics['reward_trend']) else 0,
                'steps': learning_metrics['efficiency_trend'][i] if i < len(learning_metrics['efficiency_trend']) else 0,
                'comm_rounds': learning_metrics['communication_trend'][i] if i < len(learning_metrics['communication_trend']) else 0,
                'success': learning_metrics['success_rate_progression'][i] if i < len(learning_metrics['success_rate_progression']) else False,
                'duration': learning_metrics['episode_duration_trend'][i] if i < len(learning_metrics['episode_duration_trend']) else 0
            }
            progress_data.append(row)
        
        progress_df = pd.DataFrame(progress_data)
        progress_csv = os.path.join(output_dir, 'learning_progress.csv')
        progress_df.to_csv(progress_csv, index=False)
        print(f"Learning progress CSV saved to: {progress_csv}")
    
    print("="*60)
    return episode_csv


def main():
    p = argparse.ArgumentParser("Learning Pipeline (episodes → multiverse → retrieval)")
    p.add_argument("--n", type=int, default=2, help="# agents")
    p.add_argument("--model", type=str, default="gpt-4o", help="Azure OpenAI deployment name")
    p.add_argument("--max_steps", type=int, default=100)
    p.add_argument("--num_episodes", type=int, default=3)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--max_tokens", type=int, default=900)
    p.add_argument("--disable_shared_writing", action="store_true", 
                   help="Disable writing to shared insights file (still reads existing file)")
    args = p.parse_args()

    print(f"Running {args.num_episodes} episodes; agents={args.n}; model={args.model}")
    universe = UniverseStore(root="runs/universe")

    results = []
    for ep in range(1, args.num_episodes+1):
        try:
            print(f"\n[DEBUG] Starting episode {ep}")
            r = run_episode(ep, args, universe)
            print(f"[DEBUG] Episode {ep} completed successfully")
            print(f"[DEBUG] Episode {ep} data keys: {list(r.keys()) if r else 'None'}")
            results.append(r)
            print(f"Episode {ep} → steps={r['total_steps']}, reward={r['total_reward']:.2f}, success={r['success']}")
        except Exception as e:
            print(f"Episode {ep} failed: {e}")
            import traceback
            traceback.print_exc()
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
    
    # Generate universe evolution summary
    universe_summary = universe.generate_universe_evolution_summary("runs")
    
    # Print basic summary
    print("\n" + "="*60)
    print("MULTI-EPISODE SUMMARY")
    print("="*60)
    
    successful_episodes = [r for r in results if r.get('success', False)]
    print(f"Episodes completed: {len(results)}")
    print(f"Successful episodes: {len(successful_episodes)}")
    print(f"Success rate: {len(successful_episodes)/len(results)*100:.1f}%" if results else "No episodes completed")
    
    if results:
        avg_reward = np.mean([r['total_reward'] for r in results if 'total_reward' in r])
        avg_steps = np.mean([r['total_steps'] for r in results if 'total_steps' in r])
        print(f"Average reward: {avg_reward:.1f}")
        print(f"Average steps: {avg_steps:.1f}")
    
    # Print universe information
    snapshots = universe.list_snapshots()
    print(f"\nUniverse Evolution:")
    print(f"  Current universe: {universe.json()}")
    print(f"  Episode snapshots: {len(snapshots)} saved")
    print(f"  Snapshots: {snapshots}")
    if universe_summary:
        print(f"  Evolution summary: {universe_summary}")
    
    print("="*60)
    
    # Perform learning progress analysis
    if len(results) >= 2:  # Need at least 2 episodes for meaningful analysis
        try:
            print(f"\n[DEBUG] Starting analysis with {len(results)} episodes")
            print(f"[DEBUG] Results data: {[{k: v for k, v in r.items() if k not in ['block_completion_times']} for r in results[:2]]}")
            
            analysis = analyze_learning_progress(results, universe)
            plot_path, report_path = generate_learning_visualizations(analysis, "runs")
            csv_path = export_detailed_csv(results, analysis, "runs")
            
            print(f"\n📊 Learning Analysis Complete!")
            print(f"📈 Visualization: {plot_path}")
            print(f"📄 Report: {report_path}")
            print(f"📋 CSV Export: {csv_path}")
            
            # Print key insights
            print("\n🔍 KEY LEARNING INSIGHTS:")
            reward_improvement = analysis['learning_metrics'].get('average_reward_improvement', 0)
            step_improvement = analysis['learning_metrics'].get('step_efficiency_improvement', 0)
            
            if reward_improvement > 0:
                print(f"✅ Agents showing reward improvement: +{reward_improvement:.1f}")
            else:
                print(f"📉 Reward trend: {reward_improvement:.1f}")
                
            if step_improvement > 0:
                print(f"✅ Agents becoming more efficient: -{step_improvement:.1f} steps")
            else:
                print(f"📈 Efficiency trend: {step_improvement:.1f} steps")
            
            # Planning activity insights
            planning_counts = analysis['learning_metrics'].get('planning_counts_per_episode', [])
            if planning_counts:
                avg_planning_per_episode = [np.mean(list(counts.values())) if counts else 0 for counts in planning_counts]
                if avg_planning_per_episode:
                    print(f"🧠 Average planning events per episode: {np.mean(avg_planning_per_episode):.1f}")
                    if len(avg_planning_per_episode) > 1:
                        planning_trend = avg_planning_per_episode[-1] - avg_planning_per_episode[0]
                        if planning_trend < 0:
                            print(f"✅ Planning efficiency improving: {abs(planning_trend):.1f} fewer planning events")
                        else:
                            print(f"📈 Planning activity increasing: +{planning_trend:.1f} planning events")
            
            # Strategy diversity insights
            strategy_div = analysis.get('strategy_evolution', {}).get('strategy_diversity_per_task', {})
            if strategy_div:
                total_strategies = sum(strategy_div.values())
                print(f"🧠 Total strategies explored: {total_strategies}")
                for task, count in strategy_div.items():
                    print(f"   - {task}: {count} different approaches")
            
            # Block delivery insights  
            block_analysis = analysis.get('block_delivery_analysis', {})
            success_rate = block_analysis.get('overall_block_success_rate', 0)
            if success_rate > 0:
                print(f"📦 Block delivery success rate: {success_rate:.1%}")
            
            print("="*60)
            
        except Exception as e:
            print(f"\n⚠️  Learning analysis failed: {e}")
            print("Continuing with basic summary...")
    else:
        print(f"\n📊 Learning analysis requires at least 2 episodes (current: {len(results)})")
        print("Run more episodes to see learning progress visualization.")

if __name__ == "__main__":
    main()


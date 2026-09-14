#!/usr/bin/env python3
"""
baseline_with_stats.py
=======================
Baseline agent system with comprehensive statistics collection and analysis.
This creates the same analysis figures as the learning pipeline for comparison.
"""
from __future__ import annotations
import argparse
import os
import sys
import time
import json
import io
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict
import random
import numpy as np
import matplotlib.pyplot as plt

# Environment and Controllers
from cube.env import CoopBlockPush
from cube.symbolic_actions import SymbolicController

# Framework components
from llm_agent import LLMAgent, LLMConfig, LLMAgentManager
import llm_templates as templates
from world_model import create_world_model_from_log

# ------------------------------
# Utilities
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
# Baseline Agent with Statistics
# ------------------------------
class BaselineAgentManager:
    """Manages baseline agents with detailed statistics tracking"""
    
    def __init__(self):
        self.episode_data = []
        self.block_completion_data = defaultdict(list)
        self.agent_performance_data = defaultdict(list)
        
    def collect_episode_data(self, episode_data: Dict):
        """Collect data from a completed episode"""
        self.episode_data.append(episode_data)
        
        # Track block completion patterns
        for block_id, completion_time in episode_data.get('block_completion_times', {}).items():
            self.block_completion_data[f"Block_{block_id}"].append(completion_time)
            
        # Track agent performance patterns
        for agent_id, planning_count in episode_data.get('agent_planning_counts', {}).items():
            self.agent_performance_data[agent_id].append(planning_count)

def baseline_plan(agent: LLMAgent, all_agents=None):
    """Baseline-specific planning that prioritizes closest blocks to goal"""
    
    # Track planning count for this agent
    if not hasattr(agent, 'planning_count'):
        agent.planning_count = 0
    agent.planning_count += 1
    
    # Temporarily store the original planning prompt
    original_prompt = templates.PLANNING_SYSTEM_PROMPT
    
    # Use baseline-specific planning prompt
    templates.PLANNING_SYSTEM_PROMPT = """You are a cooperative planner for a block-pushing team.

Environment rules (do not restate in the plan):
- The world is a grid.
- Each block is a w by w square with weight w.
- A block of weight w requires w simultaneous pushers on its face to move it 1 cell in the opposite direction.
- Goal: push blocks into the goal zone using the fewest possible steps.
- The goal zone is the RIGHTMOST column. Prefer rightward progress when reasonable (e.g., move to the left of a block, then push it right).

BASELINE STRATEGY - ALWAYS prioritize working with the block that is closest to the goal zone (has the smallest distance_to_goal).
This ensures the team focuses on completing blocks that are nearest to success first.

Available symbolic actions:
- MoveToBlock: The agent moves to align with the specified block face.
- Rendezvous: The agent waits at the current position until the specified number of agents gather at the block face.
- Push: Push the specified block n steps in the direction opposite the block face.
- Wait: Remain in place for a specified number of steps.
- WaitAgents: Wait until the specified number of other agents are available to communicate for task allocation.
- YieldFace: Move away from the specified block face.

Coordination tips:
- Coordinate pushes using Rendezvous to ensure enough pushers are synchronized.
- Prefer faces that push blocks toward the goal (e.g., pushing from the left face moves the block right).
- Agents communicate for task allocation.
- Keep plans short and executable (3–6 actions) that can succeed from the current state.
- Empty plans are not allowed.
Return the plan as a structured response following the specified schema."""
    
    # Call the original plan method
    agent.plan(all_agents)
    
    # Restore the original prompt
    templates.PLANNING_SYSTEM_PROMPT = original_prompt

def build_agents(env, agent_manager: LLMAgentManager, n_agents: int, model: str) -> Dict[str, LLMAgent]:
    cfg = LLMConfig(model=model)
    agents: Dict[str, LLMAgent] = {}
    for i in range(n_agents):
        aid = f"agent_{i}"
        agent = LLMAgent(aid, env, agent_manager, cfg, plan=[])
        # Initialize tracking attributes
        agent.planning_count = 0
        agent.episode_start_time = time.time()
        agents[aid] = agent
        agent_manager.add_agent(agent)
    return agents

def reset_agent_plan_runtime_state(agent: LLMAgent):
    """Reset agent state for replanning"""
    agent.plan_steps = []
    agent.plan_index = 0
    agent.phase = "planning"
    if hasattr(agent, "_plan_completion_logged"):
        delattr(agent, "_plan_completion_logged")

# ------------------------------
# Episode Runner
# ------------------------------
def run_baseline_episode(ep_num: int, args, stats_manager: BaselineAgentManager) -> Dict:
    """Run a single baseline episode with statistics collection"""
    print("\n" + "="*60)
    print(f"STARTING BASELINE EPISODE {ep_num}")
    print("="*60)

    # Timing and tracking initialization
    episode_start_time = time.time()
    block_completion_times = {}  # block_id -> completion_time
    initial_blocks = None
    
    # Agent commitment tracking  
    agent_commitments = defaultdict(list)  # agent_id -> [(step, task_name), ...]
    
    # Folders & files
    ep_root = f"runs/baseline_episode_{ep_num:02d}"
    os.makedirs(ep_root, exist_ok=True)
    log_file = os.path.join(ep_root, "trace.json")

    # Environment (fixed seed for reproducibility)
    random.seed(args.seed)
    np.random.seed(args.seed)

    env = CoopBlockPush(n=args.n, max_steps=args.max_steps, render_mode='human')
    env.reset(seed=args.seed)
    
    # Track initial blocks for completion timing
    initial_blocks = set([b.id for b in getattr(env, "_blocks", [])])
    print(f"Initial blocks: {initial_blocks}")

    # Core managers & agents
    manager = LLMAgentManager(env)
    agents = build_agents(env, manager, args.n, args.model)
    
    # Set episode start time for all agents
    for agent in agents.values():
        agent.episode_start_time = episode_start_time

    # ===== INITIAL PLANNING PHASE =====
    print("\n" + "="*60)
    print("BASELINE PLANNING PHASE")
    print("="*60)
    
    for agent in agents.values():
        print(f"\n--- Planning for {agent.id} ---")
        baseline_plan(agent, all_agents=agents)
        
        # Track basic commitments for baseline (simple task assignment)
        if hasattr(agent, 'assigned_block'):
            agent_commitments[agent.id].append((0, f"Block_{agent.assigned_block}"))
        else:
            agent_commitments[agent.id].append((0, "No_Task"))

    manager.log_planning_completed(0, list(agents.keys()))

    # Build controller
    print(f"[DEBUG] All agents: {list(agents.keys())}")
    
    # Convert agent plans to objects
    plans_obj = manager.convert_all_agent_plans_to_objects()
    print(f"[DEBUG] Plans object keys: {list(plans_obj.keys()) if plans_obj else 'None'}")
    
    controller = SymbolicController(env, plans_obj)

    # Print debug info about plans
    for aid, agent in agents.items():
        print(f"[DEBUG] {aid} plan: {agent.plan_steps}")

    # ===== EXECUTION LOOP =====
    total_reward = 0.0
    step = 0

    while step < args.max_steps:
        # Check for replanning needs (baseline approach)
        if len(getattr(env, "_blocks", [])) > 0:
            agents_needing_replan = [aid for aid, a in agents.items() if a.is_finished()]
            if agents_needing_replan:
                print(f"Agents needing replan: {agents_needing_replan}")
                # Reset those agents to planning
                for aid in agents_needing_replan:
                    a = agents[aid]
                    reset_agent_plan_runtime_state(a)
                    baseline_plan(a, all_agents=agents)
                    
                    # Update commitment tracking
                    if hasattr(a, 'assigned_block'):
                        agent_commitments[aid].append((step, f"Block_{a.assigned_block}"))
                    else:
                        agent_commitments[aid].append((step, "No_Task"))

                # Update controller for those agents
                plans_obj = manager.convert_all_agent_plans_to_objects()
                for aid in agents_needing_replan:
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
                    'committed_task': getattr(a, 'task_name', None) if hasattr(a, 'task_name') else None
                }})

        step += 1
        total_reward += sum(rewards.values())

        # Stop conditions
        if all(dones.values()) or all(truncated.values()):
            break
        if all(a.is_finished() for a in agents.values()) and len(getattr(env, "_blocks", [])) == 0:
            print("All blocks delivered — episode done.")
            break

    # ===== Save episode log & per-episode artifacts =====
    manager.save_complete_log(log_file)
    print(f"Saved episode log to {os.path.abspath(log_file)}")

    # Generate per-episode world model and visualizations
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
    except Exception as e:
        print(f"[WARNING] World model generation failed: {e}")
        # Still proceed with the episode
    finally:
        os.chdir(cwd)

    # Timeline visualization
    try:
        viz_png = os.path.join(ep_root, "log_visualization.png")
        result = subprocess.run([
            "python", "log_visualizer.py", os.path.abspath(log_file), "-o", os.path.abspath(viz_png)
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        if result.returncode != 0:
            print("Log visualizer error:", result.stderr)
    except Exception as e:
        print(f"[WARNING] Log visualization failed: {e}")

    # Episode summary data collection
    total_steps = len([e for e in manager.activity_log if e.get('event_type') == 'timestep'])
    comm_rounds = len(manager.get_communication_log())  # Will be 0 for baseline
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
        'episode_folder': ep_root,
        'agent_type': 'baseline'  # Mark as baseline for analysis
    }
    
    print(f"[DEBUG] Episode {ep_num} completed - collecting statistics")
    stats_manager.collect_episode_data(episode_data)
    
    return episode_data

# ------------------------------
# Analysis and Visualization
# ------------------------------
def analyze_baseline_performance(results: List[Dict]) -> Dict:
    """Analyze baseline agent performance across episodes"""
    print("\n" + "="*60)
    print("ANALYZING BASELINE PERFORMANCE")
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
    
    # Filter valid episodes
    episodes = [r for r in results if 'error' not in r]
    print(f"[DEBUG] Valid episodes after error filtering: {len(episodes)}")
    
    if not episodes:
        print("[WARNING] No valid episodes found for analysis")
        return analysis
    
    episode_nums = [r['episode_num'] for r in episodes]
    rewards = [r['total_reward'] for r in episodes]
    steps = [r['total_steps'] for r in episodes]
    comm_rounds = [r.get('communication_rounds', 0) for r in episodes]  # Always 0 for baseline
    success_rates = [r['success'] for r in episodes]
    
    # New metrics
    episode_durations = [r.get('episode_duration', 0) for r in episodes]
    planning_counts = [r.get('agent_planning_counts', {}) for r in episodes]
    block_completions = [r.get('block_completion_times', {}) for r in episodes]
    agent_commitments = [r.get('agent_commitments', {}) for r in episodes]
    
    analysis['learning_metrics'] = {
        'reward_trend': rewards,
        'efficiency_trend': steps,
        'communication_trend': comm_rounds,  # Always 0 for baseline
        'success_rate_progression': success_rates,
        'episode_duration_trend': episode_durations,
        'planning_counts_per_episode': planning_counts,
        'block_completion_trends': block_completions,
        'agent_commitments_per_episode': agent_commitments,
        'average_reward_improvement': np.mean(rewards[-2:]) - np.mean(rewards[:2]) if len(rewards) >= 4 else 0,
        'step_efficiency_improvement': np.mean(steps[:2]) - np.mean(steps[-2:]) if len(steps) >= 4 else 0
    }
    
    # Block completion analysis
    direct_block_completion_times = defaultdict(list)
    all_block_ids = set()
    
    for result in episodes:
        block_times = result.get('block_completion_times', {})
        all_block_ids.update(block_times.keys())
    
    for block_id in all_block_ids:
        for result in episodes:
            block_times = result.get('block_completion_times', {})
            if block_id in block_times:
                direct_block_completion_times[block_id].append(block_times[block_id])
            else:
                direct_block_completion_times[block_id].append(0)
    
    # Build block success evolution
    current_block_success_rates = defaultdict(list)
    for result in episodes:
        block_times = result.get('block_completion_times', {})
        completed_blocks = set(block_times.keys())
        
        for block_id in all_block_ids:
            success_rate = 1.0 if block_id in completed_blocks else 0.0
            current_block_success_rates[f"Block_{block_id}"].append(success_rate)
    
    analysis['strategy_evolution'] = {
        'strategy_diversity_per_task': {},  # Baseline has fixed strategy
        'strategies_tried': {},
        'block_success_evolution': dict(current_block_success_rates),
        'completion_time_trends': dict(direct_block_completion_times)
    }
    
    # Communication efficiency (baseline has no communication)
    analysis['communication_efficiency'] = {
        'avg_comm_rounds_early': 0,
        'avg_comm_rounds_late': 0,
        'communication_improvement': 0
    }
    
    # Coordination improvement (based on step efficiency and success)
    coordination_score = []
    for i, (r, s) in enumerate(zip(rewards, steps)):
        score = r / max(s, 1)  # Simple efficiency score
        coordination_score.append(score)
    
    analysis['coordination_improvement'] = {
        'coordination_scores': coordination_score,
        'coordination_trend': 'improving' if len(coordination_score) > 2 and coordination_score[-1] > coordination_score[0] else 'stable',
        'best_coordination_episode': episode_nums[np.argmax(coordination_score)] if coordination_score else 0
    }
    
    return analysis

def generate_agent_commitment_heatmap(results: List[Dict], output_dir: str = "runs"):
    """Generate agent task commitment heatmap across episodes"""
    print("\n" + "="*60)
    print("GENERATING AGENT COMMITMENT HEATMAP")
    print("="*60)
    
    if not results:
        print("[WARNING] No results data for heatmap generation")
        return
    
    # Collect commitment data across all episodes
    all_commitment_data = []
    episode_labels = []
    
    for result in results:
        if 'error' in result:
            continue
            
        episode_num = result.get('episode_num', 0)
        episode_labels.append(f"Episode {episode_num}")
        
        # Get agent commitments for this episode
        agent_commitments = result.get('agent_commitments', {})
        episode_commitment_data = {}
        
        # Process each agent's commitments
        for agent_id, commitments in agent_commitments.items():
            agent_tasks = {}
            
            # Initialize task counters
            for step, task in commitments:
                task_name = task.replace('Block_', 'Block ')
                if task_name not in agent_tasks:
                    agent_tasks[task_name] = 0
                agent_tasks[task_name] += 1
            
            episode_commitment_data[agent_id] = agent_tasks
        
        all_commitment_data.append(episode_commitment_data)
    
    if not all_commitment_data:
        print("[WARNING] No valid commitment data found")
        return
    
    # Extract all unique agents and tasks
    all_agents = set()
    all_tasks = set()
    
    for episode_data in all_commitment_data:
        all_agents.update(episode_data.keys())
        for agent_data in episode_data.values():
            all_tasks.update(agent_data.keys())
    
    all_agents = sorted(list(all_agents))
    all_tasks = sorted(list(all_tasks))
    
    print(f"[DEBUG] Found agents: {all_agents}")
    print(f"[DEBUG] Found tasks: {all_tasks}")
    
    # Create the heatmap matrix
    num_episodes = len(all_commitment_data)
    num_agents = len(all_agents)
    num_tasks = len(all_tasks)
    
    # Create separate heatmaps for each task
    fig, axes = plt.subplots(1, max(1, num_tasks), figsize=(6*num_tasks, 8))
    if num_tasks == 1:
        axes = [axes]
    
    fig.suptitle('Agent Task Commitment Heatmaps Across Episodes', fontsize=16, fontweight='bold')
    
    for task_idx, task in enumerate(all_tasks):
        ax = axes[task_idx] if num_tasks > 1 else axes[0]
        
        # Create matrix for this task
        commitment_matrix = np.zeros((num_agents, num_episodes))
        
        for ep_idx, episode_data in enumerate(all_commitment_data):
            for agent_idx, agent in enumerate(all_agents):
                if agent in episode_data and task in episode_data[agent]:
                    commitment_matrix[agent_idx, ep_idx] = episode_data[agent][task]
        
        # Create heatmap
        im = ax.imshow(commitment_matrix, cmap='YlOrRd', aspect='auto', interpolation='nearest')
        
        # Set labels
        ax.set_title(f'{task} Commitments', fontweight='bold')
        ax.set_xlabel('Episode')
        ax.set_ylabel('Agent')
        
        # Set ticks
        ax.set_xticks(range(num_episodes))
        ax.set_xticklabels([f"Ep{i+1}" for i in range(num_episodes)], rotation=45)
        ax.set_yticks(range(num_agents))
        ax.set_yticklabels(all_agents)
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax, shrink=0.6)
        cbar.set_label('Commitment Count', rotation=270, labelpad=15)
        
        # Add text annotations
        for i in range(num_agents):
            for j in range(num_episodes):
                value = commitment_matrix[i, j]
                if value > 0:
                    text_color = 'white' if value > commitment_matrix.max() * 0.6 else 'black'
                    ax.text(j, i, f'{int(value)}', ha='center', va='center', 
                           color=text_color, fontweight='bold')
    
    plt.tight_layout()
    
    # Save the heatmap
    heatmap_path = os.path.join(output_dir, "agent_commitment_heatmap.png")
    ensure_dir(heatmap_path)
    plt.savefig(heatmap_path, dpi=300, bbox_inches='tight')
    print(f"[HEATMAP] Agent commitment heatmap saved to: {heatmap_path}")
    
    # Also save as PDF
    pdf_path = os.path.join(output_dir, "agent_commitment_heatmap.pdf")
    plt.savefig(pdf_path, dpi=300, bbox_inches='tight')
    print(f"[HEATMAP] PDF version saved to: {pdf_path}")
    
    plt.close()

def generate_baseline_visualizations(analysis: Dict, output_dir: str = "runs"):
    """Generate baseline performance visualizations"""
    print("\n" + "="*60)
    print("GENERATING BASELINE VISUALIZATIONS")
    print("="*60)
    
    learning_metrics = analysis.get('learning_metrics', {})
    actual_episodes = len(learning_metrics.get('reward_trend', []))
    
    plt.style.use('default')
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    fig.suptitle(f'Baseline Agent Performance Analysis ({actual_episodes} Episodes)', fontsize=16, fontweight='bold')
    
    # 1. Agent Planning Activity Over Episodes
    ax1 = axes[0, 0]
    planning_counts = analysis.get('learning_metrics', {}).get('planning_counts_per_episode', [])
    if planning_counts:
        episodes = list(range(1, len(planning_counts) + 1))
        avg_planning_per_episode = [np.mean(list(counts.values())) if counts else 0 for counts in planning_counts]
        total_planning_per_episode = [sum(counts.values()) if counts else 0 for counts in planning_counts]
        
        ax1_twin = ax1.twinx()
        
        bars = ax1.bar(episodes, avg_planning_per_episode, alpha=0.7, color='lightblue', label='Avg Planning/Agent')
        line = ax1_twin.plot(episodes, total_planning_per_episode, 'ro-', linewidth=2, markersize=6, label='Total Planning Events')
        
        ax1.set_title('Baseline Agent Planning Activity', fontweight='bold')
        ax1.set_xlabel('Episode Number')
        ax1.set_ylabel('Average Planning Events per Agent', color='blue')
        ax1.tick_params(axis='y', labelcolor='blue')
        ax1_twin.set_ylabel('Total Planning Events', color='red')
        ax1_twin.tick_params(axis='y', labelcolor='red')
        ax1.grid(True, alpha=0.3)
        
        # Combined legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax1_twin.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    else:
        ax1.text(0.5, 0.5, 'No planning activity data available', ha='center', va='center', transform=ax1.transAxes)
        ax1.set_title('Baseline Agent Planning Activity', fontweight='bold')
    
    # 2. Block Completion Timing
    ax2 = axes[0, 1]
    block_completions = analysis.get('learning_metrics', {}).get('block_completion_trends', [])
    if block_completions:
        episode_completion_times = []
        episode_block_counts = []
        
        for ep_data in block_completions:
            if ep_data:
                times = list(ep_data.values())
                avg_time = np.mean(times) if times else 0
                episode_completion_times.append(avg_time)
                episode_block_counts.append(len(times))
            else:
                episode_completion_times.append(0)
                episode_block_counts.append(0)
        
        episodes = list(range(1, len(episode_completion_times) + 1))
        
        ax2_twin = ax2.twinx()
        
        line1 = ax2.plot(episodes, episode_completion_times, 'go-', linewidth=2, markersize=6, label='Avg Completion Time')
        bars = ax2_twin.bar(episodes, episode_block_counts, alpha=0.3, color='purple', label='Blocks Completed')
        
        ax2.set_title('Baseline Block Completion Timing', fontweight='bold')
        ax2.set_xlabel('Episode Number')
        ax2.set_ylabel('Average Completion Time (seconds)', color='green')
        ax2.tick_params(axis='y', labelcolor='green')
        ax2_twin.set_ylabel('Number of Blocks Completed', color='purple')
        ax2_twin.tick_params(axis='y', labelcolor='purple')
        ax2.grid(True, alpha=0.3)
        
        # Combined legend
        lines1, labels1 = ax2.get_legend_handles_labels()
        lines2, labels2 = ax2_twin.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    else:
        ax2.text(0.5, 0.5, 'No block completion timing data available', ha='center', va='center', transform=ax2.transAxes)
        ax2.set_title('Baseline Block Completion Timing', fontweight='bold')
    
    # 3. Performance Trends (Reward and Steps)
    ax3 = axes[0, 2]
    rewards = analysis.get('learning_metrics', {}).get('reward_trend', [])
    steps = analysis.get('learning_metrics', {}).get('efficiency_trend', [])
    
    if rewards and steps:
        episodes = list(range(1, len(rewards) + 1))
        
        ax3_twin = ax3.twinx()
        
        line1 = ax3.plot(episodes, rewards, 'bo-', linewidth=2, markersize=6, label='Total Reward')
        line2 = ax3_twin.plot(episodes, steps, 'ro-', linewidth=2, markersize=6, label='Total Steps')
        
        ax3.set_title('Baseline Performance Trends', fontweight='bold')
        ax3.set_xlabel('Episode Number')
        ax3.set_ylabel('Total Reward', color='blue')
        ax3.tick_params(axis='y', labelcolor='blue')
        ax3_twin.set_ylabel('Total Steps', color='red')
        ax3_twin.tick_params(axis='y', labelcolor='red')
        ax3.grid(True, alpha=0.3)
        
        # Combined legend
        lines1, labels1 = ax3.get_legend_handles_labels()
        lines2, labels2 = ax3_twin.get_legend_handles_labels()
        ax3.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    else:
        ax3.text(0.5, 0.5, 'No performance trend data available', ha='center', va='center', transform=ax3.transAxes)
        ax3.set_title('Baseline Performance Trends', fontweight='bold')
    
    # 4. Block Success Rate Heatmap
    ax4 = axes[1, 0]
    block_success_evolution = analysis.get('strategy_evolution', {}).get('block_success_evolution', {})
    if block_success_evolution:
        all_blocks = list(block_success_evolution.keys())
        max_episodes = max(len(rates) for rates in block_success_evolution.values()) if block_success_evolution else 1
        
        success_matrix = np.full((len(all_blocks), max_episodes), np.nan)
        
        for i, block in enumerate(all_blocks):
            rates = block_success_evolution[block]
            for j, rate in enumerate(rates):
                success_matrix[i, j] = rate
        
        im = ax4.imshow(success_matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
        
        ax4.set_title('Baseline Block Success Rate Over Episodes', fontweight='bold')
        ax4.set_xlabel('Episode Number')
        ax4.set_ylabel('Block Task')
        ax4.set_yticks(range(len(all_blocks)))
        ax4.set_yticklabels(all_blocks)
        ax4.set_xticks(range(max_episodes))
        ax4.set_xticklabels([f'Ep{i+1}' for i in range(max_episodes)])
        
        cbar = plt.colorbar(im, ax=ax4, fraction=0.046, pad=0.04)
        cbar.set_label('Success (1=✓, 0=✗)', rotation=270, labelpad=15)
        cbar.set_ticks([0, 1])
        cbar.set_ticklabels(['Failed', 'Success'])
    else:
        ax4.text(0.5, 0.5, 'No block success data available', ha='center', va='center', transform=ax4.transAxes)
        ax4.set_title('Baseline Block Success Rate Over Episodes', fontweight='bold')
    
    # 5. Success Rate Over Time
    ax5 = axes[1, 1]
    success_rates = analysis.get('learning_metrics', {}).get('success_rate_progression', [])
    if success_rates:
        episodes = list(range(1, len(success_rates) + 1))
        
        bars = ax5.bar(episodes, success_rates, alpha=0.7, color='green')
        ax5.set_title('Baseline Episode Success Rate', fontweight='bold')
        ax5.set_xlabel('Episode Number')
        ax5.set_ylabel('Success (1=Success, 0=Failure)')
        ax5.set_ylim(0, 1.1)
        ax5.grid(True, alpha=0.3)
        
        # Add percentage text
        success_pct = np.mean(success_rates) * 100
        ax5.text(0.02, 0.98, f'Overall Success: {success_pct:.1f}%', 
                transform=ax5.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    else:
        ax5.text(0.5, 0.5, 'No success rate data available', ha='center', va='center', transform=ax5.transAxes)
        ax5.set_title('Baseline Episode Success Rate', fontweight='bold')
    
    # 6. Coordination Efficiency
    ax6 = axes[1, 2]
    coordination_scores = analysis.get('coordination_improvement', {}).get('coordination_scores', [])
    if coordination_scores:
        episodes = list(range(1, len(coordination_scores) + 1))
        
        line = ax6.plot(episodes, coordination_scores, 'mo-', linewidth=2, markersize=6, label='Coordination Score')
        ax6.set_title('Baseline Coordination Efficiency', fontweight='bold')
        ax6.set_xlabel('Episode Number')
        ax6.set_ylabel('Coordination Score (Reward/Steps)')
        ax6.grid(True, alpha=0.3)
        ax6.legend()
        
        # Add trend line
        if len(coordination_scores) > 1:
            z = np.polyfit(episodes, coordination_scores, 1)
            p = np.poly1d(z)
            ax6.plot(episodes, p(episodes), "r--", alpha=0.8, label='Trend')
            ax6.legend()
    else:
        ax6.text(0.5, 0.5, 'No coordination data available', ha='center', va='center', transform=ax6.transAxes)
        ax6.set_title('Baseline Coordination Efficiency', fontweight='bold')
    
    plt.tight_layout()
    
    # Save the visualization
    viz_path = os.path.join(output_dir, "baseline_performance_analysis.png")
    ensure_dir(viz_path)
    plt.savefig(viz_path, dpi=300, bbox_inches='tight')
    print(f"[VISUALIZATION] Baseline analysis saved to: {viz_path}")
    
    # Also save as PDF for publications
    pdf_path = os.path.join(output_dir, "baseline_performance_analysis.pdf")
    plt.savefig(pdf_path, dpi=300, bbox_inches='tight')
    print(f"[VISUALIZATION] PDF version saved to: {pdf_path}")
    
    # Don't show plot interactively, just save and close
    plt.close()

def generate_baseline_summary_report(analysis: Dict, results: List[Dict], output_dir: str = "runs"):
    """Generate a comprehensive text summary of baseline performance"""
    
    report_path = os.path.join(output_dir, "baseline_performance_report.txt")
    ensure_dir(report_path)
    
    with open(report_path, 'w') as f:
        f.write("BASELINE AGENT PERFORMANCE REPORT\n")
        f.write("=" * 50 + "\n\n")
        
        # Basic stats
        episodes = [r for r in results if 'error' not in r]
        f.write(f"Episodes Analyzed: {len(episodes)}\n")
        f.write(f"Agent Type: Baseline (Closest-Block-First Strategy)\n\n")
        
        if episodes:
            # Performance metrics
            rewards = [r['total_reward'] for r in episodes]
            steps = [r['total_steps'] for r in episodes]
            success_rates = [r['success'] for r in episodes]
            durations = [r.get('episode_duration', 0) for r in episodes]
            
            f.write("PERFORMANCE SUMMARY:\n")
            f.write(f"  Average Reward: {np.mean(rewards):.3f} ± {np.std(rewards):.3f}\n")
            f.write(f"  Average Steps: {np.mean(steps):.1f} ± {np.std(steps):.1f}\n")
            f.write(f"  Success Rate: {np.mean(success_rates)*100:.1f}%\n")
            f.write(f"  Average Duration: {np.mean(durations):.2f}s ± {np.std(durations):.2f}s\n\n")
            
            # Block completion analysis
            all_block_completions = defaultdict(int)
            total_blocks = defaultdict(int)
            
            for episode in episodes:
                completed = set(episode.get('completed_blocks', []))
                initial = set(episode.get('initial_blocks', []))
                
                for block_id in initial:
                    total_blocks[block_id] += 1
                    if block_id in completed:
                        all_block_completions[block_id] += 1
            
            f.write("BLOCK COMPLETION ANALYSIS:\n")
            for block_id in sorted(total_blocks.keys()):
                if total_blocks[block_id] > 0:
                    success_rate = all_block_completions[block_id] / total_blocks[block_id] * 100
                    f.write(f"  Block {block_id}: {success_rate:.1f}% success rate ({all_block_completions[block_id]}/{total_blocks[block_id]})\n")
                else:
                    f.write(f"  Block {block_id}: No attempts recorded\n")
            
            total_attempts = sum(total_blocks.values())
            if total_attempts > 0:
                f.write(f"\nOverall Block Success Rate: {sum(all_block_completions.values())/total_attempts*100:.1f}%\n\n")
            else:
                f.write(f"\nOverall Block Success Rate: No blocks attempted\n\n")
            
            # Planning activity
            planning_counts = analysis.get('learning_metrics', {}).get('planning_counts_per_episode', [])
            if planning_counts:
                avg_planning = [np.mean(list(counts.values())) for counts in planning_counts if counts]
                if avg_planning:
                    f.write("PLANNING ACTIVITY:\n")
                    f.write(f"  Average Planning Events per Agent: {np.mean(avg_planning):.2f} ± {np.std(avg_planning):.2f}\n")
                    f.write(f"  Total Planning Events per Episode: {np.mean([sum(counts.values()) for counts in planning_counts]):.2f}\n\n")
            
            # Strategy consistency
            f.write("STRATEGY ANALYSIS:\n")
            f.write("  Strategy Type: Fixed baseline strategy (closest-block-first)\n")
            f.write("  Strategy Consistency: 100% (no adaptive learning)\n")
            f.write("  Communication: None (individual planning only)\n\n")
            
            # Comparison readiness
            f.write("COMPARISON READINESS:\n")
            f.write("  ✓ Episode-level metrics collected\n")
            f.write("  ✓ Block-level completion tracking\n") 
            f.write("  ✓ Agent-level performance metrics\n")
            f.write("  ✓ Timing and efficiency data\n")
            f.write("  ✓ Visualization-ready format\n\n")
            
            f.write("This baseline data can be directly compared with learning agent results.\n")
    
    print(f"[REPORT] Baseline performance report saved to: {report_path}")

# ------------------------------
# Main Function
# ------------------------------
def main():
    parser = argparse.ArgumentParser("Baseline Agent with Statistics Collection")
    parser.add_argument("--episodes", type=int, default=5, help="Number of episodes to run")
    parser.add_argument("--n", type=int, default=2, help="Number of agents")
    parser.add_argument("--model", type=str, default="gpt-4o", help="LLM model to use")
    parser.add_argument("--max_steps", type=int, default=150, help="Maximum steps per episode")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("BASELINE AGENT EXPERIMENT WITH STATISTICS")
    print("="*60)
    print(f"Episodes: {args.episodes}")
    print(f"Agents: {args.n}")
    print(f"Model: {args.model}")
    print(f"Max Steps: {args.max_steps}")
    print(f"Seed: {args.seed}")
    print("="*60)

    # Initialize statistics manager
    stats_manager = BaselineAgentManager()
    results = []

    # Run episodes
    for ep in range(1, args.episodes + 1):
        try:
            print(f"\n{'='*20} EPISODE {ep}/{args.episodes} {'='*20}")
            result = run_baseline_episode(ep, args, stats_manager)
            results.append(result)
            print(f"Episode {ep} completed successfully")
        except Exception as e:
            print(f"Episode {ep} failed: {e}")
            results.append({'episode_num': ep, 'error': str(e)})

    # Analyze results
    print(f"\n{'='*20} ANALYSIS PHASE {'='*20}")
    analysis = analyze_baseline_performance(results)
    
    # Generate visualizations
    generate_baseline_visualizations(analysis)
    
    # Generate agent commitment heatmap
    generate_agent_commitment_heatmap(results)
    
    # Generate summary report
    generate_baseline_summary_report(analysis, results)
    
    # Save raw data for comparison
    data_path = "runs/baseline_experiment_data.json"
    ensure_dir(data_path)
    with open(data_path, 'w') as f:
        json.dump({
            'args': vars(args),
            'results': results,
            'analysis': analysis,
            'experiment_type': 'baseline',
            'timestamp': datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"\n[DATA] Raw experiment data saved to: {data_path}")
    print(f"[ANALYSIS] Baseline experiment complete!")
    print(f"[SUMMARY] Processed {len([r for r in results if 'error' not in r])}/{args.episodes} episodes successfully")

if __name__ == "__main__":
    main()

# main_llm_with_stats.py
"""
Enhanced Multi-agent LLM Framework Main Script with Stats Analysis
================================================================
Based on main_clean.py pattern but with LLM communication, planning, and comprehensive stats analysis.
"""
from __future__ import annotations
import argparse
import os
import sys
import subprocess
import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, List

# Import the actual environment class
from cube.env import CoopBlockPush
from cube.symbolic_actions import SymbolicController

# Your framework files
from communication import MessageBoard, run_communication_round
from llm_agent import LLMAgent, LLMConfig, LLMAgentManager
import llm_templates as templates
from world_model import create_world_model_from_log

# ------------------------------
# File helpers
# ------------------------------
def ensure_dirs(path: str):
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

def write_text(path: str, content: str):
    ensure_dirs(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def append_text(path: str, content: str):
    ensure_dirs(path)
    with open(path, "a", encoding="utf-8") as f:
        f.write(content)

def create_episode_folder(episode_num: int = None) -> str:
    """Create a unique folder for this episode run."""
    if episode_num is not None:
        episode_folder = f"runs/episode_{episode_num:02d}"
    else:
        episode_folder = f"runs/episode"
    os.makedirs(episode_folder, exist_ok=True)
    print(f"Created episode folder: {episode_folder}")
    return episode_folder

def generate_episode_outputs(episode_folder: str, log_file: str):
    """Generate all episode outputs in the episode folder."""
    print(f"\nGenerating episode outputs in {episode_folder}...")
    
    # Note: trace.json is already saved directly to the episode folder
    trace_file = log_file  # log_file is already the trace.json path
    
    # 1. Generate world model graph and visualization
    try:
        print(f"[DEBUG] Starting world model generation in {episode_folder}...")
        
        # Save current working directory and change to episode folder
        original_cwd = os.getcwd()
        os.chdir(episode_folder)
        print(f"[DEBUG] Changed to episode directory: {episode_folder}")
        
        try:
            # Create world model from the trace file (which is in the episode folder)
            trace_file_path = "trace.json"
            print(f"[DEBUG] Looking for trace.json file...")
            
            if not os.path.exists(trace_file_path):
                print(f"[ERROR] {trace_file_path} not found in {episode_folder} - cannot generate world model")
                raise FileNotFoundError(f"{trace_file_path} not found")
            
            print(f"[DEBUG] Creating world model from {trace_file_path}...")
            world_model = create_world_model_from_log(
                log_file=trace_file_path, 
                show_text=False,  # Don't print to console
                show_graph=False,  # Don't show plot window
                save_graph=True,
                save_format='json'
            )
            print(f"[DEBUG] World model created successfully")
            
            # Generate and save the PNG visualization
            try:
                print(f"[DEBUG] Generating world model PNG visualization...")
                world_model.visualize(save_path='world_model_graph.png', show_plot=False)
                print(f"[DEBUG] Generated world model graph PNG")
            except Exception as e:
                print(f"[ERROR] World model PNG generation failed: {e}")
            
            # Generate and save the text concept graph
            try:
                print(f"[DEBUG] Generating concept graph text...")
                import sys
                import io
                
                # Capture the text output
                old_stdout = sys.stdout
                sys.stdout = buffer = io.StringIO()
                
                # Generate text concept graph
                world_model.visualize_text_concept_graph()
                
                # Restore stdout and get captured text
                sys.stdout = old_stdout
                concept_text = buffer.getvalue()
                
                # Save to file
                with open('world_model_concept_graph.txt', 'w', encoding='utf-8') as f:
                    f.write(concept_text)
                print(f"[DEBUG] Generated world model concept graph text")
                
            except Exception as e:
                print(f"[ERROR] World model concept graph text generation failed: {e}")
            
            print(f"[DEBUG] Generated world model files in {episode_folder}")
            
        finally:
            # Restore original working directory
            os.chdir(original_cwd)
            print(f"[DEBUG] Restored working directory to: {original_cwd}")
        
    except Exception as e:
        print(f"[ERROR] World model generation failed: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. Generate log visualization
    try:
        print(f"[DEBUG] Generating log visualization...")
        viz_output = os.path.join(episode_folder, "log_visualization.png")
        
        # Run log visualizer with absolute paths
        abs_trace_file = os.path.abspath(trace_file)
        abs_viz_output = os.path.abspath(viz_output)
        
        print(f"[DEBUG] Running log visualizer: {abs_trace_file} -> {abs_viz_output}")
        
        result = subprocess.run([
            "python", "log_visualizer.py", 
            abs_trace_file,
            "-o", abs_viz_output
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            print(f"[DEBUG] Generated log visualization: {viz_output}")
        else:
            print(f"[ERROR] Log visualization failed: {result.stderr}")
            print(f"[DEBUG] Log visualizer stdout: {result.stdout}")
            
    except Exception as e:
        print(f"[ERROR] Log visualization failed: {e}")
    
    print(f"Episode outputs completed in {episode_folder}")
    
    # Validate that key episode files were created
    expected_files = ["trace.json", "world_model_graph.json", "world_model_graph.png", "log_visualization.png"]
    created_files = []
    missing_files = []
    
    for f in expected_files:
        file_path = os.path.join(episode_folder, f)
        if os.path.exists(file_path):
            created_files.append(f)
        else:
            missing_files.append(f)
    
    print(f"[DEBUG] Episode file validation:")
    print(f"[DEBUG] - Created files: {created_files}")
    if missing_files:
        print(f"[WARN] - Missing files: {missing_files}")
        # List all files in episode directory for debugging
        all_files = os.listdir(episode_folder)
        print(f"[DEBUG] - All files in directory: {all_files}")
    else:
        print(f"[DEBUG] - All expected files created successfully")
    
    return episode_folder

# ------------------------------
# Agent and Planning
# ------------------------------
def build_agents(env, agent_manager: LLMAgentManager, n_agents: int, model: str) -> Dict[str, LLMAgent]:
    cfg = LLMConfig(model=model)
    agents: Dict[str, LLMAgent] = {}
    for i in range(n_agents):
        aid = f"agent_{i}"
        agent = LLMAgent(aid, env, agent_manager, cfg, plan=[])  # agent_manager is world_model
        agents[aid] = agent
        agent_manager.add_agent(agent)  # Add to manager
    return agents

def run_communication_and_planning(agents: Dict[str, LLMAgent], agent_manager: LLMAgentManager, step: int, extra_file: str, comm_type: str = "initial"):
    """Run communication and planning phase - returns participants that should replan"""
    print(f"\n=== COMMUNICATION & PLANNING ({comm_type.upper()}) ===")
    
    # Determine who should participate in communication
    participants = []
    for agent in agents.values():
        if agent.should_plan():
            participants.append(agent.id)
    
    if not participants:
        print("No agents need to communicate/plan")
        return []
    
    print(f"Participants: {participants}")
    
    # Run communication round
    board = run_communication_round({aid: agents[aid] for aid in participants})
    
    # Extract assignments from communication
    assignments = {}
    for commitment in board.commitments:
        assignments[commitment.agent_id] = commitment.block_id
    
    # Log communication
    agent_manager.log_communication_round(
        step=step,
        participants=participants,
        communication_type=comm_type,
        result=assignments
    )
    
    # Set assignments and run planning
    agents_with_plans = []
    for agent_id in participants:
        agent = agents[agent_id]
        if agent_id in assignments:
            block_id = assignments[agent_id]
            agent.assigned_block = block_id
            agent.task_name = f"Block_{block_id}"
            print(f"[MAIN] Fed assignment to {agent_id}: Block {block_id} -> {agent.task_name}")
        
        # Run LLM planning
        print(f"\n[PLANNING] {agent_id} planning for task: {agent.task_name}")
        agent.plan(all_agents=agents)
        agents_with_plans.append(agent_id)
        print(f"[PLAN] {agent_id}: {len(agent.plan_steps)} actions - {'; '.join(agent.plan_steps[:3])}{'...' if len(agent.plan_steps) > 3 else ''}")
    
    # Log planning completion once for all agents
    agent_manager.log_planning_completed(step, agents_with_plans)
    
    return participants

def check_need_replanning(env, agents: Dict[str, LLMAgent]) -> bool:
    """Check if we need replanning - blocks remain but all agents finished"""
    blocks_remain = len(env._blocks) > 0
    all_finished = all(agent.is_finished() for agent in agents.values())
    return blocks_remain and all_finished

# ------------------------------
# Stats Analysis Functions (from main_learning.py)
# ------------------------------

def analyze_multi_episode_results(episodes: List[Dict]) -> Dict:
    """
    Comprehensive analysis of multi-episode learning results
    """
    print("\n" + "="*60)
    print("ANALYZING MULTI-EPISODE LEARNING RESULTS")
    print("="*60)
    
    if not episodes:
        print("No episodes to analyze")
        return {}
    
    analysis = {}
    
    # Extract metrics
    episode_nums = [r['episode_num'] for r in episodes if 'error' not in r]
    rewards = [r['total_reward'] for r in episodes if 'error' not in r]
    steps = [r['total_steps'] for r in episodes if 'error' not in r]
    comm_rounds = [r['communication_rounds'] for r in episodes if 'error' not in r]
    success_flags = [r.get('success', False) for r in episodes if 'error' not in r]
    
    if not episode_nums:
        print("No successful episodes to analyze")
        return analysis
    
    print(f"Analyzing {len(episode_nums)} episodes:")
    for i, (ep, rew, stp, comm, succ) in enumerate(zip(episode_nums, rewards, steps, comm_rounds, success_flags)):
        print(f"  Episode {ep}: Reward={rew:.2f}, Steps={stp}, Comm={comm}, Success={succ}")
    
    # 1. Learning Metrics Over Time
    analysis['learning_metrics'] = {
        'reward_trend': rewards,
        'step_efficiency_trend': steps,
        'communication_efficiency_trend': comm_rounds,
        'success_rate_trend': success_flags,
        'episodes': episode_nums,
        'avg_reward': np.mean(rewards),
        'reward_improvement': rewards[-1] - rewards[0] if len(rewards) > 1 else 0,
        'avg_steps': np.mean(steps),
        'step_improvement': steps[0] - steps[-1] if len(steps) > 1 else 0,  # Lower steps = improvement
        'avg_comm_rounds': np.mean(comm_rounds),
        'overall_success_rate': np.mean(success_flags)
    }
    
    print(f"Learning metrics calculated: avg_reward={analysis['learning_metrics']['avg_reward']:.3f}")
    
    # Collect all block completion data for analysis
    all_block_ids = set()
    for result in episodes:
        if 'error' not in result:
            block_times = result.get('block_completion_times', {})
            all_block_ids.update(block_times.keys())
    
    print(f"[DEBUG] All block IDs found: {sorted(all_block_ids)}")
    
    # Direct block completion time tracking
    direct_block_completion_times = defaultdict(list)
    
    # Process each episode result directly for completion times
    for result in episodes:
        if 'error' not in result:
            block_times = result.get('block_completion_times', {})
            
            # For each block that appears in this episode, record its completion time
            for block_id, completion_time in block_times.items():
                direct_block_completion_times[block_id].append(completion_time)
            
            # For blocks that didn't appear or weren't completed, record as 0
            for block_id in all_block_ids:
                if block_id not in block_times:
                    direct_block_completion_times[block_id].append(0)
    
    print(f"[DEBUG] Direct block completion times: {dict(direct_block_completion_times)}")
    
    # 2. Block Success Analysis
    analysis['learning_metrics']['block_completion_trends'] = [r.get('block_completion_times', {}) for r in episodes if 'error' not in r]
    
    # Build block success evolution from current episode results
    current_block_success_rates = defaultdict(list)
    for result in episodes:
        if 'error' not in result:
            block_times = result.get('block_completion_times', {})
            completed_blocks = set(block_times.keys())
            
            # For each block that appeared in any episode, track if it was completed (binary)
            for block_id in all_block_ids:
                success_rate = 1.0 if block_id in completed_blocks else 0.0
                current_block_success_rates[f"Block_{block_id}"].append(success_rate)
    
    print(f"[DEBUG] Current block success rates: {dict(current_block_success_rates)}")
    
    # 3. Communication Efficiency Analysis
    analysis['communication_efficiency'] = {
        'avg_comm_rounds_early': np.mean(comm_rounds[:len(comm_rounds)//2]) if comm_rounds else 0,
        'avg_comm_rounds_late': np.mean(comm_rounds[len(comm_rounds)//2:]) if comm_rounds else 0,
        'communication_improvement': (np.mean(comm_rounds[:len(comm_rounds)//2]) - np.mean(comm_rounds[len(comm_rounds)//2:])) if len(comm_rounds) > 2 else 0
    }
    
    # 4. Strategy Evolution Analysis
    analysis['strategy_evolution'] = {
        'strategy_diversity_per_task': {},
        'strategies_tried': {},
        'block_success_evolution': dict(current_block_success_rates),
        'completion_time_trends': dict(direct_block_completion_times)
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
    
    # 1. Reward and Success Trends Over Episodes
    ax1 = axes[0, 0]
    rewards = learning_metrics.get('reward_trend', [])
    success_flags = learning_metrics.get('success_rate_trend', [])
    episodes = learning_metrics.get('episodes', [])
    
    if rewards and episodes:
        # Plot rewards as line
        ax1_twin = ax1.twinx()
        
        line1 = ax1.plot(episodes, rewards, 'bo-', linewidth=2, markersize=6, label='Total Reward')
        bars = ax1_twin.bar(episodes, success_flags, alpha=0.3, color='green', label='Episode Success')
        
        ax1.set_title('Reward and Success Trends', fontweight='bold')
        ax1.set_xlabel('Episode Number')
        ax1.set_ylabel('Total Reward', color='blue')
        ax1.tick_params(axis='y', labelcolor='blue')
        ax1_twin.set_ylabel('Episode Success (1=Success, 0=Failure)', color='green')
        ax1_twin.tick_params(axis='y', labelcolor='green')
        ax1.grid(True, alpha=0.3)
        
        # Combined legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax1_twin.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    else:
        ax1.text(0.5, 0.5, 'No reward/success data available', ha='center', va='center', transform=ax1.transAxes)
        ax1.set_title('Reward and Success Trends', fontweight='bold')
    
    # 2. Block Completion Timing Across Episodes
    ax2 = axes[0, 1]
    block_completions = learning_metrics.get('block_completion_trends', [])
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
        
        episodes_plot = list(range(1, len(episode_completion_times) + 1))
        
        # Dual axis: completion time and number of blocks
        ax2_twin = ax2.twinx()
        
        line1 = ax2.plot(episodes_plot, episode_completion_times, 'bo-', linewidth=2, markersize=6, label='Avg Completion Time')
        bars = ax2_twin.bar(episodes_plot, episode_block_counts, alpha=0.3, color='orange', label='Blocks Completed')
        
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
    
    # 3. Step Efficiency and Communication Trends
    ax3 = axes[0, 2]
    steps = learning_metrics.get('step_efficiency_trend', [])
    comm_rounds = learning_metrics.get('communication_efficiency_trend', [])
    
    if steps and comm_rounds and episodes:
        ax3_twin = ax3.twinx()
        
        line1 = ax3.plot(episodes, steps, 'ro-', linewidth=2, markersize=6, label='Steps per Episode')
        line2 = ax3_twin.plot(episodes, comm_rounds, 'go-', linewidth=2, markersize=6, label='Communication Rounds')
        
        ax3.set_title('Efficiency Trends', fontweight='bold')
        ax3.set_xlabel('Episode Number')
        ax3.set_ylabel('Steps per Episode', color='red')
        ax3.tick_params(axis='y', labelcolor='red')
        ax3_twin.set_ylabel('Communication Rounds', color='green')
        ax3_twin.tick_params(axis='y', labelcolor='green')
        ax3.grid(True, alpha=0.3)
        
        # Combined legend
        lines1, labels1 = ax3.get_legend_handles_labels()
        lines2, labels2 = ax3_twin.get_legend_handles_labels()
        ax3.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    else:
        ax3.text(0.5, 0.5, 'No efficiency data available', ha='center', va='center', transform=ax3.transAxes)
        ax3.set_title('Efficiency Trends', fontweight='bold')
    
    # 4. Block Success Rate Heatmap Over Time (Binary: Success/Failure per Episode)
    ax4 = axes[1, 0]
    block_success_evolution = analysis.get('strategy_evolution', {}).get('block_success_evolution', {})
    if block_success_evolution:
        # Prepare data for heatmap - show ALL historical episodes
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
        
        # Label ALL episodes in sequence
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
    
    # 6. Coordination Score Evolution
    ax6 = axes[1, 2]
    coordination_scores = analysis.get('coordination_improvement', {}).get('coordination_scores', [])
    
    if coordination_scores and episodes:
        ax6.plot(episodes, coordination_scores, 'mo-', linewidth=2, markersize=6, label='Coordination Score')
        ax6.set_title('Coordination Score Evolution', fontweight='bold')
        ax6.set_xlabel('Episode Number')
        ax6.set_ylabel('Coordination Score')
        ax6.grid(True, alpha=0.3)
        ax6.legend()
        
        # Add value labels
        for ep, score in zip(episodes, coordination_scores):
            ax6.text(ep, score + max(coordination_scores) * 0.02, f'{score:.3f}', 
                    ha='center', va='bottom', fontsize=8)
    else:
        ax6.text(0.5, 0.5, 'No coordination data available', ha='center', va='center', transform=ax6.transAxes)
        ax6.set_title('Coordination Score Evolution', fontweight='bold')
    
    plt.tight_layout()
    
    # Save the plot
    plot_path = os.path.join(output_dir, 'llm_learning_progress_analysis.png')
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"Learning progress visualization saved to: {plot_path}")
    
    # Create a summary text report
    report_path = os.path.join(output_dir, 'llm_learning_analysis_report.txt')
    with open(report_path, 'w') as f:
        f.write("LLM AGENT LEARNING PROGRESS ANALYSIS REPORT\n")
        f.write("="*50 + "\n\n")
        
        # Basic metrics
        f.write("1. BASIC LEARNING METRICS:\n")
        metrics = analysis.get('learning_metrics', {})
        f.write(f"   - Average reward: {metrics.get('avg_reward', 0):.3f}\n")
        f.write(f"   - Reward improvement: {metrics.get('reward_improvement', 0):.3f}\n")
        f.write(f"   - Average steps: {metrics.get('avg_steps', 0):.1f}\n")
        f.write(f"   - Step improvement: {metrics.get('step_improvement', 0):.1f}\n")
        f.write(f"   - Average communication rounds: {metrics.get('avg_comm_rounds', 0):.1f}\n")
        f.write(f"   - Overall success rate: {metrics.get('overall_success_rate', 0):.1%}\n")
        f.write("\n")
        
        # Block success rate evolution
        f.write("2. BLOCK SUCCESS RATE EVOLUTION:\n")
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
        
        # Communication efficiency
        f.write("3. COMMUNICATION EFFICIENCY:\n")
        comm_efficiency = analysis.get('communication_efficiency', {})
        f.write(f"   - Early episodes avg comm rounds: {comm_efficiency.get('avg_comm_rounds_early', 0):.1f}\n")
        f.write(f"   - Late episodes avg comm rounds: {comm_efficiency.get('avg_comm_rounds_late', 0):.1f}\n")
        f.write(f"   - Communication improvement: {comm_efficiency.get('communication_improvement', 0):.1f}\n")
        f.write("\n")
        
        # Coordination improvement
        f.write("4. COORDINATION IMPROVEMENT:\n")
        coordination = analysis.get('coordination_improvement', {})
        f.write(f"   - Coordination trend: {coordination.get('coordination_trend', 'unknown')}\n")
        f.write(f"   - Best coordination episode: {coordination.get('best_coordination_episode', 0)}\n")
    
    print(f"Learning analysis report saved to: {report_path}")
    
    return plot_path, report_path

# ------------------------------
# Single Episode Execution
# ------------------------------
def run_single_episode(episode_num: int, args) -> Dict:
    """Run a single episode and return the results."""
    print(f"\n{'='*50}")
    print(f"STARTING EPISODE {episode_num}")
    print(f"{'='*50}")
    
    # Create episode folder for this run
    episode_folder = create_episode_folder(episode_num)
    
    # Update paths to use episode folder
    episode_extra_file = os.path.join(episode_folder, "shared_extra_info.md")
    episode_log_file = os.path.join(episode_folder, "trace.json")

    # Set deterministic seed for each episode to ensure identical settings
    # Use a fixed seed so all episodes have exactly the same initial conditions
    import random
    import numpy as np
    
    # Set fixed seed for reproducibility across all episodes
    seed = args.seed  # Use seed from command line arguments
    random.seed(seed)
    np.random.seed(seed)
    
    # Track timing for block completion analysis
    episode_start_time = time.time()
    block_completion_times = {}  # block_id -> completion_time
    
    # Create environment with more blocks for longer tasks
    env = CoopBlockPush(
        n=args.n,
        max_steps=args.max_steps,
        render_mode='human'
    )

    # Initialize environment with fixed seed
    obs = env.reset(seed=seed)
    print(f"Environment initialized with {len(env._blocks)} blocks (using fixed seed {seed})")

    # Create agent manager and agents
    agent_manager = LLMAgentManager(env)
    agents = build_agents(env, agent_manager, args.n, args.model)

    # Initial communication and planning
    run_communication_and_planning(agents, agent_manager, step=0, extra_file=episode_extra_file, comm_type="initial")
    
    # Convert plans to objects for controller
    agent_plans_objects = agent_manager.convert_all_agent_plans_to_objects()
    print(f"[DEBUG] Agent plans objects: {agent_plans_objects}")
    controller = SymbolicController(env, agent_plans_objects)
    
    # Main execution loop
    total_reward = 0
    step = 0
    max_iterations = 10  # Allow more replanning iterations
    iteration = 1
    
    while step < args.max_steps and iteration <= max_iterations:
        print(f"\n=== ITERATION {iteration} ===")
        print(f"\n=== EXECUTION PHASE ===")
        
        # Execute until all agents finish or max steps reached
        execution_start_step = step
        while step < args.max_steps:
            # Check for individual agent replanning needs during execution
            if len(env._blocks) > 0:  # Only if blocks remain
                agents_needing_replan = [agent_id for agent_id, agent in agents.items() if agent.is_finished()]
                if agents_needing_replan:
                    print(f"\n=== INDIVIDUAL REPLANNING NEEDED ===")
                    print(f"Agents needing replan: {agents_needing_replan}")
                    
                    # Reset only the agents that need replanning
                    for agent_id in agents_needing_replan:
                        agent = agents[agent_id]
                        agent.plan_steps = []
                        agent.plan_index = 0
                        agent.phase = "planning"
                        # Reset plan completion logging flag for new plan
                        if hasattr(agent, '_plan_completion_logged'):
                            delattr(agent, '_plan_completion_logged')
                        print(f"[REPLAN] Reset {agent_id} for individual replanning")
                    
                    # Run communication and planning for agents that need it
                    participants = run_communication_and_planning(
                        agents, agent_manager, step, episode_extra_file, comm_type=f"individual_replan_step_{step}"
                    )
                    
                    if participants:
                        # Update controller with new plans for the replanned agents
                        agent_plans_objects = agent_manager.convert_all_agent_plans_to_objects()
                        # Only update plans for agents that participated in replanning
                        for agent_id in participants:
                            if agent_id in agent_plans_objects:
                                controller.plans[agent_id] = agent_plans_objects[agent_id]
                                controller.idx[agent_id] = 0
                                controller.rem[agent_id] = 0
                        print(f"[REPLAN] Updated controller with new plans for: {participants}")
            
            # Get actions from controller
            actions = controller.act()
            print(f"[DEBUG] Controller actions: {actions}")
            print(f"[DEBUG] Controller plans: {list(controller.plans.keys())}")
            print(f"[DEBUG] Controller indices: {controller.idx}")
            print(f"[DEBUG] Controller rem: {controller.rem}")
            
            # Debug the first agent's action execution
            if controller.plans and 'agent_0' in controller.plans:
                agent_id = 'agent_0'
                if controller.idx[agent_id] < len(controller.plans[agent_id]):
                    current_action = controller.plans[agent_id][controller.idx[agent_id]]
                    print(f"[DEBUG] {agent_id} executing: {current_action}")
                    pos = controller.env._agent_positions[agent_id]
                    print(f"[DEBUG] {agent_id} position: {pos}")
            
            # Log timestep with actions for current step (before env step)
            agent_manager.log_timestep(step, actions)
            
            # Update agent progress based on controller
            for agent_id, agent in agents.items():
                if agent_id in controller.idx:
                    controller_progress = controller.idx[agent_id]
                    if controller_progress > agent.plan_index:
                        agent.plan_index = controller_progress
            
            # Check for block completion timing
            blocks_before = set(block.id for block in env._blocks)
            
            # Step environment
            observations, rewards, dones, truncated, infos = env.step(actions)
            
            # Check for newly completed blocks
            blocks_after = set(block.id for block in env._blocks)
            completed_blocks_this_step = blocks_before - blocks_after
            
            for block_id in completed_blocks_this_step:
                if block_id not in block_completion_times:
                    completion_time = time.time() - episode_start_time
                    block_completion_times[block_id] = completion_time
                    print(f"[TIMING] Block {block_id} completed at {completion_time:.2f}s into episode")
            
            # Check for individual agents that just finished their plans and log completion
            for agent_id, agent in agents.items():
                # Check if agent just finished (plan_index >= plan_steps length)
                if (agent.plan_steps and 
                    agent.plan_index >= len(agent.plan_steps) and 
                    not hasattr(agent, '_plan_completion_logged')):
                    
                    # Mark as logged to avoid duplicate logging
                    agent._plan_completion_logged = True
                    
                    # Evaluate plan success for this individual agent
                    target_block = agent.assigned_block if hasattr(agent, 'assigned_block') else None
                    committed_task = agent.committed_task if hasattr(agent, 'committed_task') else None
                    
                    # Check if the target block is still available in the environment
                    block_still_available = False
                    if target_block is not None:
                        block_still_available = any(block.id == target_block for block in env._blocks)
                    
                    # Determine if plan was actually successful
                    plan_successful = False
                    if target_block is not None:
                        # Success = target block is no longer in the environment (was delivered)
                        plan_successful = not block_still_available
                    else:
                        # If no specific target, consider finished plan as successful
                        plan_successful = True
                    
                    # Log individual plan completion
                    individual_plan_result = {
                        agent_id: {
                            'plan_successful': plan_successful,
                            'target_block': target_block,
                            'block_still_available': block_still_available,
                            'committed_task': committed_task
                        }
                    }
                    
                    agent_manager.log_plan_execution_completed(step, individual_plan_result)
                    print(f"[PLAN] {agent_id} plan completed at step {step}: {'SUCCESS' if plan_successful else 'FAILED'} (target_block={target_block}, still_available={block_still_available})")
            
            # Render environment to show visual
            env.render()
            
            step += 1
            
            # Accumulate rewards
            step_reward = sum(rewards.values())
            total_reward += step_reward
            
            # Print progress every 25 steps (more frequent for longer runs)
            if step % 25 == 0 or step - execution_start_step < 10:
                active_agents = sum(1 for agent in agents.values() if not agent.is_finished())
                agent_status = []
                for agent_id, agent in agents.items():
                    # Get position from environment
                    if hasattr(env, '_agent_positions') and agent_id in env._agent_positions:
                        pos = env._agent_positions[agent_id]
                    else:
                        pos = 'unknown'
                    agent_status.append(f"{agent_id}: {agent.plan_index}/{len(agent.plan_steps)} at {pos}")
                print(f"[EXEC] Step {step}: {active_agents} agents active, Reward: {total_reward:.3f}")
                for status in agent_status:
                    print(f"  {status}")
            
            # Check if all agents finished their plans AND no blocks remain
            # (If blocks remain, individual agents will replan during execution)
            if all(agent.is_finished() for agent in agents.values()):
                if len(env._blocks) == 0:
                    print(f"[EXEC] All agents completed plans and all blocks delivered in {step - execution_start_step} steps")
                else:
                    print(f"[EXEC] All agents completed current plans in {step - execution_start_step} steps (blocks remain, will continue with replanning)")
                
                # Log plan execution completion with status and block availability
                agents_plan_results = {}
                for agent_id, agent in agents.items():
                    target_block = agent.assigned_block if hasattr(agent, 'assigned_block') else None
                    committed_task = agent.committed_task if hasattr(agent, 'committed_task') else None
                    
                    # Check if the target block is still available in the environment
                    block_still_available = False
                    if target_block is not None:
                        block_still_available = any(block.id == target_block for block in env._blocks)
                    
                    # Determine if plan was actually successful
                    # Plan is successful if agent finished AND their target block was delivered (no longer available)
                    plan_successful = False
                    if agent.is_finished():
                        if target_block is not None:
                            # Success = target block is no longer in the environment (was delivered)
                            plan_successful = not block_still_available
                        else:
                            # If no specific target, consider finished plan as successful
                            plan_successful = True
                    
                    agents_plan_results[agent_id] = {
                        'plan_successful': plan_successful,
                        'target_block': target_block,
                        'block_still_available': block_still_available,
                        'committed_task': committed_task
                    }
                
                # Log the plan execution completion
                agent_manager.log_plan_execution_completed(step, agents_plan_results)
                
                # Only break if no blocks remain - otherwise continue for individual replanning
                if len(env._blocks) == 0:
                    print(f"[DEBUG] Early termination - ensuring data collection is complete")
                    print(f"[DEBUG] - Current step: {step}")
                    print(f"[DEBUG] - Total reward so far: {total_reward}")
                    print(f"[DEBUG] - Block completion times: {block_completion_times}")
                    break
            
            # Check if environment is done
            if all(dones.values()) or all(truncated.values()):
                print(f"[EXEC] Environment terminated at step {step}")
                break
        
        # Final check for any remaining replanning needs (fallback)
        # Most replanning should now happen during execution via individual agent checks
        if check_need_replanning(env, agents):
            print(f"Final check: All agents finished but {len(env._blocks)} blocks remain - forcing final replan")
            iteration += 1
            
            if iteration <= max_iterations:
                print(f"\n=== FINAL REPLANNING ROUND {iteration-1} ===")
                
                # Reset agent states for replanning
                for agent in agents.values():
                    agent.plan_steps = []
                    agent.plan_index = 0
                    agent.phase = "planning"
                    # Reset plan completion logging flag for new plan
                    if hasattr(agent, '_plan_completion_logged'):
                        delattr(agent, '_plan_completion_logged')
                
                # Run communication and planning again
                participants = run_communication_and_planning(
                    agents, agent_manager, step, episode_extra_file, comm_type=f"final_replan_{iteration-1}"
                )
                
                if participants:
                    # Update controller with new plans
                    agent_plans_objects = agent_manager.convert_all_agent_plans_to_objects()
                    controller.plans = agent_plans_objects
                    controller.idx = {agent_id: 0 for agent_id in env.agents}
                    controller.rem = {agent_id: 0 for agent_id in env.agents}
                else:
                    print("No agents available for final replanning")
                    break
            else:
                print(f"Reached maximum iterations ({max_iterations})")
                break
        else:
            # No replanning needed - either no blocks left or agents are still working
            if len(env._blocks) == 0:
                print(f"All blocks delivered successfully!")
            break
    
    if iteration >= max_iterations:
        print(f"Reached maximum iterations ({max_iterations})")

    print(f"\n[INFO] Shared extra-info file: {os.path.abspath(episode_extra_file)}")
    
    # Save complete execution log with communication events
    print("\n[INFO] Saving complete execution log...")
    try:
        agent_manager.save_complete_log(episode_log_file)
        print(f"Complete execution log saved to: {os.path.abspath(episode_log_file)}")
        
        # Print summary
        comm_log = agent_manager.get_communication_log()
        total_steps = len([entry for entry in agent_manager.activity_log if entry.get("event_type") == "timestep"])
        
        print(f"[DEBUG] Episode {episode_num} final data collection:")
        print(f"[DEBUG] - Total steps recorded: {total_steps}")
        print(f"[DEBUG] - Communication rounds: {len(comm_log)}")
        print(f"[DEBUG] - Final reward: {total_reward:.3f}")
        print(f"[DEBUG] - Block completion times: {block_completion_times}")
        print(f"[DEBUG] - Blocks remaining: {len(env._blocks)}")
        
        print(f"Execution Summary:")
        print(f"   - Total execution steps: {total_steps}")
        print(f"   - Total communication rounds: {len(comm_log)}")
        for comm in comm_log:
            print(f"   - {comm['communication_type']} at step {comm['t']}: {comm['participant_count']} agents")
        print(f"   - Final reward: {total_reward:.3f}")
        
        # Generate all episode outputs
        final_episode_folder = generate_episode_outputs(episode_folder, episode_log_file)
        print(f"\nEpisode {episode_num} completed! All outputs saved to: {os.path.abspath(final_episode_folder)}")
        
        # Return episode results
        episode_results = {
            'episode_num': episode_num,
            'total_steps': total_steps,
            'total_reward': total_reward,
            'communication_rounds': len(comm_log),
            'blocks_remaining': len(env._blocks),
            'episode_folder': final_episode_folder,
            'success': len(env._blocks) == 0,  # Success if all blocks delivered
            'block_completion_times': block_completion_times,
            'completed_blocks': list(block_completion_times.keys()),
        }
        
        print(f"[DEBUG] Episode {episode_num} data validation:")
        print(f"[DEBUG] - Required fields present: {all(key in episode_results for key in ['episode_num', 'total_steps', 'total_reward', 'success'])}")
        print(f"[DEBUG] - Block data consistent: completed_blocks={len(episode_results['completed_blocks'])}, block_completion_times={len(episode_results['block_completion_times'])}")
        
        return episode_results
        
    except Exception as e:
        print(f"Episode {episode_num} log saving failed: {e}")
        return {
            'episode_num': episode_num,
            'total_steps': step,
            'total_reward': total_reward,
            'communication_rounds': 0,
            'blocks_remaining': len(env._blocks),
            'episode_folder': episode_folder,
            'success': False,
            'error': str(e),
            'block_completion_times': block_completion_times,
            'completed_blocks': list(block_completion_times.keys()),
        }

# ------------------------------
# Main Execution (Multiple Episodes)
# ------------------------------
def main():
    p = argparse.ArgumentParser("Multi-Episode LLM Framework with Stats Analysis")
    p.add_argument("--n", type=int, default=2)
    p.add_argument("--model", type=str, default="gpt-4o")
    p.add_argument("--extra_file", type=str, default="runs/shared_extra_info.md")
    p.add_argument("--max_steps", type=int, default=50)
    p.add_argument("--num_episodes", type=int, default=5, help="Number of episodes to run")
    p.add_argument("--seed", type=int, default=42, help="Fixed seed for identical episode settings")
    args = p.parse_args()

    print(f"Starting {args.num_episodes} episodes with {args.max_steps} steps each")
    print(f"Using model: {args.model}, Agents: {args.n}, Seed: {args.seed}")
    print(f"All episodes will have identical initial conditions")
    
    # Store results for all episodes
    all_episode_results = []
    
    # Run multiple episodes
    for episode_num in range(1, args.num_episodes + 1):
        try:
            episode_results = run_single_episode(episode_num, args)
            
            # Validate critical fields are present
            required_fields = ['episode_num', 'total_steps', 'total_reward', 'success', 'block_completion_times']
            missing_fields = [field for field in required_fields if field not in episode_results]
            if missing_fields:
                print(f"[WARNING] Episode {episode_num} missing required fields: {missing_fields}")
            else:
                print(f"[DEBUG] Episode {episode_num} data validation passed")
            
            all_episode_results.append(episode_results)
            
            print(f"\nEpisode {episode_num} Summary:")
            print(f"  - Steps: {episode_results['total_steps']}")
            print(f"  - Reward: {episode_results['total_reward']:.3f}")
            print(f"  - Communication rounds: {episode_results['communication_rounds']}")
            print(f"  - Success: {'Yes' if episode_results['success'] else 'No'}")
            print(f"  - Blocks remaining: {episode_results['blocks_remaining']}")
            print(f"  - Blocks completed: {len(episode_results.get('completed_blocks', []))}")
            
        except Exception as e:
            print(f"Episode {episode_num} failed with error: {e}")
            import traceback
            traceback.print_exc()
            # Add episode with basic error info but preserve episode structure for analysis
            error_episode = {
                'episode_num': episode_num,
                'error': str(e),
                'success': False,
                'total_steps': 0,
                'total_reward': 0.0,
                'communication_rounds': 0,
                'blocks_remaining': 0,
                'block_completion_times': {},
                'completed_blocks': []
            }
            all_episode_results.append(error_episode)
    
    # Perform comprehensive stats analysis
    print(f"\n{'='*60}")
    print(f"COMPREHENSIVE STATS ANALYSIS")
    print(f"{'='*60}")
    
    # Always try to run analysis if we have any episodes (even failed ones)
    try:
        print(f"Analyzing {len(all_episode_results)} episodes...")
        # Filter out episodes that have no meaningful data for debug info
        valid_results = [r for r in all_episode_results if 'total_reward' in r]
        print(f"Episodes with valid data: {len(valid_results)}")
        
        analysis = analyze_multi_episode_results(all_episode_results)
        
        # Generate visualizations even if some episodes failed
        if analysis:
            plot_path, report_path = generate_learning_visualizations(analysis, output_dir="runs")
            print(f"\nStats analysis completed:")
            print(f"  - Visualization: {plot_path}")
            print(f"  - Report: {report_path}")
        else:
            print("No analysis data available - all episodes may have failed")
            
    except Exception as e:
        print(f"\n⚠️ Stats analysis failed: {e}")
        import traceback
        traceback.print_exc()
        print("Continuing with basic summary...")
    
    # Print overall summary
    print(f"\n{'='*60}")
    print(f"OVERALL SUMMARY ({args.num_episodes} EPISODES)")
    print(f"{'='*60}")
    
    successful_episodes = [r for r in all_episode_results if r.get('success', False)]
    total_successful = len(successful_episodes)
    
    if successful_episodes:
        avg_steps = sum(r['total_steps'] for r in successful_episodes) / len(successful_episodes)
        avg_reward = sum(r['total_reward'] for r in successful_episodes) / len(successful_episodes)
        avg_comm_rounds = sum(r['communication_rounds'] for r in successful_episodes) / len(successful_episodes)
        
        print(f"Success rate: {total_successful}/{args.num_episodes} ({100*total_successful/args.num_episodes:.1f}%)")
        print(f"Average steps (successful): {avg_steps:.1f}")
        print(f"Average reward (successful): {avg_reward:.3f}")
        print(f"Average communication rounds (successful): {avg_comm_rounds:.1f}")
    else:
        print(f"Success rate: 0/{args.num_episodes} (0.0%)")
        print("No successful episodes to analyze")
    
    # Save overall summary with enhanced stats
    summary_file = f"runs/llm_multi_episode_summary.json"
    ensure_dirs(summary_file)
    
    summary_data = {
        'args': vars(args),
        'episodes': all_episode_results,
        'analysis': analysis,
        'summary': {
            'total_episodes': args.num_episodes,
            'successful_episodes': total_successful,
            'success_rate': total_successful / args.num_episodes if args.num_episodes > 0 else 0,
            'avg_steps': avg_steps if successful_episodes else None,
            'avg_reward': avg_reward if successful_episodes else None,
            'avg_comm_rounds': avg_comm_rounds if successful_episodes else None
        }
    }
    
    try:
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2)
        print(f"\nOverall summary saved to: {os.path.abspath(summary_file)}")
    except Exception as e:
        print(f"Failed to save summary: {e}")
    
    print(f"\nAll {args.num_episodes} episodes completed with comprehensive stats analysis!")

if __name__ == "__main__":
    main()

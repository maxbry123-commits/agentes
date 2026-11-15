#!/usr/bin/env python3
"""
Enhanced Multi-agent LLM Framework with Continuoudef create_episode_folder(episode_num: int = None) -> str:
    """Create a unique folder for this episode run."""
    if episode_num is not None:
        episode_folder = f"runs/episode_{episode_num:02d}"
    else:
        episode_folder = f"runs/episode"
    os.makedirs(episode_folder, exist_ok=True)
    print_color(f"ℹ Created episode folder: {episode_folder}", 'info')
    return episode_folder

def generate_episode_outputs(episode_folder: str, log_file: str):
    """Generate all episode outputs in the episode folder."""
    print_color(f"\nGenerating episode outputs in {episode_folder}...", 'processing')
    
    # Note: trace.json is already saved directly to the episode folder
    trace_file = log_file  # log_file is already the trace.json path
    
    # 1. Generate world model graph and visualization
    try:
        print_color("Generating world model graph...", 'processing')
        
        # Save current working directory and change to episode folder
        original_cwd = os.getcwd()
        os.chdir(episode_folder)
        
        try:
            # Create world model from the trace file (which is in the episode folder)
            trace_file_path = "trace.json"
            world_model = create_world_model_from_log(
                log_file=trace_file_path, 
                show_text=False,  # Don't print to console
                show_graph=False,  # Don't show plot window
                save_graph=True,
                save_format='json'
            )
            
            # Generate and save the PNG visualization
            try:
                world_model.visualize(save_path='world_model_graph.png', show_plot=False)
                print_color(f"Generated world model graph PNG", 'success')
            except Exception as e:
                print_color(f"World model PNG generation failed: {e}", 'error')
            
            # Generate and save the text concept graph
            try:
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
                print_color(f"Generated world model concept graph text", 'success')
                
            except Exception as e:
                print_color(f"World model concept graph text generation failed: {e}", 'error')
            
            print_color(f"Generated world model files in {episode_folder}", 'success')
            
        finally:
            # Restore original working directory
            os.chdir(original_cwd)
        
    except Exception as e:
        print_color(f"World model generation failed: {e}", 'error')
    
    # 2. Generate log visualization
    try:
        print_color("Generating log visualization...", 'processing')
        viz_output = os.path.join(episode_folder, "log_visualization.png")
        
        # Run log visualizer with absolute paths
        abs_trace_file = os.path.abspath(trace_file)
        abs_viz_output = os.path.abspath(viz_output)
        
        result = subprocess.run([
            "python", "log_visualizer.py", 
            abs_trace_file,
            "-o", abs_viz_output
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            print_color(f"Generated log visualization: {viz_output}", 'success')
        else:
            print_color(f"Log visualization failed: {result.stderr}", 'error')
            
    except Exception as e:
        print_color(f"Log visualization failed: {e}", 'error')
    
    print_color(f"Episode outputs completed in {episode_folder}", 'success')
    return episode_folderg
===========================================================
This version uses enhanced LLM agents with historical insights and implements
a continuous learning loop where each episode's world model is added to the universe,
and subsequent episodes benefit from accumulated historical knowledge.

Key improvements:
1. Uses EnhancedLLMAgent instead of regular LLMAgent
2. Maintains a persistent universe (multiverse) that accumulates knowledge
3. After each episode, adds the world model to the universe
4. Each new episode uses updated universe for retrieval insights
5. Continuous learning across episodes
6. Enhanced colored output for better visualization
"""
from __future__ import annotations
import argparse
import os
import sys
import subprocess
import json
from datetime import datetime
from typing import Dict, List
from pathlib import Path

# Import the actual environment class
from cube.env import CoopBlockPush
from cube.symbolic_actions import SymbolicController

# Enhanced framework files
from communication import create_enhanced_message_board, run_communication_round
from llm_agent_enhanced import EnhancedLLMAgent, EnhancedLLMAgentManager
from llm_agent import LLMConfig
import llm_templates as templates
from world_model import create_world_model_from_log, WorldModel
from multiverse import Multiverse

# Import our new utilities
from utils import (
    print_color, print_stage_header, print_step_separator, print_agent_action,
    print_success, print_error, print_info, print_debug, print_episode_start,
    print_episode_end, print_universe_update, print_enhanced_summary,
    StageMessages, STAGE_COLORS
)

# ------------------------------
# File helpers
# ------------------------------
def ensure_dirs(path: str):
    d = os.path.dirname(os.path.abspath(path))
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def write_json(path: str, data):
    ensure_dirs(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def read_json(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

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
    
    # 1. Generate world model graph and visualization
    try:
        print("Generating world model graph...")
        
        # Save current working directory and change to episode folder
        original_cwd = os.getcwd()
        os.chdir(episode_folder)
        
        try:
            # Create world model from the trace file (which is in the episode folder)
            trace_file_path = "trace.json"
            world_model = create_world_model_from_log(
                log_file=trace_file_path, 
                show_text=False,  # Don't print to console
                show_graph=False,  # Don't show plot window
                save_graph=True,
                save_format='json'
            )
            
            # Generate and save the PNG visualization
            try:
                world_model.visualize(save_path='world_model_graph.png', show_plot=False)
                print(f"Generated world model graph PNG")
            except Exception as e:
                print(f"World model PNG generation failed: {e}")
            
            # Generate and save the text concept graph
            try:
                import sys
                import io
                
                # Capture the text output
                old_stdout = sys.stdout
                sys.stdout = buffer = io.StringIO()
                world_model.visualize_text_concept_graph()
                sys.stdout = old_stdout
                
                with open('world_model_concept_graph.txt', 'w', encoding='utf-8') as f:
                    f.write(buffer.getvalue())
                print(f"Generated world model text concept graph")
            except Exception as e:
                print(f"World model text generation failed: {e}")
            
        finally:
            os.chdir(original_cwd)
            
        print(f"World model generation completed")
        return world_model
        
    except Exception as e:
        print(f"World model generation failed: {e}")
        return None
    
    # 2. Generate log visualization
    try:
        print("Generating log visualization...")
        viz_output = os.path.join(episode_folder, "log_visualization.png")
        result = subprocess.run([
            "python", "log_visualizer.py", 
            os.path.abspath(log_file),
            "-o", os.path.abspath(viz_output)
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            print(f"Generated log visualization")
        else:
            print(f"Log visualization generation failed: {result.stderr}")
    except Exception as e:
        print(f"Log visualization generation failed: {e}")
    
    return episode_folder

# ------------------------------
# Universe Management
# ------------------------------
class UniverseManager:
    """Manages the persistent universe across episodes for continuous learning"""
    
    def __init__(self, universe_path: str = "runs/updated_universe_graph.json"):
        self.universe_path = universe_path
        self.multiverse = Multiverse(name="LEARNING_UNIVERSE")
        self.episode_count = 0
        
        # Load existing universe if it exists
        self.load_universe()
    
    def load_universe(self):
        """Load existing universe from file if it exists"""
        if os.path.exists(self.universe_path):
            try:
                print_info(f"Loading existing universe from {self.universe_path}")
                # Load the universe data
                universe_data = read_json(self.universe_path)
                if universe_data:
                    # Extract episode count from existing data
                    episodes_data = universe_data.get("universe_data", {}).get("episodes", {})
                    self.episode_count = len(episodes_data)
                    print_success(f"Found {self.episode_count} existing episodes in universe")
                else:
                    print_info("No existing universe data found, starting fresh")
            except Exception as e:
                print_error(f"Failed to load existing universe: {e}, starting fresh")
        else:
            print_info("No existing universe found, starting fresh")
    
    def add_episode_to_universe(self, episode_folder: str, episode_id: str = None):
        """Add a completed episode's world model to the universe"""
        try:
            world_model_path = os.path.join(episode_folder, "world_model_graph.json")
            
            if not os.path.exists(world_model_path):
                print_error(f"World model not found at {world_model_path}")
                return False
            
            if episode_id is None:
                self.episode_count += 1
                episode_id = f"episode_{self.episode_count:02d}"
            
            print_info(f"Adding {episode_id} to universe...")
            
            # Add the world model to the multiverse
            self.multiverse.add_world_model(world_model_path, episode_id)
            
            # Export the updated universe
            self.export_universe()
            
            print_success(f"Added {episode_id} to universe (total episodes: {len(self.multiverse.episodes)})")
            return True
            
        except Exception as e:
            print_error(f"Failed to add episode to universe: {e}")
            return False
    
    def export_universe(self):
        """Export the current universe to JSON file for retrieval"""
        try:
            # Create universe data structure
            universe_data = {
                "nodes": [],
                "links": [],
                "universe_data": {
                    "episodes": {},
                    "stats": {
                        "num_episodes": len(self.multiverse.episodes),
                        "episodes_completed": sum(1 for ep in self.multiverse.episodes.values() 
                                                if ep.wm.episode_data.get("completed", False)),
                    },
                    "views": self.multiverse.views
                }
            }
            
            # Add episode data
            for episode_id, episode_record in self.multiverse.episodes.items():
                wm = episode_record.wm
                universe_data["universe_data"]["episodes"][episode_id] = {
                    "episode_data": wm.episode_data,
                    "task_data": wm.task_data
                }
            
            # Add nodes and links if graph exists
            if self.multiverse.universe_graph:
                # Convert NetworkX graph to JSON format
                universe_data["nodes"] = [{"id": node} for node in self.multiverse.universe_graph.nodes()]
                universe_data["links"] = [{"source": source, "target": target} 
                                        for source, target in self.multiverse.universe_graph.edges()]
            
            # Save to file
            write_json(self.universe_path, universe_data)
            print(f"Universe exported to {self.universe_path}")
            
        except Exception as e:
            print(f"Failed to export universe: {e}")
    
    def get_universe_path(self) -> str:
        """Get the path to the current universe file for retrieval"""
        return self.universe_path if os.path.exists(self.universe_path) else None

# ------------------------------
# Enhanced Agent and Planning
# ------------------------------
def build_enhanced_agents(env, agent_manager: EnhancedLLMAgentManager, n_agents: int, model: str, universe_path: str = None) -> Dict[str, EnhancedLLMAgent]:
    """Build enhanced LLM agents with historical insights"""
    cfg = LLMConfig(model=model)
    agents: Dict[str, EnhancedLLMAgent] = {}
    
    for i in range(n_agents):
        aid = f"agent_{i}"
        # Create enhanced agent with universe path for historical insights
        agent = agent_manager.add_enhanced_agent(aid, cfg, agent_manager)
        agents[aid] = agent
    
    print_success(f"Created {n_agents} enhanced agents with historical insights")
    return agents

def run_enhanced_communication_round(agents: Dict[str, EnhancedLLMAgent], message_board) -> object:
    """Enhanced communication round using the provided enhanced message board"""
    
    participants = [a for a in agents.values() if a.should_plan()]
    
    # Start proposal round
    message_board.start_proposal_round()
    for agent in participants:
        agent.propose_task(message_board)

    # Start commitment round  
    message_board.start_commitment_round()
    for agent in participants:
        agent.commit_to_task(message_board)

    message_board.complete_communication()
    return message_board
def run_enhanced_communication_and_planning(agents: Dict[str, EnhancedLLMAgent], agent_manager: EnhancedLLMAgentManager, 
                                           step: int, extra_file: str, comm_type: str = "initial", universe_path: str = None):
    """Enhanced communication and planning with historical insights"""
    
    # Find agents that need to plan
    participants = []
    for agent in agents.values():
        if agent.should_plan():
            participants.append(agent.id)
    
    if not participants:
        return []
    
    print_stage_header("COMMUNICATION_PROPOSAL", step, f"Participants: {participants}")
    
    # Create enhanced message board with historical insights
    message_board = create_enhanced_message_board(universe_json_path=universe_path)
    
    # Run enhanced communication round
    participating_agents = {aid: agents[aid] for aid in participants}
    board = run_enhanced_communication_round(participating_agents, message_board)
    
    # Extract assignments
    assignments = {}
    for commitment in board.commitments:
        assignments[commitment.agent_id] = commitment.block_id
    
    # Log communication round
    agent_manager.log_communication_round(
        step=step,
        participants=participants,
        communication_type=comm_type,
        result=assignments
    )
    
    # Get planning participants (agents that got assignments)
    planning_participants = list(assignments.keys())
    
    if not planning_participants:
        print_error("No planning participants after communication")
        return []
    
    print_stage_header("PLANNING", step, f"Planning participants: {planning_participants}")
    
    # Enhanced planning for each agent
    planned_agents = []
    for agent_id in planning_participants:
        agent = agents[agent_id]
        
        try:
            print_info(f"Planning for {agent_id}...")
            
            # Set agent's assigned block and task
            agent.assigned_block = assignments[agent_id]
            agent.task_name = f"Block_{assignments[agent_id]}"
            
            # Enhanced planning with historical insights
            agent.plan(all_agents=agents)
            
            if hasattr(agent, 'plan_steps') and agent.plan_steps:
                planned_agents.append(agent_id)
                
                print_success(f"{agent_id} planned for {agent.task_name} ({len(agent.plan_steps)} actions)")
                
                # Note: plan logging would go here if needed
                
            else:
                print_error(f"{agent_id} failed to generate plan")
                
        except Exception as e:
            print_error(f"Planning failed for {agent_id}: {e}")
    
    print_enhanced_summary("Successfully Planned", planned_agents, 'planning')
    return planned_agents

# ------------------------------
# Main Execution Loop
# ------------------------------
def run_enhanced_episode(episode_num: int, args, universe_manager: UniverseManager):
    """Run a single enhanced episode with historical learning"""
    
    print_episode_start(episode_num, {
        "agents": args.n,
        "max_steps": args.max_steps,
        "model": args.model,
        "comm_freq": args.communication_freq
    })
    
    # Create episode folder
    episode_folder = create_episode_folder(episode_num)
    print_info(f"Created episode folder: {episode_folder}")
    
    # Get universe path for historical insights
    universe_path = universe_manager.get_universe_path()
    if universe_path:
        print_success(f"Using historical insights from: {universe_path}")
    else:
        print_info("No historical data available - this is the first episode")
    
    # Initialize environment
    env = CoopBlockPush(
        n=args.n,
        max_steps=args.max_steps,
        render_mode="human" if (args.capture_video or args.render) else None
    )
    
    # Initialize enhanced agent manager
    enhanced_agent_manager = EnhancedLLMAgentManager(env, universe_json_path=universe_path)
    
    # Build enhanced agents
    agents = build_enhanced_agents(env, enhanced_agent_manager, args.n, args.model, universe_path)
    
    # Initialize symbolic controller
    symbolic_controller = SymbolicController(env, {})
    
    # Setup logging
    trace_file = os.path.join(episode_folder, "trace.json")
    
    # Reset environment
    obs, _ = env.reset()
    step = 0
    
    # Render initial state if requested
    if args.render or args.capture_video:
        try:
            env.render()
            print_debug("Rendered initial environment state")
            # Add a small delay to see the initial rendering
            import time
            time.sleep(1.0)
        except Exception as e:
            print_error(f"Failed to render initial environment: {e}")
    
    print_stage_header("EXECUTION", details=f"Environment: {args.n} agents, max {args.max_steps} steps")
    
    # Main execution loop
    while step < args.max_steps:
        print_step_separator(step, 'execution')
        
        # Enhanced communication and planning
        if step % args.communication_freq == 0:
            planned_agents = run_enhanced_communication_and_planning(
                agents, enhanced_agent_manager, step, trace_file, "regular", universe_path
            )
        
        # Execute symbolic actions for all agents
        if step == 0 or step % args.communication_freq == 0:
            # Update controller with agent plans
            agent_plans_objects = enhanced_agent_manager.convert_all_agent_plans_to_objects()
            for agent_id, plan_obj in agent_plans_objects.items():
                symbolic_controller.plans[agent_id] = plan_obj
                symbolic_controller.idx[agent_id] = 0
                symbolic_controller.rem[agent_id] = 0
        
        # Get actions from symbolic controller
        actions = symbolic_controller.act()
        
        # Log timestep with actions
        enhanced_agent_manager.log_timestep(step, actions)
        
        # Step environment
        if actions:
            obs, rewards, terminated, truncated, info = env.step(actions)
            print_debug(f"Step {step}: Actions: {actions}")
            print_debug(f"Step {step}: Terminated: {terminated}, Truncated: {truncated}")
        else:
            # No actions to execute, just observe
            obs, rewards, terminated, truncated, info = env.step({})
            print_debug(f"Step {step}: No actions")
            print_debug(f"Step {step}: Terminated: {terminated}, Truncated: {truncated}")
        
        # Render environment if requested
        if args.render or args.capture_video:
            try:
                env.render()
                print_debug(f"Rendered environment at step {step}")
            except Exception as e:
                print_error(f"Failed to render environment: {e}")
        
        step += 1
        
        # Check termination conditions
        if hasattr(env, '_blocks') and len(env._blocks) == 0:
            print_success(f"All blocks delivered at step {step}")
            break
        
        # For PettingZoo parallel environments, terminated and truncated are dictionaries
        if isinstance(terminated, dict) and isinstance(truncated, dict):
            # Check if any agent is terminated or truncated
            any_terminated = any(terminated.values()) if terminated else False
            any_truncated = any(truncated.values()) if truncated else False
            if any_terminated or any_truncated:
                print_info(f"Episode terminated at step {step} - Any terminated: {any_terminated}, Any truncated: {any_truncated}")
                break
        else:
            # Handle single boolean values (legacy compatibility)
            if terminated or truncated:
                print_info(f"Episode terminated at step {step} - Terminated: {terminated}, Truncated: {truncated}")
                break
    
    # Finalize episode
    episode_success = hasattr(env, '_blocks') and len(env._blocks) == 0
    print_episode_end(episode_num, episode_success, step)
    
    # Save execution trace
    enhanced_agent_manager.save_complete_log(trace_file)
    print_success(f"Execution trace saved to: {trace_file}")
    
    # Generate episode outputs (world model, visualizations)
    world_model = generate_episode_outputs(episode_folder, trace_file)
    
    # Add this episode to the universe for future learning
    episode_id = f"episode_{episode_num:02d}"
    success = universe_manager.add_episode_to_universe(episode_folder, episode_id)
    
    if success:
        print_universe_update(universe_manager.universe_path, len(universe_manager.multiverse.episodes))
    else:
        print_error(f"Failed to add episode {episode_num} to universe")
    
    # Episode summary
    if hasattr(env, 'get_episode_stats'):
        stats = env.get_episode_stats()
        print_enhanced_summary("Episode Stats", [
            f"Blocks delivered: {stats.get('delivered_blocks', 0)}",
            f"Total steps: {step}",
            f"Success rate: {stats.get('success_rate', 0):.1%}"
        ], 'episode_end')
    
    env.close()
    return episode_folder, step

def main():
    parser = argparse.ArgumentParser(description="Enhanced Multi-Agent LLM Framework with Continuous Learning")
    parser.add_argument("--n", type=int, default=3, help="Number of agents")
    parser.add_argument("--max_steps", type=int, default=100, help="Maximum steps per episode")
    parser.add_argument("--model", type=str, default="gpt-4o-mini", help="LLM model to use")
    parser.add_argument("--communication_freq", type=int, default=10, help="Steps between communication rounds")
    parser.add_argument("--n_episodes", type=int, default=5, help="Number of episodes to run")
    parser.add_argument("--capture_video", action="store_true", help="Capture video of episodes")
    parser.add_argument("--render", action="store_true", help="Render environment visualization")
    parser.add_argument("--start_episode", type=int, default=1, help="Starting episode number")
    
    args = parser.parse_args()
    
    print_color("=" * 100, 'episode_start')
    print_color("ENHANCED MULTI-AGENT LLM FRAMEWORK WITH CONTINUOUS LEARNING", 'episode_start')
    print_color("=" * 100, 'episode_start')
    print_color(f"Configuration:", 'episode_start')
    print_color(f"  Agents: {args.n}", 'episode_start')
    print_color(f"  Max steps: {args.max_steps}", 'episode_start')
    print_color(f"  Model: {args.model}", 'episode_start')
    print_color(f"  Episodes: {args.n_episodes}", 'episode_start')
    print_color(f"  Communication frequency: {args.communication_freq}", 'episode_start')
    print()
    
    # Initialize universe manager for continuous learning
    universe_manager = UniverseManager()
    
    # Run multiple episodes with continuous learning
    episode_results = []
    
    for episode_num in range(args.start_episode, args.start_episode + args.n_episodes):
        try:
            episode_folder, steps = run_enhanced_episode(episode_num, args, universe_manager)
            episode_results.append({
                "episode": episode_num,
                "folder": episode_folder,
                "steps": steps,
                "status": "completed"
            })
            
            print_success(f"Episode {episode_num} completed successfully")
            
        except Exception as e:
            print_error(f"Episode {episode_num} failed: {e}")
            episode_results.append({
                "episode": episode_num,
                "folder": None,
                "steps": 0,
                "status": "failed",
                "error": str(e)
            })
    
    # Final summary
    print_color("\n" + "=" * 100, 'universe_update')
    print_color("ENHANCED MULTI-AGENT LEARNING SESSION COMPLETE", 'universe_update')
    print_color("=" * 100, 'universe_update')
    
    successful_episodes = [r for r in episode_results if r["status"] == "completed"]
    failed_episodes = [r for r in episode_results if r["status"] == "failed"]
    
    print_color(f"Episodes completed: {len(successful_episodes)}/{args.n_episodes}", 'success' if successful_episodes else 'error')
    if failed_episodes:
        print_color(f"Episodes failed: {len(failed_episodes)}", 'error')
    
    if successful_episodes:
        avg_steps = sum(r["steps"] for r in successful_episodes) / len(successful_episodes)
        print_color(f"Average steps per episode: {avg_steps:.1f}", 'info')
    
    print_universe_update(universe_manager.universe_path, universe_manager.episode_count)
    
    print_color("Continuous learning enabled - each episode improves the next! 🚀", 'success')

if __name__ == "__main__":
    main()

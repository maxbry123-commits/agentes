# main_clean.py
"""
Clean Multi-agent LLM Framework Main Script
==========================================
Simplified execution following main_basic.py pattern but with LLM communication and planning.
"""
from __future__ import annotations
import argparse
import os
import sys
import subprocess
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
    #timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if episode_num is not None:
        episode_folder = f"runs/episode_{episode_num:02d}"#_{timestamp}"
    else:
        episode_folder = f"runs/episode"#_{timestamp}"
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
                
                # Generate text concept graph
                world_model.visualize_text_concept_graph()
                
                # Restore stdout and get captured text
                sys.stdout = old_stdout
                concept_text = buffer.getvalue()
                
                # Save to file
                with open('world_model_concept_graph.txt', 'w', encoding='utf-8') as f:
                    f.write(concept_text)
                print(f"Generated world model concept graph text")
                
            except Exception as e:
                print(f"World model concept graph text generation failed: {e}")
            
            print(f"Generated world model files in {episode_folder}")
            
        finally:
            # Restore original working directory
            os.chdir(original_cwd)
        
    except Exception as e:
        print(f"World model generation failed: {e}")
    
    # 2. Generate log visualization
    try:
        print("Generating log visualization...")
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
            print(f"Generated log visualization: {viz_output}")
        else:
            print(f"Log visualization failed: {result.stderr}")
            
    except Exception as e:
        print(f"Log visualization failed: {e}")
    
    print(f"Episode outputs completed in {episode_folder}")
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
            
            # Step environment
            observations, rewards, dones, truncated, infos = env.step(actions)
            
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
            'success': len(env._blocks) == 0  # Success if all blocks delivered
        }
        
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
            'error': str(e)
        }

# ------------------------------
# Main Execution (Multiple Episodes)
# ------------------------------
def main():
    p = argparse.ArgumentParser("Multi-Episode LLM Framework")
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
            all_episode_results.append(episode_results)
            
            print(f"\nEpisode {episode_num} Summary:")
            print(f"  - Steps: {episode_results['total_steps']}")
            print(f"  - Reward: {episode_results['total_reward']:.3f}")
            print(f"  - Communication rounds: {episode_results['communication_rounds']}")
            print(f"  - Success: {'Yes' if episode_results['success'] else 'No'}")
            print(f"  - Blocks remaining: {episode_results['blocks_remaining']}")
            
        except Exception as e:
            print(f"Episode {episode_num} failed with error: {e}")
            all_episode_results.append({
                'episode_num': episode_num,
                'error': str(e),
                'success': False
            })
    
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
    
    # Save overall summary
    #timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = f"runs/multi_episode_summary.json"
    ensure_dirs(summary_file)
    
    summary_data = {
        'args': vars(args),
        #'timestamp': timestamp,
        'episodes': all_episode_results,
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
        import json
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2)
        print(f"\nOverall summary saved to: {os.path.abspath(summary_file)}")
    except Exception as e:
        print(f"Failed to save summary: {e}")
    
    print(f"\nAll {args.num_episodes} episodes completed!")

if __name__ == "__main__":
    main()

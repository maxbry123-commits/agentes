from __future__ import annotations
import argparse
import os
import time
from datetime import datetime
from typing import Dict
import subprocess

from cube.env import CoopBlockPush
from cube.symbolic_actions import SymbolicController
from llm_agent import LLMAgent, LLMConfig, LLMAgentManager
from world_model import create_world_model_from_log

def create_episode_folder() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    episode_folder = f"runs/episode_{timestamp}"
    os.makedirs(episode_folder, exist_ok=True)
    print(f"Created episode folder: {episode_folder}")
    return episode_folder

def generate_episode_outputs(episode_folder: str, log_file: str):
    # Simplified output generation for baseline - avoid world model visualization
    print(f"Baseline episode completed. Log saved to: {log_file}")
    print(f"Episode folder: {episode_folder}")
    print("Note: Baseline mode - simplified output generation")

def baseline_plan(agent: LLMAgent, all_agents=None):
    """Baseline-specific planning that prioritizes closest blocks to goal"""
    import llm_templates as templates
    
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
        agents[aid] = agent
        agent_manager.add_agent(agent)
    return agents

def reset_agent_plan_runtime_state(agent: LLMAgent):
    # minimal runtime reset so the agent can re-plan cleanly
    agent.plan_steps = []
    agent.plan_index = 0
    agent.phase = "planning"
    if hasattr(agent, "_plan_completion_logged"):
        delattr(agent, "_plan_completion_logged")

def main():
    p = argparse.ArgumentParser("First-phase-only replanning (no comms)")
    p.add_argument("--n", type=int, default=5)
    p.add_argument("--model", type=str, default="gpt-4o")
    p.add_argument("--max_steps", type=int, default=150)
    args = p.parse_args()



    episode_folder = create_episode_folder()
    episode_log_file = os.path.join(episode_folder, "trace.json")

    env = CoopBlockPush(n=args.n, max_steps=args.max_steps, render_mode="human")
    # Start timing the episode
    episode_start_time = time.time()
    env.reset()

    # Initialize block tracking
    initial_blocks = {}
    initial_block_count = len(env._blocks)
    
    # Initialize block information for tracking
    for block in env._blocks:
        initial_distance = 19 - block.r  # Distance to goal (rightmost column is 19)
        initial_blocks[block.id] = {
            'id': block.id,
            'weight': block.weight,
            'initial_position': (block.r, block.c),
            'initial_distance_to_goal': initial_distance,
            'final_position': None,
            'in_goal': False
        }
    
    print(f"\n=== EPISODE INITIALIZATION ===")
    print(f"Total blocks: {initial_block_count}")
    for block_info in initial_blocks.values():
        print(f"  Block {block_info['id']}: weight={block_info['weight']}, "
              f"position={block_info['initial_position']}, "
              f"distance_to_goal={block_info['initial_distance_to_goal']}")

    agent_manager = LLMAgentManager(env)
    agents = build_agents(env, agent_manager, args.n, args.model)

    # -------- initial single planning phase (first phase only) --------
    for agent in agents.values():
        baseline_plan(agent, all_agents=agents)  # Use baseline-specific planning
    agent_manager.log_planning_completed(0, list(agents.keys()))

    # controller from initial plans
    agent_plans_objects = agent_manager.convert_all_agent_plans_to_objects()  #:contentReference[oaicite:2]{index=2}
    controller = SymbolicController(env, agent_plans_objects)  #:contentReference[oaicite:3]{index=3}

    step = 0
    total_reward = 0

    while step < args.max_steps:
        # -------- execute one step --------
        actions = controller.act()
        agent_manager.log_timestep(step, actions)

        # track controller progress to update each agent's plan_index
        for agent_id, agent in agents.items():
            if agent_id in controller.idx:
                prog = controller.idx[agent_id]
                if prog > agent.plan_index:
                    agent.plan_index = prog

        # log individual plan completion as they finish
        for agent_id, agent in agents.items():
            if (
                agent.plan_steps
                and agent.plan_index >= len(agent.plan_steps)
                and not hasattr(agent, "_plan_completion_logged")
            ):
                agent._plan_completion_logged = True
                # success = target block consumed (if agent had a block)
                target_block = getattr(agent, "assigned_block", None)
                block_available = False
                if target_block is not None:
                    block_available = any(b.id == target_block for b in env._blocks)
                plan_successful = (target_block is None) or (not block_available)
                agent_manager.log_plan_execution_completed(
                    step,
                    {
                        agent_id: {
                            "plan_successful": plan_successful,
                            "target_block": target_block,
                            "block_still_available": block_available,
                            "committed_task": getattr(agent, "committed_task", None),
                        }
                    },
                )

        observations, rewards, dones, truncated, infos = env.step(actions)
        env.render()
        step += 1
        total_reward += sum(rewards.values())

        # -------- first-phase-only REPLANNING trigger --------
        # If any agent finished its plan while blocks remain, replan ONLY that agent using first-phase planner.
        if len(env._blocks) > 0:
            agents_needing_replan = [aid for aid, a in agents.items() if a.is_finished()]
            if agents_needing_replan:
                for aid in agents_needing_replan:
                    a = agents[aid]
                    reset_agent_plan_runtime_state(a)
                    baseline_plan(a, all_agents=agents)  # Use baseline-specific planning

                # update controller only for those agents
                plans_obj = agent_manager.convert_all_agent_plans_to_objects()
                for aid in agents_needing_replan:
                    if aid in plans_obj:
                        controller.plans[aid] = plans_obj[aid]
                        controller.idx[aid] = 0
                        controller.rem[aid] = 0

        # stop if everyone done or env over
        if all(dones.values()) or all(truncated.values()):
            break
        if all(a.is_finished() for a in agents.values()) and len(env._blocks) == 0:
            break

    # Calculate episode completion statistics
    episode_end_time = time.time()
    total_runtime = episode_end_time - episode_start_time
    
    # Determine completed blocks
    remaining_blocks = []
    completed_blocks = []
    
    for block_info in initial_blocks.values():
        block_still_exists = False
        for current_block in env._blocks:
            if current_block.id == block_info['id']:
                # Block still exists 
                current_distance = 19 - current_block.r
                block_info['final_position'] = (current_block.r, current_block.c)
                block_info['final_distance_to_goal'] = current_distance
                block_info['completed'] = current_distance == 0  # Block reached goal (column 19)
                if block_info['completed']:
                    completed_blocks.append(block_info)
                else:
                    remaining_blocks.append(block_info)
                block_still_exists = True
                break
        
        if not block_still_exists:
            # Block was delivered to goal and removed from environment
            block_info['final_position'] = 'DELIVERED'
            block_info['final_distance_to_goal'] = 0
            block_info['completed'] = True
            completed_blocks.append(block_info)

    # Print final episode summary
    print(f"\n=== BASELINE EPISODE SUMMARY ===")
    print(f"Runtime: {total_runtime:.2f}s | Steps: {step}/{args.max_steps} | Reward: {total_reward:.3f}")
    print(f"Blocks: {len(completed_blocks)}/{initial_block_count} completed ({len(completed_blocks)/initial_block_count*100:.1f}%)")
    
    # Show block specs and completion status
    for block_info in initial_blocks.values():
        status = "[YES]" if block_info in completed_blocks else "[NO]"
        print(f"  {status} Block {block_info['id']}: weight={block_info['weight']}")
    print(f"{'='*50}")

    # save logs and artifacts
    agent_manager.save_complete_log(episode_log_file)
    generate_episode_outputs(episode_folder, episode_log_file)

if __name__ == "__main__":
    main()

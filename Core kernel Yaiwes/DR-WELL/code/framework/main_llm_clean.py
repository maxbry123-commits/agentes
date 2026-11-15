"""
Simplified Multi-agent LLM Framework
====================================
Clean version with only essential functionality.
"""
from __future__ import annotations
import argparse
import os
import sys
import subprocess
from datetime import datetime
from typing import Dict

from cube.env import CoopBlockPush
from cube.symbolic_actions import SymbolicController

from communication import run_communication_round
from llm_agent import LLMAgent, LLMConfig, LLMAgentManager
from world_model import create_world_model_from_log

def create_episode_folder() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    episode_folder = f"runs/episode_{timestamp}"
    os.makedirs(episode_folder, exist_ok=True)
    print(f"Created episode folder: {episode_folder}")
    return episode_folder

def generate_episode_outputs(episode_folder: str, log_file: str):
    # 1. Generate world model graph and visualization
    original_cwd = os.getcwd()
    os.chdir(episode_folder)
    
    # Create world model from the trace file
    world_model = create_world_model_from_log(
        log_file="trace.json", 
        show_text=False,
        show_graph=False,
        save_graph=True,
        save_format='json'
    )
    
    # Generate PNG visualization
    world_model.visualize(save_path='world_model_graph.png', show_plot=False)
    
    # Generate text concept graph
    import sys
    import io
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()
    world_model.visualize_text_concept_graph()
    sys.stdout = old_stdout
    
    with open('world_model_concept_graph.txt', 'w', encoding='utf-8') as f:
        f.write(buffer.getvalue())
    
    os.chdir(original_cwd)
    
    # 2. Generate log visualization
    viz_output = os.path.join(episode_folder, "log_visualization.png")
    subprocess.run([
        "python", "log_visualizer.py", 
        os.path.abspath(log_file),
        "-o", os.path.abspath(viz_output)
    ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
    
    return episode_folder

# ------------------------------
# Agent and Planning
# ------------------------------
def build_agents(env, agent_manager: LLMAgentManager, n_agents: int, model: str) -> Dict[str, LLMAgent]:
    cfg = LLMConfig(model=model)
    agents: Dict[str, LLMAgent] = {}
    for i in range(n_agents):
        aid = f"agent_{i}"
        agent = LLMAgent(aid, env, agent_manager, cfg, plan=[])
        agents[aid] = agent
        agent_manager.add_agent(agent)
    return agents

def run_communication_and_planning(agents: Dict[str, LLMAgent], agent_manager: LLMAgentManager, step: int, extra_file: str, comm_type: str = "initial"):
    participants = []
    for agent in agents.values():
        if agent.should_plan():
            participants.append(agent.id)
    
    if not participants:
        return []
    
    board = run_communication_round({aid: agents[aid] for aid in participants})
    
    assignments = {}
    for commitment in board.commitments:
        assignments[commitment.agent_id] = commitment.block_id
    
    agent_manager.log_communication_round(
        step=step,
        participants=participants,
        communication_type=comm_type,
        result=assignments
    )
    
    agents_with_plans = []
    for agent_id in participants:
        agent = agents[agent_id]
        if agent_id in assignments:
            block_id = assignments[agent_id]
            agent.assigned_block = block_id
            agent.task_name = f"Block_{block_id}"
        
        agent.plan(all_agents=agents)
        agents_with_plans.append(agent_id)
    
    agent_manager.log_planning_completed(step, agents_with_plans)
    return participants

def check_need_replanning(env, agents: Dict[str, LLMAgent]) -> bool:
    blocks_remain = len(env._blocks) > 0
    all_finished = all(agent.is_finished() for agent in agents.values())
    return blocks_remain and all_finished



# ------------------------------
# Main Execution
# ------------------------------
def main():
    p = argparse.ArgumentParser("Clean Multi-agent LLM Framework")
    p.add_argument("--n", type=int, default=2)
    p.add_argument("--model", type=str, default="gpt-4o")
    p.add_argument("--max_steps", type=int, default=50)
    args = p.parse_args()

    episode_folder = create_episode_folder()
    episode_extra_file = os.path.join(episode_folder, "shared_extra_info.md")
    episode_log_file = os.path.join(episode_folder, "trace.json")

    env = CoopBlockPush(n=args.n, max_steps=args.max_steps, render_mode='human')
    obs = env.reset()

    agent_manager = LLMAgentManager(env)
    agents = build_agents(env, agent_manager, args.n, args.model)

    run_communication_and_planning(agents, agent_manager, step=0, extra_file=episode_extra_file, comm_type="initial")
    
    agent_plans_objects = agent_manager.convert_all_agent_plans_to_objects()
    controller = SymbolicController(env, agent_plans_objects)
    
    total_reward = 0
    step = 0
    max_iterations = 10
    iteration = 1
    
    while step < args.max_steps and iteration <= max_iterations:
        execution_start_step = step
        while step < args.max_steps:
            if len(env._blocks) > 0:
                agents_needing_replan = [agent_id for agent_id, agent in agents.items() if agent.is_finished()]
                if agents_needing_replan:
                    for agent_id in agents_needing_replan:
                        agent = agents[agent_id]
                        agent.plan_steps = []
                        agent.plan_index = 0
                        agent.phase = "planning"
                        if hasattr(agent, '_plan_completion_logged'):
                            delattr(agent, '_plan_completion_logged')
                    
                    participants = run_communication_and_planning(
                        agents, agent_manager, step, episode_extra_file, comm_type=f"individual_replan_step_{step}"
                    )
                    
                    if participants:
                        agent_plans_objects = agent_manager.convert_all_agent_plans_to_objects()
                        for agent_id in participants:
                            if agent_id in agent_plans_objects:
                                controller.plans[agent_id] = agent_plans_objects[agent_id]
                                controller.idx[agent_id] = 0
                                controller.rem[agent_id] = 0
            
            actions = controller.act()
            agent_manager.log_timestep(step, actions)
            
            for agent_id, agent in agents.items():
                if agent_id in controller.idx:
                    controller_progress = controller.idx[agent_id]
                    if controller_progress > agent.plan_index:
                        agent.plan_index = controller_progress
            
            for agent_id, agent in agents.items():
                if (agent.plan_steps and 
                    agent.plan_index >= len(agent.plan_steps) and 
                    not hasattr(agent, '_plan_completion_logged')):
                    
                    agent._plan_completion_logged = True
                    target_block = agent.assigned_block if hasattr(agent, 'assigned_block') else None
                    committed_task = agent.committed_task if hasattr(agent, 'committed_task') else None
                    block_still_available = False
                    if target_block is not None:
                        block_still_available = any(block.id == target_block for block in env._blocks)
                    
                    plan_successful = False
                    if target_block is not None:
                        plan_successful = not block_still_available
                    else:
                        plan_successful = True
                    
                    individual_plan_result = {
                        agent_id: {
                            'plan_successful': plan_successful,
                            'target_block': target_block,
                            'block_still_available': block_still_available,
                            'committed_task': committed_task
                        }
                    }
                    
                    agent_manager.log_plan_execution_completed(step, individual_plan_result)
            
            observations, rewards, dones, truncated, infos = env.step(actions)
            env.render()
            step += 1
            total_reward += sum(rewards.values())
            
            if all(agent.is_finished() for agent in agents.values()):
                if len(env._blocks) == 0:
                    break
                else:
                    agents_plan_results = {}
                    for agent_id, agent in agents.items():
                        target_block = agent.assigned_block if hasattr(agent, 'assigned_block') else None
                        committed_task = agent.committed_task if hasattr(agent, 'committed_task') else None
                        block_still_available = False
                        if target_block is not None:
                            block_still_available = any(block.id == target_block for block in env._blocks)
                        
                        plan_successful = False
                        if agent.is_finished():
                            if target_block is not None:
                                plan_successful = not block_still_available
                            else:
                                plan_successful = True
                        
                        agents_plan_results[agent_id] = {
                            'plan_successful': plan_successful,
                            'target_block': target_block,
                            'block_still_available': block_still_available,
                            'committed_task': committed_task
                        }
                    
                    agent_manager.log_plan_execution_completed(step, agents_plan_results)
                    if len(env._blocks) == 0:
                        break
            
            if all(dones.values()) or all(truncated.values()):
                break
        
        if check_need_replanning(env, agents):
            iteration += 1
            if iteration <= max_iterations:
                for agent in agents.values():
                    agent.plan_steps = []
                    agent.plan_index = 0
                    agent.phase = "planning"
                    if hasattr(agent, '_plan_completion_logged'):
                        delattr(agent, '_plan_completion_logged')
                
                participants = run_communication_and_planning(
                    agents, agent_manager, step, episode_extra_file, comm_type=f"final_replan_{iteration-1}"
                )
                
                if participants:
                    agent_plans_objects = agent_manager.convert_all_agent_plans_to_objects()
                    controller.plans = agent_plans_objects
                    controller.idx = {agent_id: 0 for agent_id in env.agents}
                    controller.rem = {agent_id: 0 for agent_id in env.agents}
                else:
                    break
            else:
                break
        else:
            break

    agent_manager.save_complete_log(episode_log_file)
    generate_episode_outputs(episode_folder, episode_log_file)

if __name__ == "__main__":
    main()

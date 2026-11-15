"""
Base Agent Class - Core plan execution for symbolic actions
==========================================================
Minimal base class for executing symbolic action plans.
LLMAgent should inherit from this to add task negotiation and planning.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any
import datetime
import json
from .symbolic_actions import MoveToBlock, Rendezvous, Push, Wait, WaitAgents, YieldFace


class BaseAgent:
    """
    Base agent class for executing symbolic action plans.
    
    Core features:
    - Execute predefined plans of symbolic actions
    - Track plan progress and current phase
    - Basic environment observation
    - Action parsing utilities
    
    This class should be inherited by LLMAgent for task planning and negotiation.
    """
    
    def __init__(self, agent_id: str, env, plan: List = None):
        self.id = agent_id
        self.env = env
        
        # Plan execution
        self.plan_steps: List = plan or []  # List of symbolic actions
        self.plan_index: int = 0
        self.phase: str = "planning"  # "planning" | "executing" | "finished" | "waiting" | "rendezvous"
        
        # Rendezvous coordination
        self.rendezvous_ready: bool = False  # True when agent has seen all required rendezvous participants
        
        # Action tracking
        self.action_history: List[Dict[str, Any]] = []
    
    def observe(self) -> dict:
        """
        Basic environment observation.
        Returns current state information for the agent.
        """
        teammates = [a for a in self.env.possible_agents if a != self.id]
        
        # Get environment state
        available_blocks = []
        delivered_blocks = []
        goal_col = self.env.K - 1
        
        if self.env._blocks:
            for block in self.env._blocks:
                block_info = {
                    "id": block.id,
                    "weight": block.weight,
                    "position": (block.r, block.c),
                    "distance_to_goal": goal_col - (block.c + block.weight - 1),
                    "delivered": block.c == goal_col
                }
                if block_info["delivered"]:
                    delivered_blocks.append(block_info)
                else:
                    available_blocks.append(block_info)
        
        # Agent positions
        agent_positions = {}
        if hasattr(self.env, '_agent_positions'):
            for agent_name in self.env.agents:
                if agent_name in self.env._agent_positions:
                    pos = self.env._agent_positions[agent_name]
                    agent_positions[agent_name] = (pos[0], pos[1])
        
        my_position = agent_positions.get(self.id, "unknown")
        
        observation = {
            # Agent info
            "agent_id": self.id,
            "teammates": teammates,
            "my_position": my_position,
            
            # Environment state
            "grid_size": self.env.K,
            "available_blocks": available_blocks,
            "delivered_blocks": delivered_blocks,
            "agent_positions": agent_positions,
            "total_blocks": len(available_blocks) + len(delivered_blocks),
            "blocks_remaining": len(available_blocks),
            
            # Plan state
            "phase": self.phase,
            "plan_progress": f"{self.plan_index}/{len(self.plan_steps)}",
            "plan_complete": self.plan_index >= len(self.plan_steps)
        }
        
        return observation

    @staticmethod
    def parse_step(action_str: str):
        """Parse action string to symbolic action dataclass"""
        parts = action_str.strip().split()
        kind = parts[0]
        
        if kind == "MoveToBlock":
            return MoveToBlock(int(parts[1]), parts[2])
        elif kind == "Rendezvous":
            return Rendezvous(int(parts[1]), parts[2], int(parts[3]), int(parts[4]) if len(parts) > 4 else 10)
        elif kind == "Push":
            return Push(int(parts[1]), int(parts[2]))
        elif kind == "Wait":
            return Wait(int(parts[1]))
        elif kind == "WaitAgents":
            return WaitAgents(int(parts[1]), int(parts[2]))
        elif kind == "YieldFace":
            return YieldFace(int(parts[1]), parts[2], int(parts[3]))
        else:
            raise ValueError(f"Unknown action type: {kind}")

    def set_plan(self, plan: List):
        """Set a new plan for the agent"""
        self.plan_steps = plan
        self.plan_index = 0
        self.phase = "executing" if plan else "finished"
        
        # Log plan assignment
        self.action_history.append({
            "action": "plan_assigned",
            "plan_length": len(plan),
            "timestamp": len(self.action_history)
        })
    
    def get_current_action(self):
        """Get the current action the agent should execute"""
        if self.plan_index >= len(self.plan_steps):
            self.phase = "finished"
            return None
        
        current_step = self.plan_steps[self.plan_index]
        
        # Convert string to action object if needed
        if isinstance(current_step, str):
            current_action = BaseAgent.parse_step(current_step)
        else:
            current_action = current_step
        
        # Auto-update phase based on action type
        if isinstance(current_action, Rendezvous):
            self.phase = "rendezvous"
        elif isinstance(current_action, (Wait, WaitAgents)):
            self.phase = "waiting"
        elif self.phase not in ["executing", "rendezvous", "waiting"]:
            self.phase = "executing"
        
        return current_action
    
    def advance_plan(self):
        """Mark current action as completed and advance to next step"""
        if self.plan_index < len(self.plan_steps):
            completed_action = self.plan_steps[self.plan_index]
            self.plan_index += 1
            
            # Log completion
            action_name = type(completed_action).__name__ if hasattr(completed_action, '__class__') else str(completed_action)
            self.action_history.append({
                "action": "step_completed",
                "step": action_name,
                "plan_index": self.plan_index,
                "total_steps": len(self.plan_steps)
            })
            
            # Update phase if plan is finished
            if self.plan_index >= len(self.plan_steps):
                self.phase = "finished"

    def is_finished(self) -> bool:
        """Check if agent has finished its current plan"""
        return self.phase == "finished" or self.plan_index >= len(self.plan_steps)

    def get_state_summary(self) -> dict:
        """Get a summary of agent state for display purposes"""
        obs = self.observe()
        current_action = self.get_current_action()
        return {
            "id": self.id,
            "position": obs["my_position"],
            "phase": self.phase,
            "progress": f"{self.plan_index}/{len(self.plan_steps)}",
            "current_action": type(current_action).__name__ if current_action else "None"
        }
    
    def get_plan_summary(self, num_steps: int = 3) -> str:
        """Get a summary of upcoming plan steps with arguments"""
        plan_summary = []
        for i in range(self.plan_index, min(self.plan_index + num_steps, len(self.plan_steps))):
            step = self.plan_steps[i]
            
            # Handle both string and object plans
            if isinstance(step, str):
                # For string plans, extract action name and args
                parts = step.strip().split()
                if parts:
                    action_name = parts[0]
                    args = parts[1:] if len(parts) > 1 else []
                    if args:
                        step_name = f"{action_name}({', '.join(args)})"
                    else:
                        step_name = f"{action_name}()"
                else:
                    step_name = "Unknown()"
            else:
                # Handle action objects
                step_name = type(step).__name__
                if hasattr(step, 'block_id'):
                    args = []
                    if hasattr(step, 'block_id'):
                        args.append(f"block={step.block_id}")
                    if hasattr(step, 'side'):
                        args.append(f"side={step.side}")
                    if hasattr(step, 'steps'):
                        args.append(f"steps={step.steps}")
                    if hasattr(step, 'need'):
                        args.append(f"need={step.need}")
                    step_name += f"({', '.join(args)})"
                    
            plan_summary.append(step_name)
        
        return " -> ".join(plan_summary) if plan_summary else "finished"
    
    def __str__(self) -> str:
        """Detailed one-line string representation for printing"""
        # Get current action
        current_action = self.get_current_action()
        symbolic_action = type(current_action).__name__ if current_action else "None"
        
        # Get progress
        plan_progress = f"{self.plan_index}/{len(self.plan_steps)}"
        if self.plan_index >= len(self.plan_steps):
            plan_progress += " (done)"
        
        # Get position
        obs = self.observe()
        pos = obs["my_position"]
        
        # Get plan summary
        plan_str = self.get_plan_summary()
        
        return f"{self.id}: {self.phase:10} | Symbolic: {symbolic_action:12} | Progress: {plan_progress:10} | Pos: {str(pos):8} | Plan: {plan_str}"


class AgentManager:
    """Simple manager for coordinating multiple BaseAgents"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.activity_log: List[Dict[str, Any]] = []
    
    def add_agent(self, agent: BaseAgent):
        """Add an agent to the manager"""
        self.agents[agent.id] = agent
        # Log initial state when agent is added (step 0)
        self._log_step_snapshot(0, "agent_added", agent.id)
    
    def _log_step_snapshot(self, step: int, event_type: str = "step_update", trigger_agent: str = None):
        """Record current state of ALL agents at given step"""
        agents_data = {}
        for agent_id, agent in self.agents.items():
            current_action = agent.get_current_action()
            agents_data[agent_id] = {
                "phase": agent.phase,
                "plan_progress": f"{agent.plan_index}/{len(agent.plan_steps)}",
                "current_action": {
                    "type": type(current_action).__name__ if current_action else None,
                    "str": str(current_action) if current_action else None
                },
                "remaining_steps": len(agent.plan_steps) - agent.plan_index
            }
        
        log_entry = {
            "step": step,
            "event_type": event_type,
            "trigger_agent": trigger_agent,  # Which agent triggered this snapshot
            "agents": agents_data
        }
        
        self.activity_log.append(log_entry)
    
    def log_step(self, step: int):
        """Log current state of all agents at given step"""
        self._log_step_snapshot(step, "step_update")
    
    def get_agent_log(self, agent_id: str = None) -> List[Dict[str, Any]]:
        """Get activity log for specific agent or all agents"""
        if agent_id:
            # Filter entries that include the specific agent
            return [entry for entry in self.activity_log if agent_id in entry.get("agents", {})]
        return self.activity_log.copy()
    
    def save_log(self, filename: str):
        """Save activity log to file"""
        with open(filename, 'w') as f:
            json.dump(self.activity_log, f, indent=2)
    
    def log_event(self, step: int, event_type: str, trigger_agent: str = None):
        """Manually log a specific event at given step"""
        self._log_step_snapshot(step, event_type, trigger_agent)
    
    def visualize_dual_timeline(self, output_file: str = None):
        """Create dual timeline visualization showing both plans and actions"""
        try:
            from .log_visualizer import create_dual_timeline_visualization
            
            # Save current log to temporary file
            temp_file = "temp_dual_log.json"
            self.save_log(temp_file)
            
            # Create dual visualization
            fig, ax = create_dual_timeline_visualization(temp_file, output_file)
            
            # Clean up temp file
            import os
            os.remove(temp_file)
            
            return fig, ax
            
        except ImportError:
            print("Visualization requires matplotlib. Install with: pip install matplotlib")
            return None, None
    
    def get_agent_states(self) -> Dict[str, dict]:
        """Get state summaries for all agents"""
        return {agent_id: agent.get_state_summary() for agent_id, agent in self.agents.items()}
    
    def get_phase_counts(self) -> Dict[str, int]:
        """Get counts of agents in each phase"""
        phase_counts = {}
        for agent in self.agents.values():
            phase = agent.phase
            phase_counts[phase] = phase_counts.get(phase, 0) + 1
        return phase_counts
    
    def all_agents_finished(self) -> bool:
        """Check if all agents have finished their plans"""
        return all(agent.phase == "finished" for agent in self.agents.values())
    
    def get_coordination_summary(self) -> str:
        """Get a summary of coordination status"""
        phase_counts = self.get_phase_counts()
        total_agents = len(self.agents)
        
        if total_agents == 0:
            return "No agents"
        
        summary_parts = []
        for phase, count in phase_counts.items():
            summary_parts.append(f"{phase}: {count}")
        
        return " | ".join(summary_parts) + f" (Total: {total_agents})"
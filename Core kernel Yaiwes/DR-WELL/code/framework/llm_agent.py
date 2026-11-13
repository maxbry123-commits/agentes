# llm_agent.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import sys
import os
import json

# Add CUBE path to import BaseAgent
cube_path = os.path.join(os.path.dirname(__file__), '..', 'CUBE')
if cube_path not in sys.path:
    sys.path.append(cube_path)

# Framework imports
# Framework imports
from cube.agent_base import BaseAgent, AgentManager
from cube.symbolic_actions import MoveToBlock, Rendezvous, Push, Wait, WaitAgents, YieldFace
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
import llm_templates as templates
from dotenv import load_dotenv
from openai import AzureOpenAI
import llm_templates as templates

# Load environment variables
load_dotenv()

# Create Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Simple print function replacement
def print_color(text: str, color: str):
    print(text)

# Note: symbolic_actions and other imports will be done dynamically where needed
LLM_INPUT_COLOR = "yellow"

@dataclass
class LLMConfig:
    model: str = "gpt-4o"   # your Azure deployment name
    temperature: float = 1
    max_tokens: int = 1000

class LLMAgent(BaseAgent):
    """
    LLM agent that inherits from BaseAgent and adds planning capabilities.
    Plans are parsed into symbolic action dataclasses the controller can execute.
    Supports communication before planning.
    Uses structured output format with Pydantic models.
    """
    
    def __init__(self, agent_id: str, env, world_model, cfg: LLMConfig, plan: List = None, enhanced_templates=None):
        super().__init__(agent_id, env, plan)
        self.world_model = world_model
        self.cfg = cfg
        self.enhanced_templates = enhanced_templates  # Store enhanced templates if provided
        
        # Task assignment (from communication)
        self.assigned_block: Optional[int] = None
        self.task_name: Optional[str] = None
        self.previous_task: Optional[str] = None

    def observe(self) -> dict:
        """
        Enhanced observation for LLM agents.
        Calls base observe method and adds additional context.
        """
        # Get base observation
        obs = super().observe()
        
        # Add any LLM-specific observation details if needed
        obs["llm_config"] = {
            "model": self.cfg.model,
            "temperature": self.cfg.temperature
        }
        
        return obs

    def _call_llm_structured(self, system_prompt: str, user_message: str, response_format, max_tokens: int = None):
        """Call Azure OpenAI with structured output"""
        try:
            response = client.beta.chat.completions.parse(
                model=self.cfg.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                response_format=response_format,
                temperature=self.cfg.temperature,
                max_tokens=max_tokens or self.cfg.max_tokens
            )
            
            return response.choices[0].message.parsed
        except Exception as e:
            print(f"[ERROR] LLM call failed for {self.id}: {e}")
            return None

    def propose_task(self, message_board) -> None:
        """Propose a block to work on during the first communication round"""
        obs = self.observe()
        
        # Calculate participant info from teammates
        participants = [self.id] + obs["teammates"]
        participants_count = len(participants)
        participants_list = ", ".join(participants)

        user_message = templates.PROPOSAL_USER_TEMPLATE.format(
            participants_count=participants_count,
            participants_list=participants_list,
            agent=obs["agent_id"],
            blocks_info=message_board.get_blocks_info_str(obs),
            agent_states=message_board.get_agent_states_str(obs),
            world_info=message_board.get_world_info_str(obs),
            proposals=message_board.get_proposals_str(),
            commitments=message_board.get_commitments_str()
        )
        
        
        # Log what we're feeding to the LLM
        print_color(f"\n[LLM_INPUT] {self.id} PROPOSAL:", LLM_INPUT_COLOR)
        print_color("=" * 60, LLM_INPUT_COLOR)
        print_color(user_message, LLM_INPUT_COLOR)
        print_color("=" * 60, LLM_INPUT_COLOR)

        proposal = self._call_llm_structured(
            templates.PROPOSAL_SYSTEM_PROMPT, 
            user_message, 
            templates.TaskProposal,
            max_tokens=300
        )
        
        if proposal:
            message_board.add_proposal(self.id, proposal.block_id, proposal.reason)
            print(f"[COMM] {self.id}: PROPOSES: Block {proposal.block_id} - {proposal.reason}")
        else:
            # Fallback proposal
            fallback_block = self._select_target_block()
            message_board.add_proposal(self.id, fallback_block, "Fallback selection")
            print(f"[COMM] {self.id}: PROPOSES (fallback): Block {fallback_block}")

    def commit_to_task(self, message_board) -> None:
        """Commit to a specific block and task during the second communication round"""
        obs = self.observe()
        proposals_summary = message_board.get_proposals_summary()
        
        # Calculate participant info from teammates
        participants = [self.id] + obs["teammates"]
        participants_count = len(participants)
        participants_list = ", ".join(participants)

        user_message = templates.COMMITMENT_USER_TEMPLATE.format(
            participants_count=participants_count,
            participants_list=participants_list,
            agent=obs["agent_id"],
            proposals_summary=proposals_summary,
            agent_states=message_board.get_agent_states_str(obs),
            world_info=message_board.get_world_info_str(obs),
            proposals=message_board.get_proposals_str(),
            commitments=message_board.get_commitments_str()
        )
        
        # Log what we're feeding to the LLM
        print_color(f"\n[LLM_INPUT] {self.id} COMMITMENT:", LLM_INPUT_COLOR)
        print_color("=" * 60, LLM_INPUT_COLOR)
        print_color(user_message, LLM_INPUT_COLOR)
        print_color("=" * 60, LLM_INPUT_COLOR)

        commitment = self._call_llm_structured(
            templates.COMMITMENT_SYSTEM_PROMPT, 
            user_message, 
            templates.TaskCommitment,
            max_tokens=300
        )
        
        if commitment:
            # Store previous task before updating current task
            if self.task_name is not None:
                self.previous_task = self.task_name
            
            # Store commitment and add to message board
            self.assigned_block = commitment.block_id
            self.task_name = commitment.task_name
            message_board.add_commitment(self.id, commitment.block_id, commitment.task_name)
        else:
            # Fallback commitment
            fallback_block = self._select_target_block()
            self.assigned_block = fallback_block
            self.task_name = f"Block_{fallback_block}"
            message_board.add_commitment(self.id, fallback_block, f"Block_{fallback_block}")

        print(f"[COMM] {self.id}: COMMITS: {self.task_name}")

    def plan(self, all_agents=None):
        """Two-stage LLM planning: generate plan → revise plan based on analysis"""
        if all_agents is None:
            all_agents = {}
        
        target_block = self.assigned_block
        task_name = self.task_name
        previous_task = self.previous_task if self.previous_task is not None else "None (first task)"
        
        # Get current observations
        obs = self.observe()
        
        user_message = templates.PLANNING_USER_TEMPLATE.format(
            agent=obs["agent_id"],
            my_position=f"({obs['my_position'][0]},{obs['my_position'][1]})" if isinstance(obs.get('my_position'), tuple) else str(obs.get('my_position', 'unknown')),
            target_block=target_block,
            task_name=task_name,
            env_info=self._get_env_info_str(obs),
            blocks_info=self._get_blocks_info(),
            other_agents_state=self._get_other_agents_state_str(obs),
            all_committed_tasks=self._get_all_committed_tasks_str(all_agents)
        )
        
        # Log what we're feeding to the LLM
        print_color(f"\n[LLM_INPUT] {self.id} PLANNING:", LLM_INPUT_COLOR)
        print_color("=" * 60, LLM_INPUT_COLOR)
        print_color(user_message, LLM_INPUT_COLOR)
        print_color("=" * 60, LLM_INPUT_COLOR)

        plan_obj = self._call_llm_structured(
            templates.PLANNING_SYSTEM_PROMPT, 
            user_message, 
            templates.AgentPlan,
            max_tokens=self.cfg.max_tokens
        )
        
        if plan_obj and plan_obj.plan:
            # Convert structured actions to simple string format for BaseAgent compatibility
            self.plan_steps = []
            for action in plan_obj.plan:
                if action.action_type.value == "MoveToBlock":
                    self.plan_steps.append(f"MoveToBlock {action.block_id} {action.side.value}")
                elif action.action_type.value == "Rendezvous":
                    self.plan_steps.append(f"Rendezvous {action.block_id} {action.side.value} {action.need} {action.timeout}")
                elif action.action_type.value == "Push":
                    self.plan_steps.append(f"Push {action.block_id} {action.steps}")
                elif action.action_type.value == "Wait":
                    self.plan_steps.append(f"Wait {action.steps}")
                elif action.action_type.value == "WaitAgents":
                    self.plan_steps.append(f"WaitAgents {action.need} {action.timeout}")
                elif action.action_type.value == "YieldFace":
                    self.plan_steps.append(f"YieldFace {action.block_id} {action.side.value} {action.steps}")
            plan_title = f"[INITIAL PLAN] {self.id}"
        else:
            # Fallback plan
            self.plan_steps = self._fallback_plan()
            plan_title = f"[FALLBACK PLAN] {self.id}"

        # Log the plan
        self.world_model.record_plan(self.id, self.plan_steps)
        self.world_model.log_communication(self.id, "ALL", f"{plan_title}: " + "; ".join(self.plan_steps))

    def _select_target_block(self) -> int:
        """Select a target block (fallback logic)"""
        if self.env._blocks:
            return self.env._blocks[0].id
        return 0

    def _fallback_plan(self) -> List[str]:
        """Generate a simple fallback plan"""
        if self.assigned_block is not None:
            return [
                f"MoveToBlock {self.assigned_block} left",
                f"Push {self.assigned_block} steps=3"
            ]
        return ["Wait 5"]

    def _get_blocks_info(self) -> str:
        """Get formatted information about available blocks"""
        if not self.env._blocks:
            return "No blocks available."
        
        goal_col = self.env.K - 1
        lines = []
        for block in self.env._blocks:
            distance_to_goal = goal_col - (block.c + block.weight - 1)
            lines.append(f"Block {block.id}: weight={block.weight}, position=({block.r},{block.c}), distance_to_goal={distance_to_goal}")
        
        return "\n".join(lines)
    
    def _get_env_info_str(self, obs: dict) -> str:
        """Create environment info string for planning"""
        grid_size = obs.get("grid_size", "?")
        total_agents = len(obs.get("agent_positions", {}))
        
        lines = [
            f"Grid: {grid_size}x{grid_size}",
            f"Goal zone: Right edge (column {grid_size-1 if isinstance(grid_size, int) else '?'})",
            f"Total agents: {total_agents}"
        ]
        
        return "\n".join(lines)
    
    def _get_other_agents_state_str(self, obs: dict) -> str:
        """Create other agents state string for planning"""
        agent_positions = obs.get("agent_positions", {})
        
        lines = []
        for agent_id, pos in agent_positions.items():
            if agent_id != self.id:  # Exclude self
                lines.append(f"{agent_id}: Position {pos}")
        
        return "\n".join(lines) if lines else "No other agent position data available"
    
    def _get_all_committed_tasks_str(self, all_agents: dict) -> str:
        """Create string of all committed tasks across agents"""
        if not all_agents:
            return "No other agent commitments available"
        
        lines = []
        for agent_id, agent in all_agents.items():
            task = getattr(agent, 'task_name', 'No_Task')
            block = getattr(agent, 'assigned_block', 'None')
            lines.append(f"{agent_id}: {task} (Block {block})")
        
        return "\n".join(lines)
    
    def should_plan(self) -> bool:
        """Determine if this agent should participate in planning"""
        # Agent should plan if:
        # 1. It has no plan yet, or
        # 2. It has finished its current plan, or
        # 3. It's in planning phase
        return (
            not self.plan_steps or 
            self.is_finished() or 
            self.phase == "planning"
        )
    
    def _clean_action_string(self, action_str: str) -> str:
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
        
        # Handle Push X steps=Y timeout=Z -> Push X steps=Y
        if "Push" in action_str and "timeout=" in action_str:
            parts = action_str.split()
            clean_parts = [p for p in parts if not p.startswith("timeout=")]
            return " ".join(clean_parts)
        
        return action_str
    
    def get_plan_as_objects(self):
        """Convert agent plan strings to symbolic action objects for SymbolicController"""
        if not self.plan_steps:
            return []
        
        # Clean the action strings first
        cleaned_plan = [self._clean_action_string(step) for step in self.plan_steps]
        print(f"[DEBUG] {self.id} cleaned plan: {cleaned_plan}")
        
        # Convert to symbolic action objects using BaseAgent.parse_step
        try:
            action_objects = []
            for step in cleaned_plan:
                action_obj = self.parse_step(step)
                action_objects.append(action_obj)
            return action_objects
        except Exception as e:
            print(f"[ERROR] Failed to convert plan for {self.id}: {e}")
            print(f"[ERROR] Plan steps: {cleaned_plan}")
            return []

    def string_to_action(self, action_str: str):
        """Convert action string to symbolic action dataclass - enhanced for LLM outputs"""
        # Use LLM templates
        import llm_templates as templates
        action = templates.string_to_action(action_str)
        # Convert structured action back to the dataclass format expected by controller
        if hasattr(action, 'action_type'):
            action_type = action.action_type.value
            if action_type == "MoveToBlock":
                return MoveToBlock(action.block_id, action.side.value)
            elif action_type == "Rendezvous":
                return Rendezvous(action.block_id, action.side.value, action.need, action.timeout)
            elif action_type == "Push":
                return Push(action.block_id, action.steps)
            elif action_type == "Wait":
                return Wait(action.steps)
            elif action_type == "WaitAgents":
                return WaitAgents(action.need, action.timeout)
            elif action_type == "YieldFace":
                return YieldFace(action.block_id, action.side.value, action.steps)
        
        return Wait(1)  # Final fallback


class LLMAgentManager(AgentManager):
    """
    Agent manager for LLM agents that inherits from AgentManager.
    Clean timestep-based logging with JSONL output for clarity.
    """
    
    def __init__(self, env):
        super().__init__()
        self.env = env
        self._communication_log = []  # Separate log for communication events
    
    def add_agent(self, agent):
        """Override to prevent excessive logging of agent additions"""
        self.agents[agent.id] = agent
        # No individual logging - agents captured in timestep snapshots
    
    def log_timestep(self, step: int, actions: Dict[str, Any]):
        """
        Canonical 't = step' log entry that aggregates agent states for this timestep.
        Prints as JSONL and stores a snapshot in activity_log.
        """
        # Build agent state snapshot
        agents_data = {}
        for agent_id, agent in self.agents.items():
            current_action = agent.get_current_action()
            full_plan = [str(a) for a in getattr(agent, 'plan_steps', [])]
            agents_data[agent_id] = {
                "phase": agent.phase,
                "plan": full_plan,
                "plan_progress": f"{agent.plan_index}/{len(agent.plan_steps)}",
                "current_action": {
                    "type": type(current_action).__name__ if current_action else None,
                    "str": str(current_action) if current_action else None
                },
                "remaining_steps": len(agent.plan_steps) - agent.plan_index,
                "committed_task": getattr(agent, 'task_name', None),
                "assigned_block": getattr(agent, 'assigned_block', None),
            }

        # Compose the timestep record
        record = {
            "t": step,
            "event_type": "timestep",
            "actions": actions,
            "agents": agents_data,
        }

        # Store and emit
        self.activity_log.append(record)

        # Pretty JSONL one-liner (easy to grep/jq)
        ### disabled debug printing
        #try:
        #    print(json.dumps(record, default=str))
        #except Exception as e:
        #    print(f"[WARN] Failed to JSON-encode timestep {step}: {e}")
    
    def log_communication_round(self, step: int, participants: List[str], communication_type: str, result: Dict[str, str] = None):
        """
        Log communication events with clean timestep tracking.
        """
        if result and len(result) > 0:
            comm_event = {
                "t": step,
                "event_type": "communication_completed",
                "communication_type": communication_type,
                "participant_count": len(participants),
                "participants": participants.copy(),
                "commitments": result.copy()
            }
            self._communication_log.append(comm_event)
            
            # Also emit as JSONL for real-time monitoring
            try:
                print(json.dumps(comm_event, default=str))
            except Exception as e:
                print(f"[WARN] Failed to JSON-encode communication {step}: {e}")
    
    def log_plan_execution_completed(self, step: int, agents_plan_results: Dict[str, Dict[str, Any]]):
        """
        Log when agents finish executing their plans with success status and block availability.
        
        Args:
            step: Current timestep
            agents_plan_results: Dict mapping agent_id -> {
                'plan_successful': bool,
                'target_block': int,
                'block_still_available': bool,
                'committed_task': str
            }
        """
        event = {
            "t": step,
            "event_type": "plan_execution_completed",
            "agents_plan_results": agents_plan_results.copy(),
            "total_agents": len(agents_plan_results)
        }
        self.activity_log.append(event)
        
        # Also emit as JSONL for real-time monitoring
        try:
            print(json.dumps(event, default=str))
        except Exception as e:
            pass  # Silently ignore JSON encoding issues
    
    # Legacy compatibility methods - now simplified
    def log_step(self, step: int):
        """Legacy compatibility - no longer logs individual step updates"""
        pass  # Step data captured in timestep logs
    
    def log_planning_completed(self, step: int, agents_with_plans: List[str]):
        """
        Log a single event when all agents have completed their planning phase.
        """
        event = {
            "t": step,
            "event_type": "planning_completed",
            "agents_with_plans": agents_with_plans.copy(),
            "total_agents": len(agents_with_plans)
        }
        self.activity_log.append(event)
        
        # Also emit as JSONL for real-time monitoring
        try:
            print(json.dumps(event, default=str))
        except Exception as e:
            print(f"[WARN] Failed to JSON-encode planning completion {step}: {e}")

    def record_plan(self, agent_id: str, plan_steps: List[str]):
        """Record agent plan for logging purposes - simplified, no individual logging"""
        pass  # Plans are captured in timestep snapshots
    
    def log_communication(self, sender: str, recipient: str, message: str):
        """Legacy compatibility for communication logging - simplified, no individual logging"""
        pass  # Communication captured in communication_completed events
    
    def get_communication_log(self) -> List[Dict]:
        """Get the communication-specific log"""
        return self._communication_log.copy()
    
    def save_complete_log(self, filename: str):
        """
        Save complete log with clean structure for visualization.
        """
        # Convert 't' back to 'step' for compatibility with existing visualization tools
        execution_timeline = []
        for entry in self.activity_log:
            converted_entry = entry.copy()
            if 't' in converted_entry:
                converted_entry['step'] = converted_entry.pop('t')
            execution_timeline.append(converted_entry)
        
        communication_events = []
        for entry in self._communication_log:
            converted_entry = entry.copy()
            if 't' in converted_entry:
                converted_entry['step'] = converted_entry.pop('t')
            communication_events.append(converted_entry)
        
        complete_log = {
            "execution_timeline": execution_timeline,
            "communication_events": communication_events,
            "summary": {
                "total_steps": len([entry for entry in execution_timeline if entry.get("event_type") == "timestep"]),
                "total_communications": len(communication_events),
                "agents": list(self.agents.keys()) if hasattr(self, 'agents') and self.agents else []
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(complete_log, f, indent=2, default=str)
    
    def convert_all_agent_plans_to_objects(self) -> Dict[str, List]:
        """Convert all agent plans to symbolic action objects for SymbolicController"""
        agent_plans_objects = {}
        for agent_id, agent in self.agents.items():
            agent_plans_objects[agent_id] = agent.get_plan_as_objects()
        return agent_plans_objects
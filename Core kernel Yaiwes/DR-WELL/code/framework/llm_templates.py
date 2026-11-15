# llm_templates.py
"""
LLM templates and structured output schemas for cooperative block-pushing agents.
Uses Pydantic models for structured output format.
"""
from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional, Union
from enum import Enum
import os

# ==========================
# Symbolic Action Schemas
# ==========================

class SymbolicActionType(str, Enum):
    MOVE_TO_BLOCK = "MoveToBlock"
    RENDEZVOUS = "Rendezvous"
    PUSH = "Push"
    WAIT = "Wait"
    WAIT_AGENTS = "WaitAgents"
    YIELD_FACE = "YieldFace"

class Side(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"

class MoveToBlockAction(BaseModel):
    action_type: Literal[SymbolicActionType.MOVE_TO_BLOCK] = SymbolicActionType.MOVE_TO_BLOCK
    block_id: int = Field(..., description="ID of the target block")
    side: Side = Field(..., description="Which face of the block to approach")
    timeout: int = Field(default=20, description="Maximum steps to spend moving to block")

class RendezvousAction(BaseModel):
    action_type: Literal[SymbolicActionType.RENDEZVOUS] = SymbolicActionType.RENDEZVOUS
    block_id: int = Field(..., description="ID of the target block")
    side: Side = Field(..., description="Which face of the block to rendezvous at")
    need: int = Field(..., description="Number of agents needed at the face")
    timeout: int = Field(..., description="Steps to wait before giving up (must be positive integer)")

class PushAction(BaseModel):
    action_type: Literal[SymbolicActionType.PUSH] = SymbolicActionType.PUSH
    block_id: int = Field(..., description="ID of the block to push")
    steps: int = Field(1, description="Number of steps to keep pushing (must be positive integer)")

class WaitAction(BaseModel):
    action_type: Literal[SymbolicActionType.WAIT] = SymbolicActionType.WAIT
    steps: int = Field(..., description="Number of steps to wait (must be positive integer)")

class WaitAgentsAction(BaseModel):
    action_type: Literal[SymbolicActionType.WAIT_AGENTS] = SymbolicActionType.WAIT_AGENTS
    need: int = Field(..., description="Number of agents that need to be idle/available")
    timeout: int = Field(..., description="Steps to wait before giving up (must be positive integer)")

class YieldFaceAction(BaseModel):
    action_type: Literal[SymbolicActionType.YIELD_FACE] = SymbolicActionType.YIELD_FACE
    block_id: int = Field(..., description="ID of the block to move away from")
    side: Side = Field(..., description="Which face to move away from")
    steps: int = Field(2, description="Number of steps to move away (must be positive integer)")

# Union type for all actions
SymbolicAction = Union[
    MoveToBlockAction, RendezvousAction, PushAction, 
    WaitAction, WaitAgentsAction, YieldFaceAction
]

# ==========================
# Communication Schemas
# ==========================

class TaskProposal(BaseModel):
    agent: str = Field(..., description="Agent ID making the proposal")
    block_id: int = Field(..., description="Proposed block ID to work on")
    reason: str = Field(..., description="Brief tactical reason for this block choice (1-2 sentences)")

class TaskCommitment(BaseModel):
    agent: str = Field(..., description="Agent ID making the commitment")
    block_id: int = Field(..., description="Block ID to commit to working on")
    task_name: str = Field(..., description="Task name should be the block_id as a string (e.g., 'Block_1', 'Block_2')")

# ==========================
# Planning Schemas
# ==========================

class AgentPlan(BaseModel):
    agent: str = Field(..., description="Agent ID")
    target_block: int = Field(..., description="Target block ID for this plan")
    task_name: str = Field(..., description="Task name should be the block_id as a string (e.g., 'Block_1', 'Block_2')")
    plan: List[SymbolicAction] = Field(..., description="Sequence of symbolic actions")

    @field_validator("plan", mode="after")
    @classmethod
    def validate_non_empty_plan(cls, v: List[SymbolicAction]) -> List[SymbolicAction]:
        if not v:
            raise ValueError("Plan cannot be empty. Must include at least one action.")
        return v

class RevisionOutput(BaseModel):
    """Response format for plan revision phase"""
    plan: List[SymbolicAction] = Field(..., description="Revised sequence of symbolic actions")
    reflection: str = Field(..., description="Concise, generic bullet-point guidelines using imperative language (e.g., 'Coordinate pushes using Rendezvous...', 'Prefer faces that push blocks toward goal...'). Focus on actionable rules for any agent that you are fairly confident about. Empty reflection is acceptable if no confident insights. Will be appended to shared guidance file.")

    @field_validator("plan", mode="after")
    @classmethod
    def validate_non_empty_plan(cls, v: List[SymbolicAction]) -> List[SymbolicAction]:
        if not v:
            raise ValueError("Revised plan cannot be empty. Must include at least one action.")
        return v

# ==========================
# System Prompts
# ==========================

PLANNING_SYSTEM_PROMPT = """You are a cooperative planner for a block-pushing team.

Environment rules (do not restate in the plan):
- The world is a grid.
- Each block is a w by w square with weight w.
- A block of weight w requires w simultaneous pushers on its face to move it 1 cell in the opposite direction.
- Goal: push blocks into the goal zone using the fewest possible steps.
- The goal zone is the RIGHTMOST column. Prefer rightward progress when reasonable (e.g., move to the left of a block, then push it right).

Available symbolic actions:
- MoveToBlock: The agent moves to align with the specified block face.
- Rendezvous: The agent waits at the current position until the specified number of agents gather at the block face.
- Push: Push the specified block n steps in the direction opposite the block face. Probably with n = dist_to_goal
- Wait: Remain in place for a specified number of steps.
- WaitAgents: Wait until the specified number of other agents are available to communicate for task allocation.
- YieldFace: Move away from the specified block face.

Coordination tips:
- MoveToBlock is typically called BEFORE rendezvous to move the agent into position.
- Rendezvous is typically called BEFORE Push to synchronize agents at the block face in the same plan, followed by Push n steps to move the block toward the goal zone.
- WaitAgents enables group negotiation and ensures other agents are available for collaboration. It should only be called as the entire plan.
- Push n steps to push the block to the goal zone.
- Coordinate pushes using Rendezvous to ensure enough pushers are synchronized.
- Prefer faces that push blocks toward the goal (e.g., pushing from the left face moves the block right).
- Agents communicate for task allocation.
- Keep plans short and executable (3 actions) that can succeed from the current state.
- Empty plans are not allowed.
Return the plan as a structured response following the specified schema."""

# 

REVISION_SYSTEM_PROMPT = """You are a cooperative planner revising your plan based on additional information.

Environment rules (do not restate in the plan):
- The world is a grid.
- Each block is a w by w square with weight w.
- A block of weight w requires w simultaneous pushers on its face to move it 1 cell in the opposite direction.
- Goal: push blocks into the goal zone using the fewest possible steps.
- The goal zone is the RIGHTMOST column. Prefer rightward progress when reasonable.

Available symbolic actions:
- MoveToBlock: The agent moves to align with the specified block face.
- Rendezvous: The agent waits at the current position until the specified number of agents gather at the block face.
- Push: Push the specified block n steps in the direction opposite the block face. Probably with n = dist_to_goal
- Wait: Remain in place for a specified number of steps.
- WaitAgents: Wait until the specified number of other agents are available to communicate for task allocation.
- YieldFace: Move away from the specified block face.

Your task:
1. Review your previous plan and all available information including extra info from the shared file
2. Generate a revised plan based on new insights
3. Provide a reflection with bullet points that:
   - Can clarify earlier understanding or add new realizations
   - Should reference earlier knowledge by numbers when applicable
   - Will be appended to the shared file for other agents to see

Coordination tips:
- Work with blocks closer to goal first.
- MoveToBlock is typically called BEFORE rendezvous to move the agent into position.
- Rendezvous is typically called BEFORE Push to synchronize agents at the block face in the same plan, followed by Push n steps to move the block toward the goal zone.
- WaitAgents enables group negotiation and ensures other agents are available for collaboration. It should only be called as the entire plan.
- Push n steps to push the block to the goal zone.
- Coordinate pushes using Rendezvous to ensure enough pushers are synchronized.
- Prefer faces that push blocks toward the goal (e.g., pushing from the left face moves the block right).
- Agents communicate for task allocation.
- Keep plans short and executable (3–6 actions) that can succeed from the current state.
- Empty plans are not allowed.
   
Return both the revised plan and reflection as a structured response."""


PROPOSAL_SYSTEM_PROMPT = """You are analyzing the current state to propose which block your team should work on.
CRITICAL CONSTRAINT: You may ONLY propose blocks that are currently available and have not been completed yet. Do not propose blocks that are no longer in the environment.

Strategic considerations:
- Block availability: Only consider blocks listed in the "Available blocks" section
- Block weights: Heavier blocks (weight > 1) require coordinated team effort
- Block positions: Consider distance to goal (rightmost column) and current block location
- Team coordination: Assess if your team can realistically coordinate on the proposed block
- Resource efficiency: Balance effort required vs. progress toward goal
- Historical performance: PRIORITIZE blocks with higher historical success rates and avoid those with consistently poor performance
- Exploration vs. Exploitation: Your PRIMARY goal is to successfully push blocks to completion. Balance between trying proven successful strategies (exploitation) and experimenting with new approaches or unexplored blocks (exploration) to discover better methods. Once success is achieved consistently, then focus on efficiency improvements.

Evaluation criteria:
- Block availability: MUST be in the current available blocks list
- Historical success: Strongly favor blocks with proven success rates and avoid blocks with 0% success
- Exploration balance: Consider occasionally trying blocks with limited data or new strategies to discover better approaches. Remember: SUCCESS FIRST, then efficiency - prioritize completing blocks successfully before optimizing for speed
- Team coordination: Check if enough agents are already working on a block - if so, consider working on a different block to avoid redundancy
- Proximity to goal: Blocks closer to the right edge need less total movement
- Coordination feasibility: Can your team realistically gather enough agents for heavy blocks based on optimal team sizes?
- Strategic timing: Is this the right time to tackle this block given current positions and historical timing patterns?

Use the historical task performance data to make informed decisions. If a block has never been successfully completed (0% success rate), consider whether your team can try a new strategy or if it's better to focus on more promising blocks first. Balance exploitation of known successful strategies with exploration of new approaches that might lead to breakthrough improvements. REMEMBER: Your primary objective is successful block completion - efficiency optimization comes after achieving consistent success.

Provide a brief, tactical reason (1-2 sentences) explaining why this block choice makes strategic sense given both current situation AND historical performance data, including whether you're exploiting proven success or exploring for potential improvements. Focus on success first, then efficiency.
Return your proposal as a structured response with the specified schema."""

COMMITMENT_SYSTEM_PROMPT = """Based on the team's proposals, decide which block to commit to working on.
You will see all team proposals. Choose a block that:
- Aligns with team consensus or represents the best strategic option
- Consider diversification: If enough agents are already working on the same block and are likely to succeed, work on a different block to maximize overall progress
- Matches your capabilities and current position
- Enables effective team coordination without redundancy
- Maximizes collective progress toward the goal

For the task_name field, simply use the format "Block_{block_id}" (e.g., "Block_1", "Block_2", etc.).
Return your commitment as a structured response with the specified schema."""

# ==========================
# User Message Templates
# ==========================

PLANNING_USER_TEMPLATE = """Agent ID: {agent}
My position: {my_position}
Target block: {target_block}
Current task: {task_name}

=== ENVIRONMENT INFO ===
{env_info}

=== BLOCK POSITIONS ===
{blocks_info}

=== OTHER AGENTS STATE ===
{other_agents_state}

=== COMMITTED TASKS FOR ALL AGENTS ===
{all_committed_tasks}

Create a plan composed of symbolic actions. Assume best response from other agents (being fully cooperative).

"""

REVISION_USER_TEMPLATE = """Agent ID: {agent}
My position: {my_position}
Target block: {target_block}
Current task: {task_name}

=== ENVIRONMENT INFO ===
{env_info}

=== BLOCK POSITIONS ===
{blocks_info}

=== OTHER AGENTS STATE ===
{other_agents_state}

=== COMMITTED TASKS FOR ALL AGENTS ===
{all_committed_tasks}

=== PREVIOUS PLAN ===
{previous_plan}

=== EXTRA INFO FROM SHARED FILE ===
{file_text}

Based on all the above information, revise your plan and provide new insights. Your reflection should be concise, generic, rule-style bullet points using imperative language (e.g., "Avoid X", "Prioritize Y", "Consider Z when..."). Focus on actionable guidelines that could help any agent, not agent-specific observations. Keep each bullet point brief and only include insights you are fairly confident about - it's perfectly acceptable to provide an empty reflection if you don't have confident new guidance. These will be appended to the shared file as general guidance.

"""

PROPOSAL_USER_TEMPLATE = """=== COMMUNICATION ROOM ===
Participants: {participants_count} agents - {participants_list}

Agent ID: {agent}
Available blocks and their properties:
{blocks_info}
Agent states:
{agent_states}
World info:
{world_info}
Proposals:
{proposals}
Commitments:
{commitments}

Based on the historical performance data shown above, propose which block your team should prioritize working on. IMPORTANT: Only propose blocks that are still available and have not been completed yet (shown in "Available blocks" section above). Pay special attention to blocks with higher success rates and avoid blocks that have consistently failed (0% success rate) unless you have a compelling new strategy."""

COMMITMENT_USER_TEMPLATE = """=== COMMUNICATION ROOM ===
Participants: {participants_count} agents - {participants_list}

Agent ID: {agent}
{proposals_summary}
Agent states:
{agent_states}
World info:
{world_info}
Proposals:
{proposals}
Commitments:
{commitments}

Based on the proposals above, commit to a specific block and task specialization."""

# ==========================
# Utility Functions
# ==========================

def action_to_string(action: Union[MoveToBlockAction, RendezvousAction, PushAction, WaitAction, WaitAgentsAction, YieldFaceAction], grid_size: int) -> str:
    """Convert action object to string format"""
    if isinstance(action, MoveToBlockAction):
        timeout = 6 * grid_size  # Increased from 4 to 6 for better navigation
        return f"MoveToBlock {action.block_id} {action.side.value} timeout={timeout}"
    elif isinstance(action, RendezvousAction):
        # Rendezvous includes timeout from LLM
        return f"Rendezvous {action.block_id} {action.side.value} need={action.need} timeout={action.timeout}"
    elif isinstance(action, PushAction):
        timeout = 6 * grid_size  # Increased from 4 to 6 for better coordination
        return f"Push {action.block_id} steps={action.steps} timeout={timeout}"
    elif isinstance(action, WaitAction):
        timeout = 6 * grid_size  # Increased from 4 to 6 for better timing
        return f"Wait steps={action.steps} timeout={timeout}"
    elif isinstance(action, WaitAgentsAction):
        # WaitAgents includes timeout from LLM
        return f"WaitAgents need={action.need} timeout={action.timeout}"
    elif isinstance(action, YieldFaceAction):
        timeout = 6 * grid_size  # Increased from 4 to 6 for better movement
        return f"YieldFace {action.block_id} {action.side.value} steps={action.steps} timeout={timeout}"
    else:
        raise ValueError(f"Unknown action type: {type(action)}")

def string_to_action(action_str: str) -> SymbolicAction:
    """Convert a string action to the structured format."""
    parts = action_str.split()
    action_type = parts[0]
    
    # Helper function to parse key=value parameters
    def parse_param(param_str: str) -> tuple[str, str]:
        if '=' in param_str:
            key, value = param_str.split('=', 1)
            return key, value
        return param_str, param_str
    
    if action_type == "MoveToBlock":
        # Parse "MoveToBlock <block_id> <side> timeout=<T>"
        block_id = int(parts[1])
        side = Side(parts[2])
        return MoveToBlockAction(block_id=block_id, side=side)
        
    elif action_type == "Rendezvous":
        # Parse both formats:
        # Old: "Rendezvous <block_id> <side> need=<k> timeout=<T>"
        # New: "Rendezvous <block_id> <side> <k> <T>"
        block_id = int(parts[1])
        side = Side(parts[2])
        
        if len(parts) >= 5 and 'need=' in parts[3]:
            # Old format: "Rendezvous 1 left need=2 timeout=5"
            need = int(parts[3].split('=')[1])
            timeout = int(parts[4].split('=')[1])
        elif len(parts) >= 5:
            # New format: "Rendezvous 1 left 2 5"
            need = int(parts[3])
            timeout = int(parts[4])
        elif len(parts) == 4:
            # Minimal format: "Rendezvous 1 left 2"
            need = int(parts[3])
            timeout = 5  # Default timeout
        else:
            # Fallback
            need = 1
            timeout = 5
            
        return RendezvousAction(
            block_id=block_id,
            side=side,
            need=need,
            timeout=timeout
        )
        
    elif action_type == "Push":
        # Parse both formats:
        # Old: "Push <block_id> steps=<N> timeout=<T>"
        # New: "Push <block_id> <N>"
        block_id = int(parts[1])
        
        if len(parts) >= 3 and 'steps=' in parts[2]:
            # Old format: "Push 2 steps=4"
            steps = int(parts[2].split('=')[1])
        elif len(parts) >= 3:
            # New format: "Push 2 4"
            steps = int(parts[2])
        else:
            # Fallback
            steps = 1
            
        return PushAction(block_id=block_id, steps=steps)
        
    elif action_type == "Wait":
        # Parse both formats:
        # Old: "Wait steps=<N> timeout=<T>"  
        # New: "Wait <N>"
        if len(parts) >= 2 and 'steps=' in parts[1]:
            # Old format: "Wait steps=5"
            steps = int(parts[1].split('=')[1])
        elif len(parts) >= 2:
            # New format: "Wait 5"
            steps = int(parts[1])
        else:
            # Fallback
            steps = 1
            
        return WaitAction(steps=steps)
        
    elif action_type == "WaitAgents":
        # Parse both formats:
        # Old: "WaitAgents need=<k> timeout=<T>"
        # New: "WaitAgents <k> <T>"
        if len(parts) >= 2 and 'need=' in parts[1]:
            # Old format: "WaitAgents need=2 timeout=5"
            need = int(parts[1].split('=')[1])
            timeout = int(parts[2].split('=')[1]) if len(parts) >= 3 else 5
        elif len(parts) >= 3:
            # New format: "WaitAgents 2 5"
            need = int(parts[1])
            timeout = int(parts[2])
        elif len(parts) >= 2:
            # Minimal format: "WaitAgents 2"
            need = int(parts[1])
            timeout = 5
        else:
            # Fallback
            need = 1
            timeout = 5
            
        return WaitAgentsAction(need=need, timeout=timeout)
        
    elif action_type == "YieldFace":
        # Parse both formats:
        # Old: "YieldFace <block_id> <side> steps=<N> timeout=<T>"
        # New: "YieldFace <block_id> <side> <N>"
        block_id = int(parts[1])
        side = Side(parts[2])
        
        if len(parts) >= 4 and 'steps=' in parts[3]:
            # Old format: "YieldFace 1 left steps=3"
            steps = int(parts[3].split('=')[1])
        elif len(parts) >= 4:
            # New format: "YieldFace 1 left 3"
            steps = int(parts[3])
        else:
            # Fallback
            steps = 1
            
        return YieldFaceAction(
            block_id=block_id,
            side=side,
            steps=steps
        )
    else:
        raise ValueError(f"Unknown action type: {action_type}")


# ========================================
# ENHANCED TEMPLATE CLASSES
# ========================================

from retriever import UniverseRetriever
from typing import Optional

class EnhancedTemplates:
    """Enhanced template class that adds retriever-based insights to original templates"""
    
    def __init__(self, universe_json_path: str = None):
        """
        Initialize with optional retriever for historical insights
        
        Args:
            universe_json_path: Path to universe graph JSON file. If None, enhanced features disabled.
        """
        self.universe_json_path = universe_json_path
        self.retriever = None
        
        # Initialize retriever if path provided and valid
        if universe_json_path and os.path.exists(universe_json_path):
            try:
                self.retriever = UniverseRetriever(universe_json_path=universe_json_path)
                print(f"[ENHANCED] Retriever initialized with {universe_json_path}")
            except Exception as e:
                print(f"[ENHANCED] Failed to initialize retriever: {e}")
                self.retriever = None
        else:
            print("[ENHANCED] Running without historical insights")

    def get_enhanced_planning_user_template(self, **kwargs) -> str:
        """Get enhanced planning template with historical insights"""
        
        # Start with the original template
        base_template = PLANNING_USER_TEMPLATE.format(**kwargs)
        
        # Add enhanced insights if retriever is available
        if self.retriever:
            enhanced_context = self._get_historical_insights(
                task_name=kwargs.get('task_name'),
                target_block=kwargs.get('target_block'),
                team_size=kwargs.get('team_size'),
                context_type="planning"
            )
            
            if enhanced_context:
                # Insert enhanced context before the main planning request
                insertion_point = base_template.find("Create a plan")
                if insertion_point != -1:
                    enhanced_template = (
                        base_template[:insertion_point] + 
                        enhanced_context + 
                        "\n" + 
                        base_template[insertion_point:]
                    )
                    return enhanced_template
        
        return base_template

    def get_enhanced_communication_user_template(self, **kwargs) -> str:
        """Get enhanced communication template with historical insights"""
        
        # Start with the original template  
        base_template = PROPOSAL_USER_TEMPLATE.format(**kwargs)
        
        # Add enhanced insights if retriever is available
        if self.retriever:
            enhanced_context = self._get_historical_insights(
                context_type="communication",
                **kwargs
            )
            
            if enhanced_context:
                # Insert enhanced context after world info but before proposals
                insertion_point = base_template.find("Proposals:")
                if insertion_point != -1:
                    enhanced_template = (
                        base_template[:insertion_point] + 
                        enhanced_context + 
                        "\nProposals:" + 
                        base_template[insertion_point + len("Proposals:"):]
                    )
                    return enhanced_template
        
        return base_template

    def get_enhanced_revision_user_template(self, **kwargs) -> str:
        """Get enhanced revision template with historical insights"""
        
        # Start with the original revision template
        base_template = REVISION_USER_TEMPLATE.format(**kwargs)
        
        # Add enhanced insights if retriever is available
        if self.retriever:
            enhanced_context = self._get_historical_insights(
                task_name=kwargs.get('task_name'),
                target_block=kwargs.get('target_block'),
                team_size=kwargs.get('team_size'),
                context_type="planning"  # Use same context type as planning for revision
            )
            
            if enhanced_context:
                # Insert enhanced context after the previous plan but before the revision request
                insertion_point = base_template.find("Based on all the above information")
                if insertion_point != -1:
                    enhanced_template = (
                        base_template[:insertion_point] + 
                        enhanced_context + 
                        "\n" + 
                        base_template[insertion_point:]
                    )
                    return enhanced_template
        
        return base_template

    def _get_historical_insights(self, context_type: str, **kwargs) -> str:
        """Generate historical insights based on context type"""
        if not self.retriever:
            return ""
        
        print(f"[HISTORICAL_INSIGHTS] Retrieving {context_type} insights...")
        
        try:
            if context_type == "planning":
                # Planning-specific insights
                task_name = kwargs.get('task_name', '')
                target_block = kwargs.get('target_block', 0)
                team_size = kwargs.get('team_size', 1)
                
                print(f"[HISTORICAL_INSIGHTS] Planning context: task={task_name}, target_block={target_block}, team_size={team_size}")
                
                if task_name:
                    # Extract block name from task name
                    if 'Block_' in task_name:
                        block_name = task_name
                    else:
                        block_name = f"Block_{target_block}"
                    
                    # Get plan prototypes and their success rates for this specific task
                    insights = []
                    insights.append(f"=== PLAN EXECUTION INSIGHTS FOR {task_name} ===")
                    
                    # Get detailed plan feedback for this task
                    plan_feedback = self.retriever.get_plan_feedback(block_name, team_size=team_size)
                    relevant_attempts = plan_feedback.get("relevant_attempts", [])
                    
                    if relevant_attempts:
                        insights.append(f"Historical Plan Prototypes (sorted by success rate):")
                        
                        # Get actual plan prototypes with symbolic actions
                        plan_prototypes = self.retriever.get_plan_prototypes(task_name=block_name)
                        prototypes = plan_prototypes.get("plan_prototypes", {})
                        
                        if prototypes:
                            for i, (prototype_key, prototype_data) in enumerate(prototypes.items(), 1):
                                success_rate = prototype_data.get("success_rate", 0)
                                attempts = prototype_data.get("attempts", 0)
                                avg_duration = prototype_data.get("avg_duration")
                                avg_team_size = prototype_data.get("avg_team_size")
                                symbolic_actions = prototype_data.get("symbolic_actions", [])
                                
                                # Format symbolic actions
                                actions_str = " -> ".join(symbolic_actions) if symbolic_actions else "empty_plan"
                                duration_str = f"average duration {avg_duration:.1f} steps" if avg_duration else "unknown duration"
                                team_size_str = f"average team size {avg_team_size:.1f} agents" if avg_team_size else "unknown team size"
                                
                                insights.append(f"  {i}. Success rate: {success_rate:.1%} | {team_size_str} | {duration_str}")
                                insights.append(f"     Prototype: {actions_str}")
                        else:
                            insights.append(f"  No plan prototypes found for {task_name}")
                    
                    # Second phase: Detailed instance analysis
                    plan_instances = self.retriever.get_plan_instances(task_name=block_name)
                    instances = plan_instances.get("plan_instances", {})
                    
                    if instances:
                        insights.append(f"\nDetailed Plan Instances (sorted by success then duration):")
                        
                        for i, (plan_key, instance_data) in enumerate(instances.items(), 1):
                            success_rate = instance_data.get("success_rate", 0)
                            attempts = instance_data.get("attempts", 0)
                            avg_duration = instance_data.get("avg_duration")
                            plan = instance_data.get("plan", [])
                            
                            # Format plan with arguments
                            plan_str = " -> ".join(plan) if plan else "empty_plan"
                            duration_str = f"{avg_duration:.1f} steps" if avg_duration else "unknown duration"
                            
                            insights.append(f"  {i}. Success rate: {success_rate:.1%} | Attempts: {attempts} | Duration: {duration_str}")
                            insights.append(f"     Plan: {plan_str}")
                    
                    else:
                        insights.append(f"No historical execution data for {task_name}")
                        insights.append(f"This task has never been attempted before - you're pioneering new strategies!")
                    
                    if len(insights) > 1:
                        result = "\n" + "\n".join(insights) + "\n"
                        print(f"[HISTORICAL_INSIGHTS] Planning insights found: {len(insights)-1} insight sections")
                        return result
            
            elif context_type == "communication":
                # Communication effectiveness insights for decision making
                insights = []
                
                # 1. Block timing analysis with performance data
                insights.append("=== HISTORICAL TASK PERFORMANCE ===")
                timing_analysis = self.retriever.get_block_timing_analysis()
                block_stats = timing_analysis.get("block_timing_analysis", {})
                
                if block_stats:
                    # Show block performance summary
                    for block_name, stats in block_stats.items():
                        performance = stats.get("performance", {})
                        success_rate = performance.get("success_rate", 0)
                        total_attempts = performance.get("total_attempts", 0)
                        min_agents_needed = performance.get("min_agents_needed", "UNKNOWN")
                        avg_task_duration = performance.get("avg_task_duration", "UNKNOWN")
                        
                        # Format duration
                        duration_str = f"{avg_task_duration:.1f} steps" if isinstance(avg_task_duration, (int, float)) else str(avg_task_duration)
                        
                        insights.append(f"  {block_name}: {success_rate:.1%} success rate ({total_attempts} attempts)")
                        insights.append(f"    - Requires minimum {min_agents_needed} agents")
                        insights.append(f"    - Average completion time: {duration_str}")
                    
                    # 2. Optimal team size recommendations
                    insights.append("\n=== OPTIMAL TEAM SIZE RECOMMENDATIONS ===")
                    for block_name, stats in block_stats.items():
                        total_successes = stats['performance'].get('total_successes', 0)
                        success_rate = stats['performance'].get('success_rate', 0)
                        
                        if total_successes > 0:
                            # Get detailed plan feedback for optimal team size analysis
                            plan_feedback = self.retriever.get_plan_feedback(block_name)
                            
                            if plan_feedback.get("optimal_team_sizes"):
                                # Find the best team size across all contexts
                                best_success_rate = 0
                                optimal_k = "UNKNOWN"
                                
                                # Look through relevant attempts to find best performing team size
                                relevant_attempts = plan_feedback.get("relevant_attempts", [])
                                if relevant_attempts:
                                    best_entry = max(relevant_attempts, key=lambda x: x.get("completion_rate", 0))
                                    best_success_rate = best_entry.get("completion_rate", 0)
                                    # Extract team size from signature if available
                                    signature = best_entry.get("signature", "")
                                    if "|k=" in signature:
                                        try:
                                            optimal_k = int(signature.split("|k=")[1].split("|")[0])
                                        except (ValueError, IndexError):
                                            optimal_k = "UNKNOWN"
                                
                                insights.append(f"  {block_name}: optimal team size = {optimal_k} agents (success rate: {best_success_rate:.1%})")
                            else:
                                # Use minimum completed team size if no optimal team sizes found
                                min_agents = stats['performance'].get('min_agents_needed', 'UNKNOWN')
                                insights.append(f"  {block_name}: optimal team size = {min_agents} agents (success rate: {success_rate:.1%})")
                        else:
                            # No successful completions - cannot determine optimal team size
                            insights.append(f"  {block_name}: optimal team size = UNKNOWN (no successful completions yet)")
                    
                    # 3. Communication effectiveness by block type
                    insights.append("\n=== COMMUNICATION EFFECTIVENESS BY BLOCK ===")
                    for block_name, stats in block_stats.items():
                        performance = stats.get("performance", {})
                        success_rate = performance.get("success_rate", 0)
                        total_attempts = performance.get("total_attempts", 0)
                        
                        if total_attempts > 0:
                            # Categorize effectiveness
                            if success_rate > 0.7:
                                effectiveness = "HIGHLY EFFECTIVE"
                            elif success_rate > 0.4:
                                effectiveness = "MODERATELY EFFECTIVE"
                            elif success_rate > 0.1:
                                effectiveness = "CHALLENGING"
                            else:
                                effectiveness = "NEEDS NEW STRATEGY"
                            
                            insights.append(f"  {block_name}: {effectiveness} - {success_rate:.1%} success over {total_attempts} attempts")
                        else:
                            insights.append(f"  {block_name}: UNTESTED - No previous attempts recorded")
                else:
                    insights.append("  No block timing data available")
                
                if len(insights) > 1:
                    result = "\n" + "\n".join(insights) + "\n"
                    print(f"[HISTORICAL_INSIGHTS] Communication insights found: {len(insights)-1} insight sections")
                    return result
                    
        except Exception as e:
            print(f"[HISTORICAL_INSIGHTS] Error getting insights: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"[HISTORICAL_INSIGHTS] No insights found for {context_type} context")
        return ""

    # Convenience methods that delegate to original functions but can be enhanced later
    def get_planning_user_template(self, **kwargs) -> str:
        """Get planning template (enhanced if retriever available)"""
        if self.retriever:
            return self.get_enhanced_planning_user_template(**kwargs)
        else:
            return PLANNING_USER_TEMPLATE.format(**kwargs)
    
    def get_communication_user_template(self, **kwargs) -> str:
        """Get communication template (enhanced if retriever available)"""
        if self.retriever:
            return self.get_enhanced_communication_user_template(**kwargs)
        else:
            return PROPOSAL_USER_TEMPLATE.format(**kwargs)
    
    def get_planning_system_template(self) -> str:
        """Get planning system template"""
        return PLANNING_SYSTEM_PROMPT
    
    def get_communication_system_template(self) -> str:
        """Get communication system template"""
        return PROPOSAL_SYSTEM_PROMPT
        
    def parse_action_from_response(self, response: str):
        """Parse action from LLM response"""
        return string_to_action(response)


# Convenience function to create enhanced templates
def create_enhanced_templates(universe_json_path: str = None) -> EnhancedTemplates:
    """Create enhanced templates with optional historical insights"""
    return EnhancedTemplates(universe_json_path)

# llm_agent_enhanced.py
"""
Enhanced LLM agent that inherits from the original LLMAgent and adds retriever-based insights.
The original LLMAgent class remains untouched - this extends it with historical learning.
"""

from llm_agent import LLMAgent, LLMAgentManager, LLMConfig
from llm_templates import EnhancedTemplates
import llm_templates as templates
from typing import List, Optional, Dict, Any
from utils import print_color, print_agent_action, print_stage_separator, print_success, print_error, print_info

class EnhancedLLMAgent(LLMAgent):
    """
    Enhanced LLM agent that inherits from LLMAgent and adds retriever-based insights.
    Provides historical performance data to improve planning and communication decisions.
    """
    
    def __init__(self, agent_id: str, env, world_model, cfg: LLMConfig, plan: List = None, 
                 universe_json_path: str = None):
        """
        Initialize enhanced LLM agent.
        
        Args:
            agent_id: Agent identifier
            env: Environment instance
            world_model: World model instance  
            cfg: LLM configuration
            plan: Initial plan (optional)
            universe_json_path: Path to universe graph JSON for historical insights
        """
        super().__init__(agent_id, env, world_model, cfg, plan)
        
        # Initialize enhanced templates with retriever
        self.enhanced_templates = EnhancedTemplates(universe_json_path)
        self.universe_json_path = universe_json_path
        
        # Track if we have historical insights available
        self.has_historical_insights = self.enhanced_templates.retriever is not None
        
        if self.has_historical_insights:
            print_success(f"{self.id}: Historical insights enabled")
        else:
            print_info(f"{self.id}: Using original templates (no historical data)")

    def propose_task(self, message_board) -> None:
        """Enhanced task proposal with historical performance insights"""
        obs = self.observe()
        
        # Calculate participant info from teammates
        participants = [self.id] + obs["teammates"]
        participants_count = len(participants)
        participants_list = ", ".join(participants)

        # Prepare template arguments
        template_kwargs = {
            "participants_count": participants_count,
            "participants_list": participants_list,
            "agent": obs["agent_id"],
            "blocks_info": message_board.get_blocks_info_str(obs),
            "agent_states": message_board.get_agent_states_str(obs),
            "world_info": message_board.get_world_info_str(obs),
            "proposals": message_board.get_proposals_str(),
            "commitments": message_board.get_commitments_str()
        }

        # Use enhanced template if available, otherwise fall back to original
        if self.has_historical_insights:
            user_message = self.enhanced_templates.get_communication_user_template(**template_kwargs)
            system_prompt = templates.PROPOSAL_SYSTEM_PROMPT
            print(f"[ENHANCED] {self.id}: Using enhanced proposal template with historical insights")
        else:
            user_message = templates.PROPOSAL_USER_TEMPLATE.format(**template_kwargs)
            system_prompt = templates.PROPOSAL_SYSTEM_PROMPT
        
        # Log what we're feeding to the LLM
        from llm_agent import print_color, LLM_INPUT_COLOR
        print_color(f"\n[LLM_INPUT] {self.id} ENHANCED PROPOSAL:", LLM_INPUT_COLOR)
        print_color("=" * 60, LLM_INPUT_COLOR)
        print_color(user_message, LLM_INPUT_COLOR)
        print_color("=" * 60, LLM_INPUT_COLOR)

        proposal = self._call_llm_structured(
            system_prompt, 
            user_message, 
            templates.TaskProposal,
            max_tokens=400  # Slightly more tokens for enhanced reasoning
        )
        
        if proposal:
            message_board.add_proposal(self.id, proposal.block_id, proposal.reason)
            reason_preview = proposal.reason[:100] + "..." if len(proposal.reason) > 100 else proposal.reason
            print_agent_action(self.id, "PROPOSES", f"Block {proposal.block_id} - {reason_preview}", 'communication_proposal')
        else:
            # Fallback proposal
            fallback_block = self._select_target_block()
            message_board.add_proposal(self.id, fallback_block, "Fallback selection")
            print_agent_action(self.id, "PROPOSES (fallback)", f"Block {fallback_block}", 'communication_proposal')

    def commit_to_task(self, message_board) -> None:
        """Enhanced task commitment with historical performance insights"""
        obs = self.observe()
        proposals_summary = message_board.get_proposals_summary()
        
        # Calculate participant info from teammates
        participants = [self.id] + obs["teammates"]
        participants_count = len(participants)
        participants_list = ", ".join(participants)

        # Prepare template arguments
        template_kwargs = {
            "participants_count": participants_count,
            "participants_list": participants_list,
            "agent": obs["agent_id"],
            "proposals_summary": proposals_summary,
            "blocks_info": message_board.get_blocks_info_str(obs),
            "agent_states": message_board.get_agent_states_str(obs),
            "world_info": message_board.get_world_info_str(obs),
            "proposals": message_board.get_proposals_str(),
            "commitments": message_board.get_commitments_str()
        }

        # Use enhanced template if available, otherwise fall back to original
        if self.has_historical_insights:
            user_message = self.enhanced_templates.get_communication_user_template(**template_kwargs)
            system_prompt = templates.COMMITMENT_SYSTEM_PROMPT
            print(f"[ENHANCED] {self.id}: Using enhanced commitment template with historical insights")
        else:
            user_message = templates.COMMITMENT_USER_TEMPLATE.format(**template_kwargs)
            system_prompt = templates.COMMITMENT_SYSTEM_PROMPT
        
        # Log what we're feeding to the LLM
        from llm_agent import print_color, LLM_INPUT_COLOR
        print_color(f"\n[LLM_INPUT] {self.id} ENHANCED COMMITMENT:", LLM_INPUT_COLOR)
        print_color("=" * 60, LLM_INPUT_COLOR)
        print_color(user_message, LLM_INPUT_COLOR)
        print_color("=" * 60, LLM_INPUT_COLOR)

        commitment = self._call_llm_structured(
            system_prompt, 
            user_message, 
            templates.TaskCommitment,
            max_tokens=400  # Slightly more tokens for enhanced reasoning
        )
        
        if commitment:
            # Store previous task before updating current task
            if self.task_name is not None:
                self.previous_task = self.task_name
            
            # Store commitment and add to message board
            self.assigned_block = commitment.block_id
            self.task_name = commitment.task_name
            message_board.add_commitment(self.id, commitment.block_id, commitment.task_name)
            print_agent_action(self.id, "COMMITS", commitment.task_name, 'communication_commit')
        else:
            # Fallback commitment
            fallback_block = self._select_target_block()
            self.assigned_block = fallback_block
            self.task_name = f"Block_{fallback_block}"
            message_board.add_commitment(self.id, fallback_block, f"Block_{fallback_block}")
            print_agent_action(self.id, "COMMITS (fallback)", self.task_name, 'communication_commit')

        print(f"[COMM] {self.id}: COMMITS: {self.task_name}")

    def plan(self, all_agents=None):
        """Enhanced planning with historical insights and two-stage revision"""
        if all_agents is None:
            all_agents = {}
        
        target_block = self.assigned_block
        task_name = self.task_name
        previous_task = self.previous_task if self.previous_task is not None else "None (first task)"
        
        # Get current observations
        obs = self.observe()
        
        # Estimate team size for insights
        team_size = len([a for a in all_agents.values() if getattr(a, 'assigned_block', None) == target_block])
        
        # Prepare template arguments
        template_kwargs = {
            "agent": obs["agent_id"],
            "my_position": f"({obs['my_position'][0]},{obs['my_position'][1]})" if isinstance(obs.get('my_position'), tuple) else str(obs.get('my_position', 'unknown')),
            "target_block": target_block,
            "task_name": task_name,
            "team_size": team_size,
            "env_info": self._get_env_info_str(obs),
            "blocks_info": self._get_blocks_info(),
            "other_agents_state": self._get_other_agents_state_str(obs),
            "all_committed_tasks": self._get_all_committed_tasks_str(all_agents)
        }

        # Use enhanced template if available, otherwise fall back to original
        if self.has_historical_insights:
            user_message = self.enhanced_templates.get_planning_user_template(**template_kwargs)
            system_prompt = templates.PLANNING_SYSTEM_PROMPT
            print_agent_action(self.id, "Using enhanced planning template with historical insights", "", 'plan_proposal')
        else:
            user_message = templates.PLANNING_USER_TEMPLATE.format(**template_kwargs)
            system_prompt = templates.PLANNING_SYSTEM_PROMPT
        
        # Log what we're feeding to the LLM
        from llm_agent import print_color, LLM_INPUT_COLOR
        print_color(f"\n[LLM_INPUT] {self.id} ENHANCED PLANNING:", LLM_INPUT_COLOR)
        print_color("=" * 60, LLM_INPUT_COLOR)
        print_color(user_message, LLM_INPUT_COLOR)
        print_color("=" * 60, LLM_INPUT_COLOR)

        plan_obj = self._call_llm_structured(
            system_prompt, 
            user_message, 
            templates.AgentPlan,
            max_tokens=self.cfg.max_tokens + 200  # More tokens for enhanced reasoning
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
            plan_title = f"[ENHANCED INITIAL PLAN] {self.id}"
        else:
            # Fallback plan
            self.plan_steps = self._fallback_plan()
            plan_title = f"[ENHANCED FALLBACK PLAN] {self.id}"

        # Log the plan
        self.world_model.record_plan(self.id, self.plan_steps)
        self.world_model.log_communication(self.id, "ALL", f"{plan_title}: " + "; ".join(self.plan_steps))

    def enhanced_revision_plan(self, all_agents=None, shared_file_content: str = ""):
        """
        Enhanced revision planning phase that incorporates shared insights and historical data.
        This is a new method that extends the original planning capabilities.
        """
        if all_agents is None:
            all_agents = {}
        
        if not self.plan_steps:
            print_agent_action(self.id, "No initial plan to revise", "", 'plan_revise')
            return
        
        target_block = self.assigned_block
        task_name = self.task_name
        team_size = len([a for a in all_agents.values() if getattr(a, 'assigned_block', None) == target_block])
        
        # Get current observations
        obs = self.observe()
        
        # Prepare template arguments for revision
        template_kwargs = {
            "agent": obs["agent_id"],
            "my_position": f"({obs['my_position'][0]},{obs['my_position'][1]})" if isinstance(obs.get('my_position'), tuple) else str(obs.get('my_position', 'unknown')),
            "target_block": target_block,
            "task_name": task_name,
            "team_size": team_size,
            "env_info": self._get_env_info_str(obs),
            "blocks_info": self._get_blocks_info(),
            "other_agents_state": self._get_other_agents_state_str(obs),
            "all_committed_tasks": self._get_all_committed_tasks_str(all_agents),
            "previous_plan": "; ".join(self.plan_steps),
            "file_text": shared_file_content
        }

        # Use enhanced revision template if available
        if self.has_historical_insights:
            # For revision, we'll use the planning template with extra context
            user_message = self.enhanced_templates.get_planning_user_template(**template_kwargs)
            system_prompt = templates.REVISION_SYSTEM_PROMPT
            print_agent_action(self.id, "Using enhanced revision template with historical insights", "", 'plan_revise')
        else:
            user_message = templates.REVISION_USER_TEMPLATE.format(**template_kwargs)
            system_prompt = templates.REVISION_SYSTEM_PROMPT
        
        # Log what we're feeding to the LLM
        from llm_agent import print_color, LLM_INPUT_COLOR
        print_color(f"\n[LLM_INPUT] {self.id} ENHANCED REVISION:", LLM_INPUT_COLOR)
        print_color("=" * 60, LLM_INPUT_COLOR)
        print_color(user_message, LLM_INPUT_COLOR)
        print_color("=" * 60, LLM_INPUT_COLOR)

        revision_obj = self._call_llm_structured(
            system_prompt,
            user_message,
            templates.RevisionOutput,
            max_tokens=self.cfg.max_tokens + 300  # More tokens for enhanced reasoning and reflection
        )
        
        if revision_obj and revision_obj.plan:
            # Convert revised plan to string format
            revised_plan_steps = []
            for action in revision_obj.plan:
                if action.action_type.value == "MoveToBlock":
                    revised_plan_steps.append(f"MoveToBlock {action.block_id} {action.side.value}")
                elif action.action_type.value == "Rendezvous":
                    revised_plan_steps.append(f"Rendezvous {action.block_id} {action.side.value} {action.need} {action.timeout}")
                elif action.action_type.value == "Push":
                    revised_plan_steps.append(f"Push {action.block_id} {action.steps}")
                elif action.action_type.value == "Wait":
                    revised_plan_steps.append(f"Wait {action.steps}")
                elif action.action_type.value == "WaitAgents":
                    revised_plan_steps.append(f"WaitAgents {action.need} {action.timeout}")
                elif action.action_type.value == "YieldFace":
                    revised_plan_steps.append(f"YieldFace {action.block_id} {action.side.value} {action.steps}")
            
            # Update plan
            self.plan_steps = revised_plan_steps
            plan_title = f"[ENHANCED REVISED PLAN] {self.id}"
            
            # Log the revised plan
            self.world_model.record_plan(self.id, self.plan_steps)
            self.world_model.log_communication(self.id, "ALL", f"{plan_title}: " + "; ".join(self.plan_steps))
            
            print_agent_action(self.id, "Plan revised successfully", "", 'plan_revise')
            
            # Return reflection for shared file
            return revision_obj.reflection if revision_obj.reflection else "Plan revised based on available information."
        else:
            print_agent_action(self.id, "Failed to revise plan, keeping original", "", 'plan_revise')
            return "Plan revision failed, keeping original plan."

    def get_historical_context_summary(self) -> str:
        """Get a summary of available historical context for this agent"""
        if not self.has_historical_insights:
            return "No historical insights available"
        
        try:
            general_info = self.enhanced_templates.retriever.get_general_info()
            context_lines = [
                f"Historical context available:",
                f"- {general_info['episodes_count']} episodes analyzed",
                f"- {len(general_info['task_distribution'])} different tasks tracked",
                f"- Overall success rate: {general_info['overall_completion_rate']:.1%}"
            ]
            return "\n".join(context_lines)
        except Exception as e:
            return f"Historical context error: {e}"


class EnhancedLLMAgentManager(LLMAgentManager):
    """
    Enhanced agent manager that supports enhanced LLM agents with historical insights.
    Adds coordination for revision phases and shared learning.
    """
    
    def __init__(self, env, universe_json_path: str = None):
        """
        Initialize enhanced agent manager.
        
        Args:
            env: Environment instance
            universe_json_path: Path to universe graph JSON for historical insights
        """
        super().__init__(env)
        self.universe_json_path = universe_json_path
        self.shared_insights = []  # Shared learning across agents
        
        if universe_json_path:
            print(f"[ENHANCED_MANAGER] Historical insights enabled: {universe_json_path}")
        else:
            print("[ENHANCED_MANAGER] No historical insights available")

    def add_enhanced_agent(self, agent_id: str, cfg: LLMConfig, world_model):
        """Add an enhanced LLM agent to the manager"""
        agent = EnhancedLLMAgent(
            agent_id=agent_id,
            env=self.env,
            world_model=world_model,
            cfg=cfg,
            universe_json_path=self.universe_json_path
        )
        self.add_agent(agent)
        return agent
    
    def coordinate_revision_phase(self, all_agents: Dict[str, Any]) -> None:
        """
        Coordinate a revision phase where agents can improve their plans based on shared insights.
        This is a new capability that extends the original agent manager.
        """
        print_stage_separator("PLAN REVISION PHASE", 'plan_revise')
        
        # Collect insights from all enhanced agents
        shared_content = "Shared team insights:\n"
        
        for agent_id, agent in self.agents.items():
            if isinstance(agent, EnhancedLLMAgent) and agent.has_historical_insights:
                context_summary = agent.get_historical_context_summary()
                shared_content += f"\n{agent_id} context: {context_summary}\n"
        
        # Add any previous shared insights
        if self.shared_insights:
            shared_content += "\nPrevious insights:\n"
            for i, insight in enumerate(self.shared_insights, 1):
                shared_content += f"{i}. {insight}\n"
        
        # Let each enhanced agent revise their plan
        new_insights = []
        for agent_id, agent in self.agents.items():
            if isinstance(agent, EnhancedLLMAgent):
                print(f"[ENHANCED_MANAGER] {agent_id} revising plan...")
                reflection = agent.enhanced_revision_plan(all_agents, shared_content)
                if reflection and reflection.strip():
                    new_insights.append(f"{agent_id}: {reflection}")
        
        # Store new insights for future use
        self.shared_insights.extend(new_insights)
        
        print(f"[ENHANCED_MANAGER] Revision phase complete. New insights: {len(new_insights)}")

    def get_enhanced_agents_summary(self) -> str:
        """Get a summary of enhanced vs regular agents"""
        enhanced_count = sum(1 for agent in self.agents.values() if isinstance(agent, EnhancedLLMAgent))
        total_count = len(self.agents)
        with_insights = sum(1 for agent in self.agents.values() 
                           if isinstance(agent, EnhancedLLMAgent) and agent.has_historical_insights)
        
        return (f"Agent summary: {enhanced_count}/{total_count} enhanced agents, "
                f"{with_insights} with historical insights")

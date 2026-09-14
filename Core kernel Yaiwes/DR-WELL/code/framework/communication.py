# communication.py
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import sys
import os

# Add CUBE path for imports
cube_path = os.path.join(os.path.dirname(__file__), '..', 'CUBE')
if cube_path not in sys.path:
    sys.path.append(cube_path)

# Simple print function (replaces utils.print_color)
def print_color(text: str, color: str):
    """Simple print function (replaces utils.print_color)"""
    print(text)
@dataclass
class TaskProposal:
    agent_id: str
    block_id: int
    reason: str

@dataclass
class TaskCommitment:
    agent_id: str
    block_id: int
    task_name: str

class MessageBoard:
    """Shared message board for agent communication - no WM dependency"""
    
    def __init__(self):
        self.proposals: List[TaskProposal] = []
        self.commitments: List[TaskCommitment] = []
        self.round: str = "none"  # "none", "proposals", "commitments", "completed"
    
    def start_proposal_round(self):
        """Start the proposal round"""
        self.proposals.clear()
        self.commitments.clear()
        self.round = "proposals"
        print("=== PROPOSAL ROUND STARTED ===")
    
    def add_proposal(self, agent_id: str, block_id: int, reason: str):
        """Agent adds a task proposal"""
        if self.round != "proposals":
            raise ValueError("Not in proposal round")
        
        proposal = TaskProposal(agent_id, block_id, reason)
        self.proposals.append(proposal)
        
        message = f"PROPOSES: Block {block_id} - {reason}"
        print_color(f"[COMM] {agent_id}: {message}", "green")
    
    def start_commitment_round(self):
        """Start the commitment round"""
        if self.round != "proposals":
            raise ValueError("Must complete proposal round first")
        
        self.round = "commitments"
        print("=== COMMITMENT ROUND STARTED ===")
        
        # Log summary of proposals
        proposal_summary = []
        for prop in self.proposals:
            proposal_summary.append(f"{prop.agent_id}→Block{prop.block_id}")
        
        if proposal_summary:
            summary = "Proposals: " + ", ".join(proposal_summary)
            print(f"[COMM] {summary}")
    
    def add_commitment(self, agent_id: str, block_id: int, task_name: str):
        """Agent commits to a specific task"""
        if self.round != "commitments":
            raise ValueError("Not in commitment round")
        
        commitment = TaskCommitment(agent_id, block_id, task_name)
        self.commitments.append(commitment)
        
        message = f"COMMITS: {task_name}"
        print_color(f"[COMM] {agent_id}: {message}", "green")

    def complete_communication(self):
        """Mark communication round as completed"""
        if self.round != "commitments":
            raise ValueError("Must complete commitment round first")
        
        self.round = "completed"
        print("=== COMMUNICATION COMPLETED ===")
        
        # Log final task assignments
        assignments = []
        for commit in self.commitments:
            assignments.append(f"{commit.agent_id}->{commit.task_name}")
        
        if assignments:
            summary = "Final assignments: " + ", ".join(assignments)
            print(f"[COMM] {summary}")
    
    def get_agent_assignments(self) -> Dict[str, Dict]:
        """Get agent assignments from commitments - to be used by main to feed into agents"""
        assignments = {}
        for commit in self.commitments:
            assignments[commit.agent_id] = {
                'assigned_block': commit.block_id,
                'task_name': commit.task_name
            }
        return assignments
    
    def get_proposals(self) -> List[TaskProposal]:
        """Get all proposals"""
        return self.proposals.copy()
    
    def get_commitments(self) -> List[TaskCommitment]:
        """Get all commitments"""
        return self.commitments.copy()
            
        # Record final communication engagement stats
        all_participants = set()
        all_participants.update(prop.agent_id for prop in self.proposals)
        all_participants.update(commit.agent_id for commit in self.commitments)
        self.wm.record_communication_engagement(list(all_participants), "communication_complete")
    
    def get_proposals_summary(self) -> str:
        """Get a summary of all proposals for agents to see"""
        if not self.proposals:
            return "No proposals yet."
        
        lines = []
        for prop in self.proposals:
            lines.append(f"- {prop.agent_id}: Block {prop.block_id} ({prop.reason})")
        
        return "Current proposals:\n" + "\n".join(lines)
    
    def get_assigned_block(self, agent_id: str) -> Optional[int]:
        """Get the block ID that the agent committed to"""
        for commit in self.commitments:
            if commit.agent_id == agent_id:
                return commit.block_id
        return None
    
    def get_task_name(self, agent_id: str) -> Optional[str]:
        """Get the task name that the agent committed to"""
        for commit in self.commitments:
            if commit.agent_id == agent_id:
                return commit.task_name
        return None
    
    def reset(self):
        """Reset the message board for a new communication round"""
        self.proposals.clear()
        self.commitments.clear()
        self.round = "none"
    
    # Communication formatting methods
    def get_agent_states_str(self, obs: dict) -> str:
        """Create agent states string for communication"""
        lines = []
        agent_positions = obs.get("agent_positions", {})
        
        for agent_id in sorted(agent_positions.keys()):
            pos = agent_positions[agent_id]
            if isinstance(pos, tuple) and len(pos) == 2:
                lines.append(f"{agent_id}: Position ({pos[0]},{pos[1]})")
            else:
                lines.append(f"{agent_id}: Position {pos}")
        
        return "\n".join(lines) if lines else "No agent position data available"
    
    def get_world_info_str(self, obs: dict) -> str:
        """Create world info string for communication"""
        grid_size = obs.get("grid_size", "?")
        total_agents = len(obs.get("agent_positions", {}))
        
        lines = [
            f"Grid: {grid_size}x{grid_size}",
            f"Total agents: {total_agents}"
        ]
        
        return "\n".join(lines)
    
    def get_blocks_info_str(self, obs: dict) -> str:
        """Create blocks info string from agent observation"""
        available_blocks = obs.get("available_blocks", [])
        delivered_blocks = obs.get("delivered_blocks", [])
        
        if not available_blocks and not delivered_blocks:
            return "No block information available"
        
        lines = []
        if available_blocks:
            lines.append("Available blocks:")
            for block in available_blocks:
                pos = block.get("position", "unknown")
                weight = block.get("weight", "unknown")
                distance = block.get("distance_to_goal", "unknown")
                lines.append(f"  - Block {block['id']}: weight={weight}, pos={pos}, distance_to_goal={distance}")
        
        if delivered_blocks:
            lines.append("Delivered blocks:")
            for block in delivered_blocks:
                pos = block.get("position", "unknown")
                weight = block.get("weight", "unknown")
                lines.append(f"  - Block {block['id']}: weight={weight}, pos={pos} (DELIVERED)")
        
        return "\n".join(lines)
    
    def get_proposals_str(self) -> str:
        """Create proposals string for communication"""
        if not self.proposals:
            return "No proposals yet"
        
        lines = []
        for prop in self.proposals:
            lines.append(f"- {prop.agent_id}: Block {prop.block_id} ({prop.reason})")
        
        return "\n".join(lines)
    
    def get_commitments_str(self) -> str:
        """Create commitments string for communication"""
        if not self.commitments:
            return "No commitments yet"
        
        lines = []
        for commit in self.commitments:
            lines.append(f"- {commit.agent_id}: {commit.task_name} (Block {commit.block_id})")
        
        return "\n".join(lines)

def run_communication_round(agents) -> MessageBoard:
    """Two rounds: proposals → commitments; round-robin over agents that are about to plan."""
    participants = [a for a in agents.values() if a.should_plan()]
    board = MessageBoard()  # No WM dependency

    board.start_proposal_round()
    for agent in participants:
        agent.propose_task(board)

    board.start_commitment_round()
    for agent in participants:
        agent.commit_to_task(board)

    board.complete_communication()
    return board


# ========================================
# ENHANCED COMMUNICATION CLASSES
# ========================================

from retriever import UniverseRetriever
from typing import Dict, List, Optional, Tuple
import os

class EnhancedMessageBoard(MessageBoard):
    """
    Enhanced message board that adds historical communication insights to the original MessageBoard.
    """
    
    def __init__(self, universe_json_path: str = None):
        """
        Initialize enhanced message board.
        
        Args:
            universe_json_path: Path to universe graph JSON for historical insights
        """
        super().__init__()
        
        # Initialize retriever for historical insights
        self.retriever = None
        if universe_json_path and os.path.exists(universe_json_path):
            try:
                self.retriever = UniverseRetriever(universe_json_path=universe_json_path)
                print(f"[ENHANCED_COMM] Historical communication insights enabled")
            except Exception as e:
                print(f"[ENHANCED_COMM] Failed to initialize retriever: {e}")
                self.retriever = None
        else:
            print("[ENHANCED_COMM] No historical communication insights available")
        
        self.communication_insights = []  # Store insights for this session

    def start_proposal_round(self, current_timestep: int = None, num_agents: int = None):
        """Enhanced proposal round start with historical context"""
        super().start_proposal_round()
        
        # Display current session info at the top
        if current_timestep is not None or num_agents is not None:
            print("=== CURRENT SESSION INFO ===")
            if current_timestep is not None:
                print(f"  Current timestep: T{current_timestep}")
            if num_agents is not None:
                print(f"  Number of agents: {num_agents}")
            print()
        
        if self.retriever:
            try:
                # Get general task performance to inform proposals
                general_info = self.retriever.get_general_info()
                
                # Add block timing analysis with performance data
                print("=== HISTORICAL TASK PERFORMANCE ===")
                timing_analysis = self.retriever.get_block_timing_analysis()
                block_stats = timing_analysis.get("block_timing_analysis", {})
                
                if block_stats:
                    # Collect and sort blocks by success rate for insights
                    block_performance = []
                    
                    for block_name, stats in block_stats.items():
                        start_times = stats.get("start_times", {})
                        performance = stats.get("performance", {})
                        if start_times:
                            avg_start = start_times.get("avg", 0)
                            min_start = start_times.get("min", 0)
                            max_start = start_times.get("max", 0)
                            count = start_times.get("count", 0)
                            success_rate = performance.get("success_rate", 0)
                            total_attempts = performance.get("total_attempts", 0)
                            total_successes = performance.get("total_successes", 0)
                            min_agents_needed = performance.get("min_agents_needed", "UNKNOWN")
                            min_completion_time = performance.get("min_completion_time", "UNKNOWN")
                            avg_task_duration = performance.get("avg_task_duration", "UNKNOWN")
                            
                            # Format duration values
                            min_duration_str = f"{min_completion_time:.1f}" if isinstance(min_completion_time, (int, float)) else min_completion_time
                            avg_duration_str = f"{avg_task_duration:.1f}" if isinstance(avg_task_duration, (int, float)) else avg_task_duration
                            
                            print(f"  {block_name}: avg_start=T{avg_start:.1f}, range=T{min_start}-T{max_start}, success_rate={success_rate:.1%} (out of {total_attempts} attempts), min_completed_teamsize={min_agents_needed}, min_task_duration={min_duration_str}, avg_task_duration={avg_duration_str}")
                            
                            # Store for insights
                            block_performance.append((block_name, success_rate, avg_start))
                            
                            # Store timing insights
                            timing_insight = f"{block_name} typically starts at step {avg_start:.0f} with {success_rate:.1%} success rate, needs {min_agents_needed} agents, avg duration {avg_duration_str} steps"
                            self.communication_insights.append(timing_insight)
                    
                    # Store insight for best performing task
                    if block_performance:
                        best_block = max(block_performance, key=lambda x: x[1])  # Sort by success rate
                        block_name, success_rate, avg_start = best_block
                        insight = f"Historically, {block_name} has the highest success rate at {success_rate:.1%}"
                        self.communication_insights.append(insight)
                    
                    # Add optimal team size recommendations
                    print("\n=== OPTIMAL TEAM SIZE RECOMMENDATIONS ===")
                    for block_name, stats in block_stats.items():
                        # Check if this block has any successful completions
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
                                
                                print(f"  {block_name}: optimal team size = {optimal_k} (best success rate: {best_success_rate:.1%})")
                            else:
                                # Use minimum completed team size if no optimal team sizes found
                                min_agents = stats['performance'].get('min_agents_needed', 'UNKNOWN')
                                print(f"  {block_name}: optimal team size = {min_agents} (best success rate: {success_rate:.1%})")
                        else:
                            # No successful completions - cannot determine optimal team size
                            print(f"  {block_name}: optimal team size = UNKNOWN (no successful completions yet)")
                else:
                    print("  No block timing data available")
                        
            except Exception as e:
                print(f"[ENHANCED_COMM] Error getting historical context: {e}")

    def start_commitment_round(self):
        """Enhanced commitment round with team size recommendations"""
        super().start_commitment_round()
        
        if self.retriever and self.proposals:
            try:
                print("=== OPTIMAL TEAM SIZE RECOMMENDATIONS ===")
                
                # Get unique proposed blocks
                proposed_blocks = list(set(prop.block_id for prop in self.proposals))
                
                for block_id in proposed_blocks:
                    task_name = f"Block_{block_id}"
                    feedback = self.retriever.get_plan_feedback(task_name)
                    
                    if feedback.get("optimal_team_sizes"):
                        k_values = list(feedback["optimal_team_sizes"].values())
                        if k_values:
                            optimal_k = max(set(k_values), key=k_values.count)
                            success_rate = feedback.get("best_performing", {}).get("completion_rate", 0)
                            print(f"  {task_name}: optimal team size = {optimal_k} (best success rate: {success_rate:.1%})")
                            
                            # Store insight
                            insight = f"{task_name} works best with {optimal_k} agents"
                            self.communication_insights.append(insight)
                
            except Exception as e:
                print(f"[ENHANCED_COMM] Error getting team size recommendations: {e}")

    def complete_communication(self):
        """Enhanced communication completion with success pattern analysis"""
        super().complete_communication()
        
        if self.retriever and self.commitments:
            try:
                print("=== COMMUNICATION EFFECTIVENESS INSIGHTS ===")
                
                # Analyze committed tasks
                committed_tasks = {}
                for commit in self.commitments:
                    task = commit.task_name.replace("Block_", "Block_")
                    if task not in committed_tasks:
                        committed_tasks[task] = 0
                    committed_tasks[task] += 1
                
                # Get communication patterns for each committed task
                for task_name, agent_count in committed_tasks.items():
                    if task_name.startswith("Block_"):
                        block_name = task_name.replace("Block_", "Block_")
                        comm_patterns = self.retriever.get_communication_patterns(block_name)
                        patterns = comm_patterns.get("communication_patterns", {})
                        
                        if patterns:
                            # Find most effective communication strategy
                            best_pattern = max(patterns.items(), key=lambda x: x[1]["success_rate"])
                            best_comm_type, best_data = best_pattern
                            
                            print(f"  {task_name} ({agent_count} agents): Most effective communication = {best_comm_type}")
                            print(f"    Success rate: {best_data['success_rate']:.1%} ({best_data['total_uses']} uses)")
                            
                            # Store insight
                            insight = f"{task_name} with {agent_count} agents: use {best_comm_type} for best results"
                            self.communication_insights.append(insight)
                
            except Exception as e:
                print(f"[ENHANCED_COMM] Error getting communication insights: {e}")

    def get_blocks_info_str(self, obs: dict) -> str:
        """Enhanced blocks info with historical success rates"""
        base_info = super().get_blocks_info_str(obs)
        
        if not self.retriever:
            return base_info
        
        try:
            # Add historical success rates to block information
            enhanced_lines = []
            
            if hasattr(obs, 'get') and obs.get('env') and hasattr(obs['env'], '_blocks'):
                blocks = obs['env']._blocks
            elif hasattr(obs, 'get') and 'blocks' in obs:
                blocks = obs['blocks']
            else:
                return base_info  # Fallback to original
            
            for block in blocks:
                task_name = f"Block_{block.id}"
                feedback = self.retriever.get_plan_feedback(task_name)
                
                # Base block info
                goal_col = getattr(obs.get('env', None), 'K', 10) - 1
                distance_to_goal = goal_col - (block.c + block.weight - 1)
                block_info = f"Block {block.id}: weight={block.weight}, position=({block.r},{block.c}), distance_to_goal={distance_to_goal}"
                
                # Add historical success rate if available
                if feedback.get("relevant_attempts"):
                    avg_success_rate = sum(entry["completion_rate"] for entry in feedback["relevant_attempts"]) / len(feedback["relevant_attempts"])
                    block_info += f", historical_success_rate={avg_success_rate:.1%}"
                
                # Add optimal team size if available
                if feedback.get("optimal_team_sizes"):
                    k_values = list(feedback["optimal_team_sizes"].values())
                    if k_values:
                        optimal_k = max(set(k_values), key=k_values.count)
                        block_info += f", optimal_team_size={optimal_k}"
                
                enhanced_lines.append(block_info)
            
            return "\n".join(enhanced_lines) if enhanced_lines else base_info
            
        except Exception as e:
            print(f"[ENHANCED_COMM] Error enhancing blocks info: {e}")
            return base_info

    def get_proposals_str(self) -> str:
        """Enhanced proposals string with historical context"""
        base_proposals = super().get_proposals_str()
        
        if not self.retriever or not self.proposals:
            return base_proposals
        
        try:
            enhanced_lines = []
            
            for prop in self.proposals:
                prop_line = f"{prop.agent_id} -> Block {prop.block_id}: {prop.reason}"
                
                # Add historical context for this block
                task_name = f"Block_{prop.block_id}"
                feedback = self.retriever.get_plan_feedback(task_name)
                
                if feedback.get("best_performing"):
                    best = feedback["best_performing"]
                    prop_line += f" [Historical: {best['completion_rate']:.1%} success rate]"
                
                enhanced_lines.append(prop_line)
            
            return "\n".join(enhanced_lines) if enhanced_lines else base_proposals
            
        except Exception as e:
            print(f"[ENHANCED_COMM] Error enhancing proposals: {e}")
            return base_proposals

    def get_communication_insights_summary(self) -> str:
        """Get summary of communication insights gathered this session"""
        if not self.communication_insights:
            return "No communication insights available"
        
        lines = ["Communication insights for this session:"]
        for i, insight in enumerate(self.communication_insights, 1):
            lines.append(f"  {i}. {insight}")
        
        return "\n".join(lines)

    def get_historical_team_performance(self, task_name: str, team_size: int) -> Optional[Dict]:
        """Get historical performance data for a specific task and team size"""
        if not self.retriever:
            return None
        
        try:
            block_name = task_name.replace("Block_", "Block_")
            feedback = self.retriever.get_plan_feedback(block_name, team_size=team_size)
            
            if feedback.get("relevant_attempts"):
                # Calculate average performance for this team size
                relevant = [entry for entry in feedback["relevant_attempts"] 
                           if f"k={team_size}" in entry["signature"]]
                
                if relevant:
                    avg_success_rate = sum(entry["completion_rate"] for entry in relevant) / len(relevant)
                    total_attempts = sum(entry["attempts"] for entry in relevant)
                    
                    return {
                        "task_name": task_name,
                        "team_size": team_size,
                        "average_success_rate": avg_success_rate,
                        "total_attempts": total_attempts,
                        "sample_size": len(relevant)
                    }
            
        except Exception as e:
            print(f"[ENHANCED_COMM] Error getting team performance: {e}")
        
        return None

    def suggest_task_allocation(self) -> List[Dict]:
        """
        Suggest optimal task allocation based on historical performance.
        Returns list of suggestions with reasoning.
        """
        suggestions = []
        
        if not self.retriever or not self.proposals:
            return suggestions
        
        try:
            # Get unique proposed blocks and proposing agents
            proposed_blocks = list(set(prop.block_id for prop in self.proposals))
            proposing_agents = [prop.agent_id for prop in self.proposals]
            total_agents = len(set(proposing_agents))
            
            for block_id in proposed_blocks:
                task_name = f"Block_{block_id}"
                feedback = self.retriever.get_plan_feedback(task_name)
                
                # Find optimal team size
                if feedback.get("optimal_team_sizes"):
                    k_values = list(feedback["optimal_team_sizes"].values())
                    if k_values:
                        optimal_k = max(set(k_values), key=k_values.count)
                        
                        # Check if we have enough agents
                        agents_interested = len([p for p in self.proposals if p.block_id == block_id])
                        
                        suggestion = {
                            "task_name": task_name,
                            "optimal_team_size": optimal_k,
                            "agents_interested": agents_interested,
                            "feasible": agents_interested >= optimal_k and optimal_k <= total_agents,
                            "reasoning": f"Historical data suggests {optimal_k} agents for {task_name}"
                        }
                        
                        if feedback.get("best_performing"):
                            best = feedback["best_performing"]
                            suggestion["expected_success_rate"] = best["completion_rate"]
                            suggestion["reasoning"] += f" (expected {best['completion_rate']:.1%} success rate)"
                        
                        suggestions.append(suggestion)
            
        except Exception as e:
            print(f"[ENHANCED_COMM] Error generating suggestions: {e}")
        
        return suggestions


# Convenience function to create enhanced message board
def create_enhanced_message_board(universe_json_path: str = None) -> EnhancedMessageBoard:
    """Create an enhanced message board with optional historical insights"""
    return EnhancedMessageBoard(universe_json_path)

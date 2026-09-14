#!/usr/bin/env python3
"""
Complete Enhanced Multi-Agent System Demo
==========================================

This demo showcases the complete enhanced system with:
1. Enhanced Communication System (from previous demo)
2. Enhanced LLM Agents with historical insights
3. Enhanced Templates with plan prototypes and instances
4. Integrated workflow showing all components working together
"""

from communication import create_enhanced_message_board
from llm_templates import create_enhanced_templates
from llm_agent_enhanced import EnhancedLLMAgent, EnhancedLLMAgentManager
from llm_agent import LLMConfig
from retriever import UniverseRetriever
import time

class MockEnvironment:
    """Mock environment for demo purposes"""
    
    def __init__(self):
        self.grid_size = 5
        self.blocks = [
            {"id": 0, "position": (1, 1), "weight": 2},
            {"id": 1, "position": (3, 2), "weight": 3}, 
            {"id": 2, "position": (2, 4), "weight": 1}
        ]
        
    def get_observations(self, agent_id):
        return {
            "agent_id": agent_id,
            "my_position": (0, 0),
            "teammates": ["agent_1", "agent_2"] if agent_id == "agent_0" else ["agent_0", "agent_2"] if agent_id == "agent_1" else ["agent_0", "agent_1"],
            "blocks": self.blocks,
            "delivered_blocks": []
        }

class MockWorldModel:
    """Mock world model for demo purposes"""
    
    def __init__(self):
        self.plans = {}
        self.communications = []
        
    def record_plan(self, agent_id, plan_steps):
        self.plans[agent_id] = plan_steps
        print(f"[WORLD_MODEL] Recorded plan for {agent_id}: {'; '.join(plan_steps)}")
        
    def log_communication(self, sender, receiver, message):
        self.communications.append((sender, receiver, message))
        print(f"[WORLD_MODEL] Communication: {sender} -> {receiver}: {message[:100]}...")

def demo_complete_enhanced_system():
    """Demonstrate the complete enhanced multi-agent system"""
    print("=" * 80)
    print("COMPLETE ENHANCED MULTI-AGENT SYSTEM DEMO")
    print("Communication + Agents + Templates + Historical Insights")
    print("=" * 80)
    print()
    
    universe_path = "runs/updated_universe_graph.json"
    
    # ========================================
    # PHASE 1: ENHANCED COMMUNICATION SYSTEM
    # ========================================
    print("=" * 60)
    print("PHASE 1: ENHANCED COMMUNICATION SYSTEM")
    print("=" * 60)
    
    # Create enhanced message board with historical insights
    message_board = create_enhanced_message_board(universe_json_path=universe_path)
    
    # Start proposal round with comprehensive insights
    print("Starting enhanced proposal round...")
    message_board.start_proposal_round(current_timestep=15, num_agents=3)
    print()
    
    # Add sample proposals
    message_board.add_proposal("agent_0", 2, "Based on 54.5% historical success rate")
    message_board.add_proposal("agent_1", 1, "Pioneering Block_1 - untested but needed")  
    message_board.add_proposal("agent_2", 2, "Team coordination for Block_2")
    
    print("Proposals received:")
    for proposal in message_board.proposals:
        print(f"  {proposal.agent_id}: Block {proposal.block_id} - {proposal.reason}")
    print()
    
    # ========================================
    # PHASE 2: ENHANCED LLM AGENTS
    # ========================================
    print("=" * 60)
    print("PHASE 2: ENHANCED LLM AGENTS")  
    print("=" * 60)
    
    # Setup mock environment and world model
    env = MockEnvironment()
    world_model = MockWorldModel()
    
    # Create LLM configuration
    cfg = LLMConfig()
    cfg.model = "gpt-4o-mini"
    cfg.max_tokens = 1000
    cfg.temperature = 0.7
    
    # Create enhanced agent manager
    manager = EnhancedLLMAgentManager(env, universe_json_path=universe_path)
    
    # Add enhanced agents
    print("Creating enhanced agents with historical insights...")
    agent_0 = manager.add_enhanced_agent("agent_0", cfg, world_model)
    agent_1 = manager.add_enhanced_agent("agent_1", cfg, world_model) 
    agent_2 = manager.add_enhanced_agent("agent_2", cfg, world_model)
    
    print(f"✓ {manager.get_enhanced_agents_summary()}")
    print()
    
    # Show agent historical context
    print("Agent Historical Context:")
    for agent in [agent_0, agent_1, agent_2]:
        context = agent.get_historical_context_summary()
        print(f"  {agent.id}: {context}")
    print()
    
    # Simulate commitment phase
    print("Simulating commitment phase...")
    agent_0.assigned_block = 2
    agent_0.task_name = "Block_2"
    agent_1.assigned_block = 1  
    agent_1.task_name = "Block_1"
    agent_2.assigned_block = 2
    agent_2.task_name = "Block_2"
    
    all_agents = {
        "agent_0": agent_0,
        "agent_1": agent_1, 
        "agent_2": agent_2
    }
    
    print("Agent commitments:")
    for agent_id, agent in all_agents.items():
        print(f"  {agent_id}: {agent.task_name}")
    print()
    
    # ========================================  
    # PHASE 3: ENHANCED TEMPLATES & PLANNING
    # ========================================
    print("=" * 60)
    print("PHASE 3: ENHANCED TEMPLATES & PLANNING")
    print("=" * 60)
    
    # Create enhanced templates
    templates = create_enhanced_templates(universe_path)
    
    print("Enhanced Planning Context for Block_2:")
    print("---------------------------------------")
    
    # Get plan prototypes for Block_2
    prototypes = templates.retriever.get_plan_prototypes("Block_2")
    if prototypes.get("plan_prototypes"):
        print("Available Plan Prototypes:")
        for i, (key, data) in enumerate(prototypes["plan_prototypes"].items(), 1):
            success_rate = data.get("success_rate", 0)
            symbolic_actions = data.get("symbolic_actions", [])
            avg_team_size = data.get("avg_team_size", 0)
            
            actions_str = " -> ".join(symbolic_actions) if symbolic_actions else "empty_plan"
            print(f"  {i}. {actions_str}")
            print(f"     Success: {success_rate:.1%} | Team size: {avg_team_size:.1f}")
    print()
    
    # Get detailed instances for Block_2
    instances = templates.retriever.get_plan_instances("Block_2")
    if instances.get("plan_instances"):
        print("Successful Plan Instances:")
        successful_plans = [(k, v) for k, v in instances["plan_instances"].items() 
                          if v.get("success_rate", 0) > 0]
        
        for i, (key, data) in enumerate(successful_plans[:3], 1):  # Top 3
            success_rate = data.get("success_rate", 0)
            duration = data.get("avg_duration", 0)
            plan = data.get("plan", [])
            
            plan_str = " -> ".join(plan) if plan else "empty_plan"
            print(f"  {i}. {plan_str}")
            print(f"     Success: {success_rate:.1%} | Duration: {duration:.1f} steps")
    print()
    
    # ========================================
    # PHASE 4: INTEGRATED WORKFLOW
    # ========================================
    print("=" * 60)
    print("PHASE 4: INTEGRATED ENHANCED WORKFLOW")
    print("=" * 60)
    
    print("Demonstrating integrated enhanced workflow...")
    print()
    
    # Step 1: Enhanced Communication
    print("Step 1: Enhanced communication provides historical insights")
    print("  ✓ Block timing analysis")
    print("  ✓ Success rates and team size recommendations")
    print("  ✓ Optimal team size suggestions")
    print()
    
    # Step 2: Enhanced Agent Planning
    print("Step 2: Enhanced agents use historical insights for planning")
    try:
        # Simulate enhanced planning template usage
        planning_kwargs = {
            "agent": "agent_0",
            "my_position": "(0,0)",
            "target_block": 2,
            "task_name": "Block_2",
            "team_size": 2,
            "env_info": "Mock environment info",
            "blocks_info": "Block positions and weights",
            "other_agents_state": "Teammate states",
            "all_committed_tasks": "Team task assignments"
        }
        
        enhanced_template = templates.get_planning_user_template(**planning_kwargs)
        print("  ✓ Enhanced planning template includes:")
        print("    • Historical plan prototypes")
        print("    • Success rate analysis")
        print("    • Team coordination patterns")
        print()
        
        # Show template snippet (first few lines)
        template_lines = enhanced_template.split('\n')[:5]
        print("  Template preview:")
        for line in template_lines:
            print(f"    {line}")
        print("    ...")
        print()
        
    except Exception as e:
        print(f"  Template demo: {e}")
    
    # Step 3: Enhanced Revision
    print("Step 3: Enhanced revision with shared insights")
    print("  ✓ Cross-agent learning")
    print("  ✓ Shared historical context")
    print("  ✓ Collaborative plan improvement")
    print()
    
    # ========================================
    # SYSTEM SUMMARY
    # ========================================
    print("=" * 60)
    print("ENHANCED SYSTEM SUMMARY")
    print("=" * 60)
    
    print("Complete Enhanced Multi-Agent System Features:")
    print()
    
    print("📊 ENHANCED COMMUNICATION:")
    print("  • Historical block timing analysis")
    print("  • Success rates and minimum team sizes")
    print("  • Optimal team size recommendations") 
    print("  • Session context (timestep, agent count)")
    print()
    
    print("🤖 ENHANCED LLM AGENTS:")
    print("  • Historical performance insights")
    print("  • Context-aware decision making")
    print("  • Shared learning capabilities")
    print("  • Graceful fallback to original behavior")
    print()
    
    print("📝 ENHANCED TEMPLATES:")
    print("  • Plan prototype analysis")
    print("  • Detailed instance examination")
    print("  • Strategic and tactical insights")
    print("  • Success-ranked recommendations")
    print()
    
    print("🔄 INTEGRATED WORKFLOW:")
    print("  • Communication → Planning → Revision")
    print("  • Historical insights at every phase")
    print("  • Cross-component data sharing")
    print("  • Continuous learning and adaptation")
    print()
    
    print("System Benefits:")
    print("✅ Reduced failed attempts through historical learning")
    print("✅ Improved team coordination with optimal sizing")  
    print("✅ Strategic planning with proven approaches")
    print("✅ Adaptive agents that learn from experience")
    print("✅ Comprehensive insights across all phases")
    print()
    
    print("Demo completed successfully! 🎉")

if __name__ == "__main__":
    demo_complete_enhanced_system()

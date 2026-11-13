#!/usr/bin/env python3
"""
Enhanced Multi-Agent System - Quick Start Guide
===============================================

This guide shows how to use all enhanced components in your own projects.
"""

# ==============================================================================
# QUICK START EXAMPLES
# ==============================================================================

def example_enhanced_communication():
    """Example: Using enhanced communication system"""
    from communication import create_enhanced_message_board
    
    # Create enhanced message board with historical insights
    message_board = create_enhanced_message_board(
        universe_json_path="runs/updated_universe_graph.json"
    )
    
    # Start proposal round with session context
    message_board.start_proposal_round(current_timestep=15, num_agents=3)
    
    # Add proposals - agents see historical performance
    message_board.add_proposal("agent_0", 2, "Based on 54.5% success rate")
    message_board.add_proposal("agent_1", 1, "Pioneering new strategy")
    
    print("✓ Enhanced communication provides historical insights")


def example_enhanced_templates():
    """Example: Using enhanced templates with historical insights"""
    from llm_templates import create_enhanced_templates
    
    # Create enhanced templates with retriever
    templates = create_enhanced_templates("runs/updated_universe_graph.json")
    
    # Get enhanced planning template with historical context
    planning_template = templates.get_planning_user_template(
        agent="agent_0",
        my_position="(0,0)",
        target_block=2,
        task_name="Block_2",
        team_size=2,
        env_info="Environment state",
        blocks_info="Block positions",
        other_agents_state="Teammate states",
        all_committed_tasks="Team assignments"
    )
    
    # Template now includes plan prototypes and success rates
    print("✓ Enhanced templates include historical insights")


def example_enhanced_agents():
    """Example: Using enhanced LLM agents"""
    from llm_agent_enhanced import EnhancedLLMAgentManager
    from llm_agent import LLMConfig
    
    # Create configuration
    cfg = LLMConfig()
    cfg.model = "gpt-4o-mini"
    cfg.max_tokens = 1000
    
    # Create enhanced agent manager
    manager = EnhancedLLMAgentManager(
        env=None,  # Your environment
        universe_json_path="runs/updated_universe_graph.json"
    )
    
    # Add enhanced agents
    agent = manager.add_enhanced_agent("agent_0", cfg, world_model=None)
    
    # Agent now has historical context awareness
    context = agent.get_historical_context_summary()
    print(f"✓ Agent historical context: {context}")


def example_retriever_analysis():
    """Example: Direct retriever usage for analysis"""
    from retriever import UniverseRetriever
    
    # Create retriever
    retriever = UniverseRetriever("runs/updated_universe_graph.json")
    
    # Get block timing analysis
    timing_analysis = retriever.get_block_timing_analysis()
    
    # Get plan prototypes
    prototypes = retriever.get_plan_prototypes("Block_2")
    
    # Get detailed plan instances  
    instances = retriever.get_plan_instances("Block_2")
    
    print("✓ Direct retriever access for custom analysis")


# ==============================================================================
# INTEGRATION PATTERNS
# ==============================================================================

def integration_pattern_1():
    """Pattern 1: Enhanced communication + regular agents"""
    from communication import create_enhanced_message_board
    
    # Use enhanced communication with any agents
    message_board = create_enhanced_message_board("runs/updated_universe_graph.json")
    
    # Agents get historical insights during communication phases
    message_board.start_proposal_round(current_timestep=10, num_agents=2)
    
    print("✓ Pattern 1: Enhanced communication only")


def integration_pattern_2():
    """Pattern 2: Enhanced agents + regular communication"""
    from llm_agent_enhanced import EnhancedLLMAgent
    from llm_agent import LLMConfig
    
    # Use enhanced agents with regular communication
    cfg = LLMConfig()
    agent = EnhancedLLMAgent(
        agent_id="agent_0",
        env=None,
        world_model=None, 
        cfg=cfg,
        universe_json_path="runs/updated_universe_graph.json"
    )
    
    # Agents have historical insights for planning
    print("✓ Pattern 2: Enhanced agents only")


def integration_pattern_3():
    """Pattern 3: Full enhanced system"""
    from communication import create_enhanced_message_board
    from llm_agent_enhanced import EnhancedLLMAgentManager  
    from llm_agent import LLMConfig
    
    # Complete enhanced system
    message_board = create_enhanced_message_board("runs/updated_universe_graph.json")
    
    cfg = LLMConfig()
    manager = EnhancedLLMAgentManager(None, "runs/updated_universe_graph.json")
    agent = manager.add_enhanced_agent("agent_0", cfg, None)
    
    # Full historical insights across all phases
    print("✓ Pattern 3: Complete enhanced system")


# ==============================================================================
# CONFIGURATION OPTIONS
# ==============================================================================

def configuration_examples():
    """Examples of different configuration options"""
    
    # Option 1: With historical insights
    from communication import create_enhanced_message_board
    message_board = create_enhanced_message_board("runs/updated_universe_graph.json")
    print("✓ With historical insights")
    
    # Option 2: Without historical insights (graceful fallback)
    message_board_fallback = create_enhanced_message_board(None)
    print("✓ Graceful fallback to original behavior")
    
    # Option 3: Custom universe graph path
    message_board_custom = create_enhanced_message_board("path/to/custom/universe.json")
    print("✓ Custom universe graph path")


# ==============================================================================
# MAIN DEMO
# ==============================================================================

def main():
    """Run quick start examples"""
    print("=" * 60)
    print("ENHANCED MULTI-AGENT SYSTEM - QUICK START")
    print("=" * 60)
    print()
    
    print("1. Enhanced Communication:")
    try:
        example_enhanced_communication()
    except Exception as e:
        print(f"   Demo mode: {e}")
    print()
    
    print("2. Enhanced Templates:")
    try:
        example_enhanced_templates()
    except Exception as e:
        print(f"   Demo mode: {e}")
    print()
    
    print("3. Enhanced Agents:")
    try:
        example_enhanced_agents()
    except Exception as e:
        print(f"   Demo mode: {e}")
    print()
    
    print("4. Direct Retriever:")
    try:
        example_retriever_analysis()
    except Exception as e:
        print(f"   Demo mode: {e}")
    print()
    
    print("Integration Patterns:")
    integration_pattern_1()
    integration_pattern_2() 
    integration_pattern_3()
    print()
    
    print("Configuration Options:")
    try:
        configuration_examples()
    except Exception as e:
        print(f"   Demo mode: {e}")
    print()
    
    print("=" * 60)
    print("QUICK START COMPLETE")
    print("=" * 60)
    print()
    print("Available Components:")
    print("• Enhanced Communication: communication.py")
    print("• Enhanced Templates: llm_templates.py") 
    print("• Enhanced Agents: llm_agent_enhanced.py")
    print("• Historical Retriever: retriever.py")
    print()
    print("Available Demos:")
    print("• enhanced_demo.py - Complete Enhanced System Demo")
    print("• quick_start_guide.py - This file")
    print()
    print("Documentation:")
    print("• ENHANCED_SYSTEM_SUMMARY.md - Complete overview")
    print("• README.md - Quick overview")


if __name__ == "__main__":
    main()

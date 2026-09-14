#!/usr/bin/env python3
"""
Utility functions for the CUBE framework
========================================
Provides colored output, formatting, and other helper functions.
"""

from typing import Dict, Any, Optional
import sys

# ANSI color codes
class Colors:
    # Basic colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    
    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    STRIKETHROUGH = '\033[9m'
    
    # Reset
    RESET = '\033[0m'
    END = '\033[0m'

# Stage-specific colors
STAGE_COLORS = {
    'episode_start': Colors.BRIGHT_MAGENTA,
    'communication_proposal': Colors.BRIGHT_CYAN,
    'communication_commit': Colors.BRIGHT_GREEN,
    'plan_proposal': Colors.BRIGHT_YELLOW,
    'plan_revise': Colors.YELLOW,
    'planning': Colors.BRIGHT_YELLOW,
    'execution': Colors.BRIGHT_BLUE,
    'episode_end': Colors.BRIGHT_MAGENTA,
    'universe_update': Colors.MAGENTA,
    'error': Colors.BRIGHT_RED,
    'success': Colors.BRIGHT_GREEN,
    'info': Colors.CYAN,
    'debug': Colors.BRIGHT_BLACK
}

def print_color(text: str, color: str = None, end: str = '\n', file=None) -> None:
    """
    Print text with specified color.
    
    Args:
        text: Text to print
        color: Color code (from Colors class) or stage name
        end: String appended after the text
        file: File object to write to (default: sys.stdout)
    """
    if file is None:
        file = sys.stdout
        
    # If color is a stage name, get the corresponding color
    if color in STAGE_COLORS:
        color_code = STAGE_COLORS[color]
    elif color is None:
        color_code = ""
    else:
        color_code = color
    
    if color_code:
        print(f"{color_code}{text}{Colors.RESET}", end=end, file=file)
    else:
        print(text, end=end, file=file)

def print_separator(char: str = "=", length: int = 80, color: str = None, title: str = None) -> None:
    """
    Print a separator line with optional title.
    
    Args:
        char: Character to use for the line
        length: Length of the line
        color: Color for the line
        title: Optional title to center in the line
    """
    if title:
        title_with_spaces = f" {title} "
        title_length = len(title_with_spaces)
        
        if title_length >= length:
            print_color(title_with_spaces, color)
        else:
            side_length = (length - title_length) // 2
            remainder = (length - title_length) % 2
            line = char * side_length + title_with_spaces + char * (side_length + remainder)
            print_color(line, color)
    else:
        line = char * length
        print_color(line, color)

def print_stage_header(stage_name: str, step: int = None, details: str = None) -> None:
    """
    Print a colored header for different stages of execution.
    
    Args:
        stage_name: Name of the stage
        step: Optional step number
        details: Optional additional details
    """
    stage_colors = {
        'EPISODE_START': 'episode_start',
        'COMMUNICATION_PROPOSAL': 'communication_proposal', 
        'COMMUNICATION_COMMIT': 'communication_commit',
        'PLANNING': 'planning',
        'EXECUTION': 'execution',
        'EPISODE_END': 'episode_end',
        'UNIVERSE_UPDATE': 'universe_update'
    }
    
    color = stage_colors.get(stage_name.upper(), 'info')
    
    # Build title
    if step is not None:
        title = f"{stage_name} (Step {step})"
    else:
        title = stage_name
        
    if details:
        title += f" - {details}"
    
    print()  # Empty line before
    print_separator("=", 80, color, title)
    if details and step is not None:
        print_color(f"Step: {step} | {details}", color)
        print_separator("-", 80, color)

def print_step_separator(step: int, color: str = 'info') -> None:
    """Print a separator for each execution step."""
    print_separator("-", 60, color, f"Step {step}")

def print_stage_separator(stage_name: str, color: str = 'info') -> None:
    """Print a separator for different execution stages."""
    print()  # Empty line before
    print_separator("=", 80, color, stage_name)
    print()  # Empty line after

def print_agent_action(agent_id: str, action_type: str, message: str, color: str = 'info') -> None:
    """
    Print an agent action with consistent formatting.
    
    Args:
        agent_id: Agent identifier
        action_type: Type of action (PROPOSE, COMMIT, PLAN, etc.)
        message: Action message
        color: Color for the output
    """
    prefix = f"[{action_type}] {agent_id}:"
    print_color(f"{prefix} {message}", color)

def print_historical_insights(insights: Dict[str, Any], color: str = 'communication_proposal') -> None:
    """
    Print historical insights with formatting.
    
    Args:
        insights: Dictionary containing historical insights
        color: Color for the output
    """
    print_color("=== HISTORICAL INSIGHTS ===", color)
    
    for category, data in insights.items():
        if isinstance(data, dict):
            print_color(f"{category.upper()}:", color)
            for key, value in data.items():
                print_color(f"  {key}: {value}", color)
        else:
            print_color(f"{category}: {data}", color)
    print()

def print_enhanced_summary(title: str, items: list, color: str = 'success') -> None:
    """
    Print a summary with enhanced formatting.
    
    Args:
        title: Title for the summary
        items: List of items to display
        color: Color for the output
    """
    print_color(f"\n=== {title.upper()} ===", color)
    for i, item in enumerate(items, 1):
        print_color(f"  {i}. {item}", color)
    print()

def print_success(message: str) -> None:
    """Print a success message."""
    print_color(f"✓ {message}", 'success')

def print_error(message: str) -> None:
    """Print an error message."""
    print_color(f"✗ {message}", 'error')

def print_info(message: str) -> None:
    """Print an info message."""
    print_color(f"ℹ {message}", 'info')

def print_debug(message: str) -> None:
    """Print a debug message."""
    print_color(f"[DEBUG] {message}", 'debug')

# Episode-specific formatting functions
def print_episode_start(episode_num: int, config: Dict[str, Any]) -> None:
    """Print episode start information."""
    print_stage_header("EPISODE START", details=f"Episode {episode_num:02d}")
    print_color(f"Configuration: {config}", 'episode_start')
    print()

def print_episode_end(episode_num: int, success: bool, steps: int) -> None:
    """Print episode end information."""
    status = "SUCCESS" if success else "INCOMPLETE"
    print_stage_header("EPISODE END", details=f"Episode {episode_num:02d} - {status}")
    print_color(f"Steps completed: {steps}", 'episode_end')
    print_color(f"Episode result: {status}", 'success' if success else 'error')
    print()

def print_universe_update(universe_path: str, episode_count: int) -> None:
    """Print universe update information."""
    print_stage_header("UNIVERSE UPDATE", details="Continuous Learning")
    print_color(f"Universe location: {universe_path}", 'universe_update')
    print_color(f"Total episodes in universe: {episode_count}", 'universe_update')
    print()

# Template for consistent messaging
class StageMessages:
    """Predefined messages for different stages."""
    
    COMMUNICATION_START = "Starting enhanced communication round..."
    COMMUNICATION_PROPOSAL = "Agents making proposals with historical insights"
    COMMUNICATION_COMMIT = "Agents committing to tasks based on proposals"
    PLANNING_START = "Starting enhanced planning phase..."
    PLANNING_COMPLETE = "All agents have completed planning"
    EXECUTION_START = "Starting plan execution..."
    EXECUTION_STEP = "Executing symbolic actions"
    
    @staticmethod
    def agent_proposes(agent_id: str, block_id: int, reason: str) -> str:
        return f"PROPOSES Block {block_id} - {reason[:60]}{'...' if len(reason) > 60 else ''}"
    
    @staticmethod
    def agent_commits(agent_id: str, task_name: str) -> str:
        return f"COMMITS to {task_name}"
    
    @staticmethod
    def agent_plans(agent_id: str, task_name: str, num_actions: int) -> str:
        return f"PLANNED {task_name} with {num_actions} actions"
    
    @staticmethod
    def agent_executes(agent_id: str, action: str) -> str:
        return f"EXECUTING {action}"

# Backwards compatibility
def print_colored(text: str, color: str) -> None:
    """Backwards compatibility function."""
    print_color(text, color)

#!/usr/bin/env python3
"""
Dual Timeline LLM Agent Log Visualizer
======================================

Creates a three-tier timeline visualization:
1. Communication Timeline (top) - thin vertical lines showing communication events
2. Plan Timeline (middle) - showing high-level plan phases  
3. Action Timeline (bottom) - showing individual symbolic actions

Based on the new clean JSONL log format.

Usage:
    python log_visualizer.py [log_file.json] [-o output.png]
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Rectangle
import argparse
from dataclasses import dataclass
import textwrap

# Color scheme based on original design
ACTION_COLORS = {
    'MoveToBlock': '#FF6B6B',      # Red
    'Push': '#4ECDC4',             # Teal
    'Rendezvous': '#45B7D1',       # Blue
    'Wait': '#FFB347',             # Orange
    'YieldFace': '#E8E8E8',        # Light gray
    'WaitAgents': '#D3D3D3',       # Gray
    None: '#E8E8E8'                # Light gray for None
}

PLAN_COLORS = {
    'plan_success': '#28a745',       # Green for successful plans
    'plan_failure': '#dc3545',       # Red for failed plans  
    'plan_ongoing': '#6c757d',       # Gray for ongoing plans
    'unknown': '#D3D3D3'             # Gray for unknown
}

COMMUNICATION_COLOR = '#9B59B6'  # Purple for communication events

@dataclass
class Block:
    start: int
    end: int
    label: str
    color: str
    meta: Dict[str, Any]

@dataclass
class AgentStep:
    step: int
    action_type: Optional[str]
    action_args: str
    phase: str
    plan_progress: str
    committed_task: Optional[str]
    assigned_block: Optional[int]
    raw_action: int

def load_log_data(log_file: str) -> Dict[str, Any]:
    """Load log data from JSON file."""
    try:
        with open(log_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading log file {log_file}: {e}")
        return {}

def extract_agent_steps(log_data: Dict[str, Any]) -> Tuple[List[str], Dict[str, List[AgentStep]]]:
    """Extract agent timeline data from the new log format."""
    agents = set()
    agent_steps = {}
    
    execution_timeline = log_data.get('execution_timeline', [])
    
    for entry in execution_timeline:
        if entry.get('event_type') != 'timestep':
            continue
            
        step = entry.get('step', 0)
        actions = entry.get('actions', {})
        agents_data = entry.get('agents', {})
        
        for agent_id, agent_info in agents_data.items():
            agents.add(agent_id)
            
            if agent_id not in agent_steps:
                agent_steps[agent_id] = []
            
            # Extract action type from current_action
            current_action = agent_info.get('current_action', {})
            action_type = current_action.get('type')
            action_str = current_action.get('str', '')
            
            # Extract arguments from action string
            action_args = ''
            if action_str and '(' in action_str and ')' in action_str:
                start_idx = action_str.find('(')
                end_idx = action_str.rfind(')')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    action_args = action_str[start_idx+1:end_idx]
            
            agent_step = AgentStep(
                step=step,
                action_type=action_type,
                action_args=action_args,
                phase=agent_info.get('phase', 'unknown'),
                plan_progress=agent_info.get('plan_progress', '0/0'),
                committed_task=agent_info.get('committed_task'),
                assigned_block=agent_info.get('assigned_block'),
                raw_action=actions.get(agent_id, 0)
            )
            
            agent_steps[agent_id].append(agent_step)
    
    return sorted(list(agents)), agent_steps

def extract_communication_events(log_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract communication events from the log."""
    communication_events = []
    
    # First check the communication_events section
    comm_events = log_data.get('communication_events', [])
    for entry in comm_events:
        if entry.get('event_type') == 'communication_completed':
            communication_events.append({
                'step': entry.get('step', 0),
                'participant_count': entry.get('participant_count', 0),
                'communication_type': entry.get('communication_type', 'unknown'),
                'participants': entry.get('participants', [])
            })
    
    # Also check execution_timeline for communication events
    execution_timeline = log_data.get('execution_timeline', [])
    for entry in execution_timeline:
        if entry.get('event_type') == 'communication_completed':
            communication_events.append({
                'step': entry.get('step', 0),
                'participant_count': entry.get('participant_count', 0),
                'communication_type': entry.get('communication_type', 'unknown'),
                'participants': entry.get('participants', [])
            })
    
    return communication_events

def extract_plan_completion_events(log_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Extract plan execution completion events to determine plan success/failure."""
    plan_results = {}
    
    # Check execution_timeline for plan execution completion events
    execution_timeline = log_data.get('execution_timeline', [])
    for entry in execution_timeline:
        if entry.get('event_type') == 'plan_execution_completed':
            # Use 'step' field if available, fallback to 't' field
            step = entry.get('step') or entry.get('t', 0)
            agents_plan_results = entry.get('agents_plan_results', {})
            
            # Store plan results by agent
            for agent_id, result in agents_plan_results.items():
                if agent_id not in plan_results:
                    plan_results[agent_id] = []
                
                plan_results[agent_id].append({
                    'step': step,
                    'success': result.get('plan_successful', False),
                    'target_block': result.get('target_block'),
                    'committed_task': result.get('committed_task')
                })
    
    return plan_results

def create_plan_blocks(agent_steps: List[AgentStep], plan_completions: Dict[str, Any] = None, agent_id: str = "unknown") -> List[Block]:
    """Create blocks for plan timeline based on plan progress resets."""
    if not agent_steps:
        return []

    blocks = []
    
    def parse_progress(progress_str):
        """Parse progress string like '2/3' into (current, total)"""
        try:
            if '/' in progress_str:
                current, total = progress_str.split('/')
                return int(current), int(total)
            return 0, 0
        except (ValueError, AttributeError):
            return 0, 0
    
    def get_plan_color(plan_start_step: int, plan_end_step: int, agent_id: str) -> str:
        """Determine plan color based on completion status."""
        if not plan_completions or agent_id not in plan_completions:
            return PLAN_COLORS['plan_ongoing']
        
        # Find completion event that matches this plan timeframe
        for completion in plan_completions[agent_id]:
            completion_step = completion['step']
            # Plan completed if completion step is at or after plan end
            if completion_step >= plan_end_step:
                return PLAN_COLORS['plan_success'] if completion['success'] else PLAN_COLORS['plan_failure']
        
        # No completion found for this plan
        return PLAN_COLORS['plan_ongoing']

    # Extract agent_id from parameter
    # agent_id is now passed as a parameter

    plan_start = 0
    
    for i, step in enumerate(agent_steps):
        progress = step.plan_progress
        current, total = parse_progress(progress)
        
        # Plan reset detected: progress goes back to 0 (but not at the very beginning)
        if current == 0 and total > 0 and i > 0:
            prev_current, prev_total = parse_progress(agent_steps[i-1].plan_progress)
            # Only treat as reset if previous progress was not 0
            if prev_current != 0:
                # End previous plan block
                if plan_start < i:
                    # Get committed task for the label
                    committed_task = agent_steps[plan_start].committed_task or "Unknown"
                    label = f"Plan ({committed_task})"
                    
                    plan_start_step = agent_steps[plan_start].step
                    plan_end_step = agent_steps[i-1].step
                    
                    blocks.append(Block(
                        start=plan_start_step,
                        end=plan_end_step,
                        label=label,
                        color=get_plan_color(plan_start_step, plan_end_step, agent_id),
                        meta={'plan_type': 'plan', 'duration': plan_end_step - plan_start_step + 1, 'committed_task': committed_task}
                    ))
                # Start new plan block
                plan_start = i

    # Add final plan block
    if plan_start < len(agent_steps):
        # Get committed task for the label
        committed_task = agent_steps[plan_start].committed_task or "Unknown"
        label = f"Plan ({committed_task})"
        
        plan_start_step = agent_steps[plan_start].step
        plan_end_step = agent_steps[-1].step
        
        blocks.append(Block(
            start=plan_start_step,
            end=plan_end_step,
            label=label,
            color=get_plan_color(plan_start_step, plan_end_step, agent_id),
            meta={'plan_type': 'plan', 'duration': plan_end_step - plan_start_step + 1, 'committed_task': committed_task}
        ))
    
    return blocks

def create_action_blocks(agent_steps: List[AgentStep]) -> List[Block]:
    """Create blocks for action timeline based on consecutive identical actions."""
    if not agent_steps:
        return []
    
    blocks = []
    current_start = agent_steps[0].step
    current_action_type = agent_steps[0].action_type
    current_action_args = agent_steps[0].action_args
    current_phase = agent_steps[0].phase
    
    for i, step in enumerate(agent_steps):
        # Check if we need to start a new block (action type or args changed)
        if (step.action_type != current_action_type or 
            step.action_args != current_action_args or
            step.phase != current_phase):
            
            # Close the previous block
            label = current_action_type if current_action_type else "Unknown"
            if current_action_args:
                label += f"({current_action_args})"
            
            color = ACTION_COLORS.get(current_action_type, ACTION_COLORS[None])
            
            blocks.append(Block(
                start=current_start,
                end=agent_steps[i-1].step if i > 0 else current_start,
                label=label,
                color=color,
                meta={
                    'action_type': current_action_type, 
                    'action_args': current_action_args,
                    'phase': current_phase
                }
            ))
            
            # Start new block
            current_start = step.step
            current_action_type = step.action_type
            current_action_args = step.action_args
            current_phase = step.phase
    
    # Close the final block
    label = current_action_type if current_action_type else "Unknown"
    if current_action_args:
        label += f"({current_action_args})"
    
    color = ACTION_COLORS.get(current_action_type, ACTION_COLORS[None])
    
    blocks.append(Block(
        start=current_start,
        end=agent_steps[-1].step,
        label=label,
        color=color,
        meta={
            'action_type': current_action_type,
            'action_args': current_action_args, 
            'phase': current_phase
        }
    ))
    
    return blocks

def wrap_args(args: str, max_len_per_line: int = 10, max_lines: Optional[int] = None) -> str:
    """Wrap argument string on comma boundaries first, then by length."""
    if not args:
        return ""
    # Prefer splitting by comma to keep args grouped
    parts = [p.strip() for p in args.split(',')]
    lines: List[str] = []
    if len(parts) > 1:
        current = []
        current_len = 0
        for p in parts:
            seg = (p + ',') if not p.endswith(',') else p
            # +1 accounts for space when joining
            if current_len + len(seg) + (1 if current else 0) > max_len_per_line and current:
                lines.append(' '.join(current).rstrip(','))
                current = [seg]
                current_len = len(seg)
            else:
                current.append(seg)
                current_len += len(seg) + (1 if current_len > 0 else 0)
        if current:
            lines.append(' '.join(current).rstrip(','))
    else:
        lines = textwrap.wrap(args, width=max_len_per_line) or [args]

    # Optionally cap to max_lines (when provided)
    if isinstance(max_lines, int) and max_lines > 0 and len(lines) > max_lines:
        lines = lines[:max_lines]
    return '\n'.join(lines)

def create_dual_visualization(log_data: Dict[str, Any], output_file: Optional[str] = None):
    """Create a three-tier timeline visualization."""
    agents, agent_steps = extract_agent_steps(log_data)
    communication_events = extract_communication_events(log_data)
    plan_completions = extract_plan_completion_events(log_data)
    
    if not agents:
        print("No agents found in log data")
        return
    
    # Calculate max step
    max_step = 0
    for steps in agent_steps.values():
        if steps:
            max_step = max(max_step, steps[-1].step)
    
    num_agents = len(agents)
    
    # Create subplot: 1 communication row + 2 rows per agent (plan + action)
    total_rows = 1 + (2 * num_agents)
    fig, ax = plt.subplots(figsize=(max(15, max_step * 0.5), max(10, total_rows * 1.5)))
    
    # Set white background
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    # Set up the plot
    ax.set_xlim(0, max_step + 1)
    ax.set_ylim(-0.5, total_rows - 0.5)
    ax.margins(x=0.02, y=0.05)
    
    # Plot communication timeline at the top
    comm_row = total_rows - 1
    for comm_event in communication_events:
        step = comm_event['step']
        participant_count = comm_event['participant_count']
        comm_type = comm_event['communication_type']
        
        # Draw thin vertical line
        ax.axvline(x=step, ymin=(comm_row - 0.4) / total_rows, ymax=(comm_row + 0.4) / total_rows, 
                  color=COMMUNICATION_COLOR, linewidth=2, alpha=0.8)
        
        # Add label with participant count
        ax.text(step, comm_row + 0.2, f"{participant_count}", 
               ha='center', va='bottom', fontsize=8, fontweight='bold',
               bbox=dict(facecolor='white', edgecolor=COMMUNICATION_COLOR, alpha=0.8, pad=0.2))
        
        # Add communication type below the line
        ax.text(step, comm_row - 0.2, comm_type, 
               ha='center', va='top', fontsize=6, rotation=90)
    
    # Plot agent timelines
    for i, agent_id in enumerate(agents):
        # Row indices (from bottom up)
        action_row = (num_agents - 1 - i) * 2        # Actions on bottom of agent pair
        plan_row = (num_agents - 1 - i) * 2 + 1      # Plans on top of agent pair
        
        # Get agent blocks
        plan_blocks = create_plan_blocks(agent_steps[agent_id], plan_completions, agent_id)
        action_blocks = create_action_blocks(agent_steps[agent_id])
        
        # Plot plan timeline
        for block in plan_blocks:
            duration = block.end - block.start + 1
            
            # Create rectangle
            rect = Rectangle(
                (block.start, plan_row - 0.4), duration, 0.8,
                facecolor=block.color,
                edgecolor='black',
                linewidth=0.8,
                alpha=0.8
            )
            ax.add_patch(rect)
            
            # Add plan text
            if duration >= 2:
                text_x = block.start + duration / 2
                ax.text(text_x, plan_row, block.label, 
                       ha='center', va='center', fontsize=6, fontweight='bold')
        
        # Plot action timeline
        for block in action_blocks:
            duration = block.end - block.start + 1
            
            # Create rectangle
            rect = Rectangle(
                (block.start, action_row - 0.4), duration, 0.8,
                facecolor=block.color,
                edgecolor='black',
                linewidth=0.8,
                alpha=0.8
            )
            ax.add_patch(rect)
            
            # Add action text with arguments
            if block.meta['action_type'] and duration >= 1:
                text_x = block.start + duration / 2
                
                # Prepare display text
                action_type = block.meta['action_type']
                action_args = block.meta.get('action_args', '')
                
                display_text = action_type
                if action_args:
                    wrapped = wrap_args(action_args, max_len_per_line=10, max_lines=None)
                    display_text = f"{action_type}({wrapped})"
                
                fontsize = 4  # very small font to fit vertical text
                ax.text(
                    text_x, action_row + 0.1, display_text,
                    ha='center', va='center', fontsize=fontsize, fontweight='bold',
                    rotation=90, clip_on=False,
                    bbox=dict(facecolor='white', edgecolor='none', alpha=0.6, pad=0.2),
                    zorder=5,
                )
    
    # Customize plot
    ax.set_xlabel('Environment Step', fontsize=10, fontweight='bold')
    ax.set_ylabel('Agent Timelines', fontsize=10, fontweight='bold')
    ax.set_title(f'Multi-Agent Timeline Visualization\nSteps: {max_step} | Agents: {num_agents} | Communications: {len(communication_events)}', 
                fontsize=12, fontweight='bold')
    
    # Set y-tick labels
    y_labels = ['Communication']
    for i in range(num_agents):
        agent_id = agents[i]
        y_labels.extend([f"{agent_id} Plan", f"{agent_id} Action"])
    
    ax.set_yticks(range(total_rows))
    ax.set_yticklabels(y_labels[::-1], fontsize=8)
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Create legends
    comm_legend_elements = [
        patches.Patch(color=COMMUNICATION_COLOR, label="Communication Event")
    ]
    
    plan_legend_elements = [
        patches.Patch(color=PLAN_COLORS['plan_success'], label="Successful Plan"),
        patches.Patch(color=PLAN_COLORS['plan_failure'], label="Failed Plan"),
        patches.Patch(color=PLAN_COLORS['plan_ongoing'], label="Ongoing Plan")
    ]
    
    action_legend_elements = []
    for action, color in ACTION_COLORS.items():
        if action not in [None]:
            action_label = action.replace('_', ' ') if action else 'Unknown'
            action_legend_elements.append(patches.Patch(color=color, label=action_label))
    
    # Create three legends
    comm_legend = ax.legend(handles=comm_legend_elements, loc='upper left', 
                           bbox_to_anchor=(1.02, 1), title="Communication", 
                           fontsize=6, title_fontsize=7)
    plan_legend = ax.legend(handles=plan_legend_elements, loc='upper left', 
                           bbox_to_anchor=(1.02, 0.8), title="Plans", 
                           fontsize=6, title_fontsize=7)
    action_legend = ax.legend(handles=action_legend_elements, loc='upper left', 
                             bbox_to_anchor=(1.02, 0.5), title="Actions",
                             fontsize=6, title_fontsize=7)
    ax.add_artist(comm_legend)
    ax.add_artist(plan_legend)
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight', pad_inches=0.25, 
                   facecolor='white', edgecolor='white')
        print(f"Timeline visualization saved to: {output_file}")
    else:
        plt.show()
    
    return fig, ax

def main():
    parser = argparse.ArgumentParser(description='Create dual timeline visualization from LLM agent logs')
    parser.add_argument('log_file', nargs='?', default='runs/complete_execution_log.json',
                       help='Path to the JSON log file')
    parser.add_argument('-o', '--output', help='Output PNG file path')
    parser.add_argument('--summary', action='store_true', help='Print log summary')
    
    args = parser.parse_args()
    
    if not Path(args.log_file).exists():
        print(f"Log file not found: {args.log_file}")
        return
    
    print(f"📖 Loading log: {args.log_file}")
    log_data = load_log_data(args.log_file)
    
    if not log_data:
        print("No log data found")
        return
    
    # Print summary if requested
    if args.summary:
        agents, agent_steps = extract_agent_steps(log_data)
        communication_events = extract_communication_events(log_data)
        
        max_step = 0
        for steps in agent_steps.values():
            if steps:
                max_step = max(max_step, steps[-1].step)
        
        print(f"\n📊 Execution Summary:")
        print(f"   Total timesteps: {max_step}")
        print(f"   Total agents: {len(agents)}")
        print(f"   Communication events: {len(communication_events)}")
        
        print(f"\n🎯 Final Agent Assignments:")
        for agent_id in agents:
            steps = agent_steps[agent_id]
            if steps and steps[-1].committed_task:
                block_id = steps[-1].assigned_block
                print(f"   {agent_id} → Block {block_id}")
        return
    
    print("🎨 Creating timeline visualization...")
    output_file = args.output if args.output else f"{Path(args.log_file).stem}_timeline.png"
    create_dual_visualization(log_data, output_file)

if __name__ == "__main__":
    main()

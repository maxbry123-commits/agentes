"""
Log Visualizer - Create dual timeline visualizations from agent activity logs
===========================================================================
Reads JSON log files and creates dual timeline charts showing agent plans and actions over time.
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from typing import Dict, List, Any, Optional
import numpy as np
import textwrap

# Color mapping for different action types
ACTION_COLORS = {
    'MoveToBlock': '#FF6B6B',      # Red
    'Push': '#4ECDC4',             # Teal
    'Rendezvous': '#45B7D1',            # Blue
    'Wait': '#FFB347',             # Orange
    'YieldFace': '#E8E8E8',             # Light gray
    'WaitAgents': '#D3D3D3',            # Gray
    None: '#E8E8E8'                # Light gray for None
}

PLAN_COLORS = {
    'plan': '#FF6666',       # Single red color for all plans
    'unknown': '#D3D3D3'     # Gray for unknown
}

def load_agent_log(json_file: str) -> List[Dict[str, Any]]:
    """Load agent activity log from JSON file"""
    with open(json_file, 'r') as f:
        return json.load(f)

def extract_dual_timeline_data(log_data):
    """Extract separate timeline data for plans and actions"""
    # Get agent IDs
    agent_ids = set()
    for entry in log_data:
        if 'agents' in entry:
            agent_ids.update(entry['agents'].keys())
    agent_ids = sorted(agent_ids)
    
    # Raw timeline data
    raw_timeline_data = {agent_id: [] for agent_id in agent_ids}
    steps = []
    
    for entry in log_data:
        if entry.get('event_type') == 'step_update' and 'agents' in entry:
            step = entry['step']
            steps.append(step)
            
            for agent_id in agent_ids:
                if agent_id in entry['agents']:
                    agent_data = entry['agents'][agent_id]
                    action_type = agent_data.get('current_action', {}).get('type')
                    action_str = agent_data.get('current_action', {}).get('str', '')
                    
                    # Extract symbolic action arguments from action_str
                    action_args = ''
                    if action_str and '(' in action_str and ')' in action_str:
                        # Extract arguments from action string like "MoveToBlock(2, left)"
                        start_idx = action_str.find('(')
                        end_idx = action_str.rfind(')')
                        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                            action_args = action_str[start_idx+1:end_idx]
                    
                    phase = agent_data.get('phase', 'unknown')
                    progress = agent_data.get('plan_progress', '0/0')
                    
                    raw_timeline_data[agent_id].append({
                        'step': step,
                        'action_type': action_type,
                        'action_str': action_str,
                        'action_args': action_args,
                        'phase': phase,
                        'progress': progress
                    })
                else:
                    # Agent not present in this step
                    raw_timeline_data[agent_id].append({
                        'step': step,
                        'action_type': None,
                        'action_str': '',
                        'action_args': '',
                        'phase': 'unknown',
                        'progress': '0/0'
                    })
    
    # Create separate blocks for plans and actions
    plan_blocks = {agent_id: [] for agent_id in agent_ids}
    action_blocks = {agent_id: [] for agent_id in agent_ids}
    
    for agent_id in agent_ids:
        agent_data = raw_timeline_data[agent_id]
        if not agent_data:
            continue
            
        # Create plan blocks (each plan execution spans multiple actions)
        plan_blocks_list = []
        if agent_data:
            # Find when plans start and end based on plan resets
            plan_start = 0
            
            def parse_progress(progress_str):
                """Parse progress string like '2/3' into (current, total)"""
                try:
                    if '/' in progress_str:
                        current, total = progress_str.split('/')
                        return int(current), int(total)
                    return 0, 0
                except (ValueError, AttributeError):
                    return 0, 0
            
            for i, data_point in enumerate(agent_data):
                progress = data_point['progress']
                current, total = parse_progress(progress)
                
                # Plan reset detected: progress goes back to 0 (but not at the very beginning)
                if current == 0 and total > 0 and i > 0:
                    prev_current, prev_total = parse_progress(agent_data[i-1]['progress'])
                    # Only treat as reset if previous progress was not 0
                    if prev_current != 0:
                        # End previous plan block
                        if plan_start < i:
                            plan_blocks_list.append({
                                'start_step': agent_data[plan_start]['step'],
                                'end_step': agent_data[i-1]['step'],
                                'last_step': agent_data[i-1]['step'],
                                'plan_type': 'plan',
                                'duration': agent_data[i-1]['step'] - agent_data[plan_start]['step'] + 1
                            })
                        # Start new plan block
                        plan_start = i
            
            # Add final plan block
            if plan_start < len(agent_data):
                plan_blocks_list.append({
                    'start_step': agent_data[plan_start]['step'],
                    'end_step': agent_data[-1]['step'],
                    'last_step': agent_data[-1]['step'],
                    'plan_type': 'plan',
                    'duration': agent_data[-1]['step'] - agent_data[plan_start]['step'] + 1
                })
        
        plan_blocks[agent_id] = plan_blocks_list
        
        # Create action blocks (grouped by action type and phase)
        current_action_block = None
        for data_point in agent_data:
            step = data_point['step']
            action_type = data_point['action_type']
            action_str = data_point['action_str']
            action_args = data_point['action_args']
            phase = data_point['phase']
            progress = data_point['progress']
            
            if (current_action_block is None or 
                current_action_block['action_type'] != action_type or
                current_action_block['action_str'] != action_str or
                current_action_block['action_args'] != data_point['action_args'] or
                current_action_block['phase'] != phase):
                
                # Finish previous block
                if current_action_block is not None:
                    current_action_block['end_step'] = current_action_block['last_step']
                    action_blocks[agent_id].append(current_action_block)
                
                # Start new block
                current_action_block = {
                    'start_step': step,
                    'end_step': step,
                    'last_step': step,
                    'action_type': action_type,
                    'action_str': action_str,
                    'action_args': action_args,
                    'phase': phase,
                    'progress': progress,
                    'duration': 1
                }
            else:
                # Continue current block
                current_action_block['last_step'] = step
                current_action_block['duration'] = step - current_action_block['start_step'] + 1
                current_action_block['progress'] = progress
        
        # Finish the last action block
        if current_action_block is not None:
            current_action_block['end_step'] = current_action_block['last_step']
            action_blocks[agent_id].append(current_action_block)
    
    return plan_blocks, action_blocks, steps

def create_dual_timeline_visualization(json_file: str, output_file: str = None):
    """Create dual timeline visualization showing both plans and actions"""
    
    # Load and process data
    log_data = load_agent_log(json_file)
    plan_blocks, action_blocks, steps = extract_dual_timeline_data(log_data)
    
    if not plan_blocks or not action_blocks or not steps:
        print("No timeline data found in log file")
        return
    
    agent_ids = list(plan_blocks.keys())
    num_agents = len(agent_ids)
    max_step = max(steps) if steps else 0
    
    # Create figure with horizontal layout (swap width and height)
    total_rows = num_agents * 2
    fig, ax = plt.subplots(figsize=(12, 8 + total_rows * 0.8))
    
    # Set white background
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')
    
    # Set up the plot
    ax.set_xlim(0, max_step + 1)
    ax.set_ylim(-0.5, total_rows - 0.5)
    # Add small margins so texts outside bars aren't cut off
    ax.margins(x=0.02, y=0.05)

    def wrap_args(args: str, max_len_per_line: int = 10, max_lines: Optional[int] = None) -> str:
        """Wrap argument string on comma boundaries first, then by length. If max_lines is None, don't truncate."""
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
    
    # Plot timelines for each agent
    for i, agent_id in enumerate(agent_ids):
        action_row = i * 2        # Actions on bottom
        plan_row = i * 2 + 1      # Plans on top
        
        # Plot plan timeline (on top)
        agent_plan_blocks = plan_blocks[agent_id]
        
        for block in agent_plan_blocks:
            start_step = block['start_step']
            duration = block['duration']
            plan_type = block['plan_type']
            
            # Use single color for all plans
            color = PLAN_COLORS.get('plan', PLAN_COLORS['unknown'])
            
            # Create rectangle
            rect = patches.Rectangle(
                (start_step, plan_row - 0.4), duration, 0.8,
                facecolor=color,
                edgecolor='black',
                linewidth=0.8,
                alpha=0.8
            )
            ax.add_patch(rect)
            
            # Add plan text
            if duration >= 2:
                text_x = start_step + duration / 2
                fontsize = 6  # Very small font
                ax.text(text_x, plan_row, "Plan", 
                       ha='center', va='center', fontsize=fontsize, fontweight='bold')
        
        # Plot action timeline (on bottom)
        agent_action_blocks = action_blocks[agent_id]
        
        for block in agent_action_blocks:
            start_step = block['start_step']
            duration = block['duration']
            action_type = block['action_type']
            action_args = block.get('action_args', '')
            progress = block['progress']
            
            # Choose color based on action type
            color = ACTION_COLORS.get(action_type, ACTION_COLORS[None])  # Use None instead of 'other'
            
            # Create rectangle
            rect = patches.Rectangle(
                (start_step, action_row - 0.4), duration, 0.8,
                facecolor=color,
                edgecolor='black',
                linewidth=0.8,
                alpha=0.8
            )
            ax.add_patch(rect)
            
            # Add action text with arguments (always vertical, max 2 lines)
            if action_type and duration >= 1:
                text_x = start_step + duration / 2

                # Prepare display text - show action type and up to two wrapped lines of args
                display_text = action_type
                if action_args:
                    # No truncation: wrap to multiple lines as needed
                    wrapped = wrap_args(action_args, max_len_per_line=10, max_lines=None)
                    display_text = f"{action_type}({wrapped})"

                fontsize = 4  # very small font to fit vertical text
                ax.text(
                    text_x,
                    action_row + 0.1,
                    display_text,
                    ha='center', va='center', fontsize=fontsize, fontweight='bold',
                    rotation=90, clip_on=False,
                    bbox=dict(facecolor='white', edgecolor='none', alpha=0.6, pad=0.2),
                    zorder=5,
                )
            
            if progress != '0/0' and duration >= 1:
                fontsize = 3  # Very small font for progress
                ax.text(text_x, action_row - 0.1, progress, 
                       ha='center', va='center', fontsize=fontsize)
    
    # Customize plot
    ax.set_xlabel('Environment Step', fontsize=10, fontweight='bold')
    ax.set_ylabel('Agent Timelines', fontsize=10, fontweight='bold')
    ax.set_title(f'Dual Agent Timeline Visualization (Plans & Actions)\nTotal Steps: {max_step} | Agents: {num_agents}', 
                fontsize=12, fontweight='bold')
    
    # Set y-tick labels
    y_labels = []
    for i in range(num_agents):
        agent_id = agent_ids[num_agents - 1 - i]
        y_labels.extend([f"{agent_id} Plan", f"{agent_id} Action"])  # Plan first (top), then Action (bottom)
    
    ax.set_yticks(range(total_rows))
    ax.set_yticklabels(y_labels[::-1], fontsize=8)  # Small font for y-labels
    
    # Add grid
    ax.grid(True, alpha=0.3)
    
    # Create dual legend
    plan_legend_elements = []
    action_legend_elements = []
    
    # Plan legend
    plan_legend_elements.append(patches.Patch(color=PLAN_COLORS['plan'], label="Plan Execution"))
    
    # Action legend
    for action, color in ACTION_COLORS.items():
        if action not in ['other', 'idle', None]:
            action_label = action.replace('_', ' ') if action else 'Unknown'
            action_legend_elements.append(patches.Patch(color=color, label=action_label))
    
    # Create two legends
    plan_legend = ax.legend(handles=plan_legend_elements, loc='upper left', 
                           bbox_to_anchor=(1.02, 1), title="Plan Executions", 
                           fontsize=6, title_fontsize=7)
    action_legend = ax.legend(handles=action_legend_elements, loc='upper left', 
                             bbox_to_anchor=(1.02, 0.6), title="Actions",
                             fontsize=6, title_fontsize=7)
    ax.add_artist(plan_legend)  # Keep both legends
    
    # Leave a bit more room for legends and any text placed outside the axes
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight', pad_inches=0.25, facecolor='white', edgecolor='white')
        print(f"Dual timeline visualization saved to: {output_file}")
    else:
        plt.show()
    
    return fig, ax


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
        # Only create dual timeline visualization
        output_file = json_file.replace('.json', '_dual_timeline.png')
        create_dual_timeline_visualization(json_file, output_file)
        print(f"Dual timeline visualization saved to: {output_file}")
    else:
        print("Usage: python log_visualizer.py <json_file>")
        print("Example: python log_visualizer.py agent_activity_log_20250829_190054.json")

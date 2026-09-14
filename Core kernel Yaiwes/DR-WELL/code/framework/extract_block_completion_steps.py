#!/usr/bin/env python3
"""
Extract block completion times in environment steps from episode trace files.
This script parses the trace.json files to find when blocks are completed 
and creates a CSV with block completion times in environment steps.
"""

import json
import os
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse

def parse_trace_file(trace_file: str) -> Tuple[List[Dict], Dict]:
    """
    Parse a trace.json file to extract block completion information.
    
    Returns:
        - List of block completion events with step information
        - Episode summary information
    """
    try:
        with open(trace_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {trace_file}: {e}")
        return [], {}
    
    execution_timeline = data.get('execution_timeline', [])
    episode_summary = data.get('summary', {})
    
    # Track blocks over time to detect completion
    block_completions = []
    previous_blocks = None
    
    for event in execution_timeline:
        if event.get('event_type') == 'timestep':
            step = event.get('step')
            
            # We need to infer block state from the environment
            # Since the trace doesn't directly show block state, we'll look for
            # patterns in agent behavior or other indicators
            
            # For now, let's try a different approach - look for specific events
            # that might indicate block completion
            pass
    
    return block_completions, episode_summary

def find_block_completions_from_multiverse(multi_episode_file: str) -> List[Dict]:
    """
    Extract block completion data from multi_episode_summary.json file.
    This contains the block completion times but in seconds, not steps.
    We need to map these to environment steps.
    """
    try:
        with open(multi_episode_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {multi_episode_file}: {e}")
        return []
    
    episodes = data.get('episodes', [])
    results = []
    
    for episode in episodes:
        episode_num = episode.get('episode_num')
        total_steps = episode.get('total_steps')
        success = episode.get('success', False)
        block_completion_times = episode.get('block_completion_times', {})
        episode_duration = episode.get('episode_duration', 0)
        
        # For each completed block, estimate the completion step
        for block_id, completion_time_seconds in block_completion_times.items():
            if episode_duration > 0:
                # Estimate completion step based on proportion of time elapsed
                estimated_step = int((completion_time_seconds / episode_duration) * total_steps)
                
                results.append({
                    'episode_num': episode_num,
                    'block_id': int(block_id),
                    'completion_step': estimated_step,
                    'completion_time_seconds': completion_time_seconds,
                    'episode_total_steps': total_steps,
                    'episode_success': success,
                    'episode_duration': episode_duration
                })
    
    return results

def extract_exact_completion_steps(runs_dir: str) -> List[Dict]:
    """
    Try to extract exact completion steps by analyzing environment state changes
    in trace files alongside timing information.
    """
    results = []
    
    # Read the multi-episode summary for timing reference
    multi_episode_file = os.path.join(runs_dir, 'multi_episode_summary.json')
    if not os.path.exists(multi_episode_file):
        print(f"Multi-episode summary not found at {multi_episode_file}")
        return []
    
    with open(multi_episode_file, 'r') as f:
        multi_data = json.load(f)
    
    episodes = multi_data.get('episodes', [])
    
    for episode in episodes:
        episode_num = episode.get('episode_num')
        episode_folder = episode.get('episode_folder', f'episode_{episode_num:02d}')
        
        # Look for the trace file
        trace_file = os.path.join(runs_dir, f'episode_{episode_num:02d}', 'trace.json')
        if not os.path.exists(trace_file):
            print(f"Trace file not found: {trace_file}")
            continue
        
        try:
            with open(trace_file, 'r') as f:
                trace_data = json.load(f)
        except Exception as e:
            print(f"Error reading trace file {trace_file}: {e}")
            continue
        
        # Analyze the trace to find block completions
        block_completions = analyze_trace_for_block_completions(
            trace_data, episode_num, episode
        )
        results.extend(block_completions)
    
    return results

def analyze_trace_for_block_completions(trace_data: Dict, episode_num: int, episode_info: Dict) -> List[Dict]:
    """
    Analyze a single trace file to find exact block completion steps.
    """
    execution_timeline = trace_data.get('execution_timeline', [])
    block_completion_times = episode_info.get('block_completion_times', {})
    total_steps = episode_info.get('total_steps')
    success = episode_info.get('success', False)
    episode_duration = episode_info.get('episode_duration', 0)
    
    results = []
    
    # Since we don't have direct block state in the trace, we'll use timing correlation
    # Get the completion times from the episode info and try to map them to steps
    
    for block_id_str, completion_time_seconds in block_completion_times.items():
        block_id = int(block_id_str)
        
        # Method 1: Proportional estimation based on episode duration
        if episode_duration > 0:
            completion_step_estimated = int((completion_time_seconds / episode_duration) * total_steps)
        else:
            completion_step_estimated = None
        
        # Method 2: Try to find completion events in the trace
        # Look for patterns that might indicate block completion
        completion_step_exact = find_completion_step_in_trace(
            execution_timeline, block_id, completion_time_seconds, episode_duration, total_steps
        )
        
        # Use exact step if found, otherwise use estimation
        completion_step = completion_step_exact if completion_step_exact is not None else completion_step_estimated
        
        if completion_step is not None:
            results.append({
                'episode_num': episode_num,
                'block_id': block_id,
                'completion_step': completion_step,
                'completion_time_seconds': completion_time_seconds,
                'episode_total_steps': total_steps,
                'episode_success': success,
                'method': 'exact' if completion_step_exact is not None else 'estimated'
            })
    
    return results

def find_completion_step_in_trace(timeline: List[Dict], block_id: int, 
                                completion_time: float, episode_duration: float, 
                                total_steps: int) -> Optional[int]:
    """
    Try to find the exact step when a block was completed by analyzing the trace.
    """
    if not timeline or episode_duration <= 0:
        return None
    
    # Calculate the approximate step based on timing
    target_step = int((completion_time / episode_duration) * total_steps)
    
    # Look for events around that step that might indicate block completion
    search_range = 10  # Look within ±10 steps
    
    for event in timeline:
        if event.get('event_type') == 'timestep':
            step = event.get('step', 0)
            
            # Check if this step is near our target
            if abs(step - target_step) <= search_range:
                # Look for signs of block completion in agent behavior
                agents = event.get('agents', {})
                for agent_id, agent_info in agents.items():
                    assigned_block = agent_info.get('assigned_block')
                    committed_task = agent_info.get('committed_task', '')
                    
                    # Check if this agent was working on the target block
                    if (assigned_block == block_id or 
                        f'Block_{block_id}' in committed_task):
                        
                        # Look for completion indicators
                        phase = agent_info.get('phase', '')
                        if phase == 'finished' or 'completed' in phase.lower():
                            return step
    
    return None

def create_csv_output(block_data: List[Dict], output_file: str):
    """
    Create a CSV file with block completion data.
    """
    if not block_data:
        print("No block completion data found.")
        return
    
    # Sort by episode number and completion step
    block_data.sort(key=lambda x: (x['episode_num'], x.get('completion_step', 0)))
    
    fieldnames = [
        'episode_num', 'block_id', 'completion_step', 'completion_time_seconds',
        'episode_total_steps', 'episode_success'
    ]
    
    # Add method field if present
    if any('method' in item for item in block_data):
        fieldnames.append('method')
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in block_data:
            # Only write fields that exist in fieldnames
            filtered_row = {k: v for k, v in row.items() if k in fieldnames}
            writer.writerow(filtered_row)
    
    print(f"Block completion data saved to: {output_file}")
    print(f"Total records: {len(block_data)}")

def main():
    parser = argparse.ArgumentParser(description='Extract block completion times in environment steps')
    parser.add_argument('--runs-dir', default='runs', 
                       help='Directory containing episode data (default: runs)')
    parser.add_argument('--output', default='block_completion_steps.csv',
                       help='Output CSV file (default: block_completion_steps.csv)')
    parser.add_argument('--method', choices=['estimation', 'exact', 'both'], default='both',
                       help='Method to use for finding completion steps')
    
    args = parser.parse_args()
    
    # Check if runs directory exists
    if not os.path.exists(args.runs_dir):
        print(f"Runs directory not found: {args.runs_dir}")
        return
    
    print(f"Extracting block completion data from: {args.runs_dir}")
    
    if args.method in ['exact', 'both']:
        print("Attempting to extract exact completion steps from trace files...")
        block_data = extract_exact_completion_steps(args.runs_dir)
    
    if args.method in ['estimation', 'both'] or not block_data:
        if args.method == 'both' and block_data:
            print("Also extracting estimated completion steps...")
        else:
            print("Extracting estimated completion steps from multi-episode summary...")
        
        multi_episode_file = os.path.join(args.runs_dir, 'multi_episode_summary.json')
        estimated_data = find_block_completions_from_multiverse(multi_episode_file)
        
        if args.method == 'both':
            # Combine exact and estimated data
            block_data.extend(estimated_data)
        else:
            block_data = estimated_data
    
    if not block_data:
        print("No block completion data could be extracted.")
        return
    
    # Create CSV output
    create_csv_output(block_data, args.output)
    
    # Print summary statistics
    print("\nSummary:")
    episodes = set(item['episode_num'] for item in block_data)
    blocks = set(item['block_id'] for item in block_data)
    print(f"Episodes: {sorted(episodes)}")
    print(f"Blocks: {sorted(blocks)}")
    
    if 'method' in block_data[0]:
        methods = {}
        for item in block_data:
            method = item.get('method', 'unknown')
            methods[method] = methods.get(method, 0) + 1
        print(f"Methods used: {methods}")

if __name__ == '__main__':
    main()

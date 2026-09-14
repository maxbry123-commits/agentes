#!/usr/bin/env python3
"""
World Model
===========
A comprehensive world model that parses execution logs and creates a hierarchical graph representation
with Episode -> Tasks -> Plan Templates -> Plan Instances structure.
"""

import json
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from collections import OrderedDict

class WorldModel:
    def __init__(self, log_file='runs/complete_execution_log.json'):
        self.log_file = log_file
        self.graph = None
        self.task_data = {}
        self.episode_data = {}
        self.node_positions = {}
        self.node_labels = {}
        self.node_colors = []
        self.node_sizes = []
        
    def parse_log(self):
        """Parse the execution log and build the world model graph."""
        
        # Load data
        with open(self.log_file, 'r') as f:
            data = json.load(f)
        
        # Check if this is an exported world_model_graph.json format
        if 'world_model_data' in data:
            return self._parse_from_exported_graph(data)
        
        # Otherwise, parse as original execution log format
        return self._parse_from_execution_log(data)
    
    def _parse_from_exported_graph(self, data):
        """Parse from exported world_model_graph.json format."""
        world_model_data = data.get('world_model_data', {})
        self.task_data = world_model_data.get('task_data', {})
        self.episode_data = world_model_data.get('episode_data', {})
        
        # If we have valid data, build the graph
        if self.task_data and self.episode_data:
            self._build_graph()
            print(f"World model loaded from exported graph: {self.episode_data.get('total_blocks', 0)} tasks, {self.episode_data.get('completed_blocks', 0)} completed, episode {'completed' if self.episode_data.get('completed', False) else 'incomplete'}")
        else:
            # Initialize empty data if not found
            self.episode_data = {
                'completed': True,
                'max_timestep': 0,
                'total_blocks': 0,
                'completed_blocks': 0,
                'remaining_blocks': 0,
                'completed_blocks_order': [],
                'incomplete_blocks': []
            }
            self.task_data = {}
            self._build_graph()
            print("World model parsed: 0 tasks, 0 completed, episode completed")
        
        return self.graph, self.task_data, self.episode_data
    
    def _parse_from_execution_log(self, data):
        """Parse from original execution log format."""
    def _parse_from_execution_log(self, data):
        """Parse from original execution log format."""
        
        timeline = data.get('execution_timeline', [])
        communication_events = data.get('communication_events', [])
        
        print(f"Loaded {len(timeline)} timeline events and {len(communication_events)} communication events")
        
        # Extract plans with detailed tracking
        current_plans = {}
        seen_plan_signatures = set()
        
        # Process communication events to get initial commitments
        for comm_event in communication_events:
            step = comm_event.get('step', 0)
            communication_type = comm_event.get('communication_type', 'unknown')
            commitments = comm_event.get('commitments', {})
            participants = comm_event.get('participants', [])
            
            for agent_id in participants:
                if agent_id in commitments:
                    block_id = commitments[agent_id]
                    task_name = f"Block_{block_id}"
                    
                    # Get ALL agents' commitments (including this agent)
                    all_agents_commitments = {}
                    for agent, block in commitments.items():
                        all_agents_commitments[agent] = f"Block_{block}"
                    
                    # Create unique plan signature
                    plan_signature = f"{agent_id}_{task_name}_{communication_type}_{step}"
                    
                    if plan_signature not in seen_plan_signatures:
                        seen_plan_signatures.add(plan_signature)
                        current_plans[plan_signature] = {
                            'agent_id': agent_id,
                            'task_name': task_name,
                            'plan': [],
                            'start_step': step,
                            'all_agents_commitments': all_agents_commitments.copy(),
                            'success': None,
                            'end_step': None,
                            'communication_type': communication_type
                        }
        
        # Process timeline events to get actual plans and results
        for event in timeline:
            step = event.get('step', event.get('t', 0))
            
            if event.get('event_type') == 'timestep':
                agents_data = event.get('agents', {})
                
                # Update plans for agents
                for plan_sig, plan_info in current_plans.items():
                    if (plan_info['plan'] == [] and 
                        plan_info['agent_id'] in agents_data and
                        step >= plan_info['start_step']):
                        
                        agent_data = agents_data[plan_info['agent_id']]
                        plan = agent_data.get('plan', [])
                        committed_task = agent_data.get('committed_task')
                        
                        if plan and committed_task == plan_info['task_name']:
                            plan_info['plan'] = plan.copy()
            
            elif event.get('event_type') == 'plan_execution_completed':
                results = event.get('agents_plan_results', {})
                
                for agent_id, result in results.items():
                    target_block = result.get('target_block')
                    success = result.get('plan_successful', False)
                    task_name = f"Block_{target_block}"
                    
                    # Find matching plan and update success
                    for plan_sig, plan_info in current_plans.items():
                        if (plan_info['agent_id'] == agent_id and 
                            plan_info['task_name'] == task_name and 
                            plan_info['success'] is None):
                            plan_info['success'] = success
                            plan_info['end_step'] = step
                            break
        
        # Extract action templates from plans (remove arguments)
        def extract_action_template(action_str):
            """Extract action type without arguments."""
            parts = action_str.split()
            if len(parts) >= 1:
                return parts[0]
            return action_str
        
        def get_plan_template(plan_actions):
            """Get plan template (actions without arguments)."""
            return " -> ".join([extract_action_template(action) for action in plan_actions])
        
        # Organize by 3-level hierarchy: Task -> Plan Template -> Plan Instances
        task_data = {}
        max_timestep = 0
        completed_blocks_order = []  # Track completion order
        
        for plan_info in current_plans.values():
            if not plan_info['plan']:
                continue
                
            task_name = plan_info['task_name']
            plan_template = get_plan_template(plan_info['plan'])
            
            # Track max timestep
            if plan_info['end_step']:
                max_timestep = max(max_timestep, plan_info['end_step'])
            
            # Initialize task
            if task_name not in task_data:
                task_data[task_name] = {
                    'templates': {},
                    'final_success': False,
                    'completion_time': None,
                    'completion_order': None
                }
            
            # Initialize template
            if plan_template not in task_data[task_name]['templates']:
                task_data[task_name]['templates'][plan_template] = {
                    'instances': []
                }
            
            # Add instance
            task_data[task_name]['templates'][plan_template]['instances'].append(plan_info)
            
            # Update task success and completion time
            if plan_info['success'] and not task_data[task_name]['final_success']:
                task_data[task_name]['final_success'] = True
                task_data[task_name]['completion_time'] = plan_info['end_step']
        
        # Sort completed blocks by completion time to get order
        completed_tasks = [(task_name, task_info['completion_time']) 
                          for task_name, task_info in task_data.items() 
                          if task_info['final_success']]
        completed_tasks.sort(key=lambda x: x[1])  # Sort by completion time
        
        # Assign completion order
        for order, (task_name, _) in enumerate(completed_tasks, 1):
            task_data[task_name]['completion_order'] = order
            completed_blocks_order.append((task_name, task_data[task_name]['completion_time'], order))
        
        # Calculate episode completion status
        total_blocks = len(task_data)
        completed_blocks = len(completed_tasks)
        remaining_blocks = total_blocks - completed_blocks
        episode_completed = (remaining_blocks == 0)
        
        # Get incomplete blocks list
        incomplete_blocks = [task_name for task_name, task_info in task_data.items() 
                            if not task_info['final_success']]
        
        # Store episode data
        self.episode_data = {
            'completed': episode_completed,
            'max_timestep': max_timestep,
            'total_blocks': total_blocks,
            'completed_blocks': completed_blocks,
            'remaining_blocks': remaining_blocks,
            'completed_blocks_order': completed_blocks_order,
            'incomplete_blocks': incomplete_blocks
        }
        
        # Store task data
        self.task_data = task_data
        
        # Build the graph
        self._build_graph()
        
        print(f"World model parsed: {total_blocks} tasks, {completed_blocks} completed, episode {'completed' if episode_completed else 'incomplete'}")
        
        return self.graph, self.task_data, self.episode_data
    
    def _build_graph(self):
        """Build the NetworkX graph structure."""
        
        # Create NetworkX graph
        self.graph = nx.Graph()  # Use undirected graph for simpler visualization
        
        # Node colors
        colors = {
            'episode_complete': '#8e44ad',    # Purple for completed episode
            'episode_incomplete': '#e67e22',  # Orange for incomplete episode
            'task_success': '#2ecc71',        # Green
            'task_failed': '#e74c3c',         # Red
            'template_success': '#27ae60',    # Dark green
            'template_failed': '#c0392b',     # Dark red
            'instance_success': '#1e8449',    # Darker green
            'instance_failed': '#922b21',     # Darker red
            'instance_ongoing': '#5d6d7e'     # Gray
        }
        
        # Initialize data structures
        pos = {}
        node_colors = []
        node_sizes = []
        node_labels = {}
        
        # Add Episode node at the center
        episode_node = "EPISODE_STATUS"
        pos[episode_node] = (0, 0)  # Center position
        
        self.graph.add_node(episode_node, node_type='episode')
        
        # Create comprehensive episode label with completion details
        episode_status = "COMPLETED" if self.episode_data['completed'] else "INCOMPLETE"
        
        # Format completed blocks with order
        if self.episode_data['completed_blocks_order']:
            completed_str = ", ".join([f"{order}.{task}@T{time}" 
                                     for task, time, order in self.episode_data['completed_blocks_order']])
        else:
            completed_str = "None"
        
        # Format incomplete blocks
        if self.episode_data['incomplete_blocks']:
            incomplete_str = ", ".join(self.episode_data['incomplete_blocks'])
        else:
            incomplete_str = "None"
        
        episode_label = (f"EPISODE {episode_status}\n"
                        f"Final Timestep: {self.episode_data['max_timestep']}\n"
                        f"Total Blocks: {self.episode_data['total_blocks']}\n"
                        f"Completed ({self.episode_data['completed_blocks']}): {completed_str}\n"
                        f"Incomplete ({self.episode_data['remaining_blocks']}): {incomplete_str}")
        
        node_labels[episode_node] = episode_label
        
        # Color episode node
        if self.episode_data['completed']:
            node_colors.append(colors['episode_complete'])
        else:
            node_colors.append(colors['episode_incomplete'])
        node_sizes.append(6000)  # Even larger episode node for comprehensive info
        
        # Use circular layout for tasks around the episode node with more spacing
        task_count = len(self.task_data)
        task_radius = 10  # Increased radius for better spacing
        
        task_idx = 0
        for task_name, task_info in self.task_data.items():
            # Task node position (outer circle)
            task_angle = 2 * np.pi * task_idx / task_count
            task_x = task_radius * np.cos(task_angle)
            task_y = task_radius * np.sin(task_angle)
            pos[task_name] = (task_x, task_y)
            
            # Add task node
            self.graph.add_node(task_name, node_type='task')
            
            # Enhanced task label with completion info
            if task_info['final_success']:
                completion_info = f"COMPLETED\nOrder: #{task_info['completion_order']}\nTime: T{task_info['completion_time']}"
                task_label = f"{task_name}\n{completion_info}"
            else:
                task_label = f"{task_name}\nINCOMPLETE"
            
            node_labels[task_name] = task_label
            
            # Add edge from Episode to task
            self.graph.add_edge(episode_node, task_name)
            
            # Color task node
            if task_info['final_success']:
                node_colors.append(colors['task_success'])
            else:
                node_colors.append(colors['task_failed'])
            node_sizes.append(3500)  # Larger task nodes for completion info
            
            # Add template nodes with increased spacing
            template_count = len(task_info['templates'])
            template_radius = 6  # Increased radius for templates
            
            template_idx = 0
            for template_name, template_info in task_info['templates'].items():
                template_id = f"{task_name}_template_{template_idx}"
                
                # Template position with better spacing
                template_angle_offset = (template_idx - (template_count-1)/2) * 0.5  # Increased angle spacing
                template_angle = task_angle + template_angle_offset
                template_x = task_x + template_radius * np.cos(template_angle)
                template_y = task_y + template_radius * np.sin(template_angle)
                pos[template_id] = (template_x, template_y)
                
                # Add template node
                self.graph.add_node(template_id, node_type='template')
                self.graph.add_edge(task_name, template_id)
                
                # Template label (simplified)
                short_template = template_name.replace(' -> ', '\n')
                node_labels[template_id] = short_template
                
                # Color template node
                template_success = any(inst['success'] for inst in template_info['instances'])
                if template_success:
                    node_colors.append(colors['template_success'])
                else:
                    node_colors.append(colors['template_failed'])
                node_sizes.append(2500)  # Slightly larger templates
                
                # Add instance nodes with increased spacing
                instance_count = len(template_info['instances'])
                instance_radius = 3.5  # Increased radius for instances
                
                for instance_idx, instance in enumerate(template_info['instances']):
                    instance_id = f"{template_id}_instance_{instance_idx}"
                    
                    # Instance position with better spacing
                    instance_angle_offset = (instance_idx - (instance_count-1)/2) * 0.4  # Increased angle spacing
                    instance_angle = template_angle + instance_angle_offset
                    instance_x = template_x + instance_radius * np.cos(instance_angle)
                    instance_y = template_y + instance_radius * np.sin(instance_angle)
                    pos[instance_id] = (instance_x, instance_y)
                    
                    # Add instance node
                    self.graph.add_node(instance_id, node_type='instance')
                    self.graph.add_edge(template_id, instance_id)
                    
                    # Comprehensive instance label
                    agent_id = instance['agent_id']
                    start_step = instance['start_step']
                    end_step = instance['end_step'] if instance['end_step'] else 'Ongoing'
                    
                    # Full plan actions (truncated if too long)
                    full_plan = ' -> '.join(instance['plan'])
                    if len(full_plan) > 40:
                        full_plan = full_plan[:37] + '...'
                    
                    # All agents' commitments
                    commitments = []
                    for agent, task in instance['all_agents_commitments'].items():
                        commitments.append(f"{agent}:{task}")
                    commitment_str = ', '.join(commitments)
                    if len(commitment_str) > 35:
                        commitment_str = commitment_str[:32] + '...'
                    
                    # Success status
                    if instance['success'] is True:
                        status = "SUCCESS"
                    elif instance['success'] is False:
                        status = "FAILED"
                    else:
                        status = "ONGOING"
                    
                    # Communication context (abbreviated)
                    comm_type = instance['communication_type']
                    comm_abbrev = {
                        'initial': 'Init',
                        'individual_replan_step_14': 'Replan-14',
                        'individual_replan_step_25': 'Replan-25',
                        'individual_replan_step_26': 'Replan-26',
                        'individual_replan_step_47': 'Replan-47'
                    }.get(comm_type, comm_type[:10])
                    
                    # Create comprehensive label
                    comprehensive_label = (f"Agent: {agent_id}\n"
                                         f"Plan: {full_plan}\n"
                                         f"Steps: {start_step}-{end_step}\n"
                                         f"Commitments: {commitment_str}\n"
                                         f"Status: {status}\n"
                                         f"Context: {comm_abbrev}")
                    
                    node_labels[instance_id] = comprehensive_label
                    
                    # Color instance node
                    if instance['success'] is True:
                        node_colors.append(colors['instance_success'])
                    elif instance['success'] is False:
                        node_colors.append(colors['instance_failed'])
                    else:
                        node_colors.append(colors['instance_ongoing'])
                    node_sizes.append(1200)  # Slightly larger for comprehensive info
                
                template_idx += 1
            
            task_idx += 1
        
        # Store the layout data
        self.node_positions = pos
        self.node_labels = node_labels
        self.node_colors = node_colors
        self.node_sizes = node_sizes
    
    def visualize(self, save_path='world_model_graph.png', show_plot=True):
        """Visualize the world model graph."""
        
        if self.graph is None:
            raise ValueError("Graph not built. Call parse_log() first.")
        
        # Create visualization with better spacing
        plt.figure(figsize=(24, 20))  # Even larger figure for better spacing
        
        # Apply spring layout adjustment for better node repulsion
        # This will slightly adjust positions to reduce overlaps while keeping the overall structure
        episode_node = "EPISODE_STATUS"
        pos_adjusted = nx.spring_layout(self.graph, pos=self.node_positions, k=2, iterations=10, fixed=[episode_node])
        
        # Merge the adjusted positions but keep episode node fixed at center
        for node in pos_adjusted:
            if node != episode_node:
                self.node_positions[node] = pos_adjusted[node]
        
        # Draw the network
        nx.draw_networkx_nodes(self.graph, self.node_positions, node_color=self.node_colors, 
                              node_size=self.node_sizes, alpha=0.8)
        nx.draw_networkx_edges(self.graph, self.node_positions, edge_color='gray', alpha=0.6, width=1)
        
        # Draw labels with different sizes and formatting
        episode_labels = {k: v for k, v in self.node_labels.items() if self.graph.nodes[k].get('node_type') == 'episode'}
        task_labels = {k: v for k, v in self.node_labels.items() if self.graph.nodes[k].get('node_type') == 'task'}
        template_labels = {k: v for k, v in self.node_labels.items() if self.graph.nodes[k].get('node_type') == 'template'}
        instance_labels = {k: v for k, v in self.node_labels.items() if self.graph.nodes[k].get('node_type') == 'instance'}
        
        # Episode label (largest, bold, with background)
        for node_id, label in episode_labels.items():
            x, y = self.node_positions[node_id]
            plt.text(x, y, label, fontsize=14, ha='center', va='center', fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.5", facecolor="white", alpha=0.95, edgecolor="black", linewidth=2))
        
        # Task labels (large, bold)
        nx.draw_networkx_labels(self.graph, self.node_positions, task_labels, font_size=12, font_weight='bold')
        
        # Template labels (medium)
        nx.draw_networkx_labels(self.graph, self.node_positions, template_labels, font_size=8, font_weight='bold')
        
        # Instance labels (comprehensive, with background boxes for readability)
        for node_id, label in instance_labels.items():
            x, y = self.node_positions[node_id]
            plt.text(x, y, label, fontsize=6, ha='center', va='center',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.9, edgecolor="black"))
        
        # Add title and legend
        plt.title('4-Level Task Concept Graph\nEpisode Status (center) -> Tasks (around center) -> Plan Templates (outer) -> Plan Instances (detailed)\nPurple=Episode Complete, Orange=Episode Incomplete, Green=Success, Red=Failed, Gray=Ongoing', 
                  fontsize=16, fontweight='bold', pad=20)
        
        # Calculate statistics
        total_tasks = len(self.task_data)
        successful_tasks = sum(1 for task in self.task_data.values() if task['final_success'])
        total_templates = sum(len(task['templates']) for task in self.task_data.values())
        total_instances = sum(len(template['instances']) 
                             for task in self.task_data.values() 
                             for template in task['templates'].values())
        successful_instances = sum(1 for task in self.task_data.values() 
                                  for template in task['templates'].values() 
                                  for instance in template['instances'] 
                                  if instance['success'])
        
        # Add summary
        summary = (f"Summary: {successful_tasks}/{total_tasks} tasks completed ({successful_tasks/total_tasks*100:.1f}%) | "
                   f"{total_templates} unique templates | "
                   f"{successful_instances}/{total_instances} instances successful ({successful_instances/total_instances*100:.1f}%)")
        
        plt.figtext(0.5, 0.02, summary, ha='center', fontsize=11, 
                   bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.9))
        
        plt.axis('off')
        plt.tight_layout()
        
        # Save
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"World model graph saved as '{save_path}'")
        
        if show_plot:
            plt.show()
        else:
            plt.close()
        
        return save_path
    
    def save_graph(self, save_path='world_model_graph.pkl'):
        """Save the NetworkX graph structure to a file."""
        
        if self.graph is None:
            raise ValueError("Graph not built. Call parse_log() first.")
        
        import pickle
        
        # Save the complete graph structure with all data
        graph_data = {
            'graph': self.graph,
            'task_data': self.task_data,
            'episode_data': self.episode_data,
            'node_positions': self.node_positions,
            'node_labels': self.node_labels,
            'node_colors': self.node_colors,
            'node_sizes': self.node_sizes
        }
        
        with open(save_path, 'wb') as f:
            pickle.dump(graph_data, f)
        
        print(f"Graph structure saved to: {save_path}")
        return save_path
    
    def load_graph(self, load_path='world_model_graph.pkl'):
        """Load a previously saved graph structure."""
        
        import pickle
        
        with open(load_path, 'rb') as f:
            graph_data = pickle.load(f)
        
        self.graph = graph_data['graph']
        self.task_data = graph_data['task_data']
        self.episode_data = graph_data['episode_data']
        self.node_positions = graph_data['node_positions']
        self.node_labels = graph_data['node_labels']
        self.node_colors = graph_data['node_colors']
        self.node_sizes = graph_data['node_sizes']
        
        print(f"Graph structure loaded from: {load_path}")
        return self.graph
    
    def export_graph(self, save_path='world_model_graph', format='json'):
        """Export the graph structure in various formats.
        
        Args:
            save_path: Base path for saving (extension will be added)
            format: 'json', 'graphml', or 'gexf'
        """
        
        if self.graph is None:
            raise ValueError("Graph not built. Call parse_log() first.")
        
        if format == 'json':
            # Save as JSON with all node attributes
            import json
            graph_dict = nx.node_link_data(self.graph)
            
            # Add our custom data
            graph_dict['world_model_data'] = {
                'task_data': self.task_data,
                'episode_data': self.episode_data,
                'node_positions': self.node_positions,
                'node_labels': self.node_labels
            }
            
            json_path = f"{save_path}.json"
            with open(json_path, 'w') as f:
                json.dump(graph_dict, f, indent=2, default=str)
            
            print(f"Graph exported as JSON to: {json_path}")
            return json_path
            
        elif format == 'graphml':
            # Save as GraphML (compatible with Gephi, Cytoscape, etc.)
            graphml_path = f"{save_path}.graphml"
            nx.write_graphml(self.graph, graphml_path)
            print(f"Graph exported as GraphML to: {graphml_path}")
            return graphml_path
            
        elif format == 'gexf':
            # Save as GEXF (Gephi format)
            gexf_path = f"{save_path}.gexf"
            nx.write_gexf(self.graph, gexf_path)
            print(f"Graph exported as GEXF to: {gexf_path}")
            return gexf_path
            
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'json', 'graphml', or 'gexf'.")
    
    def visualize_text_concept_graph(self):
        """Create a text-based concept graph visualization."""
        
        if self.graph is None:
            raise ValueError("Graph not built. Call parse_log() first.")
        
        print("\n" + "="*140)
        print("4-LEVEL TASK CONCEPT GRAPH (TEXT)")
        print("="*140)
        
        # Episode Level
        episode_status = "COMPLETED" if self.episode_data['completed'] else "INCOMPLETE"
        print(f"\n┌─ EPISODE STATUS: {episode_status}")
        print(f"│   Final Timestep: {self.episode_data['max_timestep']}")
        print(f"│   Total Blocks: {self.episode_data['total_blocks']}")
        
        # Completed blocks with order
        if self.episode_data['completed_blocks_order']:
            completed_str = ", ".join([f"{order}.{task}@T{time}" 
                                     for task, time, order in self.episode_data['completed_blocks_order']])
            print(f"│   Completed ({self.episode_data['completed_blocks']}): {completed_str}")
        else:
            print(f"│   Completed (0): None")
        
        # Incomplete blocks
        if self.episode_data['incomplete_blocks']:
            incomplete_str = ", ".join(self.episode_data['incomplete_blocks'])
            print(f"│   Incomplete ({self.episode_data['remaining_blocks']}): {incomplete_str}")
        else:
            print(f"│   Incomplete (0): None")
        print("│")
        
        # Task Level
        for task_name, task_data in self.task_data.items():
            print(f"├─── TASK CONCEPT: {task_name}")
            if task_data['final_success']:
                print(f"│    Status: COMPLETED (Order #{task_data['completion_order']}, Time T{task_data['completion_time']})")
            else:
                print(f"│    Status: INCOMPLETE")
            print(f"│    Plan Templates: {len(task_data['templates'])}")
            print("│")
            
            # Template Level
            template_count = 0
            for template_name, template_info in task_data['templates'].items():
                template_count += 1
                template_success_count = sum(1 for inst in template_info['instances'] if inst['success'])
                template_success_rate = template_success_count / len(template_info['instances']) * 100
                
                print(f"│    ├─── PLAN TEMPLATE #{template_count}: {template_name}")
                print(f"│    │    Instances: {len(template_info['instances'])} total, {template_success_count} successful ({template_success_rate:.1f}%)")
                print("│    │")
                
                # Instance Level
                for i, instance in enumerate(template_info['instances'], 1):
                    if instance['success'] is True:
                        status_icon = "SUCCESS"
                        status_text = "SUCCESS"
                    elif instance['success'] is False:
                        status_icon = "FAILED"
                        status_text = "FAILED"
                    else:
                        status_icon = "ONGOING"
                        status_text = "ONGOING"
                    
                    print(f"│    │    ├── {status_icon} INSTANCE #{i}:")
                    print(f"│    │    │   Agent: {instance['agent_id']}")
                    print(f"│    │    │   Full Plan: {' -> '.join(instance['plan'])}")
                    print(f"│    │    │   Period: Step {instance['start_step']} to {instance['end_step'] if instance['end_step'] else 'Ongoing'}")
                    
                    # Show ALL agents' commitments at planning time
                    commitment_strs = []
                    for agent, task in instance['all_agents_commitments'].items():
                        commitment_strs.append(f"{agent}: {task}")
                    print(f"│    │    │   All Agents' Commitments: {', '.join(commitment_strs)}")
                    
                    print(f"│    │    │   Status: {status_text}")
                    print(f"│    │    │   Context: {instance['communication_type']}")
                    
                    if i < len(template_info['instances']):
                        print("│    │    │")
                
                if template_count < len(task_data['templates']):
                    print("│    │")
            
            print("│")
        
        print("└" + "─" * 80)
        print("\n" + "="*140)
        
        # Summary
        total_tasks = len(self.task_data)
        successful_tasks = sum(1 for task in self.task_data.values() if task['final_success'])
        total_templates = sum(len(task['templates']) for task in self.task_data.values())
        total_instances = sum(len(template['instances']) 
                             for task in self.task_data.values() 
                             for template in task['templates'].values())
        successful_instances = sum(1 for task in self.task_data.values() 
                                  for template in task['templates'].values() 
                                  for instance in template['instances'] 
                                  if instance['success'])
        
        print(f"SUMMARY:")
        print(f"   Tasks: {successful_tasks}/{total_tasks} completed successfully ({successful_tasks/total_tasks*100:.1f}%)")
        print(f"   Plan Templates: {total_templates} unique approaches tested")
        print(f"   Plan Instances: {successful_instances}/{total_instances} executed successfully ({successful_instances/total_instances*100:.1f}%)")
        print("="*140)

def create_world_model_from_log(log_file='runs/complete_execution_log.json', show_text=True, show_graph=True, save_graph=False, save_format='pkl'):
    """Convenience function to create and visualize a world model from a log file.
    
    Args:
        log_file: Path to the execution log file
        show_text: Whether to display text concept graph
        show_graph: Whether to display visual graph
        save_graph: Whether to save the graph structure
        save_format: Format for saving ('pkl', 'json', 'graphml', 'gexf')
    """
    world_model = WorldModel(log_file)
    graph, task_data, episode_data = world_model.parse_log()
    
    if show_text:
        world_model.visualize_text_concept_graph()
    
    if show_graph:
        world_model.visualize()
    
    if save_graph:
        if save_format == 'pkl':
            world_model.save_graph()
        else:
            world_model.export_graph(format=save_format)
    
    return world_model

if __name__ == "__main__":
    # Create world model
    world_model = create_world_model_from_log()


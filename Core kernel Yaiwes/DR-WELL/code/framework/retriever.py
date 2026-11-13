import json
from typing import Dict, Any, List, Optional

class UniverseRetriever:
    def __init__(self, universe_json_path: str = None, universe_data: Dict[str, Any] = None):
        """
        Initialize the retriever with either a file path or direct data.
        
        Args:
            universe_json_path: Path to the JSON file containing universe graph
            universe_data: Direct dictionary data (alternative to file path)
        """
        if universe_json_path:
            with open(universe_json_path, 'r') as f:
                self.universe = json.load(f)
        elif universe_data:
            self.universe = universe_data
        else:
            raise ValueError("Either universe_json_path or universe_data must be provided")
        
        # Extract different components of the universe structure
        self.nodes = self.universe.get("nodes", [])
        self.links = self.universe.get("links", [])
        self.universe_data = self.universe.get("universe_data", {})
        self.analytics = self.universe_data.get("views", {})  # COG, TCG, PDG data
        self.episodes_data = self.universe_data.get("episodes", {})
        self.stats = self.universe_data.get("stats", {})

    # ---------- 1. General Info ----------
    def get_general_info(self) -> Dict[str, Any]:
        """Get overall statistics about episodes and tasks"""
        episode_count = len(self.episodes_data)
        
        # Collect task statistics
        task_stats = {}
        total_instances = 0
        successful_tasks = 0
        
        for ep_id, ep_data in self.episodes_data.items():
            episode_info = ep_data.get("episode_data", {})
            task_data = ep_data.get("task_data", {})
            
            # Count tasks per episode
            for task_name, task_info in task_data.items():
                if task_name not in task_stats:
                    task_stats[task_name] = {
                        "episodes_seen": 0,
                        "total_instances": 0,
                        "successful_instances": 0,
                        "completion_rate": 0.0
                    }
                
                task_stats[task_name]["episodes_seen"] += 1
                
                # Count instances in templates
                for template_name, template_data in task_info.get("templates", {}).items():
                    instances = template_data.get("instances", [])
                    task_stats[task_name]["total_instances"] += len(instances)
                    total_instances += len(instances)
                    
                    # Count successful instances
                    successful = sum(1 for inst in instances if inst.get("success", False))
                    task_stats[task_name]["successful_instances"] += successful
                    successful_tasks += successful
        
        # Calculate completion rates
        for task_name in task_stats:
            total = task_stats[task_name]["total_instances"]
            successful = task_stats[task_name]["successful_instances"]
            task_stats[task_name]["completion_rate"] = successful / total if total > 0 else 0.0
        
        # Get overall completion rate from analytics if available
        overall_stats = self.stats
        
        return {
            "episodes_count": episode_count,
            "task_distribution": task_stats,
            "total_instances": total_instances,
            "successful_instances": successful_tasks,
            "overall_completion_rate": successful_tasks / total_instances if total_instances > 0 else 0.0,
            "overall_stats": overall_stats
        }

    # ---------- 2. Collaboration Info ----------
    def get_collaboration_info(self, task_name: str = None, episode_id: str = None) -> Dict[str, Any]:
        """
        Retrieve collaboration patterns and team compositions for tasks
        
        Args:
            task_name: Filter by specific task (optional)
            episode_id: Filter by specific episode (optional)
        """
        collaboration_patterns = []
        
        for ep_id, ep_data in self.episodes_data.items():
            if episode_id and ep_id != episode_id:
                continue
                
            task_data = ep_data.get("task_data", {})
            
            for t_name, t_info in task_data.items():
                if task_name and t_name != task_name:
                    continue
                    
                for template_name, template_data in t_info.get("templates", {}).items():
                    instances = template_data.get("instances", [])
                    
                    # Group instances by agent collaboration patterns
                    agent_patterns = {}
                    for instance in instances:
                        agent_id = instance.get("agent_id")
                        success = instance.get("success", False)
                        comm_type = instance.get("communication_type", "unknown")
                        start_step = instance.get("start_step", 0)
                        end_step = instance.get("end_step")
                        duration = end_step - start_step if (end_step is not None and start_step is not None and end_step > start_step) else None
                        
                        pattern_key = f"{t_name}_{template_name}_{comm_type}"
                        if pattern_key not in agent_patterns:
                            agent_patterns[pattern_key] = {
                                "task": t_name,
                                "template": template_name,
                                "communication_type": comm_type,
                                "agents": [],
                                "successes": 0,
                                "total_attempts": 0,
                                "avg_duration": None,
                                "durations": []
                            }
                        
                        agent_patterns[pattern_key]["agents"].append(agent_id)
                        agent_patterns[pattern_key]["total_attempts"] += 1
                        if success:
                            agent_patterns[pattern_key]["successes"] += 1
                        if duration:
                            agent_patterns[pattern_key]["durations"].append(duration)
                    
                    # Calculate averages
                    for pattern in agent_patterns.values():
                        if pattern["durations"]:
                            pattern["avg_duration"] = sum(pattern["durations"]) / len(pattern["durations"])
                        pattern["success_rate"] = pattern["successes"] / pattern["total_attempts"] if pattern["total_attempts"] > 0 else 0
                        pattern["episode"] = ep_id
                        collaboration_patterns.append(pattern)
        
        return {
            "collaboration_patterns": collaboration_patterns,
            "filter_task": task_name,
            "filter_episode": episode_id
        }

    def get_plan_prototypes(self, task_name: str) -> Dict[str, Any]:
        """
        Extract plan prototypes (symbolic actions without arguments) from all episodes for a specific task
        
        Args:
            task_name: Task name (e.g., "Block_1", "Block_2")
        
        Returns:
            Dictionary with plan prototypes sorted by success rate
        """
        plan_prototypes = {}
        
        # Access episodes from universe_data structure
        episodes = self.universe_data.get("episodes", {})
        
        for ep_id, ep_data in episodes.items():
            task_data = ep_data.get("task_data", {})
            
            if task_name not in task_data:
                continue
                
            task_info = task_data[task_name]
            templates = task_info.get("templates", {})
            
            for template_name, template_info in templates.items():
                instances = template_info.get("instances", [])
                
                for instance in instances:
                    plan = instance.get("plan", [])
                    success = instance.get("success", False)
                    start_step = instance.get("start_step", 0)
                    end_step = instance.get("end_step")
                    agent_id = instance.get("agent_id", "unknown")
                    all_agents_commitments = instance.get("all_agents_commitments", {})
                    
                    # Calculate team size from all_agents_commitments
                    team_size = len([agent for agent, task in all_agents_commitments.items() if task == task_name])
                    
                    # Extract symbolic actions without arguments
                    symbolic_actions = []
                    for action in plan:
                        # Extract just the action name (first word)
                        action_name = action.split()[0] if action.split() else action
                        symbolic_actions.append(action_name)
                    
                    # Create a prototype key
                    prototype_key = " -> ".join(symbolic_actions)
                    if not prototype_key:
                        prototype_key = "empty_plan"
                    
                    # Calculate duration
                    duration = end_step - start_step if (end_step is not None and start_step is not None and end_step > start_step) else None
                    
                    # Track this prototype
                    if prototype_key not in plan_prototypes:
                        plan_prototypes[prototype_key] = {
                            "symbolic_actions": symbolic_actions,
                            "attempts": 0,
                            "successes": 0,
                            "success_rate": 0.0,
                            "durations": [],
                            "avg_duration": None,
                            "agents": [],
                            "episodes": [],
                            "team_sizes": []
                        }
                    
                    plan_prototypes[prototype_key]["attempts"] += 1
                    plan_prototypes[prototype_key]["agents"].append(agent_id)
                    plan_prototypes[prototype_key]["episodes"].append(ep_id)
                    plan_prototypes[prototype_key]["team_sizes"].append(team_size)
                    
                    if success:
                        plan_prototypes[prototype_key]["successes"] += 1
                    
                    if duration is not None:
                        plan_prototypes[prototype_key]["durations"].append(duration)
        
        # Calculate averages and success rates
        for prototype_data in plan_prototypes.values():
            if prototype_data["attempts"] > 0:
                prototype_data["success_rate"] = prototype_data["successes"] / prototype_data["attempts"]
            
            if prototype_data["durations"]:
                prototype_data["avg_duration"] = sum(prototype_data["durations"]) / len(prototype_data["durations"])
            
            if prototype_data["team_sizes"]:
                prototype_data["avg_team_size"] = sum(prototype_data["team_sizes"]) / len(prototype_data["team_sizes"])
        
        # Sort by success rate, then by number of attempts
        sorted_prototypes = sorted(
            plan_prototypes.items(),
            key=lambda x: (x[1]["success_rate"], x[1]["attempts"]),
            reverse=True
        )
        
        return {
            "task_name": task_name,
            "plan_prototypes": dict(sorted_prototypes),
            "total_prototypes": len(plan_prototypes)
        }

    def get_plan_instances(self, task_name: str) -> Dict[str, Any]:
        """
        Extract detailed plan instances for a specific task, grouped by identical plans
        and sorted by success rate then duration
        
        Args:
            task_name: Task name (e.g., "Block_1", "Block_2")
        
        Returns:
            Dictionary with plan instances grouped and sorted
        """
        plan_instances = {}
        
        # Access episodes from universe_data structure
        episodes = self.universe_data.get("episodes", {})
        
        for ep_id, ep_data in episodes.items():
            task_data = ep_data.get("task_data", {})
            
            if task_name not in task_data:
                continue
                
            task_info = task_data[task_name]
            templates = task_info.get("templates", {})
            
            for template_name, template_info in templates.items():
                instances = template_info.get("instances", [])
                
                for instance in instances:
                    plan = instance.get("plan", [])
                    success = instance.get("success", False)
                    start_step = instance.get("start_step", 0)
                    end_step = instance.get("end_step")
                    
                    # Calculate duration
                    duration = end_step - start_step if (end_step is not None and start_step is not None and end_step > start_step) else None
                    
                    # Create a plan key (full plan with arguments)
                    plan_key = str(plan)  # Use string representation as key
                    
                    # Track this plan instance
                    if plan_key not in plan_instances:
                        plan_instances[plan_key] = {
                            "plan": plan,
                            "attempts": 0,
                            "successes": 0,
                            "success_rate": 0.0,
                            "durations": [],
                            "avg_duration": None,
                            "episodes": []
                        }
                    
                    plan_instances[plan_key]["attempts"] += 1
                    plan_instances[plan_key]["episodes"].append(ep_id)
                    
                    if success:
                        plan_instances[plan_key]["successes"] += 1
                    
                    if duration is not None:
                        plan_instances[plan_key]["durations"].append(duration)
        
        # Calculate averages and success rates
        for instance_data in plan_instances.values():
            if instance_data["attempts"] > 0:
                instance_data["success_rate"] = instance_data["successes"] / instance_data["attempts"]
            
            if instance_data["durations"]:
                instance_data["avg_duration"] = sum(instance_data["durations"]) / len(instance_data["durations"])
        
        # Sort by success rate, then by average duration (shorter is better)
        sorted_instances = sorted(
            plan_instances.items(),
            key=lambda x: (x[1]["success_rate"], -x[1]["avg_duration"] if x[1]["avg_duration"] else 0),
            reverse=True
        )
        
        return {
            "task_name": task_name,
            "plan_instances": dict(sorted_instances),
            "total_instances": len(plan_instances)
        }

    # ---------- 3. Plan Feedback using COG data ----------
    def get_plan_feedback(self, task: str, template_signature: str = None, team_size: int = None) -> Dict[str, Any]:
        """
        Get plan feedback using COG (Commitment-Outcome Graph) data
        
        Args:
            task: Task name (e.g., "Block_0", "Block_1")
            template_signature: Specific template pattern (optional)
            team_size: Specific team size to analyze (optional)
        """
        cog_data = self.analytics.get("COG", {})
        relevant_entries = []
        
        # Filter COG entries by task and other criteria
        for cog_key, cog_metrics in cog_data.items():
            if task in cog_key:
                # Parse the COG key to extract information
                # Format: "Task|bucket=X-Y|k=Z|comms=TYPE|template=TEMPLATE"
                if template_signature and template_signature not in cog_key:
                    continue
                if team_size and f"k={team_size}" not in cog_key:
                    continue
                
                relevant_entries.append({
                    "signature": cog_key,
                    "attempts": cog_metrics.get("attempts", 0),
                    "successes": cog_metrics.get("successes", 0),
                    "completion_rate": cog_metrics.get("cr", 0.0),
                    "avg_time": cog_metrics.get("avg_t")
                })
        
        # Sort by completion rate and then by efficiency (avg_time)
        relevant_entries.sort(key=lambda x: (x["completion_rate"], -x["avg_time"] if x["avg_time"] else 0), reverse=True)
        
        # Get k* recommendations if available
        kstar_data = self.analytics.get("COG_kstar", {})
        optimal_team_sizes = {}
        for key, kstar in kstar_data.items():
            if task in key:
                optimal_team_sizes[key] = kstar
        
        # Get PDG (Plan Dependency Graph) recommendations
        pdg_data = self.analytics.get("PDG", {})
        plan_recommendations = []
        for template_key, recommendations in pdg_data.items():
            if template_signature and template_signature in template_key:
                plan_recommendations.extend(recommendations)
        
        return {
            "task": task,
            "template_signature": template_signature,
            "team_size": team_size,
            "relevant_attempts": relevant_entries,
            "best_performing": relevant_entries[0] if relevant_entries else None,
            "optimal_team_sizes": optimal_team_sizes,
            "plan_recommendations": plan_recommendations,
            "total_relevant_entries": len(relevant_entries)
        }

    # ---------- 4. Communication Pattern Analysis ----------
    def get_communication_patterns(self, task: str = None) -> Dict[str, Any]:
        """Analyze communication patterns and their effectiveness"""
        comm_analysis = {}
        
        for ep_id, ep_data in self.episodes_data.items():
            task_data = ep_data.get("task_data", {})
            
            for t_name, t_info in task_data.items():
                if task and t_name != task:
                    continue
                    
                for template_name, template_data in t_info.get("templates", {}).items():
                    instances = template_data.get("instances", [])
                    
                    for instance in instances:
                        comm_type = instance.get("communication_type", "unknown")
                        success = instance.get("success", False)
                        
                        if comm_type not in comm_analysis:
                            comm_analysis[comm_type] = {
                                "total_uses": 0,
                                "successes": 0,
                                "success_rate": 0.0,
                                "tasks_used": set(),
                                "episodes_used": set()
                            }
                        
                        comm_analysis[comm_type]["total_uses"] += 1
                        if success:
                            comm_analysis[comm_type]["successes"] += 1
                        comm_analysis[comm_type]["tasks_used"].add(t_name)
                        comm_analysis[comm_type]["episodes_used"].add(ep_id)
        
        # Calculate success rates and convert sets to lists for JSON serialization
        for comm_type in comm_analysis:
            pattern = comm_analysis[comm_type]
            pattern["success_rate"] = pattern["successes"] / pattern["total_uses"] if pattern["total_uses"] > 0 else 0
            pattern["tasks_used"] = list(pattern["tasks_used"])
            pattern["episodes_used"] = list(pattern["episodes_used"])
        
        return {
            "communication_patterns": comm_analysis,
            "filter_task": task
        }

    # ---------- 5. Block Timing Analysis ----------
    def get_block_timing_analysis(self) -> Dict[str, Any]:
        """
        Analyze start times for all blocks across all episodes.
        Returns average, min, and max start times for each block.
        """
        block_timing = {}
        
        # Process analytics data from TCG (Task Coordination Graph)
        if hasattr(self, 'analytics') and 'TCG' in self.analytics:
            tcg_data = self.analytics['TCG']
            
            # Parse each entry in TCG data
            for entry_key, entry_data in tcg_data.items():
                # Parse entry key like "Block_2|bucket=10-20|k=1"
                parts = entry_key.split('|')
                if len(parts) >= 3:
                    # Extract block name (e.g., "Block_2")
                    block_name = parts[0]
                    
                    # Extract team size (k value)
                    k_part = next((part for part in parts if part.startswith('k=')), None)
                    team_size = None
                    if k_part:
                        try:
                            team_size = int(k_part.split('=')[1])
                        except (ValueError, IndexError):
                            continue
                    
                    # Extract bucket information (start time range)
                    bucket_part = next((part for part in parts if part.startswith('bucket=')), None)
                    if bucket_part and team_size is not None:
                        try:
                            # Parse bucket like "bucket=10-20" to get start time range
                            bucket_range = bucket_part.split('=')[1]
                            start_time, end_time = map(int, bucket_range.split('-'))
                            
                            # Use middle of bucket as representative start time
                            avg_bucket_start = (start_time + end_time) / 2
                            
                            if block_name not in block_timing:
                                block_timing[block_name] = {
                                    'start_times': [],
                                    'bucket_ranges': [],
                                    'attempts': 0,
                                    'successes': 0,
                                    'successful_team_sizes': [],
                                    'all_team_sizes': [],
                                    'completion_times': []
                                }
                            
                            # Add data weighted by number of attempts
                            attempts = entry_data.get('attempts', 0)
                            successes = entry_data.get('successes', 0)
                            avg_completion_time = entry_data.get('avg_t')  # Average completion time for this entry
                            
                            # Add start time for each attempt in this bucket
                            for _ in range(attempts):
                                block_timing[block_name]['start_times'].append(avg_bucket_start)
                                block_timing[block_name]['all_team_sizes'].append(team_size)
                            
                            # Track successful team sizes and completion times
                            if successes > 0 and avg_completion_time is not None:
                                for _ in range(successes):
                                    block_timing[block_name]['successful_team_sizes'].append(team_size)
                                    block_timing[block_name]['completion_times'].append(avg_completion_time)
                            
                            # Track all completion times (including failures) if available
                            if avg_completion_time is not None:
                                # For TCG data, avg_completion_time represents the duration for this bucket
                                for _ in range(attempts):
                                    block_timing[block_name]['completion_times'].append(avg_completion_time)
                            
                            block_timing[block_name]['bucket_ranges'].append((start_time, end_time))
                            block_timing[block_name]['attempts'] += attempts
                            block_timing[block_name]['successes'] += successes
                            
                        except (ValueError, IndexError):
                            # Skip entries with malformed bucket data
                            continue
        
        # Calculate statistics for each block
        block_stats = {}
        for block_name, timing_data in block_timing.items():
            start_times = timing_data['start_times']
            bucket_ranges = timing_data['bucket_ranges']
            
            if start_times:
                # Calculate overall start time statistics
                avg_start = sum(start_times) / len(start_times)
                min_start = min(start_times)
                max_start = max(start_times)
                
                # Calculate actual min/max from bucket ranges
                if bucket_ranges:
                    actual_min = min(start for start, end in bucket_ranges)
                    actual_max = max(end for start, end in bucket_ranges)
                else:
                    actual_min = min_start
                    actual_max = max_start
                
                # Calculate minimum agents needed for success
                successful_team_sizes = timing_data.get('successful_team_sizes', [])
                min_agents_needed = "UNKNOWN"
                if successful_team_sizes:
                    min_agents_needed = min(successful_team_sizes)
                
                # Calculate minimum completion time and average duration
                completion_times = timing_data.get('completion_times', [])
                min_completion_time = "UNKNOWN"
                avg_task_duration = "UNKNOWN"
                if completion_times:
                    min_completion_time = min(completion_times)
                    avg_task_duration = sum(completion_times) / len(completion_times)
                
                block_stats[block_name] = {
                    'start_times': {
                        'avg': avg_start,
                        'min': actual_min,
                        'max': actual_max,
                        'count': len(start_times),
                        'bucket_count': len(bucket_ranges)
                    },
                    'performance': {
                        'total_attempts': timing_data['attempts'],
                        'total_successes': timing_data['successes'],
                        'success_rate': timing_data['successes'] / timing_data['attempts'] if timing_data['attempts'] > 0 else 0,
                        'min_agents_needed': min_agents_needed,
                        'min_completion_time': min_completion_time,
                        'avg_task_duration': avg_task_duration
                    }
                }
        
        return {
            "block_timing_analysis": block_stats,
            "summary": {
                "total_blocks_analyzed": len(block_stats),
                "blocks_with_timing": list(block_stats.keys())
            }
        }

    # ---------- 5. Episode-specific insights ----------
    def get_episode_insights(self, episode_id: str = None) -> Dict[str, Any]:
        """Get detailed insights for specific episode(s)"""
        if episode_id:
            episodes_to_analyze = {episode_id: self.episodes_data.get(episode_id, {})}
        else:
            episodes_to_analyze = self.episodes_data
        
        insights = {}
        
        for ep_id, ep_data in episodes_to_analyze.items():
            episode_info = ep_data.get("episode_data", {})
            task_data = ep_data.get("task_data", {})
            
            insights[ep_id] = {
                "completion_status": episode_info.get("completed", False),
                "max_timestep": episode_info.get("max_timestep", 0),
                "total_blocks": episode_info.get("total_blocks", 0),
                "completed_blocks": episode_info.get("completed_blocks", 0),
                "completion_rate": episode_info.get("completed_blocks", 0) / episode_info.get("total_blocks", 1),
                "task_performance": {}
            }
            
            # Analyze each task in the episode
            for task_name, task_info in task_data.items():
                task_success = task_info.get("final_success", False)
                completion_time = task_info.get("completion_time")
                
                templates_analysis = {}
                for template_name, template_data in task_info.get("templates", {}).items():
                    instances = template_data.get("instances", [])
                    successful_instances = sum(1 for inst in instances if inst.get("success", False))
                    
                    templates_analysis[template_name] = {
                        "total_instances": len(instances),
                        "successful_instances": successful_instances,
                        "success_rate": successful_instances / len(instances) if instances else 0
                    }
                
                insights[ep_id]["task_performance"][task_name] = {
                    "final_success": task_success,
                    "completion_time": completion_time,
                    "templates": templates_analysis
                }
        
        return insights

    # ---------- to_str for LLM ----------
    def to_str(self, data: Dict[str, Any]) -> str:
        """Convert any retrieved dict into a string for LLM consumption"""
        return json.dumps(data, indent=2)

    # ---------- Helper method to get actionable insights ----------
    def get_actionable_insights(self, current_task: str, current_team_size: int = None) -> str:
        """
        Get actionable insights formatted for LLM consumption
        
        Args:
            current_task: The task the agent is currently planning for
            current_team_size: Current team size (optional)
        """
        # Get plan feedback
        plan_feedback = self.get_plan_feedback(current_task, team_size=current_team_size)
        
        # Get communication patterns
        comm_patterns = self.get_communication_patterns(current_task)
        
        # Get general info for context
        general_info = self.get_general_info()
        
        insights = []
        
        # Add task-specific performance insights
        task_stats = general_info["task_distribution"].get(current_task, {})
        if task_stats:
            insights.append(f"Task '{current_task}' historical performance:")
            insights.append(f"  - Completion rate: {task_stats['completion_rate']:.1%}")
            insights.append(f"  - Total attempts: {task_stats['total_instances']}")
            insights.append(f"  - Seen in {task_stats['episodes_seen']} episodes")
        
        # Add best performing approaches
        if plan_feedback["best_performing"]:
            best = plan_feedback["best_performing"]
            insights.append(f"\nBest performing approach for '{current_task}':")
            insights.append(f"  - Signature: {best['signature']}")
            insights.append(f"  - Success rate: {best['completion_rate']:.1%}")
            insights.append(f"  - Average time: {best['avg_time']} steps" if best['avg_time'] else "  - Average time: N/A")
        
        # Add team size recommendations
        if plan_feedback["optimal_team_sizes"]:
            insights.append(f"\nOptimal team size recommendations for '{current_task}':")
            for context, k_star in plan_feedback["optimal_team_sizes"].items():
                insights.append(f"  - {context}: k* = {k_star}")
        
        # Add communication recommendations
        comm_data = comm_patterns["communication_patterns"]
        if comm_data:
            insights.append(f"\nCommunication pattern effectiveness for '{current_task}':")
            sorted_comms = sorted(comm_data.items(), key=lambda x: x[1]["success_rate"], reverse=True)
            for comm_type, data in sorted_comms[:3]:  # Top 3
                insights.append(f"  - {comm_type}: {data['success_rate']:.1%} success rate ({data['total_uses']} uses)")
        
        # Add plan modification suggestions
        if plan_feedback["plan_recommendations"]:
            insights.append(f"\nPlan modification suggestions:")
            for rec in plan_feedback["plan_recommendations"][:3]:  # Top 3
                insights.append(f"  - {rec['delta']}: +{rec['cr_gain']:.1%} completion rate gain")
                insights.append(f"    Context: {rec['where']}")
        
        # Add block timing insights
        timing_analysis = self.get_block_timing_analysis()
        block_stats = timing_analysis.get("block_timing_analysis", {})
        if block_stats and current_task in block_stats:
            block_timing = block_stats[current_task]
            start_times = block_timing.get("start_times", {})
            if start_times:
                avg_start = start_times.get("avg", 0)
                min_start = start_times.get("min", 0)
                max_start = start_times.get("max", 0)
                insights.append(f"\nTiming patterns for '{current_task}':")
                insights.append(f"  - Average start time: step {avg_start:.1f}")
                insights.append(f"  - Start time range: steps {min_start}-{max_start}")
                insights.append(f"  - Based on {start_times.get('count', 0)} historical attempts")
        
        return "\n".join(insights)

from smolagents import VLLMModel
from .utils import ExperimentAgent
from .general_planning_agent import GeneralPlanningAgent
from .architecture_planning_agent import ArchitecturePlanningAgent
from .dependency_planning_agent import DependencyPlanningAgent
from .config_planning_agent import ConfigPlanningAgent
import yaml
import os
class PlanningAgent(ExperimentAgent):
    def __init__(self, model, prompt_dir: str, root_dir: str, step_multiplier: int, **kwargs):
        env_name = kwargs.get("env_name", None)
        prompt_path = os.path.join(prompt_dir, "planning_agent.yaml")
        with open(prompt_path, "r") as f:
            prompt_templates = yaml.safe_load(f)
        super().__init__(
            model = model,
            root_dir = root_dir,
            prompt_templates = prompt_templates,
            managed_agents = [
                GeneralPlanningAgent(model=model, 
                                     prompt_dir=prompt_dir, 
                                     root_dir=root_dir, 
                                     env_name=env_name, 
                                     max_steps=10 * step_multiplier),
                
                ArchitecturePlanningAgent(model=model, 
                                          prompt_dir=prompt_dir, 
                                          root_dir=root_dir, 
                                          env_name=env_name, 
                                          max_steps=10 * step_multiplier),
                
                DependencyPlanningAgent(model=model, 
                                        prompt_dir=prompt_dir, 
                                        root_dir=root_dir, 
                                        env_name=env_name, 
                                        max_steps=10 * step_multiplier),
                
                ConfigPlanningAgent(model=model, 
                                    prompt_dir=prompt_dir, 
                                    root_dir=root_dir, 
                                    env_name=env_name, 
                                    max_steps=10 * step_multiplier)
            ],
            name='planning_agent',
            description='A planning agent that managing multiple other agents to make a series of experiment plans.',
            **kwargs
        )
        
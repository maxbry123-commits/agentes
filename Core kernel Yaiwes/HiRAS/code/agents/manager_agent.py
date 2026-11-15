from smolagents import VLLMModel
from .utils import ExperimentAgent
import os
import yaml
from .planning_agent import PlanningAgent
from .analysing_agent import AnalysingAgent
from .coding_agent import CodingAgent
from .execution_agent import ExecutionAgent
from .report_agent import ReportAgent
from pprint import pprint
class ManagerAgent(ExperimentAgent):
    def __init__(self, model, prompt_dir: str, root_dir: str, step_multiplier: int, **kwargs):
        env_name = kwargs.get("env_name", None)
        prompt_path = os.path.join(prompt_dir, "manager_agent.yaml")
        with open(prompt_path, "r") as f:
            prompt_templates = yaml.safe_load(f)
        super().__init__(
            model = model,
            root_dir = root_dir,
            prompt_templates = prompt_templates,
            managed_agents = [
                PlanningAgent(model=model, 
                              prompt_dir=prompt_dir, 
                              root_dir=root_dir, 
                              max_steps=16 * step_multiplier,
                              step_multiplier=step_multiplier,
                              env_name=env_name),
                
                AnalysingAgent(model=model, 
                               prompt_dir=prompt_dir, 
                               root_dir=root_dir, 
                               max_steps=16 * step_multiplier,
                               env_name=env_name),
                
                CodingAgent(model=model, 
                            prompt_dir=prompt_dir, 
                            root_dir=root_dir, 
                            max_steps=32 * step_multiplier, 
                            env_name=env_name),
                
                ExecutionAgent(model=model, 
                               prompt_dir=prompt_dir, 
                               root_dir=root_dir, 
                               max_steps=32 * step_multiplier, 
                               env_name=env_name),
                #ReportAgent(model, prompt_dir, root_dir),
            ],
            name='manager_agent',
            description='The manager agent for the whole experiment reproduction.',
            **kwargs
        )
        
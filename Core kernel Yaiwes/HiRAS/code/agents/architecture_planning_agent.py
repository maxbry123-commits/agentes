from smolagents import VLLMModel
from .utils import ExperimentAgent
import yaml
import os
class ArchitecturePlanningAgent(ExperimentAgent):
    def __init__(self, model, prompt_dir: str, root_dir: str, **kwargs):
        prompt_path = os.path.join(prompt_dir, "architecture_planning_agent.yaml")
        with open(prompt_path, "r") as f:
            prompt_templates = yaml.safe_load(f)
        super().__init__(
            model = model,
            root_dir = root_dir,
            prompt_templates = prompt_templates,
            name='architecture_planning_agent',
            description='A planning agent that designs the architecture.',
            **kwargs
        )
        
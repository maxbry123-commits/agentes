from smolagents import VLLMModel
from .utils import generate_file_management_tools
import yaml
import os
from .utils import ExperimentAgent
class CodingAgent(ExperimentAgent):
    def __init__(self, model, prompt_dir: str, root_dir: str, **kwargs):
        prompt_path = os.path.join(prompt_dir, "coding_agent.yaml")
        with open(prompt_path, "r") as f:
            prompt_templates = yaml.safe_load(f)
        super().__init__(
            model = model,
            root_dir = root_dir,
            prompt_templates = prompt_templates,
            name='coding_agent',
            description='A coding agent that writes the code for the components.',
            **kwargs
        )
        




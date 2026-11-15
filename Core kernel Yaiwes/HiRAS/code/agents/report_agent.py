from smolagents import VLLMModel
from .utils import ExperimentAgent
import yaml
import os
class ReportAgent(ExperimentAgent):
    def __init__(self, model, prompt_dir: str, root_dir: str, **kwargs):
        prompt_path = os.path.join(prompt_dir, "report_agent.yaml")
        with open(prompt_path, "r") as f:
            prompt_templates = yaml.safe_load(f)
        super().__init__(
            model = model,
            root_dir = root_dir,
            prompt_templates = prompt_templates,
            name='report_agent',
            description='A report agent that writes the experiment reproduction report.',
            **kwargs
        )
        
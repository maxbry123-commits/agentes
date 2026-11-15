from .utils import ExperimentAgent, BashTool
import yaml
import os
class ExecutionAgent(ExperimentAgent):
    def __init__(self, model, prompt_dir: str, root_dir: str, **kwargs):
        env_name = kwargs.get("env_name", None)
        if env_name is None:
            raise ValueError("env_name is required for ExecutionAgent")
        prompt_path = os.path.join(prompt_dir, "execution_agent.yaml")
        with open(prompt_path, "r") as f:
            prompt_templates = yaml.safe_load(f)
        tools = [BashTool(root_dir, env_name)]
        super().__init__(
            model = model,
            root_dir = root_dir,
            prompt_templates = prompt_templates,
            tools = tools,
            name='execution_agent',
            description='An execution agent that executes the code to reproduce the experiment.',
            **kwargs
        )


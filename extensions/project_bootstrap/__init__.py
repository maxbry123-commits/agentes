# project_bootstrap — kernel auto-conocimiento
# Enchufe: wordflow.kernel.project_bootstrap

from .ktp.engine import create_engine, KTPEngine, KTPContext
from .input_handler import handle_input, make_input_block, InputBlock
from .updater import IncrementalUpdater
from .resource_brain import ResourceBrain
from .microflows.runner import run_microflujo, extract_goal, decompose_tasks

__all__ = [
    "create_engine",
    "KTPEngine",
    "KTPContext",
    "handle_input",
    "make_input_block",
    "InputBlock",
    "IncrementalUpdater",
    "ResourceBrain",
    "run_microflujo",
    "extract_goal",
    "decompose_tasks",
]

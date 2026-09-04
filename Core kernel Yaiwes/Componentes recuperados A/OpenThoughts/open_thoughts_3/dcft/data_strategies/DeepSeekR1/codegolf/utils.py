import json
import logging
import re

logger = logging.getLogger(__name__)

from bespokelabs import curator
from bespokelabs.curator.llm.llm import _get_function_source
from datasets import Dataset


class CodeGolfTestExecutor(curator.CodeExecutor):
    """Test Executor."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parsed_code = None

    def code(self, row):
        """Extract code string from a dataset row."""

        code = row["deepseek_solution_extracted"]
        return code

    def code_input(self, row):
        """Extract single input from a dataset row."""
        inputs = row["test_inputs"]
        inputs = "\n".join([str(i) for i in inputs])
        return inputs

    def code_output(self, row, execution_output):
        """Parse execution results."""
        output = row["test_outputs"]
        output = "\n".join([str(o) for o in output])
        row["correct"] = output == execution_output.stdout
        row["execution_output"] = execution_output.stdout
        return row


def test_codegolf(dataset: Dataset) -> Dataset:
    executor = CodeGolfTestExecutor(backend="ray")
    return executor(dataset)

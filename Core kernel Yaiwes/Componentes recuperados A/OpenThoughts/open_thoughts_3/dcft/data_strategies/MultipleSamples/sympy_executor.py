import re

from bespokelabs import curator
from bespokelabs.curator.llm.llm import _get_function_source
from datasets import Dataset


class SympyExecutor(curator.CodeExecutor):
    """Test Executor."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parsed_code = None

    def code(self, row):
        """Extract code string from a dataset row."""
        code = re.search(r"```python\n(.*?)\n```", row["sympy_code"], re.DOTALL).group(
            1
        )
        return code

    def code_input(self, row):
        """Extract single input from a dataset row."""
        inputs = row["r1_distill_70b_extracted_answer"]
        inputs = "\n".join([str(i) for i in inputs])
        return inputs

    def code_output(self, row, execution_output):
        """Parse execution results."""

        correctness = execution_output.stdout.split()
        correctness = [item == "True" for item in correctness]
        row["correct"] = correctness
        row["execution_output"] = execution_output.stdout
        return row


def test_sympy(dataset: Dataset) -> Dataset:
    executor = SympyExecutor(backend="ray")
    return executor(dataset)

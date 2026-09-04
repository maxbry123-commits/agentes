from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap


class TestCases(BaseModel):
    """Represents a set of generated test cases"""

    test_inputs: list[str]
    test_outputs: list[str]


class TestCaseMapConfig(BaseModel):
    input_prompt_column: str
    output_test_inputs_column: str = "test_inputs"
    output_test_outputs_column: str = "test_outputs"


TESTCASE_SYSTEM_PROMPT = """You are a judge of a code competition. Your job is to write test cases for the prompts. 
You will do this by generating a list of inputs and a list of expected outputs. Each input and output should be represented as a string.
If an input is multiple values, you should separate them with a comma.
These inputs will be provided to the code in the stdin. If the code does not need an input, you should use an empty string.
You should have as many inputs as outputs. 
"""


class TestCaseMap(CompletionsMap):
    """
    A map that generates test cases for coding problems.
    """

    def __init__(self, config: dict):
        config = TestCaseMapConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """
        return TestCases

    def prompt(self, dataset_row: dict) -> list[dict]:
        """
        Args:
            dataset_row: dict - A row from the dataset containing the coding problem
        Returns:
            A messages list for the completions model
        """
        return [
            {"role": "system", "content": TESTCASE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Write test cases for this problem:\n\n{dataset_row[self.config.input_prompt_column]}",
            },
        ]

    def parse(self, original_dataset_row: dict, response: TestCases) -> dict:
        """
        Args:
            original_dataset_row: dict - The original dataset row
            response: TestCase - A response from the completions model containing the test function
        Returns:
            dict - The original row with the test case added
        """
        new_row = original_dataset_row.copy()
        new_row[self.config.output_test_inputs_column] = response.test_inputs
        new_row[self.config.output_test_outputs_column] = response.test_outputs
        return new_row

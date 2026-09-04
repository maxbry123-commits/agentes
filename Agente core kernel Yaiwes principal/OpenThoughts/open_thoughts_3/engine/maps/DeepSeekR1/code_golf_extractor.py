from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap


class ExtractedCode(BaseModel):
    """Represents the extracted code from the code golf problem"""

    code: str


class CodeGolfExtractorConfig(BaseModel):
    input_solution_column: str
    output_code_column: str = "code"


TESTCASE_SYSTEM_PROMPT = """ 
Take the following solution to a code golf problem and rewrite it so that it can be run as a Python script, 
accepting input from stdin and printing the output to stdout.

The input will be provided so that a single line of input represents a single test case. If a function requires multiple inputs, they will be separated by a comma.
If a function does not require any inputs, then it will be provided an empty string.
Your code will then provide an output for each test case. 

Do not include anything else in your response. Do not include any comments or other text.
Do not print any extra values (besides the result of executing the code).

For example, let's say that the solution to a problem is:

```python
   def add(a, b):
    return a + b
```

Then, you would rewrite it as:

```python 
def add(a,b):
    return a + b

# Read entire input
data = input()
# Split by lines and print each
while line := input():
    args = line.split(",")
    a = int(args[0])
    b = int(args[1])
    result = add(a, b)
    print(result)
```

"""


class CodeGolfExtractorMap(CompletionsMap):
    """
    A map that generates test cases for coding problems.
    """

    def __init__(self, config: dict):
        config = CodeGolfExtractorConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """
        return ExtractedCode

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
                "content": f"Extract the code from the following solution:\n\n{dataset_row[self.config.input_solution_column]}",
            },
        ]

    def parse(self, original_dataset_row: dict, response: ExtractedCode) -> dict:
        """
        Args:
            original_dataset_row: dict - The original dataset row
                response: ExtractedCode - A response from the completions model containing the extracted code
        Returns:
            dict - The original row with the extracted code added
        """
        new_row = original_dataset_row.copy()
        new_row[self.config.output_code_column] = response.code
        return new_row

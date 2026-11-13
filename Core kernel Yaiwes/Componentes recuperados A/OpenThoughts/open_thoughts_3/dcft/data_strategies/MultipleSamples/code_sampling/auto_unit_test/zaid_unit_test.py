"""UTGen-based components for generating adversarial test cases that try to break Python code solutions.

Given a problem description and a code solution, this module uses a prompted LLM to generate test cases
designed to expose bugs or edge cases.

Quick usage:
```python
hypothesis, inputs, expected = get_adversarial_test(
    code="your code here",
    description="your problem description",
    model=your_llm
)
# Then run your code with 'inputs' and compare against 'expected'
```
"""

import ast
import re
from dataclasses import dataclass
from typing import Callable, Tuple

from datasets import Dataset


def extract_code(response):
    """Extract code blocks from a text response.

    Args:
        response (str): Text that may contain code blocks

    Returns:
        list: List of code block contents
    """
    pattern = r"```(?:[a-zA-Z]*)\n(.*?)```"
    # Use re.DOTALL to match multiline content inside backticks
    matches = re.findall(pattern, response, re.DOTALL)
    if len(matches) == 0:
        return None
    return matches[-1]


@dataclass
class AdversarialTest:
    """Class for handling adversarial test prompts and responses."""

    _prompt_template = """
You are given a Python function `{signature}` to solve the following task:

## Task
{description}

## Code Solution:
```
{code}
```
The code solution I have provided to you is **incorrect**. Your job is to give feedback by generating a unit test that 
1. Is **valid** input based on the task description, i.e., an acceptable input consistent with task description that a correct program should be able to execute.
2. The output enclosed in ```.``` and is **faithful** to the task description, i.e., the output of the unit test is consistent with what a correct program would return.
3. **Breaks** the given code, i.e., does **not** execute to the **correct** output and brings out its mistakes and vulnerabilities.

Provide a reasoning for your answer and identify a general hypothesis or rationale identifying the cause of error. Then provide input and output of the unit test consistent with the pattern (hypotheis) you have identified.
Note:
- that you MUST directly write ALL input arguments of the function in the correct order. Skip writing any names of arguments.
- you MUST enclose the unit test inputs and outputs in ```.```

Respond in the format below:

## Hypothesis
< step-by-step reasoning >

Error Pattern: <an identified pattern of inputs that yields erroneous or incorrect outputs>

## Unit Test

### Input Arguments
< step-by-step reasoning for constructing a unit test that fits the error pattern identified above and is valid as per the task description>
Arguments: ```{entry_point}(<all arguments>)```

### Output
< step-by-step reasoning for what a **correct** {entry_point} would execute to based on the task description and your input above. Make sure your data type of the final answer matches the expected output type of the function. >
Output: ```<your final answer>```
"""

    def format_prompt(
        self, signature: str, description: str, entry_point: str, code: str
    ) -> str:
        """
        Formats the adversarial prompt with the given arguments.

        Args:
            signature: The function signature
            description: The task description
            entry_point: The entry point function name
            code: The code solution to analyze

        Returns:
            str: The formatted prompt

        Example:
            >>> prompt = AdversarialTest().format_prompt(
            ...     "sum_numbers(numbers: List[int]) -> int",
            ...     "Write a function that takes a list of integers and returns their sum.",
            ...     "sum_numbers",
            ...     "def sum_numbers(numbers):\\n    return sum(numbers)"
            ... )
        """
        return self._prompt_template.format(
            signature=signature,
            description=description,
            entry_point=entry_point,
            code=code,
        )

    def extract_test(self, response: str) -> Tuple[str, str, str]:
        """
        Extracts the hypothesis, input arguments, and expected output from an adversarial prompt response.

        Args:
            response: The response string from the LLM

        Returns:
            tuple[str, str, str]: A tuple containing (hypothesis, input_args, expected_output)

        Example:
            >>> response = '''
            ... ## Hypothesis
            ... The function fails to handle empty lists.
            ...
            ... Error Pattern: Function crashes when given an empty list
            ...
            ... ## Unit Test
            ...
            ... ### Input Arguments
            ... Testing with an empty list to verify handling.
            ... Arguments: ```sum_numbers([])```
            ...
            ... ### Output
            ... An empty list should sum to 0
            ... Output: ```0```
            ... '''
            >>> hypothesis, input_args, expected_output = AdversarialTest().extract_test(response)
            >>> print(hypothesis)
            The function fails to handle empty lists.
            >>> print(input_args)
            sum_numbers([])
            >>> print(expected_output)
            0
        """
        hypothesis_start = response.find("## Hypothesis\n") + len("## Hypothesis\n")
        hypothesis_end = response.find("Error Pattern:")
        hypothesis = response[hypothesis_start:hypothesis_end].strip()

        args_start = response.find("Arguments: ```") + len("Arguments: ```")
        args_end = response.find("```", args_start)
        input_args = response[args_start:args_end].strip()

        output_start = response.find("Output: ```") + len("Output: ```")
        output_end = response.find("```", output_start)
        expected_output = response[output_start:output_end].strip()

        return hypothesis, input_args, expected_output


def get_function_signatures(code: str) -> dict[str, str]:
    # Parse the code to get an Abstract Syntax Tree (AST)
    parsed_code = ast.parse(code)

    # A dictionary to hold function names and their signatures
    function_signatures = {}

    # Walk through the AST to find all function definitions
    for node in ast.walk(parsed_code):
        if isinstance(node, ast.FunctionDef):
            # Construct the function signature
            function_name = node.name
            args = []
            for arg in node.args.args:
                # Check if the argument has a type hint
                if arg.annotation:
                    # The annotation can be a Name (e.g., int) or more complex (e.g., List[int]).
                    # We use ast.get_source_segment to extract the original source code for the annotation.
                    # This will never be None because we check if arg.annotation is not None first.
                    arg_type = ": " + ast.get_source_segment(code, arg.annotation)  # type: ignore
                else:
                    arg_type = ""
                args.append(f"{arg.arg}{arg_type}")
            signature = f"{function_name}({', '.join(args)})"
            function_signatures[function_name] = signature

    return function_signatures


def get_adversarial_test_single(
    code: str, description: str, model: Callable[[str], str]
) -> Tuple[str, str, str]:
    """
    Generates adversarial test cases for a given code solution and problem description.

    Args:
        code: The code solution to analyze
        description: The problem description/requirements
        model: An LLM capable of generating text completions

    Returns:
        Tuple[str, str, str]: A tuple containing (hypothesis, input_args, expected_output)
        - hypothesis: Explanation of the identified vulnerability
        - input_args: The input arguments that expose the vulnerability
        - expected_output: The expected correct output for these inputs

    Example:
        >>> code = '''
        ... def sum_positive(numbers):
        ...     return sum(n for n in numbers)  # Fails to check if numbers are positive
        ... '''
        >>> description = "Write a function that sums only positive numbers in a list"
        >>> hypothesis, inputs, expected = get_adversarial_test(code, description, model)
        >>> print(inputs)
        sum_positive([-1, 2, -3, 4])
        >>> print(expected)
        6
    """

    return prompt


def extract_code_from_model(
    dataset: Dataset, code_column: str, extraction_column: str
) -> Dataset:
    def f(x):
        x[extraction_column] = extract_code(x[code_column])
        return x

    dataset = dataset.map(f)
    return dataset


def filter_no_extract(dataset: Dataset, code_column: str) -> Dataset:
    dataset = dataset.filter(lambda x: x[code_column] is not None)
    return dataset


def get_adversarial_test(
    dataset: Dataset, problem_column: str, code_column: str
) -> Dataset:
    def f(x):
        code = x[code_column]
        description = x[problem_column]
        # Extract the function signature from the code
        signatures = get_function_signatures(code)
        # Assumes there is only one function in the code, or that the first function is the one to test
        if len(signatures.keys()) > 0:
            entry_point = list(signatures.keys())[0]  # Get the first function name
            signature = signatures[entry_point]
        else:
            entry_point = code

        # Create adversarial prompt
        adversarial = AdversarialTest()
        x["_prompt_for_adversarial_test"] = adversarial.format_prompt(
            signature=signature,
            description=description,
            entry_point=entry_point,
            code=code,
        )
        return x

    def filter_func(x):
        code = x[code_column]
        description = x[problem_column]
        try:
            signatures = get_function_signatures(code)
            return len(signatures.keys()) > 0
        except:
            return False

    dataset = dataset.filter(filter_func)
    dataset = dataset.map(f)
    return dataset


def generate_input_output(dataset: Dataset, response_column: str) -> Dataset:
    def f(x):
        adversarial = AdversarialTest()
        hypothesis, input_args, expected_output = adversarial.extract_test(
            x[response_column]
        )
        x["input_args"] = input_args
        x["hypothesis"] = hypothesis
        x["expected_output"] = expected_output
        return x

    dataset = dataset.map(f)
    return dataset

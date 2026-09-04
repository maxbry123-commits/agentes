from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap


class NumericalAnswer(BaseModel):
    numerical_answer: str


class ExtractMathAnswerMapConfig(BaseModel):
    detailed_answer_column: str
    output_numerical_answer_column: str


class ExtractMathAnswerMap(CompletionsMap):
    """
    Given a question and answer pair, extract the numerical answer from the question.
    """

    def __init__(self, config: dict):
        config = ExtractMathAnswerMapConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """
        return NumericalAnswer

    def prompt(self, dataset_row: dict) -> list[dict]:
        """
        Prompt model to extract the numerical answer from a detailed answer.
        """
        system_prompt = """
        You are an expert at extracting the short final numerical answer from a detailed
        answer.

        Example 1:
        Detailed answer: John has 2 apples and Alex has 5 apples. So in total they have 2 + 5 = 7 apples.
        Output: {"numerical_answer": "7"}

        Example 2:
        Detailed answer: First count the number of apples in the basket. Then count the number of oranges in the basket.
        Finally, add the two numbers together to get the total number of fruits in the basket.
        The number of apples is 145 and the number of oranges is 293. So the total number of fruits is 145 + 293 = 438.
        Output: {"numerical_answer": "438"}
        """
        return [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Detailed answer: {dataset_row[self.config.detailed_answer_column]}",
            },
        ]

    @staticmethod
    def _is_numeric(s: str) -> bool:
        """Check if string contains a number."""
        return any(char.isdigit() for char in s)

    def parse(self, dataset_row: dict, response: NumericalAnswer):
        """
        Parse the response from the completions model and filter out non-numeric answers.

        Args:
            dataset_row: A row from the dataset
            response: The response from the completions model

        Returns:
            The numerical answer if it is numeric, otherwise an empty list.
        """
        if self._is_numeric(response.numerical_answer):
            dataset_row[self.config.output_numerical_answer_column] = (
                response.numerical_answer
            )
            return [dataset_row]
        return []

from abc import ABC, abstractmethod

from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap

SKY_T1_SYSTEM_PROMPT = """
Your role as an assistant involves thoroughly exploring questions through a systematic long thinking process
before providing the final precise and accurate solutions. This requires engaging in a comprehensive cycle of
analysis, summarizing, exploration, reassessment, reflection, backtracing, and iteration to develop well-considered
thinking process.
"""


def extract_boxed_answer(text):
    """Extract the boxed answer from the text."""
    text = strip_answer_string(text)
    return extract_answer(text)


class JudgeResult(BaseModel):
    """Result of the judge's evaluation."""

    correct: bool
    reasoning: str


class JudgeConfig(BaseModel):
    ground_truth_column: str
    answer_column: str
    output_correct_column: str = "correct"
    output_reasoning_column: str = "judge_reasoning"


class DeepSeekJudgeMap(CompletionsMap):
    """Curator class for processing Numina dataset."""

    def __init__(self, config: dict):
        config = JudgeConfig(**config)
        self.config = config

    def example(self) -> str:
        return """
        Here is an example:
        SOLUTION: The capital of Spain is Madrid.
        GROUND TRUTH SOLUTION: Madrid is the Capital of Spain.

        correct: True
        reasoning: Model correctly identified that Madrid is capital of Spain
        """

    @property
    def response_format(self):
        """
        Returns:
            A string that describes the format of the response from the completions model via Pydantic
        """
        return JudgeResult

    def prompt(self, input):
        """Create a prompt for the judge to evaluate the correctness of a solution."""
        return f"""
        You are a judge that evaluates the correctness of a solution.
        You will be given a solution and a ground truth solution.
        You will need to determine if the solution is correct.

        {self.example()}

        SOLUTION: {input[self.config.answer_column]}
        GROUND TRUTH SOLUTION: {input[self.config.ground_truth_column]}
        """

    def parse(self, input, response):
        """Parse the judge's response to extract correctness and reasoning."""
        return {
            **input,
            self.config.output_correct_column: response.correct,
            self.config.output_reasoning_column: response.reasoning,
        }

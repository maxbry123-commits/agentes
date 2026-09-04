from typing import Optional

from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap

SKY_T1_SYSTEM_PROMPT = """
Your role as an assistant involves thoroughly exploring questions through a systematic long thinking process
before providing the final precise and accurate solutions. This requires engaging in a comprehensive cycle of
analysis, summarizing, exploration, reassessment, reflection, backtracing, and iteration to develop well-considered
thinking process.
"""


class GrokReasonerMapConfig(BaseModel):
    input_problem_column: str
    output_grok_solution_column: Optional[str] = "grok_solution"
    output_reasoning_column: Optional[str] = "reasoning"


class GrokReasonerMap(CompletionsMap):
    """Curator class for processing Numina dataset."""

    return_completions_object = True

    def __init__(self, config: dict):
        config = GrokReasonerMapConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A string that describes the format of the response from the completions model via Pydantic
        """
        return None

    def prompt(self, input):
        """Create a prompt for the LLM to reason about the problem."""
        return [{"role": "user", "content": input[self.config.input_problem_column]}]

    def parse(self, input, response):
        """Parse the LLM response to extract reasoning and solution."""
        input[self.config.output_reasoning_column] = response["choices"][0]["message"]["reasoning_content"]
        input[self.config.output_grok_solution_column] = response["choices"][0]["message"]["content"]
        return input

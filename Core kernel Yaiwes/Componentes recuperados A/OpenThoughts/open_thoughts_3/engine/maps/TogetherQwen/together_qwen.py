from typing import Optional

from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap

SKY_T1_SYSTEM_PROMPT = """
Your role as an assistant involves thoroughly exploring questions through a systematic long thinking process
before providing the final precise and accurate solutions. This requires engaging in a comprehensive cycle of
analysis, summarizing, exploration, reassessment, reflection, backtracing, and iteration to develop well-considered
thinking process.
"""


class TogetherQwenConfig(BaseModel):
    input_problem_column: str
    output_grok_solution_column: Optional[str] = "qwen_solution"
    output_reasoning_column: Optional[str] = "reasoning"


class TogetherQwenMap(CompletionsMap):
    """Curator class for processing Numina dataset."""

    return_completions_object = True

    def __init__(self, config: dict):
        config = TogetherQwenConfig(**config)
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
        response = response["choices"][0]["message"]["content"]
        thinking = response.split("</think>")[0].strip()
        answer = response.split("</think>")[1].strip()
        input["qwq_thinking_trajectory"] = thinking
        input["qwq_attempt"] = answer
        input["qwq_response"] = response
        return input
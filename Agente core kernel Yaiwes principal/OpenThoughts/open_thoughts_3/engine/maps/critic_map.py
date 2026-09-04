from typing import Optional

from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap
from engine.maps.chat_map import ChatMap, ChatMapConfig


class CriticMapConfig(BaseModel):
    query_column: str
    responses_column: str
    system_prompt: Optional[str] = "You are a critical evaluator"
    output_column: str


class CriticMap(CompletionsMap):
    def __init__(self, config: CriticMapConfig):
        config = CriticMapConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """
        return None

    def prompt(self, dataset_row: dict) -> list[dict] | str:
        """
        Args:
            dataset_row: dict - A row from the dataset
        Returns:
            A messages list for the completions model or string which gets converted to user prompt
        """

        messages = []
        candidates = dataset_row[self.config.responses_column]
        num = len(candidates)
        query = dataset_row[self.config.query_column]
        prompt = f"I will provide you with 1 response. Evaluate the strengths and weaknesses of each response based on the instruction: {query}.\n"

        for j in range(len(candidates)):
            prompt += f"\n[{j+1}] {candidates[j]}"

        prompt += f"\n\nInstruction: {query}.\n\nEvaluate the response above based on their relevance to the instruction. "
        prompt += (
            f"All the responses should be included and evaluated using identifiers. "
        )
        # user_prompt += f"The output format should be in the form of strengths and weaknesses for each response. "
        prompt += f"For each response, start the critique with the numerical identifier (e.g. [1]) followed by the strengths and weaknesses. "
        prompt += f"You must include both strengths and weaknesses, even if there are more of one than the other. "
        # user_prompt += f"Only separate the strengths and weaknesses with a single new line. "
        prompt += f"At the end of each response's analysis, include two new lines to separate the critiques. "
        prompt += f"Do not include any preface or text after the critiques. Do not include any references to previous critiques within a critique. Start with the analysis for the first response and end with the analysis for the last response. "
        prompt += f"All of the {num} responses should be included and evaluated using identifiers. "
        prompt += f"Structure each response's analysis as follows: [1]\nStrengths:\n- <strength #1>\n- <strength #2>\n- <strength #n> \nWeaknesses:\n- <weakness #1>\n- <weakness #2>\n- <weakness #n>\n\n"

        messages = []
        messages.append({"role": "system", "content": self.config.system_prompt})
        messages.append({"role": "user", "content": prompt})

        return messages

    def parse(self, original_dataset_row: dict, response: dict) -> list[dict] | dict:
        """
        Args:
            original_dataset_row: dict - The original dataset row
            response: str - A response from the completions model
        Returns:
            new_dataset_rows: list[dict] | dict - A list of new dataset rows or a single new dataset row
        """
        original_dataset_row[self.config.output_column] = response
        return original_dataset_row

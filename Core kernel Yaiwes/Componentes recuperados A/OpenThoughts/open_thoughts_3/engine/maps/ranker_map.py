from typing import Optional

from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap
from engine.maps.chat_map import ChatMap, ChatMapConfig


class RankerMapConfig(BaseModel):
    query_column: str
    responses_column: str
    system_prompt: Optional[str] = (
        "You are a helpful assistant who ranks multiple answers"
    )
    critic_column: Optional[str]
    output_column: str


class RankerResponse(BaseModel):
    response: list[int]


class RankerMap(CompletionsMap):
    def __init__(self, config: RankerMapConfig):
        config = RankerMapConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """
        return RankerResponse

    def prompt(self, dataset_row: dict) -> list[dict] | str:
        """
        Args:
            dataset_row: dict - A row from the dataset
        Returns:
            A messages list for the completions model or string which gets converted to user prompt
        """

        messages = []
        generations = dataset_row[self.config.responses_column]
        num = len(generations)
        query = dataset_row[self.config.query_column]
        if self.config.critic_column:
            critiques = dataset_row[self.config.query_column]
        # No longer uses self.use_critiques
        if self.config.critic_column:
            prompt = f"I will provide you with {num} responses, each indicated by a numerical identifier []. Rank the responses based on their relevance to the instruction and their provided critique of strengths/weaknesses: {query}.\n"
        else:
            prompt = f"I will provide you with {num} responses, each indicated by a numerical identifier []. Rank the responses based on their relevance to the instruction: {query}.\n"

        try:
            for j in range(len(generations)):
                prompt += f"\n[{j+1}] {generations[j]}"
                if self.config.critic_column:
                    prompt += f"\n\nCritique:\n{critiques[j]}"
        except:
            breakpoint()
        if self.config.critic_column:
            prompt += f"\n\nInstruction: {query}.\n\nRank the {num} responses above based on their relevance to the instruction and their provided critique of strengths/weaknesses. "
            prompt += f"All the responses should be included and listed using identifiers, in descending order of relevance to the instruction, using the provided critiques of strengths/weaknesses to assist in the ranking. "
        else:
            prompt += f"\n\nInstruction: {query}.\n\nRank the {num} responses above based on their relevance to the instruction. "
            prompt += f"All the responses should be included and listed using identifiers, in descending order of relevance to the instruction. "

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
        original_dataset_row[self.config.output_column] = response.response
        return original_dataset_row

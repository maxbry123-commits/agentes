import math
from typing import Optional

from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap
from engine.maps.chat_map import ChatMap, ChatMapConfig


class FuserMapConfig(BaseModel):
    query_column: str
    responses_column: str
    system_prompt: Optional[str] = (
        "You are a helpful assistant who fuses multiple answers"
    )
    critic_column: Optional[str]
    output_column: str
    ranking_column: str
    top_ranking: Optional[int] = 5
    length_control: Optional[bool] = False


class FuserMap(CompletionsMap):
    def __init__(self, config: FuserMapConfig):
        config = FuserMapConfig(**config)
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
        generations = dataset_row[self.config.responses_column]
        query = dataset_row[self.config.query_column]
        ranking = dataset_row[self.config.ranking_column]
        critiques = dataset_row[self.config.critic_column]

        if len(ranking) != len(generations):
            return "Ranking != Generations. Please return N/A"

        # Create pairs of (ranking, generation) and sort by ranking
        ranked_pairs = sorted(zip(map(int, ranking), generations))
        # Take only pairs where ranking < top_ranking and extract just the generations
        top_generations = [
            gen for rank, gen in ranked_pairs if rank <= self.config.top_ranking
        ]

        if self.config.critic_column:
            # Do the same for critiques
            ranked_critiques = sorted(zip(map(int, ranking), critiques))
            top_critiques = [
                critique
                for rank, critique in ranked_critiques
                if rank <= self.config.top_ranking
            ]

        if critiques:
            prompt = f"You have been provided with a ranked set of responses with their individual critiques of strengths/weaknesses from various open-source models to the latest user query, which is {query}. Your task is to \
                synthesize these responses into a single, high-quality response. It is crucial to critically evaluate the information provided in these responses and their provided critiques of \
                strengths/weaknesses, recognizing that some of it may be biased or incorrect. Your response should not simply replicate the given answers but should offer a refined, accurate, \
                and comprehensive reply to the instruction. Ensure your response is well-structured, coherent, and adheres to the highest standards of accuracy and reliability.\n"
            prompt += f"Once again, the query is: {query}\n"
            if self.config.length_control:
                prompt += "The fused response can only be as long as the longest response in the current candidate pool.\n"

            prompt += "Responses from models:\n\n"

            count = 0
            assert len(top_generations) == len(top_critiques)
            for reference, critique in zip(top_generations, top_critiques):
                prompt += f"{count+1}. {reference} \n\nCritique:\n{critique}"
                count += 1
                if count != len(top_generations):
                    prompt += "\n\n"
                    return prompt

        else:
            prompt = f"You have been provided with a set of responses from various open-source models to the latest user query, which is {query}.\
                Your task is to synthesize these responses into a single, high-quality response. \
                It is crucial to critically evaluate the information provided in these responses, recognizing that some of it may be biased or incorrect. \
                Your response should not simply replicate the given answers but should offer a refined, accurate, and comprehensive reply to the instruction. \
                Ensure your response is well-structured, coherent, and adheres to the highest standards of accuracy and reliability.\n"
            prompt += f"Once again, the query is: {query}\n"

            prompt += "Responses from models:"

            for i, reference in enumerate(top_generations):
                prompt += f"\n{i+1}. {reference}"

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

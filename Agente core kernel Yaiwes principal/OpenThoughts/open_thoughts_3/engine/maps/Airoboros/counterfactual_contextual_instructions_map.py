from typing import List

from pydantic import BaseModel, HttpUrl

from engine.maps.chat_map import ChatMap, ChatMapConfig


class Fact(BaseModel):
    content: str
    source_url: HttpUrl


class CounterfactualSet(BaseModel):
    fact: List[Fact]
    counter_fact: List[str]
    questions: List[str]


class CounterfactualFactsResponse(BaseModel):
    facts_sets: List[CounterfactualSet]


class CounterfactualContextualInstructionsList(BaseModel):
    prompts: list[CounterfactualFactsResponse]


class CounterfactualContextualInstructionsMap(ChatMap):
    def __init__(self, config: dict):
        config = ChatMapConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """
        return CounterfactualContextualInstructionsList

    def parse(self, original_dataset_row: dict, response: dict) -> list[dict] | dict:
        """
        Args:
            original_dataset_row: dict - The original dataset row
            response: CounterfactualContextualInstructionsResponse - A Pydantic model response
        Returns:
            new_dataset_rows: list[dict] | dict - A list of new dataset rows or a single new dataset row
        """
        new_dataset_rows = []
        for facts_set in response.facts_sets:
            for fact, counter_fact, question in zip(
                facts_set.fact, facts_set.counter_fact, facts_set.questions
            ):
                prompt_str = "\n".join(
                    [
                        "BEGININPUT",
                        "BEGINCONTEXT",
                        f"url: {fact.source_url}",
                        "ENDCONTEXT",
                        fact.content,
                        "ENDINPUT",
                        "BEGININSTRUCTION",
                        question,
                        "ENDINSTRUCTION",
                    ]
                )
                new_dataset_rows.append(
                    {**original_dataset_row, self.config.output_column: prompt_str}
                )

        return new_dataset_rows

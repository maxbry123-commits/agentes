import re

from pydantic import BaseModel, confloat

from engine.maps.chat_map import ChatMap, ChatMapConfig


class ScoreResponse(BaseModel):
    response: confloat(ge=1, le=100)
    reasoning: str


class ScorerMap(ChatMap):
    def __init__(self, config: dict):
        super().__init__(config)

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """
        return ScoreResponse

    def parse(self, original_dataset_row: dict, response: dict) -> list[dict] | dict:
        """
        Args:
            original_dataset_row: dict - The original dataset row
            response: str - A response from the completions model
        Returns:
            new_dataset_rows: list[dict] | dict - A list of new dataset rows or a single new dataset row
        """
        original_dataset_row[self.config.output_column] = response.response
        original_dataset_row["classifier_reasoning"] = response.reasoning

        return original_dataset_row

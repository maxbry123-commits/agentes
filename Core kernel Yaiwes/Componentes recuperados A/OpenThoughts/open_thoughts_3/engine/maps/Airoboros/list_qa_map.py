from pydantic import BaseModel

from engine.maps.chat_map import ChatMap, ChatMapConfig


class QA(BaseModel):
    question: str
    answer: str


class ListQA(BaseModel):
    qas: list[QA]


class ListQAMapConfig(BaseModel):
    user_message: str | None = None
    user_message_column: str | None = None
    system_message: str | None = None
    system_message_column: str | None = None
    output_instruction_column: str
    output_response_column: str


class ListQAMap(ChatMap):
    """
    Very similar to ChatMap but uses structured output to get a list of strings that are turned into multiple rows in the dataset.
    """

    def __init__(self, config: dict):
        config = ListQAMapConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """
        return ListQA

    def parse(self, original_dataset_row: dict, response: dict) -> list[dict] | dict:
        """
        Args:
            original_dataset_row: dict - The original dataset row
            response: ListResponse - A Pydantic model response
        Returns:
            new_dataset_rows: list[dict] | dict - A list of new dataset rows or a single new dataset row
        """
        new_dataset_rows = []
        for qa in response.qas:
            new_dataset_rows.append(
                {
                    **original_dataset_row,
                    self.config.output_instruction_column: qa.question,
                    self.config.output_response_column: qa.answer,
                }
            )

        return new_dataset_rows

from pydantic import BaseModel

from engine.maps.chat_map import ChatMap, ChatMapConfig


class ListMap(ChatMap):
    """
    Very similar to ChatMap but uses structured output to get a list of strings that are turned into multiple rows in the dataset.
    """

    def __init__(self, config: dict):
        config = ChatMapConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """

        class ListResponse(BaseModel):
            # Use the output column name from config as the field name
            __annotations__ = {self.config.output_column: list[str]}

        return ListResponse

    def parse(self, original_dataset_row: dict, response: dict) -> list[dict] | dict:
        """
        Args:
            original_dataset_row: dict - The original dataset row
            response: ListResponse - A Pydantic model response
        Returns:
            new_dataset_rows: list[dict] | dict - A list of new dataset rows or a single new dataset row
        """
        new_dataset_rows = []
        for list_item in getattr(response, self.config.output_column):
            new_dataset_rows.append(
                {**original_dataset_row, self.config.output_column: list_item}
            )

        return new_dataset_rows

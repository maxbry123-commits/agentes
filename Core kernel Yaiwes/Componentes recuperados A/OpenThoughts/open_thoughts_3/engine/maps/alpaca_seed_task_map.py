import copy

from pydantic import BaseModel

from engine.maps.chat_map import ChatMap, ChatMapConfig


class AlpacaSeedTask(BaseModel):
    instruction: str
    input: str
    output: str


class AlpacaSeedTaskMap(ChatMap):
    def __init__(self, config: dict):
        config["output_column"] = "dummy"
        config = ChatMapConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """
        return AlpacaSeedTask

    def parse(
        self, original_dataset_row: dict, response: AlpacaSeedTask
    ) -> list[dict] | dict:
        """
        Args:
            original_dataset_row: dict - The original dataset row
            response: AlpacaSeedTask - A response from the completions model
        Returns:
            new_dataset_rows: list[dict] | dict - A list of new dataset rows or a single new dataset row
        """

        dataset_row = copy.deepcopy(original_dataset_row)
        dataset_row["instruction"] = response.instruction
        dataset_row["input"] = response.input
        dataset_row["output"] = response.output
        return [dataset_row, original_dataset_row]

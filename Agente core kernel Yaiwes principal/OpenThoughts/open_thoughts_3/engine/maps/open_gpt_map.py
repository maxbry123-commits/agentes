from pydantic import BaseModel

from engine.maps.chat_map import ChatMap


class OpenGPTMapConfig(BaseModel):
    output_task_column: str
    output_instruction_column: str
    output_input_column: str
    output_output_column: str
    user_message: str | None = None
    user_message_column: str | None = None
    system_message: str | None = None
    system_message_column: str | None = None


class OpenGPTMap(ChatMap):
    """
    Map for the OpenGPT dataset.
    """

    def __init__(self, config: dict):
        config = OpenGPTMapConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """

        class OpenGPTTask(BaseModel):
            task: str
            instruction: str
            input: str
            output: str

        class OpenGPTTaskList(BaseModel):
            tasks: list[OpenGPTTask]

        return OpenGPTTaskList

    def parse(self, original_dataset_row: dict, response: dict) -> list[dict] | dict:
        """
        Args:
            original_dataset_row: dict - The original dataset row
            response: UnnaturalInstructionsResponse - A Pydantic model response
        Returns:
            new_dataset_rows: list[dict] | dict - A list of new dataset rows or a single new dataset row
        """

        new_dataset_rows = []
        for list_item in response.tasks:
            new_dataset_rows.append(
                {
                    **original_dataset_row,
                    "task": list_item.task,
                    "instruction": list_item.instruction,
                    "input": list_item.input,
                    "output": list_item.output,
                }
            )

        return new_dataset_rows

from pydantic import BaseModel

from engine.maps.chat_map import ChatMap


class UnnaturalInstructionsMapConfig(BaseModel):
    output_instruction_column: str
    output_input_column: str
    output_constraints_column: str
    user_message: str | None = None
    user_message_column: str | None = None
    system_message: str | None = None
    system_message_column: str | None = None


class UnnaturalInstructionsMap(ChatMap):
    """
    Map for the Unnatural Instructions dataset.
    """

    def __init__(self, config: dict):
        config = UnnaturalInstructionsMapConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """

        class UnnaturalInstructionsResponse(BaseModel):
            instruction: str
            input: str
            constraints: str

            model_config = {"coerce_numbers_to_str": True}

        return UnnaturalInstructionsResponse

    def parse(self, original_dataset_row: dict, response: dict) -> list[dict] | dict:
        """
        Args:
            original_dataset_row: dict - The original dataset row
            response: UnnaturalInstructionsResponse - A Pydantic model response
        Returns:
            new_dataset_rows: list[dict] | dict - A list of new dataset rows or a single new dataset row
        """

        original_dataset_row[self.config.output_instruction_column] = str(
            response.instruction
        )
        original_dataset_row[self.config.output_input_column] = str(response.input)
        original_dataset_row[self.config.output_constraints_column] = str(
            response.constraints
        )
        return original_dataset_row

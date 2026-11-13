from pydantic import BaseModel

from engine.maps.chat_map import ChatMap, ChatMapConfig


class TextBlock(BaseModel):
    metadata: dict[str, str]
    content: str


class ContextualInstructions(BaseModel):
    text_blocks: list[TextBlock]
    instruction: str


class ContextualInstructionsList(BaseModel):
    prompts: list[ContextualInstructions]


class ContextualInstructionsMap(ChatMap):
    def __init__(self, config: dict):
        config = ChatMapConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """
        return ContextualInstructionsList

    def parse(self, original_dataset_row: dict, response: dict) -> list[dict] | dict:
        """
        Args:
            original_dataset_row: dict - The original dataset row
            response: ContextualInstructionsResponse - A Pydantic model response
        Returns:
            new_dataset_rows: list[dict] | dict - A list of new dataset rows or a single new dataset row
        """
        new_dataset_rows = []
        for prompt in response.prompts:
            prompt_str = ""
            for block in prompt.text_blocks:
                prompt_str += "BEGININPUT\nBEGINCONTEXT\n"
                for key, value in block.metadata.items():
                    prompt_str += f"{key}: {value}\n"
                prompt_str += f"ENDCONTEXT\n{block.content}\nENDINPUT\n"
            prompt_str += f"BEGININSTRUCTION\n{prompt.instruction}\nENDINSTRUCTION\n"
            new_dataset_rows.append(
                {**original_dataset_row, self.config.output_column: prompt_str}
            )

        return new_dataset_rows

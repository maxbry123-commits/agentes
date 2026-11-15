import re
import string

from pydantic import BaseModel

from dcft.data_strategies.Alpaca.utils import find_word_in_string
from engine.maps.base_map import CompletionsMap


class AlpacaMapConfig(BaseModel):
    alpaca_prompt_column: str
    output_instruction_column: str
    num_seed_instructions: int
    output_input_column: str
    output_output_column: str


class AlpacaMap(CompletionsMap):
    def __init__(self, config: dict):
        config = AlpacaMapConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A string that describes the format of the response from the completions model via Pydantic
        """
        return None

    def prompt(self, dataset_row: dict) -> list[dict] | str:
        """
        Args:
            dataset_row: dict - A row from the dataset
        Returns:
            A messages list for the completions model or string which gets converted to user prompt
        """
        return [
            {"role": "user", "content": dataset_row[self.config.alpaca_prompt_column]}
        ]

    # NOTE(Ryan): Slight difference, we don't discard truncated instructions here, since this isn't really issue we encounter with the newer models.
    def parse(self, original_dataset_row: dict, response: dict) -> list[dict] | dict:
        """
        Args:
            original_dataset_row: dict - The original dataset row
            response: str - A response from the completions model
        Returns:
            new_dataset_rows: list[dict] | dict - A list of new dataset rows or a single new dataset row
        """
        raw_instructions = (
            f"{self.config.num_seed_instructions+1}. Instruction:" + response
        )
        raw_instructions = re.split("###", raw_instructions)
        instructions = []
        for idx, inst in enumerate(raw_instructions):
            idx += self.config.num_seed_instructions + 1
            # NOTE(Ryan): This results in SyntaxWarning: invalid escape sequence '\.', but this is what the alpaca source has, so we keep it.
            splitted_data = re.split(f"{idx}\.\s+(Instruction|Input|Output):", inst)
            if len(splitted_data) != 7:
                continue
            else:
                inst = splitted_data[2].strip()
                input = splitted_data[4].strip()
                input = "" if input.lower() == "<noinput>" else input
                output = splitted_data[6].strip()
            # filter out too short or too long instructions
            if len(inst.split()) <= 3 or len(inst.split()) > 150:
                continue
            # filter based on keywords that are not suitable for language models.
            blacklist = [
                "image",
                "images",
                "graph",
                "graphs",
                "picture",
                "pictures",
                "file",
                "files",
                "map",
                "maps",
                "draw",
                "plot",
                "go to",
                "video",
                "audio",
                "music",
                "flowchart",
                "diagram",
            ]
            blacklist += []

            if any(find_word_in_string(word, inst) for word in blacklist):
                continue
            if inst.startswith("Write a program"):
                continue
            if inst[0] in string.punctuation:
                continue
            if not inst[0].isascii():
                continue
            instructions.append(
                {
                    self.config.output_instruction_column: inst,
                    self.config.output_input_column: input,
                    self.config.output_output_column: output,
                }
            )
        return instructions

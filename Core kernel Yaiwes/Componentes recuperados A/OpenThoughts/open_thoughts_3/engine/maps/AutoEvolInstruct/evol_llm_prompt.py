from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap


class AutoEvolResponse(BaseModel):
    methods_list: str
    plan: str
    rewritten_instruction: str
    finally_rewritten_instruction: str


class AutoEvolLLMMap(CompletionsMap):
    """
    Very similar to ChatMap but uses structured output to get a list of strings that are turned into multiple rows in the dataset.
    """

    def __init__(self, *args, **kwargs):
        pass

    def prompt(self, dataset_row: dict) -> list[dict]:
        """
        Generates completion requests for the LLM judge for a given dataset row.

        This method constructs a list of messages based on the dataset row. The system message
        is provided as a static string specific to the LLM judge. The system message is followed by a user message that
        includes the inputs, targets, and attempt from the dataset row. Only one request is created per row.

        Args:
            dataset_row (dict): A dictionary representing a single row of the dataset.

        Returns:
            list[dict]: A list containing a single request body dictionary.
        """
        # Store messages as request body
        messages = []
        message = f"""
        {dataset_row['evol_prompt']}
        #Instruction#:
        {dataset_row['finally_rewritten_instructions'][-1]}
        """
        messages.append(
            {
                "role": "user",
                "content": message,
            }
        )
        return messages

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """
        return AutoEvolResponse

    def parse(self, original_dataset_row: dict, response: dict) -> list[dict] | dict:
        """
        Args:
            original_dataset_row: dict - The original dataset row
            response: ListResponse - A Pydantic model response
        Returns:
            new_dataset_rows: list[dict] | dict - A list of new dataset rows or a single new dataset row
        """
        original_dataset_row["finally_rewritten_instructions"].append(
            response.finally_rewritten_instruction
        )
        return [original_dataset_row]

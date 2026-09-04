from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap


class AutoTrajectoryAnalysisLLMMap(CompletionsMap):
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
        The following list shows cases where an Instruction evolves into a
        more complex version of an Instruction.
        For each case, stage 0 represents the Instruction in its initial state, and
        each subsequent stage requires an increase in complexity based on
        the previous stage.
        Please identify cases that failed to evolve, and provide their case ID
        and reasons.
        """
        for idx, instr in enumerate(dataset_row["finally_rewritten_instructions"]):
            message += f"Instruction {idx + 1}: {instr} \n"
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
        return None

    def parse(self, original_dataset_row: dict, response: dict) -> list[dict] | dict:
        """
        Args:
            original_dataset_row: dict - The original dataset row
            response: ListResponse - A Pydantic model response
        Returns:
            new_dataset_rows: list[dict] | dict - A list of new dataset rows or a single new dataset row
        """
        original_dataset_row["feedback"] = response
        return [original_dataset_row]

import re

from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap


class ChatMapConfig(BaseModel):
    user_message: str | None = None
    user_message_column: str | None = None
    system_message: str | None = None
    system_message_column: str | None = None
    output_column: str


class ChatMap(CompletionsMap):
    def __init__(self, config: dict):
        config = ChatMapConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """
        return None

    def _fill_templated_strings(self, template: str, dataset_row: dict) -> str:
        """
        Replaces templated strings in a template string with values from a dataset row

        Args:
            template: str - A template string with {{column_name}} patterns
            dataset_row: dict - Dictionary containing values to replace the patterns
        Returns:
            str - A template string with {{column_name}} patterns replaced with values from the dataset row

        Example: Pattern looks for {{something}}
            template = "Hello {{name}}, your age is {{age}}"
            dataset_row = {"name": "Alice", "age": 30}

            For each match, the regex groups are:
            - group(0): full match (e.g., "{{name}}")
            - group(1): captured column name (e.g., "name")
        """
        pattern = r"\{\{(\w+)\}\}"
        # For each match, lambda gets a match object (x) where:
        # x.group(0) would be the full match like "{{name}}"
        # x.group(1) gets just the column name like "name" to use as the dictionary key
        return re.sub(pattern, lambda x: str(dataset_row[x.group(1)]), template)

    def prompt(self, dataset_row: dict) -> list[dict] | str:
        """
        Args:
            dataset_row: dict - A row from the dataset
        Returns:
            A messages list for the completions model or string which gets converted to user prompt
        """
        messages = []

        # Set system message
        system_message = None
        if self.config.system_message and self.config.system_message_column:
            raise ValueError(
                "Both system_message and system_message_column provided, only one can be used at a time"
            )
        if self.config.system_message:
            system_message = self._fill_templated_strings(
                self.config.system_message, dataset_row
            )
        if self.config.system_message_column:
            system_message = dataset_row[self.config.system_message_column]
        if system_message:
            messages.append({"role": "system", "content": system_message})

        # Set user message
        user_message = None
        if self.config.user_message and self.config.user_message_column:
            raise ValueError(
                "Both user_message and user_message_column provided, only one can be used at a time"
            )
        if self.config.user_message:
            user_message = self._fill_templated_strings(
                self.config.user_message, dataset_row
            )
        if self.config.user_message_column:
            user_message = dataset_row[self.config.user_message_column]
        if user_message:
            messages.append({"role": "user", "content": user_message})
        else:
            raise ValueError(
                "You must provide either user_message or user_message_column and the values in user_message_column must be non-null"
            )

        return messages

    def parse(self, original_dataset_row: dict, response: dict) -> list[dict] | dict:
        """
        Args:
            original_dataset_row: dict - The original dataset row
            response: str - A response from the completions model
        Returns:
            new_dataset_rows: list[dict] | dict - A list of new dataset rows or a single new dataset row
        """
        original_dataset_row[self.config.output_column] = response
        return original_dataset_row

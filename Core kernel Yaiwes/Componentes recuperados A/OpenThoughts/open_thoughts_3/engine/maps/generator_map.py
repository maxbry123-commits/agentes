from engine.maps.list_map import ListMap


class GeneratorMap(ListMap):
    """
    Very similar to ListMap but uses structured output to get a list of strings that are turned into one single row in the dataset.
    """

    def parse(self, original_dataset_row: dict, response: dict) -> list[dict] | dict:
        """
        Args:
            original_dataset_row: dict - The original dataset row
            response: ListResponse - A Pydantic model response
        Returns:
            new_dataset_rows: list[dict] | dict - A list of new dataset rows or a single new dataset row
        """
        new_dataset_rows = []
        new_dataset_rows.append(
            {
                **original_dataset_row,
                self.config.output_column: getattr(response, self.config.output_column),
            }
        )
        return new_dataset_rows

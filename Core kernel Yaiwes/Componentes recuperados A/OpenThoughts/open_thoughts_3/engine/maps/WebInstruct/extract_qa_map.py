import re

from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap


class QAPair(BaseModel):
    question: str
    answer: str


class ExtractedQAs(BaseModel):
    qa_exists: bool
    extracted_qa_pairs: list[QAPair]


class ExtractQAMapConfig(BaseModel):
    input_text_column: str
    output_question_column: str
    output_answer_column: str


EXTRACT_QA_SYSTEM_PROMPT = """You are given a set of pre-processed documents, each of which may contain natural question-answer (Q-A) pairs. Your task is to identify and extract these pairs while ignoring unrelated content such as ads, markup, or boilerplate text.
Input: Each document contains multiple sections of text. Some of these sections may have clear questions followed by answers, while others may be irrelevant (e.g., ads or noise).
Output: Extract the Q-A pairs found within each document. A valid Q-A pair must consist of a clearly defined question and its corresponding answer. 
If no natural Q-A pair exists in the document, return an empty list and set qa_exists to False.
"""


class ExtractQAMap(CompletionsMap):
    """
    A map that extracts Q-A pairs from a given text.
    """

    def __init__(self, config: dict):
        config = ExtractQAMapConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """
        return ExtractedQAs

    def prompt(self, dataset_row: dict) -> list[dict] | str:
        """
        Args:
            dataset_row: dict - A row from the dataset
        Returns:
            A messages list for the completions model or string which gets converted to user prompt
        """

        return [
            {"role": "system", "content": EXTRACT_QA_SYSTEM_PROMPT},
            {"role": "user", "content": dataset_row[self.config.input_text_column]},
        ]

    def parse(self, original_dataset_row: dict, response: dict) -> list[dict] | dict:
        """
        Args:
            original_dataset_row: dict - The original dataset row
            response: str - A response from the completions model
        Returns:
            new_dataset_rows: list[dict] | dict - A list of new dataset rows or a single new dataset row
        """
        new_dataset_rows = []
        if response.qa_exists or len(response.extracted_qa_pairs) > 0:
            for qa_pair in response.extracted_qa_pairs:
                new_dataset_row = original_dataset_row.copy()
                new_dataset_row[self.config.output_question_column] = qa_pair.question
                new_dataset_row[self.config.output_answer_column] = qa_pair.answer
                new_dataset_rows.append(new_dataset_row)
        return new_dataset_rows

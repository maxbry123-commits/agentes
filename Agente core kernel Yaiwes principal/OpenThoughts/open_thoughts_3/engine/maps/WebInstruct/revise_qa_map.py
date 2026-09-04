import re

from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap


class RevisedQAs(BaseModel):
    revised_question: str
    revised_answer: str


class ReviseQAMapConfig(BaseModel):
    input_question_column: str
    input_answer_column: str
    input_source_document_column: str
    output_question_column: str
    output_answer_column: str


REVISE_QA_SYSTEM_PROMPT = """
Your task is to revise a collection of educational question-and-answer pairs sourced from the web.
These questions and answers come from a source document.

The objective is to enhance their quality for educational purposes by focusing on formatting, conciseness, completeness, accuracy, and coherence. Please adhere to the following guidelines for each pair:
1. Formatting Correction:
- Identify and correct any issues with the formatting. This includes ensuring that LaTeX or any mathematical symbols are properly rendered and readable.
- Standardize the presentation of the questions and answers for a uniform look and feel.
2. Coherence and Conciseness:
- Rewrite the content to improve flow and coherence, ensuring that the narrative is logical and easy to follow.
- Make the content concise. Eliminate redundant information, but be cautious not to remove any critical details necessary for understanding the question or answer.
3. Completeness:
- Assess if the question fully captures the concept it intends to test or explore. Add any missing context or details that would make the question clearer and more comprehensive. Use
context from the source document to augment the question.
- Ensure that the answer provides a complete solution or explanation. Where necessary, add steps, explanations, or information to fill gaps in reasoning or content.
4. Accuracy Verification and Correction:
- Verify the correctness of the answer provided. Use the information from the source document to help ensure answer accuracy. 
- If inaccuracies are found, correct them with the right solution. **ONLY MAKE CHANGES IF YOU ARE VERY CONFIDENT ABOUT YOUR ANSWER!**
Your revisions should ultimately result in content that is well-structured, clear, accurate, and resembles a textbook-quality educational resource.
"""


class ReviseQAMap(CompletionsMap):
    """
    A map that revises Q-A pairs.
    """

    def __init__(self, config: dict):
        config = ReviseQAMapConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """
        return RevisedQAs

    def prompt(self, dataset_row: dict) -> list[dict] | str:
        """
        Args:
            dataset_row: dict - A row from the dataset
        Returns:
            A messages list for the completions model or string which gets converted to user prompt
        """
        user_message = f"Source Document: {dataset_row[self.config.input_source_document_column]}\nQuestion: {dataset_row[self.config.input_question_column]}\nAnswer: {dataset_row[self.config.input_answer_column]}"
        return [
            {"role": "system", "content": REVISE_QA_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

    def parse(self, original_dataset_row: dict, response: dict) -> list[dict] | dict:
        """
        Args:
            original_dataset_row: dict - The original dataset row
            response: str - A response from the completions model
        Returns:
            new_dataset_rows: list[dict] | dict - A list of new dataset rows or a single new dataset row
        """
        new_dataset_row = original_dataset_row.copy()
        new_dataset_row[self.config.output_question_column] = response.revised_question
        new_dataset_row[self.config.output_answer_column] = response.revised_answer
        return new_dataset_row

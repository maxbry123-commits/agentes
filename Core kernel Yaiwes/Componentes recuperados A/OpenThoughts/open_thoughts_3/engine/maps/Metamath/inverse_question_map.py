from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap


class Quantity(BaseModel):
    surrounding_context: str
    inverse_question: str
    inverse_answer: str


class Quantities(BaseModel):
    quantities: list[Quantity]


class InverseQuestionMapConfig(BaseModel):
    question_column: str
    output_inverse_question_column: str
    output_inverse_answer_column: str


class InverseQuestionMap(CompletionsMap):
    """
    Given a question and answer pair, generate a list of inverse questions and answers
    based on replacing numerical quantities in the original question with X.
    """

    def __init__(self, config: dict):
        config = InverseQuestionMapConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """
        return Quantities

    def prompt(self, dataset_row: dict) -> list[dict]:
        """
        Prompt model to generate inverse questions and answers.
        """
        system_prompt = """
        You are an expert at extracting numerical quantities from questions and "inverting" the questions to create new questions by replacing them with X.
        The answer to the new question should be the quantity you extracted and then replaced with X. Also output your
        confidence (between 1 and 5) that the answer is correct.

        Rules:
        - Numerical quantities are numbers, e.g. 1, 2.5, three, 4/10, etc. Only return a number, no units.
        - Non-numerical quantities are: unknown variables, e.g. x, y, z,, ranges, e.g. 1,2,3,..,4,5, days of the week, e.g. Monday to Friday.
        - Do not repeat the original question. Do not try to answer the original question itself.
        - Make sure the surrounding context verbatim matches text from the original question.
        - For the inverse question, don't change anything other than the numerical quantity you're replacing. 
        Simply replace the numerical quantity with X.

        Example 1:
        Question: Let a, b be positive integers. If a + b = 2\sqrt\{2\}, and b = 2, then what is the value of a?
        Answer: 
        [{
            "inverse_question": "Let a, b be positive integers. If a + b = X, and b = 2, then what is the value of a?",
            "inverse_answer": "2\sqrt\{2\}",
            "surrounding_context": "a + b = 2\sqrt\{2\}",
        },
        {
            "inverse_question": "Let a, b be positive integers. If a + b = X, and b = 2, then what is the value of a?",
            "inverse_answer": "2",
            "surrounding_context": "a + b = 2\sqrt\{2\}",
        }, 
        {
            "inverse_question": "Let a, b be positive integers. If a + b = 2\sqrt\{2\}, and b = X, then what is the value of a?",
            "inverse_answer": "2",
            "surrounding_context": "b = 2",
        }]

        Example 2:
        Question: Determine the value of r in the equation r^2 - 3 = 0.
        Answer: 
        [{
            "inverse_question": "Determine the value of r in the equation r^X - 3 = 0.",
            "inverse_answer": "2",
            "surrounding_context": "r^2 - 3 = 0",
        },
        {
            "inverse_question": "Determine the value of r in the equation r^2 - X = 0.",
            "inverse_answer": "3",
            "surrounding_context": "r^2 - 3 = 0",
        },
        {
            "inverse_question": "Determine the value of X in the equation r^2 - 3 = X.",
            "inverse_answer": "0",
            "surrounding_context": "r^2 - 3 = 0",
        },
        {
            "inverse_question": "Determine the value of X in the equation ^2 - 3 = X.",
            "inverse_answer": "0",
            "surrounding_context": "r^2 - 3 = 0",
        }
        ]
        """
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": dataset_row[self.config.question_column]},
        ]

    @staticmethod
    def _is_numeric(s: str) -> bool:
        """Check if string contains a number."""
        return any(char.isdigit() for char in s)

    @staticmethod
    def _contains_X(s: str) -> bool:
        """Check if string contains X."""
        return "X" in s.split(" ")

    def parse(self, dataset_row: dict, response: Quantities):
        """
        Parse the response from the completions model and filter out bad
        inverse questions and answers.

        Args:
            dataset_row: A row from the dataset
            response: The response from the completions model

        Returns:
            A list of dictionaries with the original question, answer, and the inverse question and answer.
        """
        new_rows = []
        for quantity in response.quantities:
            if self._is_numeric(quantity.inverse_answer) and self._contains_X(
                quantity.inverse_question
            ):
                new_row = dataset_row.copy()
                new_row[self.config.output_inverse_question_column] = (
                    quantity.inverse_question
                )
                new_row[self.config.output_inverse_answer_column] = (
                    quantity.inverse_answer
                )
                new_rows.append(new_row)
        return new_rows

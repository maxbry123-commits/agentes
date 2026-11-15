from enum import Enum
from typing import Optional

from pydantic import BaseModel, conlist

from engine.maps.base_map import CompletionsMap


class MathSameConfig(BaseModel):
    math_column: str
    question_column: str
    output_column: str
    ending_characters: Optional[int] = 1000
    num_responses: int


class Choices1(Enum):
    _0 = "0"


class Choices3(Enum):
    _0 = "0"
    _1 = "1"
    _2 = "2"



class Choices4(Enum):
    _0 = "0"
    _1 = "1"
    _2 = "2"
    _3 = "3"



class Choices6(Enum):
    _0 = "0"
    _1 = "1"
    _2 = "2"
    _3 = "3"
    _4 = "4"
    _5 = "5"



class Choices8(Enum):
    _0 = "0"
    _1 = "1"
    _2 = "2"
    _3 = "3"
    _4 = "4"
    _5 = "5"
    _6 = "6"
    _7 = "7"


class Choices9(Enum):
    _0 = "0"
    _1 = "1"
    _2 = "2"
    _3 = "3"
    _4 = "4"
    _5 = "5"
    _6 = "6"
    _7 = "7"
    _8 = "8"


class Choices12(Enum):
    _0 = "0"
    _1 = "1"
    _2 = "2"
    _3 = "3"
    _4 = "4"
    _5 = "5"
    _6 = "6"
    _7 = "7"
    _8 = "8"
    _9 = "9"
    _10 = "10"
    _11 = "11"


class Choices16(Enum):
    _0 = "0"
    _1 = "1"
    _2 = "2"
    _3 = "3"
    _4 = "4"
    _5 = "5"
    _6 = "6"
    _7 = "7"
    _8 = "8"
    _9 = "9"
    _10 = "10"
    _11 = "11"
    _12 = "12"
    _13 = "13"
    _14 = "14"
    _15 = "15"


class MathSameMap(CompletionsMap):
    def __init__(self, config: MathSameConfig):
        config = MathSameConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """

        # Pre-define response models for different num_responses
        class MathSameResponse1(BaseModel):
            response: conlist(Choices1, min_length=0, max_length=1)
            reasoning: str

        class MathSameResponse3(BaseModel):
            response: conlist(Choices3, min_length=0, max_length=3)
            reasoning: str
        
        class MathSameResponse4(BaseModel):
            response: conlist(Choices4, min_length=0, max_length=4)
            reasoning: str

        class MathSameResponse6(BaseModel):
            response: conlist(Choices6, min_length=0, max_length=6)
            reasoning: str

        class MathSameResponse8(BaseModel):
            response: conlist(Choices8, min_length=0, max_length=8)
            reasoning: str

        class MathSameResponse9(BaseModel):
            response: conlist(Choices9, min_length=0, max_length=9)
            reasoning: str

        class MathSameResponse12(BaseModel):
            response: conlist(Choices12, min_length=0, max_length=12)
            reasoning: str

        class MathSameResponse16(BaseModel):
            response: conlist(Choices16, min_length=0, max_length=16)
            reasoning: str

        # Select appropriate response model based on num_responses
        response_models = {
            1: MathSameResponse1,
            3: MathSameResponse3,
            4: MathSameResponse4,
            6: MathSameResponse6,
            8: MathSameResponse8,
            9: MathSameResponse9,
            12: MathSameResponse12,
            16: MathSameResponse16,
        }

        return response_models[self.config.num_responses]

    def prompt(self, dataset_row: dict) -> str:
        prompt = f"""
            I will provide you the last words of {len(dataset_row[self.config.math_column])} math problem solutions.
            They are candidate solutions to a problem.

            They will typically contain the solution to a math problem. I want you to return the indices of the responses with the most common final numerical answer.
            Only the final numerical answer matters.

            Question: What is 3 x 5?

            Solution 0:
            answer is 15.
            
            Solution 1:
            15.0 is the solution to this problem.
            
            Solution 2:
            The answer is 14.
            
            You would return: [0, 1] since they are both saying 15 is the same answer and only one response is saying 14 is the answer.

            Here is your question:
            {dataset_row[self.config.question_column]}

            Here are your candidate solutions: 
            """
        for idx, math_sample in enumerate(dataset_row[self.config.math_column]):
            length_of_string = len(math_sample)
            mini = -1 * min(length_of_string, self.config.ending_characters)
            prompt += f"Solution {idx}: \n\n {math_sample[mini:]}\n\n"
        prompt += f"\n\n Now tell me the solutions. Please remember to zero index these solutions. Do not include the number {len(dataset_row[self.config.math_column])} as an index."
        return prompt

    def parse(self, original_dataset_row: dict, response: dict) -> list[dict] | dict:
        """
        Args:
            original_dataset_row: dict - The original dataset row
            response: str - A response from the completions model
        Returns:
            new_dataset_rows: list[dict] | dict - A list of new dataset rows or a single new dataset row
        """
        original_dataset_row[self.config.output_column] = [
            val.value for val in response.response
        ]
        original_dataset_row["_judge_reasoning"] = response.reasoning

        return original_dataset_row

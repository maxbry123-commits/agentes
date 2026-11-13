from enum import Enum
from typing import Optional

from pydantic import BaseModel, conlist

from engine.maps.base_map import CompletionsMap


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

class ScienceSameConfig(BaseModel):
    answer_column: str
    question_column: str
    output_column: str
    ending_characters: Optional[int] = 1000
    num_responses: int

class ScienceSameMap(CompletionsMap):
    def __init__(self, config: ScienceSameConfig):
        config = ScienceSameConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """
        
        # Pre-define response models for different num_responses
        class ScienceSameResponse1(BaseModel):
            response: conlist(Choices1, min_length=0, max_length=1)
            reasoning: str

        class ScienceSameResponse3(BaseModel):
            response: conlist(Choices3, min_length=0, max_length=3)
            reasoning: str
        
        class ScienceSameResponse4(BaseModel):
            response: conlist(Choices4, min_length=0, max_length=4)
            reasoning: str

        class ScienceSameResponse6(BaseModel):
            response: conlist(Choices6, min_length=0, max_length=6)
            reasoning: str

        class ScienceSameResponse8(BaseModel):
            response: conlist(Choices8, min_length=0, max_length=8)
            reasoning: str

        class ScienceSameResponse9(BaseModel):
            response: conlist(Choices9, min_length=0, max_length=9)
            reasoning: str

        class ScienceSameResponse12(BaseModel):
            response: conlist(Choices12, min_length=0, max_length=12)
            reasoning: str

        class ScienceSameResponse16(BaseModel):
            response: conlist(Choices16, min_length=0, max_length=16)
            reasoning: str

        # Select appropriate response model based on num_responses
        response_models = {
            1: ScienceSameResponse1,
            3: ScienceSameResponse3,
            4: ScienceSameResponse4,
            6: ScienceSameResponse6,
            8: ScienceSameResponse8,
            9: ScienceSameResponse9,
            12: ScienceSameResponse12,
            16: ScienceSameResponse16,
        }

        return response_models[self.config.num_responses]

    def prompt(self, dataset_row: dict) -> str:
        prompt = f"""
            I will provide you the last words of {len(dataset_row[self.config.answer_column])} math problem solutions.
            They are candidate solutions to a problem.

            They will typically contain the solution to a science problem. I want you to return the indices of the responses with the most common answer.
            
            Here is your question:
            {dataset_row[self.config.question_column]}

            Here are your candidate solutions: 
            """
        for idx, science_sample in enumerate(dataset_row[self.config.answer_column]):
            length_of_string = len(science_sample)
            mini = -1 * min(length_of_string, self.config.ending_characters)
            prompt += f"Solution {idx}: \n\n {science_sample[mini:]}\n\n"
        prompt += f"\n\n Now tell me the solutions. Please remember to zero index these solutions. Do not include the number {len(dataset_row[self.config.answer_column])} as an index."
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
            int(val) for val in response.response
        ]
        original_dataset_row["_judge_reasoning"] = response.reasoning

        return original_dataset_row

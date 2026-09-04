from enum import Enum
from typing import Optional

from pydantic import BaseModel, conlist

from engine.maps.base_map import CompletionsMap


class CodeSameConfig(BaseModel):
    code_column: str
    question_column: str
    output_column: str
    num_responses: int
    ending_character: Optional[int] = None


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



class CodeSameMap(CompletionsMap):
    def __init__(self, config: CodeSameConfig):
        config = CodeSameConfig(**config)
        self.config = config

    @property
    def response_format(self):
        """
        Returns:
            A Pydantic model that describes the format of the response from the completions model
        """

        # Pre-define response models for different num_responses
        class CodeSameResponse1(BaseModel):
            response: conlist(Choices1, min_length=0, max_length=1)
            reasoning: str

        class CodeSameResponse3(BaseModel):
            response: conlist(Choices3, min_length=0, max_length=3)
            reasoning: str

        class CodeSameResponse4(BaseModel):
            response: conlist(Choices4, min_length=0, max_length=4)
            reasoning: str

        class CodeSameResponse6(BaseModel):
            response: conlist(Choices6, min_length=0, max_length=6)
            reasoning: str

        class CodeSameResponse8(BaseModel):
            response: conlist(Choices8, min_length=0, max_length=8)
            reasoning: str

        class CodeSameResponse9(BaseModel):
            response: conlist(Choices9, min_length=0, max_length=9)
            reasoning: str

        class CodeSameResponse12(BaseModel):
            response: conlist(Choices12, min_length=0, max_length=12)
            reasoning: str

        class CodeSameResponse16(BaseModel):
            response: conlist(Choices16, min_length=0, max_length=16)
            reasoning: str

        # Select appropriate response model based on num_responses
        response_models = {
            1: CodeSameResponse1,
            3: CodeSameResponse3,
            4: CodeSameResponse4,
            6: CodeSameResponse6,
            8: CodeSameResponse8,
            9: CodeSameResponse9,
            12: CodeSameResponse12,
            16: CodeSameResponse16,
        }

        return response_models[self.config.num_responses]

    def prompt(self, dataset_row: dict) -> str:
        prompt = f"""
            I will provide you {len(dataset_row[self.config.code_column])} code_samples.
            They are candidate solutions to a coding problem.

            I want you to compare all of the code samples functionally and return a list of indeces corresponding to
            the samples that constitute the most common solutions that are functionally equivalent. If there are sets 
            of solutions that are of the same size, pick one of the sets at random. I want you to also provide your reasoning
            for the indices you respond being functionally equivalent. Here is an example:

            Question: Solve fizzbuzz.

            Solution 0:
            def fizzbuzz1(n):
                for i in range(1, n + 1):
                    output = ''
                    
                    if i % 3 == 0:
                        output += 'Fizz'
                    if i % 5 == 0:
                        output += 'Buzz'
                        
                    print(output or i)
            
            Solution 1:
            def fizzbuzz2(n):
                for i in range(1, n + 1):
                    if i % 3 == 0 and i % 5 == 0:
                        print('FizzBuzz')
                    elif i % 3 == 0:
                        print('Fizz')
                    elif i % 5 == 0:
                        print('Buzz')
                    else:
                        print(i)
            
            Solution 2:
            def fizzbuzz3(n):
                for i in range(1, n + 1):
                    # Multiple logical errors:
                    if i % 3 == 0:  # Notice no brackets needed for simple if statements
                        print('Fizz')
                    elif i % 5 == 0:
                        print('Buzz')
                    elif i % 3 == 0 or i % 5 == 0:  # Wrong logic order and operator
                        print('FizzBuzz')
                    else:
                        print(i)
            
            You would return: [0, 1] since they are functionally equivalent but the third response is different. 

            Here is your question:
            {dataset_row[self.config.question_column]}

            Here are your candidate solutions: 
            """
        for idx, code_sample in enumerate(dataset_row[self.config.code_column]):
            if self.config.ending_character is not None:
                code_sample = code_sample[-1 * self.config.ending_character :]
            prompt += f"Solution {idx}: \n\n {code_sample}\n\n"
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

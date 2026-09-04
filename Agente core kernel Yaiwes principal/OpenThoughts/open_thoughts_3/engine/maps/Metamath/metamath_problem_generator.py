from pydantic import BaseModel

from engine.maps.base_map import CompletionsMap

class Problem(BaseModel):
    question: str
    detailed_answer: str
    answer: str 

class GeneratedProblem(BaseModel):
    problems: list[Problem]


class GenerateMathProblemConfig(BaseModel):
    starting_id: int = 75001
    ending_id: int = 150000
    problems_per_input: int = 2
    question_column: str = "question"
    detailed_answer_column: str = "detailed_answer"
    answer_column: str = "answer"


class GenerateMathProblemMap(CompletionsMap):
    """
    Generate multiple new math problems similar to each input problem while maintaining
    the same structure and including both detailed and numerical answers.
    """

    def __init__(self, config: dict):
        super().__init__()
        self.init(config)

    def init(self, config: dict):
        config = GenerateMathProblemConfig(**config)
        self.config = config
        self.current_id = config.starting_id

    @property
    def response_format(self):
        return GeneratedProblem

    def prompt(self, dataset_row: dict) -> list[dict]:
        system_prompt = """
        You are an expert mathematics problem generator. Given a sample math problem with its detailed solution 
        and numerical answer, create new, unique problems of similar style. Each new problem MUST include:
        1. A "question" field with the problem text
        2. A "detailed_answer" field with the step-by-step solution
        3. An "answer" field with ONLY the final numerical answer

        Format your response EXACTLY as a JSON object:
        {
            "problems": [
                {
                    "question": "Problem text here",
                    "detailed_answer": "Step-by-step solution here",
                    "answer": "Final numerical answer here"
                },
                ...
            ]
        }
        """

        user_prompt = f"""
        Original Problem:
        {dataset_row[self.config.question_column]}
        
        Detailed Solution:
        {dataset_row[self.config.detailed_answer_column]}
        
        Numerical Answer:
        {dataset_row[self.config.answer_column]}
        
        Generate {self.config.problems_per_input} new, similar problems with both detailed solutions and numerical answers.
        Ensure each problem is unique and uses different numbers and contexts.
        """

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def get_next_id(self) -> str:
        if self.current_id > self.config.ending_id:
            raise ValueError(f"Exceeded maximum question ID {self.config.ending_id}")

        next_id = str(self.current_id)
        self.current_id += 1
        return next_id

    def parse(self, dataset_row: dict, response: GeneratedProblem) -> list[dict]:
        """
        Parse the response and add unique question IDs to each generated problem.
        """
        result = []

        for problem_data in response.problems:
            if self.current_id > self.config.ending_id:
                break

            try:
                new_problem = {
                    "question": str(problem_data.question),
                    "detailed_answer": str(problem_data.detailed_answer),
                    "answer": str(problem_data.answer),
                    "question_id": str(self.get_next_id()),
                }

                if self.validate_problem(new_problem):
                    result.append(new_problem)
            except Exception as e:
                print(f"Error processing problem: {e}")
                continue

        return result

    def validate_problem(self, problem: dict) -> bool:
        """
        Validate that a generated problem meets basic requirements.
        """
        required_fields = ["question", "detailed_answer", "answer"]
        if not all(field in problem and problem[field] for field in required_fields):
            return False

        # Check that the problem and solution contain mathematical content
        math_indicators = ["$", "=", "+", "-", "*", "/", "\\frac", "\\sqrt"]
        has_math = any(
            indicator in problem["question"] or indicator in problem["detailed_answer"]
            for indicator in math_indicators
        )

        # Convert answer to string before checking for numerical content
        answer_str = str(problem["answer"])
        has_numerical_answer = any(char.isdigit() for char in answer_str)

        return has_math and has_numerical_answer

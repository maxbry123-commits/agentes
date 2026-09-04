import os

from bespokelabs import curator
from datasets import load_dataset
from math_verify.metric import math_metric
from math_verify.parser import ExprExtractionConfig, LatexExtractionConfig
from pydantic import BaseModel

num_cpus = os.cpu_count()


class Reasoner(curator.LLM):
    """Curator class for processing Numina dataset."""

    return_completions_object = True

    def prompt(self, input):
        return input["problem"]

    def parse(self, input, response):
        """Parse the LLM response to extract reasoning and solution."""
        response_text = response["choices"][0]["message"]["content"]

        # Extract reasoning between <think> tags
        reasoning_start = response_text.find("<think>") + len("<think>")
        reasoning_end = response_text.find("</think>")
        input["r1_reasoning"] = response_text[reasoning_start:reasoning_end].strip()

        # Everything after </think> is the solution
        solution_start = reasoning_end + len("</think>")
        input["r1_solution"] = response_text[solution_start:].strip()

        return input


# https://api.together.ai/models/deepseek-ai/DeepSeek-R1
llm = Reasoner(
    model_name="deepseek-ai/DeepSeek-R1",
    backend="openai",
    generation_params={
        "max_tokens": 16000,
    },
    backend_params={
        "base_url": "https://api.together.xyz/v1",
        "api_key": os.environ.get("TOGETHER_API_KEY"),
        "max_retries": 3,
        "request_timeout": 60 * 30,
        "max_requests_per_minute": 90,
        "max_tokens_per_minute": 249_960,
        "require_all_responses": False,
    },
)

ds = load_dataset("AI-MO/NuminaMath-1.5", split="train")
ds = ds.filter(lambda x: x["question_type"] != "proof")
ds = ds.filter(
    lambda x: x["source"]
    in ["inequalities", "number_theory", "cn_contest", "olympiads_ref"]
)
ds = ds.filter(
    lambda x: x["problem_is_valid"] == "Yes" and x["solution_is_valid"] == "Yes"
)
ds = ds.filter(lambda x: x["problem"] not in [None, "", " ", "  "])
ds = ds.filter(lambda x: x["answer"] not in [None, "", " ", "  ", "not found", "proof"])
ds = llm(ds)
ds.push_to_hub("mlfoundations-dev/numina_math_1_5_extra_r1")


# class JudgeResult(BaseModel):
#     """Result of the judge's evaluation."""

#     correct: bool
#     reasoning: str


# class MathJudge(curator.LLM):
#     """Curator class for processing Numina dataset."""

#     response_format = JudgeResult

#     def prompt(self, input):
#         """Create a prompt for the judge to evaluate the correctness of a solution."""
#         return f"""
#         You are a judge that evaluates the correctness of a solution.
#         You will be given a solution and a ground truth solution.
#         You will need to determine if the solution is correct.
#         Answers are in the format of \\boxed{{}}.

#         SOLUTION: {input["r1_solution"]}
#         GROUND TRUTH SOLUTION: {input["solution"]}
#         """

#     def parse(self, input, response):
#         """Parse the judge's response to extract correctness and reasoning."""
#         return {
#             **input,
#             "judge_correct": response.correct,
#             "judge_reasoning": response.reasoning,
#         }

# math_judge = MathJudge(model_name="gpt-4o")
# ds = math_judge(ds)


# gold_is_latex = True
# verify_func = math_metric(
#     gold_extraction_target=(LatexExtractionConfig() if gold_is_latex else ExprExtractionConfig(),),
#     pred_extraction_target=(ExprExtractionConfig(), LatexExtractionConfig()),
#     aggregation_function=max,
#     fallback_mode="first_match",
#     precision=6,
# )


# def validate_solution(row):
#     extracted_answers = ""
#     gold_answers = ""
#     grade = 0
#     try:
#         grade, extracted_answers = verify_func([row["solution"]], [row["r1_solution"]])

#         if extracted_answers is None:
#             extracted_answers = ""
#             gold_answers = ""
#         else:
#             gold_answers = str(extracted_answers[0])
#             extracted_answers = str(extracted_answers[1])

#         row['math_verify_extracted_r1_answer'] = extracted_answers
#         row['math_verify_extracted_ground_truth_answer'] = gold_answers
#         row['math_verify_correct'] = grade == 1
#         row['math_verify_error'] = ""

#     except Exception as e:
#         row['math_verify_extracted_r1_answer'] = ""
#         row['math_verify_extracted_ground_truth_answer'] = ""
#         row['math_verify_correct'] = False
#         row['math_verify_error'] = str(e)

#     return row

# ds = ds.map(validate_solution, num_proc=os.cpu_count())

# ds.push_to_hub("mlfoundations-dev/hardmath_r1")
# ds.to_json(os.path.expanduser("~/Downloads/hardmath_r1.jsonl"))

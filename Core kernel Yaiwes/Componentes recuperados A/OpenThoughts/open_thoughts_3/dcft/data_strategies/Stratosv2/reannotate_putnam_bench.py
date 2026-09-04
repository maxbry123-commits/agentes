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
        return input["informal_statement"]

    def parse(self, input, response):
        """Parse the LLM response to extract reasoning and solution."""
        input["r1_reasoning"] = response["choices"][0]["message"]["reasoning"]
        input["r1_solution"] = response["choices"][0]["message"]["content"]
        return input


# https://openrouter.ai/deepseek/deepseek-r1/providers
llm = Reasoner(
    model_name="deepseek/deepseek-r1",
    backend="openai",
    generation_params={
        "include_reasoning": True,
        "max_tokens": 32000,
        "provider": {
            "order": ["Fireworks", "Kluster"],
            "allow_fallbacks": False,
            "sort": "throughput",
            "require_parameters": True,
        },
    },
    backend_params={
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": os.environ.get("OPENROUTER_API_KEY"),
        "invalid_finish_reasons": [
            "content_filter",
            "length",
            "unknown",
        ],
        "max_retries": 20,
        "max_requests_per_minute": 20,
        "max_tokens_per_minute": 10000000000000,
        "request_timeout": 60 * 30,
    },
)

ds = load_dataset("amitayusht/PutnamBench", split="train")
ds = ds.filter(lambda x: x["informal_statement"] is not None)
print(ds)
ds = llm(ds)


class JudgeResult(BaseModel):
    """Result of the judge's evaluation."""

    correct: bool
    reasoning: str


class MathJudge(curator.LLM):
    """Curator class for processing Numina dataset."""

    response_format = JudgeResult

    def prompt(self, input):
        """Create a prompt for the judge to evaluate the correctness of a solution."""
        return f"""
        You are a judge that evaluates the correctness of a solution.
        You will be given a solution and a ground truth solution.
        You will need to determine if the solution is correct.
        Answers are in the format of \\boxed{{}}.

        SOLUTION: {input["r1_solution"]}
        GROUND TRUTH SOLUTION: {input["informal_solution"]}
        """

    def parse(self, input, response):
        """Parse the judge's response to extract correctness and reasoning."""
        return {
            **input,
            "judge_correct": response.correct,
            "judge_reasoning": response.reasoning,
        }


math_judge = MathJudge(model_name="gpt-4o")
ds = math_judge(ds)

gold_is_latex = True
verify_func = math_metric(
    gold_extraction_target=(
        LatexExtractionConfig() if gold_is_latex else ExprExtractionConfig(),
    ),
    pred_extraction_target=(ExprExtractionConfig(), LatexExtractionConfig()),
    aggregation_function=max,
    fallback_mode="first_match",
    precision=6,
)


def validate_solution(row):
    extracted_answers = ""
    gold_answers = ""
    grade = 0
    try:
        grade, extracted_answers = verify_func(
            [row["informal_solution"]], [row["r1_solution"]]
        )

        if extracted_answers is None:
            extracted_answers = ""
            gold_answers = ""
        else:
            gold_answers = str(extracted_answers[0])
            extracted_answers = str(extracted_answers[1])

        row["math_verify_extracted_r1_answer"] = extracted_answers
        row["math_verify_extracted_ground_truth_answer"] = gold_answers
        row["math_verify_correct"] = grade == 1
        row["math_verify_error"] = ""

    except Exception as e:
        row["math_verify_extracted_r1_answer"] = ""
        row["math_verify_extracted_ground_truth_answer"] = ""
        row["math_verify_correct"] = False
        row["math_verify_error"] = str(e)

    return row


ds = ds.map(validate_solution, num_proc=os.cpu_count())
ds.push_to_hub("mlfoundations-dev/putnambench_r1")
ds.to_json(os.path.expanduser("~/Downloads/putnambench_r1.jsonl"))

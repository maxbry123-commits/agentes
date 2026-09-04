import re

from bespokelabs import curator
from datasets import load_dataset

dataset = load_dataset(
    "mlfoundations-dev/math_stratos_scale_judged_and_annotated_with_difficulty",
    split="train",
)
dataset = dataset.filter(lambda x: x["correct"] == False and x["difficulty"] >= 9)
print(dataset)
dataset.push_to_hub(
    "mlfoundations-dev/math_stratos_scale_judged_and_annotated_with_difficulty_incorrect_and_hardest"
)


class Reasoner(curator.LLM):
    def prompt(self, input):
        """Create a prompt for the LLM to reason about the problem."""
        return f"Return your final response within \\boxed{{}}. {input['problem']}"

    def parse(self, input, response):
        """Parse the LLM response to extract reasoning and solution.

        The response format is expected to be '<think>reasoning</think>answer'
        """
        full_response = response

        # Extract reasoning and answer using regex
        reasoning_pattern = r"<think>(.*?)</think>"
        reasoning_match = re.search(reasoning_pattern, full_response, re.DOTALL)

        reasoning = reasoning_match.group(1).strip() if reasoning_match else ""
        # Answer is everything after </think>
        answer = re.sub(reasoning_pattern, "", full_response, flags=re.DOTALL).strip()

        input["deepseek_reasoning_2"] = reasoning
        input["deepseek_solution_2"] = answer

        return input


llm = Reasoner(
    model_name="deepseek-ai/DeepSeek-R1",
    backend="klusterai",
    batch=True,
    generation_params={"max_tokens": 40000},
    backend_params={"completion_window": "12h", "batch_size": 5000},
)
output = llm(dataset)
output.push_to_hub(
    "mlfoundations-dev/math_stratos_scale_judged_and_annotated_with_difficulty_incorrect_and_hardest_reannotated"
)

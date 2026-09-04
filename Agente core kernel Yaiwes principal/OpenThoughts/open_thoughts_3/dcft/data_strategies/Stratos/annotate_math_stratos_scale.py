from datasets import load_dataset

from dcft.data_strategies.Stratos.deepseek_reasoner import DeepSeekReasoner
from dcft.data_strategies.Stratos.math_judge import Judge
from dcft.data_strategies.Stratos.prompts import SKY_T1_SYSTEM_PROMPT_FINAL

reasoner = DeepSeekReasoner(
    model_name="deepseek-reasoner",
    generation_params={"temp": 0.0},
    backend_params={
        "max_requests_per_minute": 500,
        "max_tokens_per_minute": 100_000_000,
    },
)
math_dataset = load_dataset("mlfoundations-dev/math_stratos_scale")["train"]

deepseek_result = reasoner(math_dataset)
deepseek_result.push_to_hub("mlfoundations-dev/math_stratos_scale_annotated")

judge = Judge(model_name="gpt-4o-mini")
judge_result = judge(deepseek_result)
judge_result.push_to_hub("mlfoundations-dev/math_stratos_scale_judged_and_annotated")

rejection_sampled = judge_result.filter(lambda x: x["correct"])
rejection_sampled.push_to_hub("mlfoundations-dev/math_stratos_scale_rejection_sampled")


rejection_sampled = load_dataset(
    "mlfoundations-dev/math_stratos_scale_rejection_sampled"
)["train"]

rejection_sampled_share_gpt = rejection_sampled.filter(lambda x: x["correct"])


def map_numina_conversations(x):
    """Map the Numina dataset to the required format."""
    user_message = f"Return your final response within \\boxed{{}}. {x['problem']}"
    assistant_message = f"<|begin_of_thought|>\n\n{x['reasoning']}\n\n<|end_of_thought|>\n\n<|begin_of_solution|>\n\n{x['deepseek_solution']}\n\n<|end_of_solution|>"
    return {
        "system": SKY_T1_SYSTEM_PROMPT_FINAL,
        "conversations": [
            {"from": "user", "value": user_message},
            {"from": "assistant", "value": assistant_message},
        ],
    }


rejection_sampled_share_gpt = rejection_sampled_share_gpt.map(
    map_numina_conversations, num_proc=32
)
rejection_sampled_share_gpt = rejection_sampled_share_gpt.select_columns(
    ["system", "conversations"]
)
rejection_sampled_share_gpt.push_to_hub(
    "mlfoundations-dev/math_stratos_scale_share_gpt"
)

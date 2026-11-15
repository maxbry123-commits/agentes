import os

from datasets import load_dataset

ds = load_dataset("open-r1/OpenR1-Math-Raw", split="train")
ds = ds.add_column("open-r1-idx", range(len(ds)))

print(ds)
"""
Dataset({
    features: ['problem', 'solution', 'answer', 'problem_type', 'question_type', 'problem_is_valid', 'solution_is_valid', 'source', 'synthetic', 'generations', 'generations_count', 'correctness_math_verify', 'correct_count'],
    num_rows: 516499
})
"""
ds = ds.filter(lambda x: x["correct_count"] > 0, num_proc=os.cpu_count())
print(ds)
"""
Dataset({
    features: ['problem', 'solution', 'answer', 'problem_type', 'question_type', 'problem_is_valid', 'solution_is_valid', 'source', 'synthetic', 'generations', 'generations_count', 'correctness_math_verify', 'correct_count'],
    num_rows: 267709
})
"""


# all correct problems
def get_all_correct_generations(x):
    generations = []
    assert (
        len(x["generations"])
        == len(x["correctness_math_verify"])
        == len(x["correct_count"])
    )
    for i in range(len(x["generations"])):
        correct_generations = [
            gen
            for gen, verify in zip(x["generations"][i], x["correctness_math_verify"][i])
            if verify
        ]
        assert len(correct_generations) == x["correct_count"][i]
        generations.extend(correct_generations)
    return {
        "problem": x["problem"] * len(generations),
        "problem_type": x["problem_type"] * len(generations),
        "question_type": x["question_type"] * len(generations),
        "generation": generations,
        "solution": x["solution"] * len(generations),
        "answer": x["answer"] * len(generations),
        "open-r1-idx": x["open-r1-idx"] * len(generations),
    }


all_correct_ds = ds.map(
    get_all_correct_generations,
    batched=True,
    batch_size=1,
    num_proc=os.cpu_count(),
    remove_columns=[
        "correctness_math_verify",
        "correct_count",
        "synthetic",
        "source",
        "generations_count",
        "solution_is_valid",
        "problem_is_valid",
        "generations",
    ],
)
print(all_correct_ds)
# all_correct_ds.push_to_hub("mlfoundations-dev/OpenR1-Math-Raw-all-correct")


def map_to_sharegpt(x):
    x["conversations"] = [
        {"from": "user", "value": x["problem"]},
        {"from": "assistant", "value": x["generation"]},
    ]
    return x


all_correct_ds = all_correct_ds.map(map_to_sharegpt, num_proc=os.cpu_count())
print(all_correct_ds)
all_correct_ds = all_correct_ds.select_columns(["conversations"])
all_correct_ds.push_to_hub("mlfoundations-dev/OpenR1-Math-Raw-all-correct-sharegpt")


def get_first_correct_generation(x):
    generations = []
    correct_generations = [
        gen
        for gen, verify in zip(x["generations"], x["correctness_math_verify"])
        if verify
    ]
    assert len(correct_generations) == x["correct_count"]
    generations.extend(correct_generations)
    first_correct_generation = generations[0]
    return {
        "problem": x["problem"],
        "problem_type": x["problem_type"],
        "question_type": x["question_type"],
        "generation": first_correct_generation,
        "solution": x["solution"],
        "answer": x["answer"],
        "open-r1-idx": x["open-r1-idx"],
    }


first_correct_ds = ds.map(get_first_correct_generation, num_proc=os.cpu_count())
print(first_correct_ds)
# first_correct_ds.push_to_hub("mlfoundations-dev/OpenR1-Math-Raw-first-correct")

first_correct_ds = first_correct_ds.map(map_to_sharegpt, num_proc=os.cpu_count())
first_correct_ds = first_correct_ds.select_columns(["conversations"])
print(first_correct_ds)
first_correct_ds.push_to_hub("mlfoundations-dev/OpenR1-Math-Raw-first-correct-sharegpt")

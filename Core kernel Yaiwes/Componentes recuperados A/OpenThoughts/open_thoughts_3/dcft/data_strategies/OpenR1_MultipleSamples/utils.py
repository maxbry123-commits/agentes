from datasets import load_dataset, Dataset
import os
import copy


# all correct problems
def expand_generation(x):
    generations = []
    correct_generations = [
        gen for gen, verify in zip(x["generations"], x["correctness_math_verify"])
    ]
    generations.extend(correct_generations)
    return {
        "problem": x["problem"],
        "problem_type": x["problem_type"],
        "question_type": x["question_type"],
        "generation": generations,
        "solution": x["solution"],
        "answer": x["answer"],
    }


def apply_expand_generation(dataset: Dataset) -> Dataset:
    dataset = dataset.map(expand_generation)

    all_rows = []
    for row in dataset:
        for generation in row["generation"]:
            new_row = copy.deepcopy(row)
            new_row["generation"] = generation
            all_rows.append(new_row)

    return Dataset.from_list(all_rows)

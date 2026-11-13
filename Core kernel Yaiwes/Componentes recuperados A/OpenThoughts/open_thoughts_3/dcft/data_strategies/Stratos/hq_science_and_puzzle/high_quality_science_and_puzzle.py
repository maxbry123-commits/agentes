import pandas as pd
from datasets import Dataset, concatenate_datasets, load_dataset


def camel_subsample(dataset, domain, num_samples_per_subtopic):
    # Convert to pandas for faster operations
    df = dataset.to_pandas()

    # Group by subtopic and sample
    sampled_dfs = []
    for subtopic in df["sub_topic"].unique():
        subtopic_sample = df[df["sub_topic"] == subtopic].sample(
            n=num_samples_per_subtopic, random_state=42
        )
        sampled_dfs.append(subtopic_sample)

    # Combine all samples
    result_df = pd.concat(sampled_dfs)
    result_df["domain"] = domain

    # Convert back to HuggingFace dataset
    return Dataset.from_pandas(result_df)


##### CREATE THE SCALED DATASET #####
# For conversions and re-uploads to mlfoundations-dev hub:
# python science_and_puzzle_investigate.py
# python camel_load_fast.py

if __name__ == "__main__":
    camel_physics = load_dataset("mlfoundations-dev/camel-ai-physics", split="train")
    camel_biology = load_dataset("mlfoundations-dev/camel-ai-biology", split="train")
    camel_chemistry = load_dataset(
        "mlfoundations-dev/camel-ai-chemistry", split="train"
    )
    riddle_sense = load_dataset(
        "mlfoundations-dev/riddle_sense_converted", split="train"
    )

    puzzle_scaled = riddle_sense.shuffle(seed=42).take(1_250)
    puzzle_scaled = puzzle_scaled.remove_columns(["answerKey"])
    puzzle_scaled = puzzle_scaled.add_column("domain", ["puzzle"] * len(puzzle_scaled))

    biology_scaled = camel_subsample(camel_biology, "biology", 2)
    physics_scaled = camel_subsample(camel_physics, "physics", 2)
    chemistry_scaled = camel_subsample(camel_chemistry, "chemistry", 2)
    science_scaled = concatenate_datasets(
        [biology_scaled, physics_scaled, chemistry_scaled]
    )
    science_scaled = science_scaled.rename_column("message_1", "question")
    science_scaled = science_scaled.rename_column("topic;", "topic")
    science_scaled = science_scaled.select_columns(
        ["question", "domain", "topic", "sub_topic"]
    )

    science_and_puzzle_stratos_scaled = concatenate_datasets(
        [science_scaled, puzzle_scaled]
    )
    science_and_puzzle_stratos_scaled.push_to_hub(
        "mlfoundations-dev/science_and_puzzle_stratos_scale_pre_decontamination"
    )

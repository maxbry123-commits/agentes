from datasets import Dataset

DCFT_V1_2_SOURCES_TO_SHARD_MAPPING = {
    "unnatural_instructions": "unnatural_instructions_gpt-4o-mini::convert_to_sharegpt",
    "camel_chemistry": "camel_chemistry_gpt-4o-mini::convert_to_sharegpt",
    "slim_orca": "slim-orca_gpt-4o-mini::subsample",
    "camel_biology": "camel_biology_gpt-4o-mini::convert_to_sharegpt",
    "airoboros": "oh-dcft-v1.2_no-curation_gpt-4o-mini::airoboros_drop_shard_id",
    "evol_instruct": "evol_instruct_gpt-4o-mini::to_sharegpt",
    "metamath": "metamath_gpt-4o-mini::convert_instruction_response_to_sharegpt",
    "alpaca": "alpaca_gpt-4o-mini::convert_alpaca_to_sharegpt",
    "opengpt": "opengpt_gpt-4o-mini::convert_alpaca_to_sharegpt",
    "camel_math": "camel_math_gpt-4o-mini::convert_to_sharegpt",
}


def keep_source_oh_dcft_v1_2(
    dataset: Dataset, source_to_keep: str, column_name: str
) -> Dataset:
    """
    Keeps only the rows where the source_label_exact contains the source_to_keep string.
    """
    assert column_name in dataset.column_names
    assert source_to_keep in DCFT_V1_2_SOURCES_TO_SHARD_MAPPING

    return dataset.filter(
        lambda x: DCFT_V1_2_SOURCES_TO_SHARD_MAPPING[source_to_keep] == x[column_name]
    )


def remove_source(dataset: Dataset, source_to_remove: str, column_name: str):
    """
    Removes the rows where the source_label_exact contains the source_to_remove string.
    """
    assert (
        source_to_remove in DCFT_V1_2_SOURCES_TO_SHARD_MAPPING
    ), f"OH source not recognized: {source_to_remove}"
    return dataset.filter(
        lambda x: DCFT_V1_2_SOURCES_TO_SHARD_MAPPING[source_to_remove] != x[column_name]
    )


def filter_away_sources(
    dataset_with_sources: Dataset, actual_dataset: Dataset, source_to_remove: str
) -> Dataset:
    instruction_to_source_mapping = {}
    for row in dataset_with_sources:
        if row["conversations"][0]["from"] == "human":
            instruction_to_source_mapping[row["conversations"][0]["value"]] = row[
                "source_label_exact"
            ]
        else:
            instruction_to_source_mapping[row["conversations"][1]["value"]] = row[
                "source_label_exact"
            ]

    all_examples = []
    num_missing = 0
    for i in range(len(actual_dataset)):
        if actual_dataset[i]["conversations"][0]["from"] == "human":
            if (
                actual_dataset[i]["conversations"][0]["value"]
                in instruction_to_source_mapping
            ):
                source_label = instruction_to_source_mapping[
                    actual_dataset[i]["conversations"][0]["value"]
                ]
                if source_to_remove not in source_label:
                    all_examples.append(
                        {
                            "conversations": actual_dataset[i]["conversations"],
                            "source_label_exact": source_label,
                        }
                    )
            else:
                num_missing += 1
        else:
            if (
                actual_dataset[i]["conversations"][1]["value"]
                in instruction_to_source_mapping
            ):
                source_label = instruction_to_source_mapping[
                    actual_dataset[i]["conversations"][1]["value"]
                ]
                if source_to_remove not in source_label:
                    all_examples.append(
                        {
                            "conversations": actual_dataset[i]["conversations"],
                            "source_label_exact": source_label,
                        }
                    )
            else:
                num_missing += 1
    print(f"Num Missing: {num_missing}")
    actual_dataset = Dataset.from_list(all_examples)
    return actual_dataset


def filter_null_sources(dataset: Dataset) -> Dataset:
    """
    Filters out all rows in Original OH where exact_match_on_instruction_response == False.
    """
    all_examples = []
    for i in range(len(dataset)):
        if len(dataset[i]["source_label_exact"]) == 0:
            continue
        all_examples.append(
            {
                "conversations": dataset[i]["conversations"],
                "source_label_exact": dataset[i]["source_label_exact"],
            }
        )
    actual_dataset = Dataset.from_list(all_examples)
    return actual_dataset


def keep_sources(
    dataset_with_sources: Dataset, actual_dataset: Dataset, sources_to_keep
) -> Dataset:
    """
    Similar to filter_away_sources but instead provide list of sources to keep
    """
    instruction_to_source_mapping = {}
    for row in dataset_with_sources:
        if row["conversations"][0]["from"] == "human":
            instruction_to_source_mapping[row["conversations"][0]["value"]] = row[
                "source_label_exact"
            ]
        else:
            instruction_to_source_mapping[row["conversations"][1]["value"]] = row[
                "source_label_exact"
            ]

    all_examples = []
    num_missing = 0
    for i in range(len(actual_dataset)):
        if (
            actual_dataset[i]["conversations"][0]["value"]
            in instruction_to_source_mapping
        ):
            source_label = instruction_to_source_mapping[
                actual_dataset[i]["conversations"][0]["value"]
            ]
            is_overlap = False
            for s in sources_to_keep:
                if s in source_label:
                    is_overlap = True
            if is_overlap:
                all_examples.append(
                    {
                        "conversations": actual_dataset[i]["conversations"],
                        "source_label_exact": source_label,
                    }
                )
        elif (
            actual_dataset[i]["conversations"][1]["value"]
            in instruction_to_source_mapping
        ):
            source_label = instruction_to_source_mapping[
                actual_dataset[i]["conversations"][1]["value"]
            ]
            is_overlap = False
            for s in sources_to_keep:
                if s in source_label:
                    is_overlap = True
            if is_overlap:
                all_examples.append(
                    {
                        "conversations": actual_dataset[i]["conversations"],
                        "source_label_exact": source_label,
                    }
                )
        else:
            num_missing += 1
    print(f"Num Missing: {num_missing}")
    actual_dataset = Dataset.from_list(all_examples)
    return actual_dataset


if __name__ == "__main__":
    print(DCFT_V1_2_SOURCES_TO_SHARD_MAPPING)

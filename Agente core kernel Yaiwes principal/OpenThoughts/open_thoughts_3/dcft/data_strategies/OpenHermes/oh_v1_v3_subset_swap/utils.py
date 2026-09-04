from collections import defaultdict

from datasets import Dataset, concatenate_datasets, load_dataset

BATCH_SIZE = 1000


V1_CHOI_LABELS_TO_SOURCE = {
    "mlfoundations-dev/alpaca_threshold90_it": "CoT Alpaca",
    "mlfoundations-dev/camel_biology_gpt-4o-mini": "CamelAI Biology",
    "mlfoundations-dev/opengpt": "CogStackMed",
    "mlfoundations-dev/camel_chemistry_gpt-4o-mini": "CamelAI Chemistry",
    "mlfoundations-dev/unnatural_instructions": "Unnatural Instructions",
    "mlfoundations-dev/camel_math_gpt-4o-mini": "CamelAI Math",
    "mlfoundations-dev/evol_instruct": "Evol Instruct 70K",
    "mlfoundations-dev/slim-orca-500k": "SlimOrca 550K",
    "mlfoundations-dev/metamath": "MetaMath 40k",
}


def filter_away_overlapping_v3_instructions(
    v3_dataset: Dataset,
    v1_dataset: Dataset,
    dataset_with_sources: Dataset,
    source_to_swap: str,
) -> Dataset:
    # Setup
    v3_dataset_source_name = V1_CHOI_LABELS_TO_SOURCE[source_to_swap]
    if "__" in source_to_swap:
        source_to_swap, variant = source_to_swap.split("__")
        print(
            f'SUBSTITUTING "{source_to_swap}" FROM V1 WITH "{v3_dataset_source_name}" FROM V3.'
        )
    else:
        print(
            f'SUBSTITUTING "{source_to_swap}" FROM V1 WITH "{v3_dataset_source_name}" FROM V3.'
        )

    # Iterate through the v1 dataset and get rid of all the instructions that match the source to swap
    v1_dataset_length = len(v1_dataset)
    v1_without_source_to_swap = v1_dataset.filter(
        lambda x: x["source"] != source_to_swap,
        desc=f"Filtering v1 dataset for {source_to_swap}",
    )
    v1_without_source_to_swap_length = len(v1_without_source_to_swap)

    # Iterate through dataset_with_sources and add all the instructions that match the value of the labels_to_source mapping
    source_instructions_from_oh25 = []
    sanity_check_instructions_oh25 = []
    instructions_to_source_labels = defaultdict(list)

    def process_dataset_with_sources(batch):
        column_name = (
            "source_label_exact"
            if v3_dataset_source_name != "CogStackMed"
            else "source"
        )
        for i, source_labels in enumerate(batch[column_name]):
            if source_labels is not None and v3_dataset_source_name in source_labels:
                if batch["conversations"][i][0]["from"] == "human":
                    source_instructions_from_oh25.append(
                        batch["conversations"][i][0]["value"]
                    )
                    sanity_check_instructions_oh25.append(
                        {
                            "conversations": batch["conversations"][i],
                            "source_label_exact": source_labels,
                        }
                    )
                    instructions_to_source_labels[
                        batch["conversations"][i][0]["value"]
                    ].append(source_labels)
                else:
                    source_instructions_from_oh25.append(
                        batch["conversations"][i][1]["value"]
                    )
                    sanity_check_instructions_oh25.append(
                        {
                            "conversations": batch["conversations"][i],
                            "source_label_exact": source_labels,
                        }
                    )
                    instructions_to_source_labels[
                        batch["conversations"][i][1]["value"]
                    ].append(source_labels)

    dataset_with_sources.map(
        process_dataset_with_sources,
        batched=True,
        batch_size=BATCH_SIZE,
        desc="Getting source instructions from OH2.5 dataset",
    )
    # Remove duplicates. This is fine because we only care about the instruction, not the rest of the conversation
    source_instructions_from_oh25 = set(source_instructions_from_oh25)

    # Sanity check
    instructions_to_source_labels_sanity_check = defaultdict(list)

    def process_dataset_with_sources_sanity_check(batch):
        for i, conversation in enumerate(batch["conversations"]):
            if conversation[0]["from"] == "human":
                if conversation[0]["value"] in source_instructions_from_oh25:
                    instructions_to_source_labels_sanity_check[
                        conversation[0]["value"]
                    ].append(batch["source_label_exact"][i])
            else:
                if conversation[1]["value"] in source_instructions_from_oh25:
                    instructions_to_source_labels_sanity_check[
                        conversation[1]["value"]
                    ].append(batch["source_label_exact"][i])

    dataset_with_sources.map(
        process_dataset_with_sources_sanity_check,
        batched=True,
        batch_size=BATCH_SIZE,
        desc="Sanity checking source instructions from OH2.5 dataset",
    )

    # Iterate through the v3 dataset and add all the instructions we want from source_instructions_from_v3
    v3_instructions_to_add = []
    instruction_freq_dict = {}

    def process_v3_dataset(batch):
        for i, conversation in enumerate(batch["conversations"]):
            if conversation[0]["from"] == "human":
                if conversation[0]["value"] in source_instructions_from_oh25:
                    v3_instructions_to_add.append(
                        {"sample": conversation, "source": v3_dataset_source_name}
                    )
                    instruction_freq_dict[conversation[0]["value"]] = (
                        instruction_freq_dict.get(conversation[0]["value"], 0) + 1
                    )
            else:
                if conversation[1]["value"] in source_instructions_from_oh25:
                    v3_instructions_to_add.append(
                        {"sample": conversation, "source": v3_dataset_source_name}
                    )
                    instruction_freq_dict[conversation[1]["value"]] = (
                        instruction_freq_dict.get(conversation[1]["value"], 0) + 1
                    )

    v3_dataset.map(
        process_v3_dataset,
        batched=True,
        batch_size=BATCH_SIZE,
        desc="Filtering v3 dataset for source instructions",
    )

    # Sanity check
    for instruction, instruction_freq in instruction_freq_dict.items():
        num_sources = len(instructions_to_source_labels_sanity_check[instruction])
        assert (
            num_sources == instruction_freq
        ), f"Instruction {instruction} has {num_sources} sources but {instruction_freq} frequency with source labels {instructions_to_source_labels_sanity_check[instruction]}"

    # combine the v1 dataset without the source to swap with the v3 instructions to add
    v3_instructions_to_add = Dataset.from_list(v3_instructions_to_add)
    final_dataset = concatenate_datasets(
        [v1_without_source_to_swap, v3_instructions_to_add]
    )
    final_dataset_length = len(final_dataset)

    print("===========================================")
    print(f"SUMMARY")
    print("===========================================")
    print(f"V1 DATASET LENGTH: {v1_dataset_length}")
    print(
        f"INSTRUCTIONS REMOVED FROM V1: {v1_dataset_length - v1_without_source_to_swap_length}"
    )
    print(f"INSTRUCTIONS FOUND IN OH2.5: {len(source_instructions_from_oh25)}")
    print(f"INSTRUCTIONS TO ADD FROM V3: {len(v3_instructions_to_add)}")
    print(f"FINAL DATASET LENGTH: {final_dataset_length}")
    print("===========================================")

    assert final_dataset_length == v1_dataset_length - (
        v1_dataset_length - v1_without_source_to_swap_length
    ) + len(v3_instructions_to_add)

    return final_dataset


if __name__ == "__main__":
    ohv1 = load_dataset(
        "mlfoundations-dev/oh-dcft-v1-no-curation-sharegpt-format", split="train"
    )
    ohv3 = load_dataset("mlfoundations-dev/oh-dcft-v3-sharegpt-format", split="train")
    choi = load_dataset("cchoi1/oh_with_sources", split="train")
    for source in V1_CHOI_LABELS_TO_SOURCE.keys():
        filter_away_overlapping_v3_instructions(ohv3, ohv1, choi, source)

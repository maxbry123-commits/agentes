import json
import os
import re
import zipfile
from typing import Any, Dict, List, Set, Tuple

import wget
from datasets import Dataset, load_dataset
from tqdm import tqdm

from dcft.data_strategies.OpenHermes.data_curation.source_dataset_info import (
    SOURCE_DATASET_INFO,
)

# https://huggingface.co/docs/datasets/en/package_reference/utilities#datasets.enable_progress_bars
# Use these to make it more readable
# from datasets import disable_progress_bars
# disable_progress_bars()
"""
Expected output:
OpenHermes 2.5 Statistics:
Total examples: 1,001,551
Examples without source: 504,808

Dataset Overlap Analysis
-------------------------------------------------------------------------------------
Dataset Name                      Prompts    No-Source Overlap        Total Overlap
-------------------------------------------------------------------------------------
Airoboros 2.2                      44,838               30,665               30,665
CamelAI Biology                    20,000               13,285               13,285
CamelAI Chemistry                  20,000               17,419               17,419
CamelAI Math                       50,000               46,539               46,539
CamelAI Physics                    20,000                    0                    0
Chatbot Arena                      33,000                2,838                2,840
lmsys-1m                        1,000,000                3,440                3,454
Collective Cognition                  156                    1                   50
Evol Instruct 70K                  70,000               54,367               54,367
Evol Instruct 140K                143,000               54,367               94,288
Glaive Code Assistant              136,109              125,593              125,593
GPT4-LLM                           54,568               24,895               24,895
GPTeacher                          89,260                    6                6,793
MetaMath 40k                      395,000               10,961               10,961
SlimOrca 550K                     517,982                    0              398,156
Platypus                           24,926               16,646               16,646
ShareGPT                           92,837                   45                1,473
CogStack                            4,689                4,409                4,409
CoT Alpaca                         46,801               23,574               23,575
Unnatural Instructions             66,010                    1                    1
caseus_custom                       2,688                2,525                2,525
dataforge_economics                   880                  656                  656
-------------------------------------------------------------------------------------
"""

NUM_PROC = os.cpu_count()


# https://github.com/huggingface/datasets/issues/2644
def extract_prompts(
    dataset: Dataset,
    convo_key: str = "conversations",
    message_key: str = "value",
    from_key: str = "from",
    human_value: str = "human",
    save_source: bool = True,
) -> Dataset:
    """Extract human prompts from a conversation dataset.

    Args:
        dataset: Input dataset containing conversations
        convo_key: Key for accessing conversation list in dataset
        message_key: Key for accessing message content
        from_key: Key for identifying message sender
        human_value: Value indicating human messages
        save_source: Whether to include source information in output

    Returns:
        Dataset containing extracted prompts
    """

    def extract_map(row):
        conversation = row[convo_key]
        # Extract first message from human
        for message in conversation:
            if message[from_key] == human_value:
                if save_source:
                    return {"prompt": message[message_key], "source": row["source"]}
                else:
                    return {"prompt": message[message_key]}
        return {"prompt": None}

    ds = dataset.map(extract_map, num_proc=NUM_PROC)
    return ds.filter(lambda x: x["prompt"], num_proc=NUM_PROC)


def extract_prompts_cogstack(dataset: Dataset, text_key: str = "text") -> List[str]:
    """Extract user prompts from CogStack dataset format.

    Args:
        dataset: Input CogStack dataset
        text_key: Key for accessing text content

    Returns:
        List of extracted user prompts
    """
    questions = []
    user_pattern = re.compile(r"<\|user\|>(.*?)<\|eos\|>", re.DOTALL)
    for text in tqdm(dataset[text_key]):
        matches = user_pattern.findall(text)
        if matches:
            questions.extend([match.strip() for match in matches])
    return questions


def extract_prompts_unnatural(
    dataset: Dataset, text_key: str = "instances"
) -> List[str]:
    """Extract prompts from Unnatural Instructions dataset.

    Args:
        dataset: Input Unnatural Instructions dataset
        text_key: Key for accessing instances

    Returns:
        List of extracted instructions with input
    """
    questions = []
    for text in tqdm(dataset[text_key]):
        questions.extend(text["instruction_with_input"])
    return questions


def check_overlap(
    source_questions: List[str], source_prompts: List[str]
) -> Tuple[Set[str], Set[str]]:
    """Check overlap between two sets of questions/prompts.

    Args:
        source_questions: First list of questions
        source_prompts: Second list of prompts

    Returns:
        Tuple containing:
            - Set of overlapping questions
            - Set of questions from source_questions not in source_prompts
    """
    overlap = set(source_questions) & set(source_prompts)
    still_missing = set(source_questions) - set(source_prompts)
    return overlap, still_missing


def load_camel_ai(subject: str, directory: str) -> Dataset:
    """Load CamelAI dataset for a specific subject.

    Args:
        subject: Subject area ('biology', 'chemistry', 'math', or 'physics')
        directory: Directory to store/load dataset files

    Returns:
        Dataset containing CamelAI examples
    """
    directory = os.path.join(directory, subject)
    os.makedirs(directory, exist_ok=True)

    urls = {
        "biology": "https://huggingface.co/datasets/camel-ai/biology/resolve/main/biology.zip?download=true",
        "chemistry": "https://huggingface.co/datasets/camel-ai/chemistry/resolve/main/chemistry.zip?download=true",
        "math": "https://huggingface.co/datasets/camel-ai/math/resolve/main/math.zip?download=true",
        "physics": "https://huggingface.co/datasets/camel-ai/physics/resolve/main/physics.zip?download=true",
    }

    url = urls[subject]
    zip_filename = url.split("/")[-1].split("?")[0]
    subject = zip_filename.split(".")[0]
    zip_filepath = os.path.join(directory, zip_filename)

    # Check if directory already has json files
    if not any(f.endswith(".json") for f in os.listdir(directory)):
        wget.download(url, zip_filepath, bar=None)
        with zipfile.ZipFile(zip_filepath, "r") as zip_ref:
            zip_ref.extractall(directory)
        os.remove(zip_filepath)

    dataset = load_jsons_sequential(directory)

    return dataset


def load_json(file_path: str) -> Dict[str, Any]:
    """Load JSON file into dictionary.

    Args:
        file_path: Path to JSON file

    Returns:
        Dictionary containing JSON data
    """
    with open(file_path, "r") as f:
        return json.load(f)


def process_file(file_name: str, directory: str) -> Dict[str, Any]:
    """Process a single JSON file from directory.

    Args:
        file_name: Name of JSON file
        directory: Directory containing the file

    Returns:
        Dictionary containing JSON data
    """
    file_path = os.path.join(directory, file_name)
    return load_json(file_path)


def load_jsons_sequential(directory: str) -> Dataset:
    """Load multiple JSON files from directory into dataset.

    Args:
        directory: Directory containing JSON files

    Returns:
        Dataset containing combined JSON data
    """
    data = []
    json_files = [f for f in os.listdir(directory) if f.endswith(".json")]

    for file_name in json_files:
        file_path = os.path.join(directory, file_name)
        with open(file_path, "r") as f:
            data.append(json.load(f))

    # Create a Dataset object
    dataset = Dataset.from_list(data)

    return dataset


def load_cogstack(directory: str, dataset_dict: Dict[str, Any]) -> Dataset:
    """Load CogStack dataset from CSV.

    Args:
        directory: Directory to store/load dataset files
        dataset_dict: Dictionary containing dataset information

    Returns:
        Loaded CogStack dataset
    """
    os.makedirs(directory, exist_ok=True)
    # Check if directory already has csv files
    download_filepath = os.path.join(directory, "prepared_generated_data.csv")
    if not os.path.exists(download_filepath):
        wget.download(dataset_dict["url"], download_filepath, bar=None)
    data_files = [download_filepath]
    dataset = load_dataset("csv", data_files=data_files, delimiter=",", split="train")
    return dataset


def load_source_prompts(dataset_name: str, add_source: bool = True) -> Dataset:
    """Load prompts from a source dataset.

    Args:
        dataset_name: Name of the dataset to load
        add_source: Whether to add source column to output dataset

    Returns:
        Dataset containing prompts (and optionally source information)
    """
    dataset_dict = SOURCE_DATASET_INFO[dataset_name]
    if dataset_name == "ShareGPT":
        dataset = load_dataset(
            dataset_dict["path"], data_files=dataset_dict["data_files"], split="train"
        )
    elif dataset_name == "CamelAI Biology":
        dataset = load_camel_ai("biology", "./datasets/camel-ai/")
    elif dataset_name == "CamelAI Chemistry":
        dataset = load_camel_ai("chemistry", "./datasets/camel-ai/")
    elif dataset_name == "CamelAI Math":
        dataset = load_camel_ai("math", "./datasets/camel-ai/")
    elif dataset_name == "CamelAI Physics":
        dataset = load_camel_ai("physics", "./datasets/camel-ai/")
    elif dataset_name == "CogStack":
        dataset = load_cogstack("./datasets/cogstack/", dataset_dict)
    else:
        dataset = load_dataset(dataset_dict["path"], split="train")

    if dataset_name == "CogStack":
        source_prompts = extract_prompts_cogstack(dataset=dataset)
    elif dataset_name == "Unnnatural Instructions":
        source_prompts = extract_prompts_unnatural(dataset=dataset)
    elif "question" in dataset.column_names:
        source_prompts = dataset["question"]
    elif "original_question" in dataset.column_names:
        source_prompts = dataset["original_question"]
    elif "instruction" in dataset.column_names:
        source_prompts = dataset["instruction"]
    elif "message_1" in dataset.column_names:
        source_prompts = dataset["message_1"]
    else:
        source_prompts = extract_prompts(
            dataset=dataset,
            convo_key=dataset_dict["convo_key"],
            message_key=dataset_dict["message_key"],
            from_key=dataset_dict["from_key"],
            human_value=dataset_dict["human_value"],
            save_source=False,
        )
        source_prompts = source_prompts["prompt"]

    if add_source:
        source_prompts = Dataset.from_dict({"prompt": source_prompts})
        source_prompts = source_prompts.add_column(
            "source", [dataset_name] * len(source_prompts)
        )

    return source_prompts


if __name__ == "__main__":
    openhermes = load_dataset("teknium/OpenHermes-2.5", split="train")
    openhermes_prompts_dataset = extract_prompts(openhermes)
    openhermes_prompts = list(openhermes_prompts_dataset["prompt"])
    print(f"\nOpenHermes 2.5 Statistics:")
    print(f"Total examples: {len(openhermes_prompts):,}")
    openhermes_no_source_prompts_dataset = openhermes_prompts_dataset.filter(
        lambda x: x["source"], num_proc=NUM_PROC
    )
    openhermes_no_source_prompts = list(openhermes_no_source_prompts_dataset["prompt"])
    print(f"Examples without source: {len(openhermes_no_source_prompts):,}\n")

    # Print header
    print("Dataset Overlap Analysis")
    print("-" * 85)
    print(
        f"{'Dataset Name':<20} {'Prompts':>20} {'No-Source Overlap':>20} {'Total Overlap':>20}"
    )
    print("-" * 85)

    for dataset_name in SOURCE_DATASET_INFO.keys():
        source_prompts = load_source_prompts(dataset_name, add_source=False)
        no_source_overlap, _ = check_overlap(
            openhermes_no_source_prompts, source_prompts
        )
        all_overlap, _ = check_overlap(openhermes_prompts, source_prompts)

        # Print formatted row
        print(
            f"{dataset_name:<20} {len(source_prompts):>20,} {len(no_source_overlap):>20,} {len(all_overlap):>20,}"
        )

    print("-" * 85)

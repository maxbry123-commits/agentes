import json
import re
from typing import Dict, List, Optional

from datasets import load_dataset
from load import load_jsons_sequential
from source_dataset_info import SOURCE_DATASET_INFO
from tqdm import tqdm


class SourceDatasetExample:
    """
    Represents an example from the source dataset with instruction, response, index, and source name.

    Attributes:
        instruction (str): The instruction text from the dataset.
        response (str): The response or answer corresponding to the instruction.
        index_in_source (int): The index of the example in the source dataset.
        source_name (str): The name of the source dataset.
    """

    def __init__(
        self, instruction: str, response: str, index_in_source: int, source_name: str
    ):
        self.instruction = instruction
        self.response = response
        self.index_in_source = index_in_source
        self.source_name = source_name

    def __repr__(self) -> str:
        """
        Returns a string representation of the SourceDatasetExample object.

        Returns:
            str: String representation of the object.
        """
        return (
            f"SourceDatasetExample(instruction='{self.instruction}', "
            f"response='{self.response}', index_in_source={self.index_in_source}, "
            f"source_name='{self.source_name}')"
        )


def extract_source_dataset_structured(
    dataset: Dict,
    source_name: str,
    convo_key: str = "conversations",
    message_key: str = "value",
    from_key: str = "from",
    human_value: str = "human",
    bot_value: str = "gpt",
) -> List[SourceDatasetExample]:
    """
    Extracts structured datasets with conversation-style examples and organizes them into SourceDatasetExample objects.

    Args:
        dataset (Dict): The dataset containing conversation-style examples.
        source_name (str): The name of the source dataset.
        convo_key (str, optional): Key to access the conversation data. Defaults to "conversations".
        message_key (str, optional): Key to access the message text within the conversation. Defaults to "value".
        from_key (str, optional): Key to identify who sent the message (e.g., human or bot). Defaults to "from".
        human_value (str, optional): Value indicating the human speaker. Defaults to "human".
        bot_value (str, optional): Value indicating the bot speaker. Defaults to "gpt".

    Returns:
        List[SourceDatasetExample]: A list of structured SourceDatasetExample objects containing instructions and responses.
    """
    source_dataset = []
    for i, convo in tqdm(
        enumerate(dataset[convo_key]),
        total=len(dataset[convo_key]),
        desc="Extracting source dataset",
    ):
        instruction = None
        response = None
        if isinstance(convo, str):
            instruction = dataset[convo_key]
            response = dataset[message_key]
        else:
            for message in convo:
                if message[from_key] == human_value:
                    instruction = message[message_key]
                elif message[from_key] == bot_value:
                    response = message[message_key]
                if instruction is not None and response is not None:
                    break
        if instruction and response:
            if isinstance(instruction, list):
                breakpoint()
            source_dataset.append(
                SourceDatasetExample(
                    instruction=instruction.strip(),
                    response=response.strip(),
                    index_in_source=i,
                    source_name=source_name,
                )
            )
    return source_dataset


def extract_source_dataset_main(
    dataset: Dict,
    source_name: str,
    instruction_key: str,
    response_key: str,
    conversation_key: str = "conversations",
) -> List[SourceDatasetExample]:
    """
    Extracts source dataset examples from datasets that have explicit instruction and response keys.

    Args:
        dataset (Dict): The dataset containing explicit instruction and response keys.
        source_name (str): The name of the source dataset.
        instruction_key (str): Key to access the instruction data in the dataset.
        response_key (str): Key to access the response data in the dataset.
        conversation_key (str, optional): Key for the conversation if applicable. Defaults to 'conversations'.

    Returns:
        List[SourceDatasetExample]: A list of SourceDatasetExample objects containing instructions and responses.
    """
    source_dataset = []
    for source_index, (instruction, response) in tqdm(
        enumerate(zip(dataset[instruction_key], dataset[response_key])),
        desc="Extracting source dataset",
    ):
        source_dataset.append(
            SourceDatasetExample(
                instruction=instruction.strip(),
                response=response.strip(),
                index_in_source=source_index,
                source_name=source_name,
            )
        )
    return source_dataset


def extract_source_dataset_cogstack(
    dataset: Dict, source_name: str, text_key: str = "text"
) -> List[SourceDatasetExample]:
    """
    Extracts source dataset examples for datasets formatted like CogStack, where user and AI patterns are embedded in text.

    Args:
        dataset (Dict): The dataset containing textual data with user and AI patterns.
        source_name (str): The name of the source dataset.
        text_key (str, optional): Key to access the text data in the dataset. Defaults to "text".

    Returns:
        List[SourceDatasetExample]: A list of SourceDatasetExample objects containing instructions and responses.
    """
    source_dataset = []
    user_pattern = re.compile(r"<\|user\|>(.*?)<\|eos\|>", re.DOTALL)
    ai_pattern = re.compile(r"<\|ai\|>(.*?)<\|eos\|>", re.DOTALL)

    for i, text in tqdm(
        enumerate(dataset[text_key]),
        total=len(dataset[text_key]),
        desc="Extracting source dataset",
    ):
        user_match = user_pattern.findall(text)
        ai_match = ai_pattern.findall(text)
        if user_match and ai_match:
            instruction = user_match[0].strip()
            response = ai_match[0].strip()
            source_dataset.append(
                SourceDatasetExample(
                    instruction=instruction,
                    response=response,
                    index_in_source=i,
                    source_name=source_name,
                )
            )
    return source_dataset


def extract_source_dataset_unnatural(
    dataset: Dict, source_name: str, text_key: str = "instances"
) -> List[SourceDatasetExample]:
    """
    Extracts source dataset examples for datasets formatted like Unnatural Instructions, which contains instances of instructions and outputs.

    Args:
        dataset (Dict): The dataset containing instruction and output instances.
        source_name (str): The name of the source dataset.
        text_key (str, optional): Key to access the instances in the dataset. Defaults to "instances".

    Returns:
        List[SourceDatasetExample]: A list of SourceDatasetExample objects containing instructions and responses.
    """
    source_dataset = []
    for i, instance in tqdm(
        enumerate(dataset[text_key]),
        total=len(dataset[text_key]),
        desc="Extracting source dataset",
    ):
        instance = instance[0]
        instruction = instance.get("instruction_with_input", "").strip()
        response = instance.get("output", "").strip()
        source_dataset.append(
            SourceDatasetExample(
                instruction=instruction,
                response=response,
                index_in_source=i,
                source_name=source_name,
            )
        )
    return source_dataset


def extract_source_dataset(
    dataset: Dict,
    source_name: str,
    convo_key: str = "conversations",
    message_key: str = "value",
    from_key: str = "from",
    human_value: str = "human",
    bot_value: str = "gpt",
    path: Optional[str] = None,
) -> List[SourceDatasetExample]:
    """
    Determines the appropriate extraction method based on the dataset structure and source name.

    Args:
        dataset (Dict): The dataset to be processed.
        source_name (str): The name of the source dataset.
        convo_key (str, optional): Key to access the conversation data. Defaults to "conversations".
        message_key (str, optional): Key to access the message text within the conversation. Defaults to "value".
        from_key (str, optional): Key to identify the message sender (e.g., human or bot). Defaults to "from".
        human_value (str, optional): Value representing the human speaker. Defaults to "human".
        bot_value (str, optional): Value representing the bot speaker. Defaults to "gpt".
        path (Optional[str], optional): Path to the dataset (if necessary for specific datasets). Defaults to None.

    Returns:
        List[SourceDatasetExample]: A list of SourceDatasetExample objects based on the dataset type.
    """
    if source_name == "CogStack":
        source_dataset = extract_source_dataset_cogstack(dataset, source_name)
    elif source_name == "Unnatural Instructions":
        source_dataset = extract_source_dataset_unnatural(dataset, source_name)
    else:
        if "instruction" in dataset.column_names and "response" in dataset.column_names:
            source_dataset = extract_source_dataset_main(
                dataset, source_name, "instruction", "response"
            )
        elif "instruction" in dataset.column_names and "output" in dataset.column_names:
            source_dataset = extract_source_dataset_main(
                dataset, source_name, "instruction", "output"
            )
        elif "question" in dataset.column_names and "answer" in dataset.column_names:
            source_dataset = extract_source_dataset_main(
                dataset, source_name, "question", "answer"
            )
        elif (
            "original_question" in dataset.column_names
            and "response" in dataset.column_names
        ):
            source_dataset = extract_source_dataset_main(
                dataset, source_name, "original_question", "response"
            )
        elif "input" in dataset.column_names and "output" in dataset.column_names:
            source_dataset = extract_source_dataset_main(
                dataset, source_name, "input", "output"
            )
        elif (
            "message_1" in dataset.column_names and "message_2" in dataset.column_names
        ):
            source_dataset = extract_source_dataset_main(
                dataset, source_name, "message_1", "message_2"
            )
        else:
            source_dataset = extract_source_dataset_structured(
                dataset,
                source_name,
                convo_key,
                message_key,
                from_key,
                human_value,
                bot_value,
            )
    return source_dataset


def create_instruction_response_map(source_datasets: Dict[str, Dict]) -> Dict:
    """
    Creates a map between instruction-response pairs and the datasets they appear in.

    Args:
        source_datasets (Dict[str, Dict]): Dictionary mapping source dataset names to their respective datasets.

    Returns:
        Dict: A dictionary where keys are (instruction, response) tuples and values are lists of source datasets containing those pairs.
    """
    instruction_response_map = {}

    for source_name, dataset in tqdm(
        source_datasets.items(), desc="Processing source datasets"
    ):
        dataset_dict = SOURCE_DATASET_INFO[source_name]
        source_dataset = extract_source_dataset(
            dataset=dataset, source_name=source_name, **dataset_dict
        )

        for example in source_dataset:
            key = (example.instruction, example.response)
            if key not in instruction_response_map:
                instruction_response_map[key] = []
            instruction_response_map[key].append(source_name)

    return instruction_response_map


def process_datasets(SOURCE_DATASET_INFO: Dict) -> Dict:
    """
    Main function that loads each dataset subset, processes its data, and creates the instruction-response map.

    Args:
        SOURCE_DATASET_INFO (Dict): A dictionary containing information about the source datasets to process.

    Returns:
        Dict: The resulting instruction-response map after processing all datasets.
    """
    source_datasets = {}
    for dataset_name, dataset_info in SOURCE_DATASET_INFO.items():
        path = dataset_info["path"]
        print(f"Loading dataset: {dataset_name} from path: {path}")
        if "CamelAI" in dataset_name:
            # Faster loading for CamelAI
            subject = dataset_name.split()[1].lower()
            dataset = load_jsons_sequential(directory="./", subject=subject)
        elif "json" in path:
            dataset = load_dataset("json", data_files=path, split="train")
        elif "csv" in path:
            dataset = load_dataset("csv", data_files=path, split="train")
        else:
            dataset = load_dataset(path, split="train")
        source_datasets[dataset_name] = dataset
    instruction_response_map = create_instruction_response_map(source_datasets)

    return instruction_response_map


if __name__ == "__main__":
    from huggingface_hub import login

    login(token="")

    instruction_response_map = process_datasets(SOURCE_DATASET_INFO)

    output_file_path = "./all_subsets_map.json"
    # with open(output_file_path, "w", encoding="utf-8") as json_file:
    #     json.dump(instruction_response_map, json_file, ensure_ascii=False, indent=4)

    # Before saving to JSON, convert the tuple keys to strings
    instruction_response_map_str = {
        f"{key[0]}|||{key[1]}": value for key, value in instruction_response_map.items()
    }
    with open(output_file_path, "w", encoding="utf-8") as json_file:
        json.dump(instruction_response_map_str, json_file, ensure_ascii=False, indent=4)

    print(f"Instruction-response map saved to {output_file_path}")

import json
import os
import subprocess
import zipfile
from functools import partial
from multiprocessing import Pool

from datasets import Dataset

urls = [
    "https://huggingface.co/datasets/camel-ai/biology/resolve/main/biology.zip?download=true",
    "https://huggingface.co/datasets/camel-ai/chemistry/resolve/main/chemistry.zip?download=true",
    "https://huggingface.co/datasets/camel-ai/math/resolve/main/math.zip?download=true",
    "https://huggingface.co/datasets/camel-ai/physics/resolve/main/physics.zip?download=true",
]

for url in urls:
    zip_filename = url.split("/")[-1].split("?")[0]
    subject = zip_filename.split(".")[0]

    # Check if the folder already exists
    if not os.path.exists(subject):
        # Download the zip file
        subprocess.run(["wget", "-P", ".", url, "-O", zip_filename])

        # Create a subfolder
        os.makedirs(subject, exist_ok=True)

        # Unzip the file into the subfolder
        with zipfile.ZipFile(zip_filename, "r") as zip_ref:
            zip_ref.extractall(subject)

        # Remove the zip file
        os.remove(zip_filename)
    else:
        print(f"Folder {subject} already exists. Skipping download and extraction.")


def load_json(file_path):
    with open(file_path, "r") as f:
        return json.load(f)


def process_file(file_name, directory):
    file_path = os.path.join(directory, file_name)
    return load_json(file_path)


def load_jsons_sequential(directory, subject):
    data = []
    subject_dir = os.path.join(directory, subject)
    json_files = [f for f in os.listdir(subject_dir) if f.endswith(".json")]

    for file_name in json_files:
        file_path = os.path.join(subject_dir, file_name)
        with open(file_path, "r") as f:
            data.append(json.load(f))

    dataset = Dataset.from_list(data)
    return dataset


def load_instruction_response_map(json_file_path, delimiter="|||"):
    """
    Loads a JSON file where the keys are instruction-response pairs stored as strings,
    and converts them back to tuple keys.

    Args:
        json_file_path (str): Path to the JSON file.
        delimiter (str): The delimiter used to join the instruction and response strings.

    Returns:
        dict: A dictionary with (instruction, response) tuple keys and source dataset names as values.
    """
    with open(json_file_path, "r", encoding="utf-8") as json_file:
        instruction_response_map_str = json.load(json_file)

    # Convert the string keys back to tuple keys
    instruction_response_map = {
        tuple(key.split(delimiter)): value
        for key, value in instruction_response_map_str.items()
    }

    return instruction_response_map


if __name__ == "__main__":
    directory = "."
    subjects = ["biology", "chemistry", "math", "physics"]

    for subject in subjects:
        dataset = load_jsons_sequential(directory, subject)
        print(f"{subject.capitalize()} dataset size: {len(dataset)}")
        print(f"{subject.capitalize()} dataset features: {dataset.features}")
        print()  # Add a blank line between subjects for readability

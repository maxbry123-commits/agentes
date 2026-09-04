import json
import os
import subprocess
import zipfile
from functools import partial
from multiprocessing import Pool

from datasets import Dataset


def download_to_directory(directory):
    urls = [
        "https://huggingface.co/datasets/camel-ai/biology/resolve/main/biology.zip?download=true",
        "https://huggingface.co/datasets/camel-ai/chemistry/resolve/main/chemistry.zip?download=true",
        "https://huggingface.co/datasets/camel-ai/math/resolve/main/math.zip?download=true",
        "https://huggingface.co/datasets/camel-ai/physics/resolve/main/physics.zip?download=true",
    ]

    for url in urls:
        zip_filename = url.split("/")[-1].split("?")[0]
        subject_folder = os.path.join(directory, zip_filename.split(".")[0])

        # Check if the folder already exists
        if not os.path.exists(subject_folder):
            # Create a subfolder
            os.makedirs(subject_folder, exist_ok=True)

            # Download the zip file
            subprocess.run(["wget", "-P", ".", url, "-O", zip_filename])

            # Unzip the file into the subfolder
            with zipfile.ZipFile(zip_filename, "r") as zip_ref:
                zip_ref.extractall(subject_folder)

            # Remove the zip file
            os.remove(zip_filename)
        else:
            print(
                f"Folder {subject_folder} already exists. Skipping download and extraction."
            )


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

    # Create a Dataset object
    dataset = Dataset.from_list(data)

    return dataset


if __name__ == "__main__":
    directory = os.path.join(os.path.expanduser("~"), "Downloads")
    subjects = ["biology", "chemistry", "math", "physics"]

    download_to_directory(directory)

    for subject in subjects:
        dataset = load_jsons_sequential(directory, subject)
        print(f"{subject.capitalize()} dataset size: {len(dataset)}")
        print(f"{subject.capitalize()} dataset features: {dataset.features}")
        dataset.push_to_hub(f"mlfoundations-dev/camel-ai-{subject}")
        print()  # Add a blank line between subjects for readability

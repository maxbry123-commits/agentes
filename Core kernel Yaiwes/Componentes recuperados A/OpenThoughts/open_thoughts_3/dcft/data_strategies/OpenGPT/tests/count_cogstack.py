import os
import re

from datasets import Dataset, load_dataset
from datasets.utils.logging import disable_progress_bar
from tqdm import tqdm


def extract_questions(
    dataset,
    convo_key="conversations",
    message_key="value",
    from_key="from",
    human_value="human",
):
    questions = []
    for convo in tqdm(dataset[convo_key]):
        # Extract first message from human
        for message in convo:
            if message[from_key] == human_value:
                questions.append(message[message_key])
                break
    return questions


def extract_questions_cogstack(dataset, text_key="text"):
    questions = []
    user_pattern = re.compile(r"<\|user\|>(.*?)<\|eos\|>", re.DOTALL)
    for text in tqdm(dataset[text_key]):
        matches = user_pattern.findall(text)
        if matches:
            questions.extend([match.strip() for match in matches])
    return questions


def check_overlap(source_questions, target_questions):
    overlap = set(source_questions) & set(target_questions)
    still_missing = set(source_questions) - set(target_questions)
    print(f"num_overlap with OH2.5: {len(overlap):,}")
    return overlap, still_missing


if __name__ == "__main__":
    disable_progress_bar()
    openhermes = load_dataset("teknium/OpenHermes-2.5")
    print(f"Number of examples in OH2.5: {len(openhermes['train']):,}")
    openhermes_questions = extract_questions(
        Dataset.from_pandas(openhermes["train"].to_pandas())
    )

    dataset_dict = {
        "data_dir": "./dcft/external_repositories/OpenGPT/data/",
        "convo_key": "conversations",
        "message_key": "value",
        "from_key": "from",
        "human_value": "human",
    }
    data_files = []
    for root, dirs, files in os.walk(dataset_dict["data_dir"]):
        for f in files:
            if f.endswith(".csv") and "prepared" in f:
                data_files.append(os.path.join(root, f))

    print(f"Looking at each prepared dataset file in {dataset_dict['data_dir']}")

    for f in data_files:
        print(f"Looking at {f}")
        dataset = load_dataset("csv", data_files=f, delimiter=",")["train"]
        print(f"num_examples: {len(dataset):,}")
        target_questions = extract_questions_cogstack(dataset=dataset)
        print(f"num_questions: {len(target_questions):,}")
        overlap, still_missing = check_overlap(openhermes_questions, target_questions)


"""
Expected output

Data files:
./dcft/external_repositories/OpenGPT/data/nhs_uk_full/prepared_generated_data_for_nhs_uk_qa.csv
./dcft/external_repositories/OpenGPT/data/nhs_uk_full/prepared_generated_data_for_nhs_uk_conversations.csv
./dcft/external_repositories/OpenGPT/data/medical_tasks_gpt4/prepared_generated_data_for_medical_tasks.csv
./dcft/external_repositories/OpenGPT/data/example_project_data/prepared_generated_data_for_example_project.csv
Number of examples in dataset CogStack: 32,014
Number of questions in CogStack: 42,085
"""

"""
Number of CogStack in OH2.5 (original labels): 4,443
Number of CogStack in OH2.5 (our matched labels): 4,409
"""

"""
https://aiforhealthcare.substack.com/p/a-large-language-model-for-healthcare
NHS UK Q/A, 24,665 Q/A pairs - A dataset of questions and answers generated via OpenGPT for all conditions found on the NHS UK website.
NHS UK Conversations, 2,354 Conversations - A dataset of conversations between an AI-Assitant and a User, generated via OpenGPT and grounded in the data available on the NHS UK website.
Medical Task/Solution, 4,688 pairs generated via OpenGPT using the GPT-4 model as a teacher.
"""

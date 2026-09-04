# MIT License
# modified from https://github.com/da03/Internalize_CoT_Step_by_Step/blob/main/src/data.py

import re
from datasets import Dataset, DatasetDict

def extract_answer(text):
    split_pattern = "####"
    if split_pattern not in text:
        return text.strip().replace(",", "")
    else:
        _, ans = text.strip().split("####", 1)
        ans = "Answer: " + ans.strip()
        ans = ans.strip().replace(",", "")
        return ans


def extract_cot(text):
    split_pattern = "####"
    if split_pattern not in text:
        return None
    else:
        cot, _ = text.strip().split("####", 1)
        cot = cot.strip()
        return cot

file_paths = [
    ("train", "data/train.txt"),
    ("valid", "data/valid.txt"),
    ("test", "data/test.txt"),
]

data = {
    "train": [],
    "valid": [],
    "test": [],
}

for split, file_path in file_paths:
    with open(file_path, encoding="utf-8") as f:
        lines = [
            line.strip().split("||")
            for line in f.readlines()
            if (
                len(line.strip()) > 0
                and not line.strip().isspace()
                and len(line.strip().split("||")) == 2
            )
        ]
    
    print(split, len(lines))

    for line in lines:
        question, answer_with_steps = line[0], line[1]
        cot_steps = extract_cot(answer_with_steps)
        if cot_steps is None:
            continue
        cot_steps = re.findall(r'<<([^<>]+)>>', cot_steps)
        answer = extract_answer(answer_with_steps)
        data[split].append({
            "question": question,
            "cot": cot_steps,
            "answer": answer,
        })

data = {
    split: Dataset.from_list(split_data) for split, split_data in data.items()
}

dataset_dict = DatasetDict(data)

dataset_dict.push_to_hub("casperhansen/gsm8k_synthetic_cot")

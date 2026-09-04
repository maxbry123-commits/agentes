from datasets import concatenate_datasets, load_dataset

print("##### RUC-AIBOX/long_form_thought_data_5k #####")
long_form_thought_data_5k = load_dataset(
    "RUC-AIBOX/long_form_thought_data_5k", split="train"
)
print(long_form_thought_data_5k)
print(f"total: {len(long_form_thought_data_5k)}")

"""
EXISTING STRATOS / SKYT1 / STILL-2 DATASET
total: 4922
math: 3929
physics: 271
biology: 147
chemistry: 238
puzzle: 159
code: 178
science_and_puzzle: 815
"""

##### INVESTIGATE THE EXISTING DATASET #####
domains = long_form_thought_data_5k.unique("domain")
domain_datasets = {}
for domain in domains:
    domain_data = long_form_thought_data_5k.filter(lambda x: x["domain"] == domain)
    domain_datasets[domain] = domain_data
    print(f"{domain}: {len(domain_data)}")

science_and_puzzle = long_form_thought_data_5k.filter(
    lambda x: x["domain"] in ["puzzle", "physics", "biology", "chemistry"]
)
print()
print(f"science_and_puzzle: {len(science_and_puzzle)}")

physics = domain_datasets["physics"]
camel_physics = load_dataset("mlfoundations-dev/camel-ai-physics", split="train")
# Compare physics datasets
physics_texts = set(physics["question"])
camel_physics_texts = set(camel_physics["message_1"])
physics_overlap = physics_texts.intersection(camel_physics_texts)
print(f"\nPhysics overlap: {len(physics_overlap)} questions")

biology = domain_datasets["biology"]
camel_biology = load_dataset("mlfoundations-dev/camel-ai-biology", split="train")
# Compare biology datasets
biology_texts = set(biology["question"])
camel_biology_texts = set(camel_biology["message_1"])
biology_overlap = biology_texts.intersection(camel_biology_texts)
print(f"Biology overlap: {len(biology_overlap)} questions")

chemistry = domain_datasets["chemistry"]
camel_chemistry = load_dataset("mlfoundations-dev/camel-ai-chemistry", split="train")
# Compare chemistry datasets
chemistry_texts = set(chemistry["question"])
camel_chemistry_texts = set(camel_chemistry["message_1"])
chemistry_overlap = chemistry_texts.intersection(camel_chemistry_texts)
print(f"Chemistry overlap: {len(chemistry_overlap)} questions")


# 'Before getting a divorce, what did the wife feel who was doing all the work?\nA: harder\nB: anguish\nC: bitterness\nD: tears\nE: sadness'
def riddle_sense_map(x):
    question = x["question"]
    stem = question["stem"]
    choices = question["choices"]
    full_question = stem
    for choice in choices:
        full_question += f"\n{choice['label']}: {choice['text']}"
    return {"question": full_question, "answer": x["answerKey"]}


puzzle = domain_datasets["puzzle"]
"""
NOTE:
If you want to, you can fill out the form and download the zip dataset from here https://github.com/INK-USC/RiddleSense 
directory = os.path.join(os.path.expanduser('~'), 'Downloads')
riddle_sense = load_dataset(directory, split="train")
For conveinence, I've already downloaded the dataset and uploaded it to the mlfoundations-dev hub
"""
riddle_sense = load_dataset("mlfoundations-dev/riddle_sense", split="train")
print(riddle_sense)
riddle_sense = riddle_sense.map(riddle_sense_map)
print(riddle_sense[0]["question"])
riddle_sense.remove_columns(["answerKey", "id"])
riddle_sense.push_to_hub("mlfoundations-dev/riddle_sense_converted")

riddle_sense_texts = set(riddle_sense["question"])
puzzle_texts = set(puzzle["question"])
puzzle_overlap = puzzle_texts.intersection(riddle_sense_texts)
print(f"Puzzle overlap: {len(puzzle_overlap)} questions")

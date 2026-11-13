import random

from datasets import Dataset
from tqdm import tqdm

def create_new_prompt(dataset: Dataset, question_column: str) -> Dataset:
    def f(ori_row):
        total_examples = len(dataset)
        num_examples = 5
        selected_indices = random.sample(
            range(total_examples), min(num_examples, total_examples)
        )

        # Create the base prompt

        prompt_template = f"""Help the user to create a new math problem similar that are of similar difficulty to the examples below. 
        Make the new problem reasonable and solvable. 
        Here are some examples of how to complete this task:
        """
        # Format examples
        examples = []
        for idx in selected_indices:
            row = dataset[idx]
            # Assuming the dataset has 'question' and 'answer' fields
            # Modify these field names based on your actual dataset structure
            example = f"Example {idx}:\n"
            example += row[question_column]
            examples.append(example)
            prompt_template += f"\n\n {example}"
        prompt_template += "\n\n Write another problem similar to these examples. Start directly with the problem statement and DO NOT include any phrases such as 'Here is a new problem similar to a given one'. After the problem is generated, finish your response right away."
        row["prompt_for_new_question"] = prompt_template
        return row

    dataset = dataset.map(f)
    return dataset


def create_new_prompt_repeat(dataset: Dataset, question_column: str, n_repeat: int) -> Dataset:
    def f(ori_row):
        total_examples = len(dataset)
        num_examples = 5
        all_rows = []
        for _ in range(n_repeat):
            selected_indices = random.sample(range(total_examples), min(num_examples, total_examples))

            # Create the base prompt

            prompt_template = f"""Help the user to create a new math problem similar that are of similar difficulty to the examples below. 
            Make the new problem reasonable and solvable. 
            Here are some examples of how to complete this task:
            """
            # Format examples
            examples = []
            for idx in selected_indices:
                row = dataset[idx]
                # Assuming the dataset has 'question' and 'answer' fields
                # Modify these field names based on your actual dataset structure
                example = f"Example {idx}:\n"
                example += row[question_column]
                examples.append(example)
                prompt_template += f"\n\n {example}"
            prompt_template += "\n\n Write another problem similar to these examples. Start directly with the problem statement and DO NOT include any phrases such as 'Here is a new problem similar to a given one'. After the problem is generated, finish your response right away."
            all_rows.append(prompt_template)
        row["prompts_for_new_question"] = all_rows
        return row

    dataset = dataset.map(f)
    all_rows = []
    for row in tqdm(dataset):
        for prompt in row["prompts_for_new_question"]:
            new_row = {}
            new_row["prompt_for_new_question"] = prompt
            all_rows.append(new_row)
    dataset = Dataset.from_list(all_rows)
    return dataset

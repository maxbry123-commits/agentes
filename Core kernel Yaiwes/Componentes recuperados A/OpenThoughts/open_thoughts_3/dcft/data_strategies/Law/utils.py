from datasets import Dataset, load_dataset


def format_prompt(row, max_tokens=8192, token_multiplier=5):
    instruction = row["instruction"]
    opinion = row["opinion"]
    question = row["question"]
    choices = row["choices"]
    choices_str = "\n".join([f"{i + 1}: {choice}" for i, choice in enumerate(choices)])

    # shorten opinion if it is too long
    len_rest = (
        len(instruction)
        + len(question)
        + len(choices_str)
        + len("\n\nQuestion: \n\n\n ")
    )
    if len(opinion) + len_rest > max_tokens * token_multiplier:
        opinion = opinion[: int(max_tokens * token_multiplier - len_rest)]

    prompt = f"{instruction}\n\n{opinion}\n\nQuestion: {question}\n{choices_str}"
    return prompt


def verify(row, solution_key="deepseek_solution_formatted", verbose=False):

    choices = row["choices"]
    formatted_choices = [f"{i + 1}: {choice}" for i, choice in enumerate(choices)]
    answer_index = row["answer"][0]
    correct_answer = formatted_choices[answer_index]
    attempt = row[solution_key]
    if verbose:
        print("-----------------------------------------------------------------")
        print("CORRECT: ", correct_answer)
        print("ATTEMPT: ", attempt)
        print("CORRECT ANSWER: ", correct_answer, "\n")
    only_correct = correct_answer in attempt and all(
        choice not in attempt or choice == correct_answer
        for choice in formatted_choices
    )
    # check if any of the formated choices is part of the attempt string

    contains_choices = any(choice in attempt for choice in formatted_choices)

    contains_choices = any(choice in attempt for choice in formatted_choices)

    return {"verify": correct_answer in attempt, "format_correct": contains_choices}


def duplicate_rows(ds, Q):
    """Duplicates each row Q times and returns a new dataset"""
    new_data = {key: [] for key in ds.column_names}  # Initialize new dataset structure

    for row in ds:
        for _ in range(Q):  # Repeat each row Q times
            for key in row:
                new_data[key].append(row[key])  # Append duplicated values

    return Dataset.from_dict(new_data)  # Create new dataset

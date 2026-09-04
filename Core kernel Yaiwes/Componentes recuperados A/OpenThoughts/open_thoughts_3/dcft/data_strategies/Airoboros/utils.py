import logging
import math
import random
import re

from datasets import Dataset

response_regex_filters = [
    re.compile(pattern)
    for pattern in [
        "my programming",
        "openai",
        "language model",
        "large language",
        "as an? (ai|generative language|gpt|bot)",
        "illegal and dangerous",
        "i do(n't| not) (possess|have|exhibit) (personal|consciousness|subjective)",
        "personal (feelings|thoughts|emotions|desires|experiences|goals|objective|belief)",
        "(can('t| ?not)|w(on't|will not)|unable.?) (\\w+\\s)+(with (that|your)|your \\w+|provide)",
        "my limitations",
        "the limitations of my",
        "my abilities",
        "violates my",
        "i (can('t| ?not)|w(on't|will not)|am (not |un)able.?).{0,30}(you are|you're|your )",
        "please note that",
    ]
]

response_prefix_filters = [
    "I'm sorry,",
    "Apologies,",
    "I can't",
    "I won't",
]

logger = logging.getLogger(__name__)


def filter_banned_responses_map(row, response_column):
    text = row[response_column]
    for banned in response_regex_filters:
        if banned.search(text, re.I):
            logger.warning(f"Banned response [{banned}]: {text}")
            return {"filtered_out_banned_response": True}
    for prefix in response_prefix_filters:
        if text.startswith(prefix):
            logger.warning(f"Banned response [prefix]: {text}")
            return {"filtered_out_banned_response": True}
    return {"filtered_out_banned_response": False}


def filter_banned_responses(dataset: Dataset, response_column: str):
    dataset = dataset.map(
        filter_banned_responses_map, fn_kwargs={"response_column": response_column}
    )
    before_filter = len(dataset)
    dataset = dataset.filter(lambda x: not x["filtered_out_banned_response"])
    after_filter = len(dataset)
    logger.info(
        f"Filtered out {before_filter - after_filter} rows with banned responses"
    )
    return dataset.remove_columns(["filtered_out_banned_response"])


def create_topics_strings_dataset(
    dataset: Dataset,
    input_topic_column: str,
    n_topics_per_string: int,
    n_strings: int,
    target_name: str,
    output_topics_str_column: str,
):
    topics = dataset[input_topic_column]
    rows = []
    for _ in range(n_strings):
        sampled_topics = random.sample(topics, n_topics_per_string)
        topics_str = "\n".join(
            [
                f" * {target_name} {idx + 1} must be related to topic: {topic}"
                for idx, topic in enumerate(sampled_topics)
            ]
        )
        row = {output_topics_str_column: topics_str}
        rows.append(row)
    return Dataset.from_list(rows)


def sample_contextual_instructions_args(dataset: Dataset, n_samples: int):
    """
    Do this as a function since there is complex sampling logic.
    """
    # Args used for all samples
    topics = dataset["topic"]
    context_styles = dataset["context_styles"][0]
    formatting_options = dataset["formatting_options"][0]
    batch_size = dataset["batch_size"][0]
    topic_avoidance = dataset["topic_avoidance"][0]
    flesch = dataset["flesch"][0]
    language = dataset["language"][0]
    next_year = dataset["next_year"][0]
    TARGET_OPTIONS = [
        "the first generated text block.",
        "the last generated text block.",
        "all generated text blocks.",
        "one or more of the generated text blocks.",
        "one, randomly selected generated text block.",
    ]
    ASK_FOR_SOURCE = 'Instruct or ask the user to provide a source/references for the information, e.g. "What is your source?", "Please provide references.", "Cite.", "Source?", "[insert references]", "Add a citation.", or other similar variations.'
    TASK_DISPLAY_OPTIONS = [
        "a paragraph",
        "multiple lines, one task per line",
        "a bullet list",
    ]
    TASK_DISPLAY = "The set of task(s) should be displayed as {task_format}."
    REQUEST_FORMATTING = "One task should ask for output to be formatted in a specific way, such as {sample_formats}, or similar type of formatting that would be appropriate for the task."

    # construct samples
    rows = []
    for _ in range(n_samples):
        row = {
            "context_styles": context_styles,
            "formatting_options": formatting_options,
            "batch_size": batch_size,
            "topic_avoidance": topic_avoidance,
            "flesch": flesch,
            "language": language,
            "next_year": next_year,
        }
        # Number of input context blocks to generate.
        row["input_count"] = random.choice([1, 1, 1, 2, 2, 3, 4])

        # Configure the number of metadata key/value pairs per input block.
        row["metadata_counts"] = "\n".join(
            [
                f"- context block {idx + 1} should have {random.randint(0, 8)} metadata key/value pairs"
                for idx in range(row["input_count"])
            ]
        )

        # Select which input context block to target with question(s).
        row["target_selection"] = random.choice(TARGET_OPTIONS)

        # Number of questions/instructions to include for the given prompt.
        row["task_count"] = random.choice([1, 1, 1, 2, 2, 3])

        # Select the writing style for each context block.
        row["styles"] = ""
        if row["context_styles"]:
            row["styles"] = "\n".join(
                [
                    f"- text {idx + 1} should be in the form of: {random.choice(row['context_styles'])}"
                    for idx in range(row["input_count"])
                ]
            )

        # Ask for specific output format in one of the tasks.
        row["format_task"] = ""
        if row["formatting_options"] and random.random() <= 0.2:
            sample = random.sample(
                row["formatting_options"], min(len(row["formatting_options"]), 3)
            )
            row["format_task"] = REQUEST_FORMATTING.format(
                sample_formats=", ".join(sample)
            )

        # Add instructions indicating how context blocks should relate to each other.
        row["reference_texts"] = (
            "The random text blocks should not reference each other."
        )
        if random.random() <= 0.1 and row["input_count"] > 1:
            row["reference_texts"] = (
                "One of the random text blocks should reference details in another"
            )
            if random.random() <= 0.5:
                row[
                    "reference_texts"
                ] += " using metadata, e.g. a link from one text block should be referenced in the text of another."
            else:
                row["reference_texts"] += "."

        # Add instructions to include source/reference information.
        row["include_source"] = ""
        if random.random() <= 0.2:
            row["include_source"] = ASK_FOR_SOURCE
            if row["formatting_options"] and random.random() <= 0.2:
                row[
                    "include_source"
                ] += f" Ask for the references/source as: {random.choice(row['formatting_options'])}"

        # Add instructions to add some confounders, i.e. unanswerable questions.
        row["task_confounder"] = ""
        if random.random() < 0.1:
            if row["task_count"] > 1:
                if random.random() < 0.5:
                    row["task_confounder"] = (
                        "One of the tasks should be completely unrelated to the generated text(s)."
                    )
                else:
                    row["task_confounder"] = (
                        "One of the tasks should be somewhat related to provided input text(s), but not answerable by any of them."
                    )
            else:
                if random.random() < 0.5:
                    row["task_confounder"] = (
                        "The task should be completely unrelated to the generated text(s)."
                    )
                else:
                    row["task_confounder"] = (
                        "The task should be somewhat related to the provided input text(s), but not answerable by any of them."
                    )

        # Inject instructions to relate the input text blocks to specific topics.
        current_topics = []
        cycle_index = 0
        for _ in range(row["input_count"]):
            current_topics.append(topics[cycle_index])
            cycle_index += 1
            if cycle_index >= len(topics):
                cycle_index = 0
        row["topics"] = "\n".join(
            [
                f" * text {idx + 1} should be related to topic: {topic}"
                for idx, topic in enumerate(current_topics)
            ]
        )

        # How to present the tasks in the instruction block.
        row["task_display_style"] = TASK_DISPLAY.format(
            task_format=random.choice(TASK_DISPLAY_OPTIONS)
        )

        rows.append(row)

    return Dataset.from_list(rows)


def cleanup_tsk(dataset: Dataset):
    """
    Remove 'TSK #' from the beginning of instruction.
    """

    def remove_task_prefix(example):
        # Use regex to remove any prefix that starts with "TSK X." (where X is any number)
        example["instruction"] = re.sub(r"^TSK \d+[:.]?\s*", "", example["instruction"])
        return example

    return dataset.map(remove_task_prefix)


def _sample_writing_styles_map(row):
    batch_size = row["batch_size"]
    with_styles = math.floor(batch_size / 4)
    batch_styles = random.sample(row["styles"], with_styles)
    row["style_extra"] = "Additional requirements:\n" + "\n".join(
        [
            f"- instruction {idx + 1} should specify that the style be {batch_styles[idx]}"
            for idx in range(with_styles)
        ]
    )
    return row


def sample_writing_instructions_args(dataset: Dataset):
    return dataset.map(_sample_writing_styles_map)


def sample_coding_instructions_args(dataset: Dataset, n_samples: int):
    first_row = dataset.select(range(1))[0]
    coding_languages = first_row["coding_languages"]
    related_software = first_row["related_software"]
    language = first_row["language"]
    batch_size = first_row["batch_size"]

    # construct samples
    rows = []
    for _ in range(n_samples):
        # Take a random sample without replacement if batch size is less than the number of topics
        # otherwise take a random sample with replacement.
        current_languages = (
            random.sample(coding_languages, batch_size)
            if batch_size < len(coding_languages)
            else random.choices(coding_languages, k=batch_size)
        )
        languages_str = "\n".join(
            [
                f" * task {idx + 1} should ask the user to use {language}"
                for idx, language in enumerate(current_languages)
            ]
        )
        related_str = ""
        if batch_size > 3:
            related_str = f"One of the tasks should require interacting with {random.choice(related_software)}."

        row = first_row.copy()
        row["language"] = language
        row["coding_languages"] = languages_str
        row["related_software"] = related_str
        row["batch_size"] = batch_size
        rows.append(row)

    return Dataset.from_list(rows)


def _cleanup_qa_map(row, instruction_column, response_column):
    row[instruction_column] = row[instruction_column].replace("QUESTION: ", "", 1)
    row[response_column] = row[response_column].replace("ANSWER: ", "", 1)
    return row


def cleanup_qa(dataset: Dataset, instruction_column: str, response_column: str):
    dataset = dataset.map(
        _cleanup_qa_map,
        fn_kwargs={
            "instruction_column": instruction_column,
            "response_column": response_column,
        },
    )
    return dataset

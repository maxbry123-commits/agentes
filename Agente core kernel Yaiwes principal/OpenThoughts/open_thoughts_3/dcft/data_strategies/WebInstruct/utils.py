import logging
import re
from typing import List
from urllib.parse import urlparse

from datasets import Dataset
from resiliparse.extract.html2text import extract_plain_text


def filter_if_contains(dataset: Dataset, input_column: str, phrase: str) -> Dataset:
    return dataset.filter(
        lambda x: phrase in x[input_column], desc=f"Filtering entries"
    )


def clean_text(text):
    # Remove extra whitespace and newlines
    text = re.sub(r"\s+", " ", text).strip()
    # Remove any non-printable characters
    text = "".join(char for char in text if char.isprintable())
    return text


def remove_non_question(text):
    phrase = "CONTENTS CHAPTER PREVIOUS NEXT PREP FIND PROBLEM"
    if phrase in text:
        return text[len(phrase) + 12 :]
    else:
        return False


def parse_html(
    dataset: Dataset,
    input_column: str = "html",
    output_column: str = "text",
    remove_columns: List[str] = None,
) -> Dataset:
    def extract_and_keep(data):
        result = {
            output_column: extract_plain_text(data[input_column], main_content=True)
        }
        return result

    columns_to_remove = remove_columns or []

    return dataset.map(
        extract_and_keep,
        remove_columns=columns_to_remove,
        desc="Extracting plain text from HTML",
    )


def clean_dataset(
    dataset: Dataset,
    input_column: str = "text",
    output_column: str = "text",
    remove_columns: List[str] = None,
) -> Dataset:
    columns_to_remove = remove_columns or []

    # map allows you to remove columns, although if you are just removing columns, you should use .remove_columns() or .select_columns()
    return dataset.map(
        lambda example: {output_column: clean_text(example[input_column])},
        remove_columns=columns_to_remove,
        desc="Cleaning text data",
    )


def remove_text(
    dataset: Dataset,
    input_column: str,
    output_column: str,
    phrase: str,
    remove_columns: List[str] = None,
    num_truncate: int = None,
):
    columns_to_remove = remove_columns or []
    dataset = dataset.map(
        lambda example: {
            output_column: re.sub(
                re.escape(phrase), "", example[input_column], flags=re.IGNORECASE
            )
        },
        remove_columns=columns_to_remove,
        desc=f"Removing text from entries",
    )
    if num_truncate is not None:
        dataset = dataset.select(range(min(len(dataset), num_truncate)))
    return dataset


def sample_from_dataset(
    dataset: Dataset, num_examples: int = 100_000, seed: int = 42
) -> Dataset:
    dataset = dataset.shuffle(seed=seed)
    print(f"Shuffled dataset. Total length: {len(dataset)}")
    if num_examples > len(dataset):
        raise ValueError(
            f"Not enough samples in dataset to meet the requested number of samples ({num_examples}). Input dataset has {len(dataset)} samples."
        )
    return dataset.select(range(num_examples))


def extract_root_domain(url: str) -> str:
    """Helper function to extract root domain from URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc

        if domain.startswith("www."):
            domain = domain[4:]

        if not domain:
            return "invalid_url"

        return domain.lower()

    except Exception:
        return "invalid_url"


def count_domains_per_shard(
    dataset: Dataset,
    input_url_column: str,
    output_domain_column: str,
    output_count_column: str,
) -> Dataset:
    """
    Returns a dataset containing the count of each top-level domain in the shard.
    """
    count = {}
    for row in dataset:
        domain = extract_root_domain(row[input_url_column])
        count[domain] = count.get(domain, 0) + 1

    return Dataset.from_list(
        [
            {output_domain_column: domain, output_count_column: cnt}
            for domain, cnt in count.items()
        ]
    )


def sum_and_filter_low_frequency_domains(
    dataset: Dataset, input_domain_column: str, input_count_column: str, min_count: int
) -> Dataset:
    """
    Sum the counts in the dataset and also filter out domains with counts less than min_count.
    Will return a dataset with the same columns as the input.
    """
    count = {}
    for row in dataset:
        count[row[input_domain_column]] = (
            count.get(row[input_domain_column], 0) + row[input_count_column]
        )
    result = Dataset.from_list(
        [
            {input_domain_column: domain, input_count_column: cnt}
            for domain, cnt in count.items()
            if cnt >= min_count
        ]
    )
    logging.info(
        f"Found {len(result)} / {len(dataset)} domains with counts >= {min_count}. "
        f"Yield: {len(result) / len(dataset):.2%}"
    )
    return result


def annotate_frequent_and_educational_domains(
    dataset: Dataset, domains: Dataset
) -> Dataset:
    """
    Annotate documents with whether they are from frequent and educational domains.
    """
    educational_domains = set(
        domains.filter(lambda x: x["is_educational_domain"])["domain"]
    )
    result = dataset.map(
        lambda x: {
            **x,
            "is_educational_domain": extract_root_domain(x["url"])
            in educational_domains,
        },
        desc="Annotating educational domains",
    )
    educational_count = len(result.filter(lambda x: x["is_educational_domain"]))
    logging.info(
        f"Found {educational_count} / {len(dataset)} docs from educational domains. "
        f"Yield: {educational_count / len(dataset):.2%}"
    )
    return result

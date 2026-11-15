from datasets import Dataset
from difflib import SequenceMatcher
from typing import List, Dict
import copy
import re


def _fill_templated_strings(template: str, dataset_row: dict) -> str:
    """
    Replaces templated strings in a template string with values from a dataset row

    Args:
        template: str - A template string with {{column_name}} patterns
        dataset_row: dict - Dictionary containing values to replace the patterns
    Returns:
        str - A template string with {{column_name}} patterns replaced with values from the dataset row

    Example: Pattern looks for {{something}}
        template = "Hello {{name}}, your age is {{age}}"
        dataset_row = {"name": "Alice", "age": 30}

        For each match, the regex groups are:
        - group(0): full match (e.g., "{{name}}")
        - group(1): captured column name (e.g., "name")
    """
    pattern = r"\{\{(\w+)\}\}"
    # For each match, lambda gets a match object (x) where:
    # x.group(0) would be the full match like "{{name}}"
    # x.group(1) gets just the column name like "name" to use as the dictionary key
    return re.sub(pattern, lambda x: str(dataset_row[x.group(1)]), template)


def construct_prompt(dataset: Dataset, output_column: str, prompt: str):
    def f(x):
        x[output_column] = _fill_templated_strings(prompt, x)
        return x

    dataset = dataset.map(f)
    return dataset


def cluster_similar_responses(responses: List[str]) -> List[List[str]]:
    clusters = []
    for response in responses:
        added_to_cluster = False
        for cluster in clusters:
            if SequenceMatcher(None, response, cluster[0]).ratio() >= 1000000:
                cluster.append(response)
                added_to_cluster = True
                break
        if not added_to_cluster:
            clusters.append([response])
    return clusters


def aggregate_results(responses: List[str]) -> Dict[str, any]:
    final_answers = responses
    clusters = cluster_similar_responses(final_answers)

    cluster_info = []
    for cluster in clusters:
        cluster_info.append(
            {"answer": cluster[0], "frequency": len(cluster), "variants": cluster}
        )

    cluster_info.sort(key=lambda x: x["frequency"], reverse=True)

    return {
        "clusters": cluster_info,
        "total_responses": len(responses),
        "num_unique_clusters": len(clusters),
    }


def self_consistency_multiple_samples(
    dataset: Dataset, response_column: str, verified_response_column: str
) -> Dataset:
    def f(x):
        clusters = aggregate_results(x[response_column])["clusters"]
        best_cluster = clusters[0]
        x["_majority_responses"] = best_cluster["variants"][0]
        return x

    dataset = dataset.map(f)

    all_rows = []
    for row in dataset:
        for majority_response in row["_majority_responses"]:
            new_row = copy.deepcopy(row)
            new_row[verified_response_column] = majority_response
            all_rows.append(new_row)

    return Dataset.from_list(all_rows)

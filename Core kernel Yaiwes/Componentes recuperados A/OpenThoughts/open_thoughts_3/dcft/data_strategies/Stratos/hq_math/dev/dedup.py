from typing import Dict, List, Tuple

import numpy as np
from datasets import load_dataset


def analyze_column_overlap(dataset_column_pairs: List[Tuple[str, str, str]]) -> Dict:
    """
    Analyze overlap between columns in HuggingFace datasets.

    Args:
        dataset_column_pairs: List of tuples (dataset_name, split, column_name)

    Returns:
        Dictionary of overlap metrics between pairs
    """
    pair_values = {}
    for dataset_name, split, column in dataset_column_pairs:
        ds = load_dataset(dataset_name, split=split, trust_remote_code=True)
        values = set(str(x) for x in ds[column] if x is not None)
        pair_values[(dataset_name, split, column)] = values

    results = {}
    pairs = list(pair_values.keys())

    for i in range(len(pairs)):
        for j in range(i + 1, len(pairs)):
            pair1 = pairs[i]
            pair2 = pairs[j]

            set1 = pair_values[pair1]
            set2 = pair_values[pair2]

            intersection = set1.intersection(set2)
            union = set1.union(set2)

            overlap_metrics = {
                "intersection_size": len(intersection),
                "intersection_values": sorted(list(intersection)),
                "jaccard_similarity": len(intersection) / len(union) if union else 0,
                "overlap_coefficient": (
                    len(intersection) / min(len(set1), len(set2))
                    if min(len(set1), len(set2)) > 0
                    else 0
                ),
                "set1_size": len(set1),
                "set2_size": len(set2),
                "set1_unique": sorted(list(set1 - set2)),
                "set2_unique": sorted(list(set2 - set1)),
            }

            key1 = f"{pair1[0]}:{pair1[1]}:{pair1[2]}"
            key2 = f"{pair2[0]}:{pair2[1]}:{pair2[2]}"
            results[(key1, key2)] = overlap_metrics

    return results


def print_overlap_summary(results: Dict) -> None:
    """Print human-readable overlap analysis summary."""
    for (pair1, pair2), metrics in results.items():
        print(f"\nOverlap Analysis: {pair1} vs {pair2}")
        print("-" * 80)
        print(f"Set 1 size: {metrics['set1_size']}")
        print(f"Set 2 size: {metrics['set2_size']}")
        print(f"Intersection size: {metrics['intersection_size']}")
        print(f"Jaccard similarity: {metrics['jaccard_similarity']:.3f}")
        print(f"Overlap coefficient: {metrics['overlap_coefficient']:.3f}")

        # max_sample = 5
        # if metrics["intersection_values"]:
        #     sample = metrics["intersection_values"][:max_sample]
        #     print(f"\nSample overlapping values: {sample}")
        #     if len(metrics["intersection_values"]) > max_sample:
        #         print(f"... and {len(metrics['intersection_values']) - max_sample} more")

        # if metrics["set1_unique"]:
        #     sample = metrics["set1_unique"][:max_sample]
        #     print(f"\nSample values unique to {pair1}: {sample}")
        #     if len(metrics["set1_unique"]) > max_sample:
        #         print(f"... and {len(metrics['set1_unique']) - max_sample} more")

        # if metrics["set2_unique"]:
        #     sample = metrics["set2_unique"][:max_sample]
        #     print(f"\nSample values unique to {pair2}: {sample}")
        #     if len(metrics["set2_unique"]) > max_sample:
        #         print(f"... and {len(metrics['set2_unique']) - max_sample} more")


# Example usage:
if __name__ == "__main__":
    pairs = [
        ("MatrixStudio/Codeforces-Python-Submissions", "train", "problem-description"),
        ("BAAI/TACO", "train", "question"),
        ("deepmind/code_contests", "train", "description"),
        ("codeparrot/apps", "train", "question"),
        ("Asap7772/leetcode-rosetta-processed-with-test-cases", "train", "content"),
        ("AI-MO/NuminaMath-CoT", "train", "problem"),
        ("KbsdJames/Omni-MATH", "test", "problem"),
        ("Maxwell-Jia/AIME_2024", "train", "Problem"),
        ("AI-MO/aimo-validation-amc", "train", "problem"),
        ("HuggingFaceH4/MATH-500", "test", "problem"),
        ("livecodebench/code_generation_lite", "test", "question_content"),
    ]

    results = analyze_column_overlap(pairs)
    print_overlap_summary(results)

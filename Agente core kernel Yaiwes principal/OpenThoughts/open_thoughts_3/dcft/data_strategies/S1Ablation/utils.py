import logging
import math
import random
import re
from collections import defaultdict

from datasets import Dataset

# logger = logging.getLogger(__name__)


def filter_longest_entries(dataset: Dataset, filter_column: str, num_keep: int):
    """
    Filters the dataset to keep only the num_keep longest entries based on filter_column.
    """
    logging.info(
        f"Filtering by length of {filter_column}, total entries: {len(dataset)}."
    )

    # Add a column with the length of the specified column
    dataset = dataset.map(lambda x: {**x, "length": len(x[filter_column])})

    # Sort dataset by length in descending order
    sorted_dataset = dataset.sort("length", reverse=True)

    # Select the top num_keep entries
    filtered_dataset = sorted_dataset.select(range(min(num_keep, len(sorted_dataset))))

    return filtered_dataset


SYSTEM_PROMPT = "Your role as an assistant involves thoroughly exploring questions through a systematic long thinking process before providing the final precise and accurate solutions. This requires engaging in a comprehensive cycle of analysis, summarizing, exploration, reassessment, reflection, backtracing, and iteration to develop well-considered thinking process. Please structure your response into two main sections: Thought and Solution. In the Thought section, detail your reasoning process using the specified format: <|begin_of_thought|> {thought with steps separated with '\n\n'} <|end_of_thought|> Each step should include detailed considerations such as analisying questions, summarizing relevant findings, brainstorming new ideas, verifying the accuracy of the current steps, refining any errors, and revisiting previous steps. In the Solution section, based on various attempts, explorations, and reflections from the Thought section, systematically present the final solution that you deem correct. The solution should remain a logical, accurate, concise expression style and detail necessary step needed to reach the conclusion, formatted as follows: <|begin_of_solution|> {final formatted, precise, and clear solution} <|end_of_solution|> Now, try to solve the following question through the above guidelines:"


def convert_to_share_gpt(dataset: Dataset, user_column: str) -> Dataset:
    def map_to_share_gpt(x):
        user = x[user_column]

        return {
            "system": SYSTEM_PROMPT,
            "conversations": [
                {"from": "user", "value": user},
                {
                    "from": "assistant",
                    "value": f"<|begin_of_thought|>\n\n{x['reasoning']}\n\n<|end_of_thought|>\n\n<|begin_of_solution|>\n\n{x['deepseek_solution']}\n\n<|end_of_solution|>",
                },
            ],
        }

    dataset = dataset.map(map_to_share_gpt)
    return dataset


class_labels = [
    "00 General and overarching topics; collections",
    "01 History and biography",
    "03 Mathematical logic and foundations",
    "05 Combinatorics",
    "06 Order, lattices, ordered algebraic structures",
    "08 General algebraic systems",
    "11 Number theory",
    "12 Field theory and polynomials",
    "13 Commutative algebra",
    "14 Algebraic geometry",
    "15 Linear and multilinear algebra; matrix theory",
    "16 Associative rings and algebras",
    "17 Nonassociative rings and algebras",
    "18 Category theory; homological algebra",
    "19 K-theory",
    "20 Group theory and generalizations",
    "22 Topological groups, Lie groups",
    "26 Real functions",
    "28 Measure and integration",
    "30 Functions of a complex variable",
    "31 Potential theory",
    "32 Several complex variables and analytic spaces",
    "33 Special functions",
    "34 Ordinary differential equations",
    "35 Partial differential equations",
    "37 Dynamical systems and ergodic theory",
    "39 Difference and functional equations",
    "40 Sequences, series, summability",
    "41 Approximations and expansions",
    "42 Harmonic analysis on Euclidean spaces",
    "43 Abstract harmonic analysis",
    "44 Integral transforms, operational calculus",
    "45 Integral equations",
    "46 Functional analysis",
    "47 Operator theory",
    "49 Calculus of variations and optimal control; optimization",
    "51 Geometry",
    "52 Convex and discrete geometry",
    "53 Differential geometry",
    "54 General topology",
    "55 Algebraic topology",
    "57 Manifolds and cell complexes",
    "58 Global analysis, analysis on manifolds",
    "60 Probability theory and stochastic processes",
    "62 Statistics",
    "65 Numerical analysis",
    "68 Computer science",
    "70 Mechanics of particles and systems",
    "74 Mechanics of deformable solids",
    "76 Fluid mechanics",
    "78 Optics, electromagnetic theory",
    "80 Classical thermodynamics, heat transfer",
    "81 Quantum theory",
    "82 Statistical mechanics, structure of matter",
    "83 Relativity and gravitational theory",
    "85 Astronomy and astrophysics",
    "86 Geophysics",
    "90 Operations research, mathematical programming",
    "91 Game theory, economics, social and behavioral sciences",
    "92 Biology and other natural sciences",
    "93 Systems theory; control",
    "94 Information and communication, circuits",
    "97 Mathematics education",
]


def shuffle_and_truncate(dataset: Dataset, num_truncate: int) -> Dataset:
    shuffled_dataset = dataset.shuffle(
        seed=42
    )  # Shuffle with a fixed seed for reproducibility
    truncated_dataset = shuffled_dataset.select(range(num_truncate))
    return truncated_dataset


def stratified_uniform_sampling(dataset: Dataset, num_samples: int) -> Dataset:
    none_count = 0

    # Function to extract the math classification label
    def extract_class(example):
        nonlocal none_count
        match = re.search(r'{"class":\s*"(.+?)"}', example["response"])
        extracted_class = match.group(1) if match else None
        matched_label = next(
            (
                label
                for label in class_labels
                if extracted_class and extracted_class in label
            ),
            None,
        )
        if matched_label is None:
            none_count += 1
        return {"math_class": matched_label}

    # Apply the function to the dataset
    dataset = dataset.map(extract_class)

    total_count = dataset.num_rows
    none_fraction = none_count / total_count if total_count > 0 else 0
    logging.info(f"Fraction of {none_fraction} has no math class label attached.")

    # Group data by class
    class_data = defaultdict(list)
    err_ctr = 0
    for example in dataset:
        label = example["math_class"]
        if label in class_labels:
            class_data[label].append(example)
        else:
            err_ctr += 1

    # Compute class distribution percentages
    logging.info(f"Class label distribution:")
    for label in class_labels:
        if len(class_data[label]) > 0:
            logging.info(f"  {label}: {len(class_data[label]) / total_count:.2f}")
            print(f"  {label}: {len(class_data[label]) / total_count:.2f}")

    if none_count > 0:
        logging.info(f"  None: {none_count / total_count:.2f}")
        print(f"  None: {none_count / total_count:.2f}")

    #    num_samples_per_class = max(1, num_samples // len(class_labels))
    #    new_data = []
    #    for class_label in class_labels:
    #        available_samples = class_data[class_label]
    #        sample_size = min(len(available_samples), num_samples_per_class)
    #        new_data.extend(random.sample(available_samples, sample_size))

    # Group data by class
    class_data = defaultdict(list)
    for example in dataset:
        label = example["math_class"]
        if label in class_labels:
            class_data[label].append(example)

    # Prepare a list of available classes for selection
    available_classes = [cls for cls in class_data if class_data[cls]]

    # Ensure we don't sample more than available data
    total_available_samples = sum(len(examples) for examples in class_data.values())
    num_samples = min(num_samples, total_available_samples)

    selected_samples = []

    while len(selected_samples) < num_samples:
        # Randomly pick a class
        chosen_class = random.choice(available_classes)

        # Randomly pick an example from that class
        example = random.choice(class_data[chosen_class])

        # Remove the selected example
        class_data[chosen_class].remove(example)
        selected_samples.append(example)

        # Remove class if empty
        if not class_data[chosen_class]:
            available_classes.remove(chosen_class)

    # Convert to HF Dataset
    new_dataset = Dataset.from_list(selected_samples)

    # Shuffle the dataset
    new_dataset = new_dataset.shuffle(seed=42)

    logging.info(f"Label error in {err_ctr}/{len(dataset)} entries.")
    logging.info(f"New dataset has  {len(new_dataset)} entries.")

    return new_dataset

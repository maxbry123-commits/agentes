import os
import re
import json
import requests
import tempfile
import subprocess
import pandas as pd
from datasets import Dataset
from tqdm import tqdm
import argparse
from pathlib import Path
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
from functools import partial
import numpy as np


def parse_github_url(github_url: str) -> tuple:
    """Extract owner and repo name from a GitHub URL."""
    pattern = r"github\.com/([^/]+)/([^/]+)"
    match = re.search(pattern, github_url)
    if match:
        return match.group(1), match.group(2)
    else:
        pattern = r"^([^/]+)/([^/]+)$"
        match = re.search(pattern, github_url)
        if match:
            return match.group(1), match.group(2)
    raise ValueError(f"Could not parse GitHub URL: {github_url}")


def clone_repo(owner: str, repo: str, temp_dir: str) -> str:
    """Clone a GitHub repository to a temporary directory."""
    repo_url = f"https://github.com/{owner}/{repo}.git"
    repo_path = os.path.join(temp_dir, repo)

    print(f"Cloning {repo_url} to {repo_path}...")
    subprocess.run(["git", "clone", "--depth=1", repo_url, repo_path], check=True)

    return repo_path


def is_code_file(file_path: str) -> bool:
    """Check if a file is a code file based on its extension."""
    code_extensions = {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".cs",
        ".go",
        ".rb",
        ".php",
        ".swift",
        ".kt",
        ".rs",
        ".scala",
        ".sh",
        ".bash",
        ".pl",
        ".pm",
        ".lua",
        ".sql",
        ".r",
        ".m",
        ".f90",
        ".f95",
        ".hs",
        ".erl",
        ".ex",
        ".exs",
        ".clj",
        ".groovy",
        ".dart",
        ".fs",
    }
    return os.path.splitext(file_path)[1].lower() in code_extensions


def collect_code_files(repo_path: str) -> List[Dict[str, Any]]:
    """Collect all code files from a repository."""
    code_files = []

    for root, _, files in tqdm(list(os.walk(repo_path))):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, repo_path)

            # Skip .git directory
            if ".git" in rel_path.split(os.path.sep):
                continue

            if is_code_file(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    code_files.append(
                        {
                            "file_path": rel_path,
                            "content": content,
                            "extension": os.path.splitext(file_path)[1][
                                1:
                            ],  # Remove the dot
                            "size_bytes": os.path.getsize(file_path),
                        }
                    )
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")

    return code_files


def get_unique_code_sources(dataset: Dataset) -> Dataset:
    """Get unique code sources from a Hugging Face dataset."""
    unique_repos = dataset.unique("repo")
    return Dataset.from_list([{"repo": repo} for repo in unique_repos])


def process_single_repo(repo: str, temp_dir: str) -> List[Dict]:
    try:
        # Parse owner and repo name from repo string
        owner, repo_name = repo.split("/")[-2:]

        repo_path = clone_repo(owner, repo_name, temp_dir)

        # Collect code files
        print(f"Collecting code files for {owner}/{repo_name}...")
        code_files = collect_code_files(repo_path)
        print(f"Found {len(code_files)} code files")

        # Add repo info to each file
        for file in code_files:
            file["owner"] = owner
            file["repo"] = repo_name

        return code_files

    except Exception as e:
        print(f"Error processing repo {repo}: {e}")
        return []


def create_hf_dataset(
    code_files: List[Dict[str, Any]], owner: str, repo: str, output_dir: str
) -> None:
    """Create a Hugging Face dataset from code files."""
    # Convert to DataFrame first for easier manipulation
    df = pd.DataFrame(code_files)

    # Create the dataset
    dataset = Dataset.from_pandas(df)

    # Save the dataset
    dataset_name = f"{owner}_{repo}_code"
    dataset_path = os.path.join(output_dir, dataset_name)

    # Create the directory if it doesn't exist
    Path(dataset_path).mkdir(parents=True, exist_ok=True)

    return dataset


def get_files_for_repo(dataset: Dataset, repo_column: str) -> Dataset:
    """Get code files for multiple repos in a dataset in parallel."""
    all_code_files = []
    with tempfile.TemporaryDirectory() as temp_dir:
        # Use ProcessPoolExecutor for parallel processing
        with ProcessPoolExecutor() as executor:
            # Create futures for all repos
            future_to_repo = {
                executor.submit(process_single_repo, repo, temp_dir): repo
                for repo in dataset[repo_column]
            }

            # Process completed futures
            for future in tqdm(
                as_completed(future_to_repo),
                total=len(future_to_repo),
                desc="Processing repositories",
            ):
                repo = future_to_repo[future]
                try:
                    code_files = future.result()
                    all_code_files.append({"repo": repo, "code_files": code_files})
                except Exception as e:
                    print(f"Error processing repo {repo}: {e}")

    # Create combined dataset
    return Dataset.from_list(all_code_files)


def process_item(item, code_files_dict):
    # Look up code files directly from dictionary
    code_files = code_files_dict.get(item["repo"])

    if code_files:
        # Create new row with original data plus code files
        new_row = dict(item)
        new_row["code_files"] = code_files
        return new_row
    return None


def compute_relevant_context(
    dataset: Dataset, dataset_with_code_files: Dataset
) -> Dataset:
    # Convert dataset_with_code_files to dictionary for O(1) lookups
    code_files_dict = {
        item["repo"]: item["code_files"] for item in dataset_with_code_files
    }

    new_rows = []
    # Process items in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor() as executor:
        # Create futures for all items
        future_to_item = {
            executor.submit(process_item, item, code_files_dict): item
            for item in dataset
        }

        # Process completed futures
        for future in tqdm(
            as_completed(future_to_item),
            total=len(future_to_item),
            desc="Processing items",
        ):
            result = future.result()
            if result:
                new_rows.append(result)

    # Create new dataset from the rows
    return Dataset.from_list(new_rows)


def bm25k(dataset: Dataset, num_docs: int = 2) -> Dataset:
    def f(examples):
        prompts = examples["problem_statement"]
        all_code_files = examples["code_files"]
        final_prompts = []

        for prompt, code_files in zip(prompts, all_code_files):
            all_files = [file["content"] for file in code_files]
            file_names = [file["file_path"] for file in code_files]

            tokenized_corpus = [doc.lower().split() for doc in all_files]
            bm25 = BM25Okapi(tokenized_corpus)
            del tokenized_corpus
            tokenized_prompt = prompt.lower().split()
            scores = bm25.get_scores(tokenized_prompt)
            top_n_indices = np.argsort(scores)[::-1][:num_docs]

            top_docs = [all_files[i] for i in top_n_indices]
            top_file_names = [file_names[i] for i in top_n_indices]

            final_prompt = prompt

            for i in range(len(top_docs)):
                lines = top_docs[i].split("\n")
                numbered_lines = [f"{j+1}: {line}" for j, line in enumerate(lines)]
                numbered_doc = "\n".join(numbered_lines)
                final_prompt += f"\n\n{top_file_names[i]}: \n\n{numbered_doc}"

            final_prompt += """\n\n\n\nAnswer the Github Issue with a diff patch format. Here is an example:
            <patch>
            diff --git a/backend/config.py b/backend/config.py
            --- a/backend/config.py
            +++ b/backend/config.py
            @@ -24,7 +24,7 @@ class Config:
                DEBUG = False
                TESTING = False
            -    SECRET_KEY = 'default-insecure-key'
            +    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-insecure-key')
            
                @staticmethod
                def init_app(app):
            </patch>
            """
            final_prompts.append(final_prompt)

        examples["final_prompt"] = final_prompts
        return examples

    dataset = dataset.map(f, batched=True, batch_size=2)
    return dataset


def bm25k_with_metadata(dataset: Dataset, num_docs: int = 2) -> Dataset:
    def f(examples):
        prompts = examples["problem_statement"]
        all_code_files = examples["code_files"]
        final_prompts = []

        for prompt, code_files in zip(prompts, all_code_files):
            all_files = [file["content"] for file in code_files]
            file_names = [file["file_path"] for file in code_files]

            tokenized_corpus = [doc.lower().split() for doc in all_files]
            bm25 = BM25Okapi(tokenized_corpus)
            del tokenized_corpus
            tokenized_prompt = prompt.lower().split()
            scores = bm25.get_scores(tokenized_prompt)
            top_n_indices = np.argsort(scores)[::-1][:num_docs]

            top_docs = [all_files[i] for i in top_n_indices]
            top_file_names = [file_names[i] for i in top_n_indices]

            final_prompt = prompt

            for i in range(len(top_docs)):
                lines = top_docs[i].split("\n")
                numbered_lines = [f"{j+1}: {line}" for j, line in enumerate(lines)]
                numbered_doc = "\n".join(numbered_lines)
                final_prompt += f"\n\n{top_file_names[i]}: \n\n{numbered_doc}"

            final_prompt += """\n\n\n\nAnswer the Github Issue with a diff patch format. Here is an example:
            <patch>
            diff --git a/backend/config.py b/backend/config.py
            --- a/backend/config.py
            +++ b/backend/config.py
            @@ -24,7 +24,7 @@ class Config:
                DEBUG = False
                TESTING = False
            -    SECRET_KEY = 'default-insecure-key'
            +    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-insecure-key')
            
                @staticmethod
                def init_app(app):
            </patch>
            """
            final_prompts.append(final_prompt)
        newexamples = {}
        newexamples["final_prompt"] = final_prompts
        newexamples["instance_id"] = examples["instance_id"]
        return newexamples

    dataset = dataset.map(f, batched=True, batch_size=2)
    return dataset


import re


def add_patch_tags_helper(text):
    """
    Add <patch> </patch> tags around diff blocks that don't already have them.

    Handles different formats:
    1. ```diff ... ``` blocks
    2. ```patch ... ``` blocks
    3. ``` ... ``` blocks containing diff-like content
    """
    # First, find the text after </think> tag if it exists
    think_match = re.search(r"</think>(.*)", text, re.DOTALL)
    if think_match:
        content = think_match.group(1)
    else:
        content = text

    # Function to determine if a code block contains diff-like content
    def is_diff_content(block_content):
        # Check for common diff patterns like "diff --git", "+++", "---", or lines starting with + or -
        diff_patterns = [
            r"diff --git",
            r"^\+\+\+\s",
            r"^---\s",
            r"^@@ .* @@",
            r"^\+[^+]",
            r"^-[^-]",
        ]

        for pattern in diff_patterns:
            if re.search(pattern, block_content, re.MULTILINE):
                return True
        return False

    # Pattern to find code blocks that might be diffs
    code_block_pattern = r"```(?:diff|patch)?(.*?)```"

    # Find all code blocks
    matches = list(re.finditer(code_block_pattern, content, re.DOTALL))

    # Process matches in reverse order to avoid offset issues when replacing
    result = content
    for match in reversed(matches):
        full_match = match.group(0)
        block_content = match.group(1).strip()

        # Skip if it's an empty block
        if not block_content:
            continue

        # Check if this block is already wrapped in patch tags
        start_pos = max(0, match.start() - 20)
        end_pos = min(len(content), match.end() + 20)
        surrounding = content[start_pos:end_pos]

        if re.search(
            r"<patch>\s*" + re.escape(full_match.replace("\\", "\\\\")),
            surrounding,
            re.DOTALL,
        ) or re.search(
            re.escape(full_match.replace("\\", "\\\\")) + r"\s*</patch>",
            surrounding,
            re.DOTALL,
        ):
            continue

        # Check if it looks like a diff
        if is_diff_content(block_content):
            # Replace the code block with the same block wrapped in patch tags
            patched_block = f"<patch>\n{block_content}\n</patch>"
            result = result[: match.start()] + patched_block + result[match.end() :]

    # If we found and processed a </think> tag
    if think_match:
        return text[: think_match.start()] + "</think>" + result
    else:
        return result


def add_patch_tags(dataset: Dataset) -> Dataset:
    def f(example):
        example["final_reasoning_trace"] = add_patch_tags_helper(
            example["final_reasoning_trace"]
        )
        return example

    dataset = dataset.map(f)
    return dataset


def filter_top_num_comments(
    dataset: Dataset, dataset_metadata: Dataset, percentage_kept: float
) -> Dataset:

    def get_example_comments(example):
        repo = example["repo"]
        issue_number = example["issue_numbers"][0]
        response = requests.get(
            f"https://api.github.com/repos/{repo}/issues/{issue_number}"
        )
        data = json.loads(response.content)
        example["num_comments"] = data.get("comments", 0)
        return example

    def flag_good_issue(example, threshold):
        if example["num_comments"] > threshold:
            example["good_issue"] = True
        else:
            example["good_issue"] = False
        return example

    def filter(example, issue_flags):
        return issue_flags[example["__original_row_idx"]]

    dataset_metadata = dataset_metadata.map(get_example_comments)

    num_comments = dataset_metadata["num_comments"]

    threshold = np.quantile(num_comments, 1 - percentage_kept)

    dataset_metadata = dataset_metadata.map(
        partial(flag_good_issue, threshold=threshold)
    )

    issue_flags = dataset_metadata["good_issue"]

    dataset = dataset.filter(partial(filter, issue_flags))

    return dataset


if __name__ == "__main__":
    main()

import argparse
import hashlib
import json
import os
from typing import Dict, List

import datasets
from combine import combine_code_datasets
from constants import COLUMNS
from filters import filter_num_solutions, filter_problem, filter_solutions, filter_tests
from mappers import codecontests_map_sources
from utils import get_domain


def compute_problem_id(description: str) -> str:
    return hashlib.md5(description.encode()).hexdigest()


def dump_tests(tests: Dict[str, List[str]]) -> str:
    return json.dumps(tests)


def codecontests_combine_tests(
    public_tests: List[Dict[str, List[str]]],
    private_tests: List[Dict[str, List[str]]],
    generated_tests: List[Dict[str, List[str]]],
) -> Dict[str, List[str]]:
    return {
        "inputs": public_tests["input"]
        + private_tests["input"]
        + generated_tests["input"],
        "outputs": public_tests["output"]
        + private_tests["output"]
        + generated_tests["output"],
    }


def codecontests_rename_columns(dataset: datasets.Dataset) -> datasets.Dataset:
    dataset = dataset.map(
        lambda x: {
            "problem_id": x["problem_id"],
            "problem": x["description"],
            "test_cases": x["tests"],
            "difficulty": x["difficulty"],
            "source": x["source"],
            "language": "PYTHON3",
        }
    )

    return dataset


def apps_rename_columns(dataset: datasets.Dataset) -> datasets.Dataset:
    df = dataset.to_pandas()

    df = df.rename(
        columns={
            "question": "problem",
            "input_output": "test_cases",
            "difficulty": "difficulty",
            "problem_id": "problem_id",
            "name": "name",
            "language": "language",
            "source": "source",
        }
    )

    return datasets.Dataset.from_pandas(df)


def apps_process(
    dataset: datasets.Dataset, num_hf_proc_workers: int = 1
) -> datasets.Dataset:
    dataset = dataset.map(
        lambda x: {
            "problem_id": compute_problem_id(x["question"]),
            "difficulty": x["difficulty"].upper(),
            "name": x.get("name") if x.get("name") else "UNKNOWN",
            "language": "PYTHON3",
            "source": (
                get_domain(x["url"]).replace("www.", "").replace(".com", "").upper()
                if x["url"]
                else "UNKNOWN_SOURCE"
            ),
        },
        num_proc=num_hf_proc_workers,
    )

    dataset = dataset.filter(
        lambda x: filter_problem(x["question"]), num_proc=num_hf_proc_workers
    )
    dataset = dataset.filter(
        lambda x: filter_tests(x["input_output"]), num_proc=num_hf_proc_workers
    )

    dataset = dataset.map(
        lambda x: {
            "num_solutions": len(x["solutions"]),
        },
        num_proc=num_hf_proc_workers,
    )

    dataset = dataset.filter(
        lambda x: x["num_solutions"] > 0, num_proc=num_hf_proc_workers
    )

    dataset = apps_rename_columns(dataset)
    dataset = dataset.select_columns(COLUMNS)

    return dataset


def cps_groupby_problem_id(dataset: datasets.Dataset) -> datasets.Dataset:
    df = dataset.to_pandas()
    df = (
        df.groupby("problem_id")
        .agg(
            {
                "test_cases": list,
                "code": list,
                "name": "first",
                "description": "first",
            }
        )
        .reset_index()
    )

    return datasets.Dataset.from_pandas(df)


def rename_cps(dataset: datasets.Dataset) -> datasets.Dataset:
    df = dataset.to_pandas()
    df = df.rename(
        columns={
            "description": "problem",
            "tests": "test_cases",
            "difficulty": "difficulty",
            "source": "source",
            "problem_id": "problem_id",
            "name": "name",
        }
    )

    return datasets.Dataset.from_pandas(df)


def cps_process(
    dataset: datasets.Dataset, num_hf_proc_workers: int = 1
) -> datasets.Dataset:
    dataset = dataset.filter(
        lambda x: x["verdict"] == "OK", num_proc=num_hf_proc_workers
    )

    dataset = dataset.map(
        lambda x: {
            "sample-tests": f"Sample Input\n{''.join(x['demo-input'])}\nSample Output\n{''.join(x['demo-output'])}",
        },
        num_proc=num_hf_proc_workers,
    )

    dataset = dataset.map(
        lambda x: {
            "description": x["problem-description"]
            + "\n"
            + x["input-specification"]
            + "\n"
            + x["output-specification"]
            + "\n"
            + x["sample-tests"],
            "problem_id": compute_problem_id(
                x["problem-description"]
                + "\n"
                + x["input-specification"]
                + "\n"
                + x["output-specification"]
                + "\n"
                + x["sample-tests"]
            ),
        },
        num_proc=num_hf_proc_workers,
    )

    dataset = cps_groupby_problem_id(dataset)

    dataset = dataset.filter(
        lambda x: filter_problem(x["description"]), num_proc=num_hf_proc_workers
    )

    dataset = dataset.map(
        lambda x: {
            "source": "CODEFORCES",
            "difficulty": "UNKNOWN",
            "test_cases": {
                "inputs": [i["input"] for i in x["test_cases"][0]],
                "outputs": [i["output"] for i in x["test_cases"][0]],
            },
            "language": "PYTHON3",
        },
        num_proc=num_hf_proc_workers,
    )

    dataset = dataset.filter(
        lambda x: filter_tests(x["test_cases"]), num_proc=num_hf_proc_workers
    )

    dataset = rename_cps(dataset)

    dataset = dataset.map(
        lambda x: {
            "solutions": x["code"],
            "num_solutions": len(x["code"]),
            "starter_code": "",
        },
        num_proc=num_hf_proc_workers,
    )

    dataset = dataset.select_columns(COLUMNS)

    # dump tests
    dataset = dataset.map(
        lambda x: {"test_cases": json.dumps(x["test_cases"])},
        num_proc=num_hf_proc_workers,
    )

    return dataset


def codecontests_process(
    dataset: datasets.Dataset, num_hf_proc_workers: int = 1
) -> datasets.Dataset:
    """Process code contests dataset."""

    dataset = dataset.filter(
        lambda x: filter_problem(x["description"]), num_proc=num_hf_proc_workers
    )

    dataset = dataset.map(
        lambda x: {
            "problem_id": compute_problem_id(x["description"]),
            "source": codecontests_map_sources(x["source"]),
        },
        num_proc=num_hf_proc_workers,
    )

    dataset = dataset.map(
        lambda x: {
            "tests": codecontests_combine_tests(
                x["public_tests"], x["private_tests"], x["generated_tests"]
            ),
            "num_solutions": len(x["solutions"]),
        },
        num_proc=num_hf_proc_workers,
    )

    dataset = dataset.filter(
        lambda x: filter_tests(x["tests"]),
        num_proc=num_hf_proc_workers,
    )

    dataset = dataset.filter(
        lambda x: filter_solutions(x["solutions"]),
        num_proc=num_hf_proc_workers,
    )

    dataset = dataset.filter(
        lambda x: filter_num_solutions(x["num_solutions"]), num_proc=num_hf_proc_workers
    )

    dataset = dataset.map(
        lambda x: {
            "starter_code": "",
        },
        num_proc=num_hf_proc_workers,
    )

    dataset = codecontests_rename_columns(dataset)
    dataset = dataset.select_columns(COLUMNS)

    # dump tests
    dataset = dataset.map(
        lambda x: {
            "test_cases": dump_tests(x["test_cases"]),
        },
        num_proc=num_hf_proc_workers,
    )

    return dataset


def process_code_dataset(
    dataset_name_or_path: str, num_hf_proc_workers: int = 1
) -> datasets.Dataset:
    """
    Process code dataset.

    Args:
        dataset_name_or_path (str): Dataset name or path.
        num_hf_proc_workers (int): Number of Hugging Face processing workers.

    Returns:
        datasets.Dataset: Processed dataset.
    """

    dataset = datasets.load_dataset(
        dataset_name_or_path,
        split="all",
        trust_remote_code=True,
    )

    process_fn_map = {
        "code_contests": codecontests_process,
        "apps": apps_process,
        "taco": apps_process,
        "codeforces-python-submissions": cps_process,
    }

    dataset_name = dataset_name_or_path.split("/")[-1]

    process_fn = process_fn_map.get(dataset_name.lower())

    dataset = process_fn(dataset, num_hf_proc_workers)

    return dataset


def main(
    process_all: bool = False,
    upload: bool = False,
    process_dataset_ids: List[str] = None,
):
    DATASETS_DIR = os.environ.get("DATASETS_DIR", None)

    if not process_dataset_ids:
        dataset_ids = [
            "MatrixStudio/Codeforces-Python-Submissions",
            "BAAI/TACO",
            "codeparrot/apps",
            "deepmind/code_contests",
        ]

    else:
        dataset_ids = process_dataset_ids

    if process_all:
        for dataset_id in dataset_ids:
            d = f"{DATASETS_DIR}/{dataset_id}" if DATASETS_DIR else dataset_id
            dataset = process_code_dataset(d, num_hf_proc_workers=16)
            print(dataset)
            print(dataset[0])

            # push to HF
            d_name = d.split("/")[-1]
            org_name = "mlfoundations-dev"
            repo_id = f"{org_name}/{d_name}_processed"
            print(f"Pushing to {repo_id}")
            dataset.push_to_hub(
                repo_id,
            )
            dataset = dataset.cast_column("difficulty", datasets.Value("string"))

            print(f"Pushed to https://huggingface.co/datasets/{repo_id}")

    if upload:
        repo_id_list = [
            f"mlfoundations-dev/{d.split('/')[-1]}_processed" for d in dataset_ids
        ]

        code_datasets = {
            repo_id.split("/")[-1].replace("_processed", ""): datasets.load_dataset(
                repo_id, split="train"
            )
            for repo_id in repo_id_list
        }

        code_stratos_scale = combine_code_datasets(code_datasets)
        code_stratos_scale.push_to_hub(
            "mlfoundations-dev/code_stratos_scale_pre_decontamination"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--process_all",
        action="store_true",
        help="Process all datasetsa dn upload separetely.",
    )
    parser.add_argument(
        "--upload", action="store_true", help="Upload combined dataset."
    )
    parser.add_argument(
        "--process_dataset_ids", nargs="+", help="Process specific dataset ids."
    )

    args = parser.parse_args()

    main(
        process_all=args.process_all,
        upload=args.upload,
        process_dataset_ids=args.process_dataset_ids,
    )

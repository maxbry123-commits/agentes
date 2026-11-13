#!/usr/bin/env python3
"""Build the bounded Batch C TaskTrove repairs without remote mutations."""

from __future__ import annotations

import argparse
import gc
import gzip
import hashlib
import importlib.util
import io
import json
import os
import re
import resource
import subprocess
import sys
import tarfile
import tempfile
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from types import ModuleType
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
from harbor.models.task.config import TaskConfig

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

BATCH_SIZE = 32
MIN_TASKS = 300
TULU_INPUT = "laion__tulu3-sft-personas-math-sandboxes-verified-v2"
TULU_OUTPUT = "laion__tulu3-sft-personas-math-sandboxes-verified-v3"
TASKTROVE_V4_REVISION = "81820c33ba26d705b9ea7ebac2d090d70fac93f4"
TASK_SCHEMA = pa.schema(
    (pa.field("path", pa.string()), pa.field("task_binary", pa.binary()))
)
EXPECTED_RE = re.compile(r'^\s*expected_content\s*=\s*"(.*)"\s*$', re.MULTILINE)


def load_semantic_answer() -> ModuleType:
    path = (
        REPO_ROOT
        / "data"
        / "tulu-3-sft-personas-math-grade-filtered"
        / "semantic_answer.py"
    )
    spec = importlib.util.spec_from_file_location("tulu_semantic_answer", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SEMANTIC_ANSWER = load_semantic_answer()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def peak_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024


def deterministic_archive(files: Mapping[str, bytes], executable: set[str]) -> bytes:
    output = io.BytesIO()
    with gzip.GzipFile(fileobj=output, mode="wb", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w") as archive:
            directories = sorted(
                {
                    str(parent)
                    for name in files
                    for parent in Path(name).parents
                    if str(parent) != "."
                }
            )
            for directory in directories:
                info = tarfile.TarInfo(directory)
                info.type = tarfile.DIRTYPE
                info.mode = 0o755
                info.mtime = 0
                archive.addfile(info)
            for name, content in sorted(files.items()):
                info = tarfile.TarInfo(name)
                info.size = len(content)
                info.mode = 0o755 if name in executable else 0o644
                info.mtime = 0
                archive.addfile(info, io.BytesIO(content))
    return output.getvalue()


def archive_files(task_binary: bytes) -> tuple[dict[str, bytes], set[str]]:
    files: dict[str, bytes] = {}
    executable: set[str] = set()
    names: set[str] = set()
    with tarfile.open(fileobj=io.BytesIO(task_binary), mode="r:gz") as archive:
        for member in archive.getmembers():
            path = Path(member.name)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"Unsafe archive path: {member.name}")
            if member.name in names:
                raise ValueError(f"Duplicate archive member: {member.name}")
            names.add(member.name)
            if member.issym() or member.islnk():
                raise ValueError(f"Archive links are not allowed: {member.name}")
            if not (member.isfile() or member.isdir()):
                raise ValueError(f"Unsupported archive member: {member.name}")
            if not member.isfile():
                continue
            extracted = archive.extractfile(member)
            if extracted is None:
                raise RuntimeError(f"Cannot read archive member {member.name}")
            files[member.name] = extracted.read()
            if member.mode & 0o111:
                executable.add(member.name)
    return files, executable


def write_parquet(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = pq.ParquetWriter(path, TASK_SCHEMA, compression="zstd")
    count = 0
    pending: list[dict[str, Any]] = []
    try:
        for row in rows:
            pending.append(row)
            if len(pending) == BATCH_SIZE:
                writer.write_table(
                    pa.Table.from_pylist(pending, schema=TASK_SCHEMA),
                    row_group_size=BATCH_SIZE,
                )
                count += len(pending)
                pending.clear()
        if pending:
            writer.write_table(
                pa.Table.from_pylist(pending, schema=TASK_SCHEMA),
                row_group_size=BATCH_SIZE,
            )
            count += len(pending)
    finally:
        writer.close()
    if count < MIN_TASKS:
        raise RuntimeError(
            f"Repair retained only {count} tasks; minimum is {MIN_TASKS}"
        )
    return count


def extract_expected(test_source: str) -> str:
    match = EXPECTED_RE.search(test_source)
    if not match:
        raise ValueError("Tulu verifier has no expected_content string")
    return match.group(1).replace('\\"', '"')


def tulu_rows(input_parquet: Path) -> Iterator[dict[str, Any]]:
    paths: set[str] = set()
    for batch in pq.ParquetFile(input_parquet).iter_batches(batch_size=BATCH_SIZE):
        for row in batch.to_pylist():
            if row["path"] in paths:
                raise ValueError(f"Duplicate dataset path: {row['path']}")
            paths.add(row["path"])
            files, executable = archive_files(row["task_binary"])
            instruction = files["instruction.md"].decode("utf-8")
            expected = extract_expected(files["tests/test_state.py"].decode("utf-8"))
            files["tests/test_state.py"] = SEMANTIC_ANSWER.render_test_state(
                expected, instruction
            ).encode()
            files["tests/test.sh"] = SEMANTIC_ANSWER.TEST_SH.encode()
            yield {
                "path": row["path"],
                "task_binary": deterministic_archive(
                    files, executable | {"tests/test.sh"}
                ),
            }


def validate_source_output(source: Path, output: Path) -> None:
    source_rows = pq.ParquetFile(source).iter_batches(batch_size=BATCH_SIZE)
    output_rows = pq.ParquetFile(output).iter_batches(batch_size=BATCH_SIZE)
    checked = 0
    test_sh: bytes | None = None
    for source_batch, output_batch in zip(source_rows, output_rows, strict=True):
        if source_batch.num_rows != output_batch.num_rows:
            raise ValueError("Tulu source/output batch-size mismatch")
        for source_row, output_row in zip(
            source_batch.to_pylist(), output_batch.to_pylist(), strict=True
        ):
            if source_row["path"] != output_row["path"]:
                raise ValueError("Tulu source/output path mismatch")
            source_files, _ = archive_files(source_row["task_binary"])
            output_files, _ = archive_files(output_row["task_binary"])
            if set(source_files) != set(output_files):
                raise ValueError(f"Tulu archive members changed: {source_row['path']}")
            for name, content in source_files.items():
                if name not in {"tests/test.sh", "tests/test_state.py"}:
                    if output_files[name] != content:
                        raise ValueError(
                            f"Unrelated Tulu member changed: {source_row['path']}/{name}"
                        )
            TaskConfig.model_validate_toml(output_files["task.toml"].decode())
            if test_sh is None:
                test_sh = output_files["tests/test.sh"]
                subprocess.run(["bash", "-n"], input=test_sh, check=True)
            elif output_files["tests/test.sh"] != test_sh:
                raise ValueError("Tulu output contains multiple verifier wrappers")
            checked += 1
    if checked != pq.ParquetFile(output).metadata.num_rows:
        raise ValueError("Tulu source/output row-count mismatch")


def tasktrove_v4_input(explicit_root: Path | None) -> Path:
    if explicit_root:
        return explicit_root / TULU_INPUT / "tasks.parquet"
    cached = (
        Path.home()
        / ".cache/huggingface/hub/datasets--open-thoughts--TaskTrove/snapshots"
        / TASKTROVE_V4_REVISION
        / TULU_INPUT
        / "tasks.parquet"
    )
    if not cached.is_file():
        raise FileNotFoundError(f"Exact TaskTrove v4 input is not cached: {cached}")
    return cached


def validate_tulu(path: Path) -> dict[str, int]:
    rows = 0
    embedded_compile_passes = 0
    oracle_passes = 0
    wrong_value_attempts = 0
    wrong_value_rejections = 0
    trailing_contradiction_attempts = 0
    trailing_contradiction_rejections = 0
    tuple_swap_attempts = 0
    tuple_swap_rejections = 0
    unit_mutation_attempts = 0
    unit_mutation_rejections = 0
    representative_source: str | None = None
    representative_expected: str | None = None
    for batch in pq.ParquetFile(path).iter_batches(batch_size=BATCH_SIZE):
        for row in batch.to_pylist():
            files, _ = archive_files(row["task_binary"])
            source = files["tests/test_state.py"].decode()
            compile(source, f"{row['path']}/tests/test_state.py", "exec")
            embedded_compile_passes += 1
            expected = re.search(r"^EXPECTED = (.*)$", source, re.MULTILINE)
            instruction = re.search(r"^INSTRUCTION = (.*)$", source, re.MULTILINE)
            if not expected or not instruction:
                raise AssertionError(row["path"])
            expected_value = json.loads(expected.group(1))
            instruction_value = json.loads(instruction.group(1))
            if representative_source is None:
                representative_source = source
                representative_expected = expected_value
            assert SEMANTIC_ANSWER.answer_matches(
                expected_value, expected_value, instruction_value
            )
            oracle_passes += 1

            number_matches = list(SEMANTIC_ANSWER.NUMBER_RE.finditer(expected_value))
            for match_index, match in enumerate(number_matches):
                wrong_value_attempts += 1
                replacement = str(900_000_000 + rows * 100 + match_index)
                mutated = (
                    expected_value[: match.start()]
                    + replacement
                    + expected_value[match.end() :]
                )
                if not SEMANTIC_ANSWER.answer_matches(
                    expected_value, mutated, instruction_value
                ):
                    wrong_value_rejections += 1

            if number_matches:
                contradiction = str(800_000_000 + rows)
                trailing = f"{expected_value}\nContradictory value: {contradiction}"
                trailing_contradiction_attempts += 1
                if not SEMANTIC_ANSWER.answer_matches(
                    expected_value, trailing, instruction_value
                ):
                    trailing_contradiction_rejections += 1

                last_match = number_matches[-1]
                mutated_unit = (
                    expected_value[: last_match.end()]
                    + " furlongs "
                    + expected_value[last_match.end() :]
                )
                unit_mutation_attempts += 1
                if not SEMANTIC_ANSWER.answer_matches(
                    expected_value, mutated_unit, instruction_value
                ):
                    unit_mutation_rejections += 1
            else:
                trailing_contradiction_attempts += 1
                trailing = f"{expected_value}\nContradictory answer"
                if not SEMANTIC_ANSWER.answer_matches(
                    expected_value, trailing, instruction_value
                ):
                    trailing_contradiction_rejections += 1

            for first_index, first in enumerate(number_matches):
                first_value = SEMANTIC_ANSWER.numeric_value(first.group())
                for second in number_matches[first_index + 1 :]:
                    second_value = SEMANTIC_ANSWER.numeric_value(second.group())
                    if first_value == second_value:
                        continue
                    swapped = (
                        expected_value[: first.start()]
                        + second.group()
                        + expected_value[first.end() : second.start()]
                        + first.group()
                        + expected_value[second.end() :]
                    )
                    tuple_swap_attempts += 1
                    if not SEMANTIC_ANSWER.answer_matches(
                        expected_value, swapped, instruction_value
                    ):
                        tuple_swap_rejections += 1
            rows += 1

    labeled_expected = "(Aelira:5,Brenna:1,Caelith:3)"
    labeled_swapped = "(Aelira:1,Brenna:5,Caelith:3)"
    tuple_swap_attempts += 1
    if not SEMANTIC_ANSWER.answer_matches(
        labeled_expected, labeled_swapped, "Assign values to each named person"
    ):
        tuple_swap_rejections += 1
    if wrong_value_attempts != wrong_value_rejections:
        raise AssertionError("A wrong-value mutation passed the Tulu verifier")
    if trailing_contradiction_attempts != trailing_contradiction_rejections:
        raise AssertionError("A trailing contradiction passed the Tulu verifier")
    if tuple_swap_attempts != tuple_swap_rejections:
        raise AssertionError("A swapped numeric association passed the Tulu verifier")
    if unit_mutation_attempts != unit_mutation_rejections:
        raise AssertionError("A wrong-unit mutation passed the Tulu verifier")
    if representative_source is None or representative_expected is None:
        raise AssertionError("Tulu output has no verifier source")
    runner_validation = validate_tulu_runner(
        representative_source, representative_expected
    )
    return {
        "embedded_compile_passes": embedded_compile_passes,
        "oracle_passes": oracle_passes,
        "rows": rows,
        "trailing_contradiction_attempts": trailing_contradiction_attempts,
        "trailing_contradiction_rejections": trailing_contradiction_rejections,
        "tuple_swap_attempts": tuple_swap_attempts,
        "tuple_swap_rejections": tuple_swap_rejections,
        "unit_mutation_attempts": unit_mutation_attempts,
        "unit_mutation_rejections": unit_mutation_rejections,
        "wrong_value_attempts": wrong_value_attempts,
        "wrong_value_rejections": wrong_value_rejections,
        **runner_validation,
    }


def run_tulu_runner(
    test_source: str | None, answer: str | None
) -> tuple[int, str | None]:
    with tempfile.TemporaryDirectory(
        prefix="tasktrove-tulu-runner-"
    ) as temporary_directory:
        root = Path(temporary_directory)
        logs = root / "logs"
        test_path = root / "test_state.py"
        answer_path = root / "answer.txt"
        test_sh = root / "test.sh"
        test_sh.write_text(SEMANTIC_ANSWER.TEST_SH, encoding="utf-8")
        if test_source is not None:
            test_path.write_text(test_source, encoding="utf-8")
        if answer is not None:
            answer_path.write_text(answer, encoding="utf-8")
        environment = {
            **os.environ,
            "TULU_ANSWER_PATH": str(answer_path),
            "TULU_LOGS_DIR": str(logs),
            "TULU_TEST_PATH": str(test_path),
        }
        result = subprocess.run(
            ["bash", str(test_sh)],
            capture_output=True,
            check=False,
            env=environment,
            text=True,
        )
        reward_path = logs / "reward.txt"
        reward = (
            reward_path.read_text(encoding="utf-8").strip()
            if reward_path.is_file()
            else None
        )
        return result.returncode, reward


def validate_tulu_runner(test_source: str, expected: str) -> dict[str, int]:
    scoreable_cases = {
        "missing_answer": (None, "0"),
        "empty_answer": ("", "0"),
        "wrong_answer": ("definitely not the expected answer", "0"),
        "oracle_answer": (expected, "1"),
    }
    scoreable_passes = 0
    for answer, wanted_reward in scoreable_cases.values():
        returncode, reward = run_tulu_runner(test_source, answer)
        if returncode != 0 or reward != wanted_reward:
            raise AssertionError(
                f"Direct Tulu runner classification failed: returncode={returncode}, reward={reward}"
            )
        scoreable_passes += 1

    injected_matcher_error = test_source.replace(
        'if __name__ == "__main__":',
        'def answer_matches(expected, actual, instruction):\n    raise RuntimeError("injected matcher failure")\n\n\nif __name__ == "__main__":',
    )
    infrastructure_cases = {
        "missing_verifier": None,
        "corrupt_verifier": "this is not valid Python !!!\n",
        "matcher_exception": injected_matcher_error,
    }
    infrastructure_passes = 0
    for source in infrastructure_cases.values():
        returncode, reward = run_tulu_runner(source, expected)
        if returncode == 0 or reward is not None:
            raise AssertionError(
                f"Tulu verifier infrastructure failure was masked: returncode={returncode}, reward={reward}"
            )
        infrastructure_passes += 1
    return {
        "direct_runner_infrastructure_cases": len(infrastructure_cases),
        "direct_runner_infrastructure_passes": infrastructure_passes,
        "direct_runner_scoreable_cases": len(scoreable_cases),
        "direct_runner_scoreable_passes": scoreable_passes,
    }


def build(args: argparse.Namespace) -> dict[str, Any]:
    args.output_root.mkdir(parents=True, exist_ok=False)
    report: dict[str, Any] = {"batch_size": BATCH_SIZE, "outputs": {}}
    source = tasktrove_v4_input(args.tasktrove_v4_root)
    output = args.output_root / TULU_OUTPUT / "tasks.parquet"
    count = write_parquet(output, tulu_rows(source))
    validate_source_output(source, output)
    report["outputs"][TULU_OUTPUT] = {
        "rows": count,
        "sha256": sha256_file(output),
        "validation": validate_tulu(output),
    }
    gc.collect()
    report["peak_rss_bytes"] = peak_rss_bytes()
    manifest = args.output_root / "batch-c-manifest.json"
    manifest.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--tasktrove-v4-root", type=Path)
    return parser.parse_args()


def main() -> None:
    print(json.dumps(build(parse_args()), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

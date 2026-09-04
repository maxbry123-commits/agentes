#!/usr/bin/env python3
"""Build the bounded deterministic-verifier repairs from TaskTrove v4.0."""

from __future__ import annotations

import argparse
import gc
import gzip
import hashlib
import io
import json
import os
import re
import resource
import shutil
import subprocess
import sys
import tarfile
import tempfile
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import duckdb
from harbor.models.task.config import TaskConfig
from huggingface_hub import hf_hub_download

REPO_ID = "open-thoughts/TaskTrove"
TASKTROVE_V4_REVISION = "81820c33ba26d705b9ea7ebac2d090d70fac93f4"
BATCH_SIZE = 32
MIN_TASKS = 300
MAX_RSS_BYTES = 1024**3
MCQA_SHARD_ROWS = 8192
TASK_SCHEMA = pa.schema(
    (pa.field("path", pa.string()), pa.field("task_binary", pa.binary()))
)


@dataclass(frozen=True)
class DatasetSpec:
    source: str
    target: str
    family: str


SPECS = (
    DatasetSpec(
        "laion__nemotron-gym-agentic-swe-pivot-v2",
        "laion__nemotron-gym-agentic-swe-pivot-v3",
        "swe_tool_call",
    ),
    DatasetSpec(
        "laion__nemotron-gym-arc-agi-python-inductive",
        "laion__nemotron-gym-arc-agi-python-inductive-v2",
        "grid_transform",
    ),
    DatasetSpec(
        "laion__nemotron-gym-arc-agi-transductive-v2",
        "laion__nemotron-gym-arc-agi-transductive-v3",
        "grid_match",
    ),
    DatasetSpec(
        "laion__nemotron-gym-competitive-coding",
        "laion__nemotron-gym-competitive-coding-v2",
        "stdio_diff",
    ),
    DatasetSpec(
        "laion__nemotron-gym-instruction-following-calendar",
        "laion__nemotron-gym-instruction-following-calendar-v2",
        "calendar",
    ),
    DatasetSpec(
        "laion__nemotron-gym-instruction-following-freeform",
        "laion__nemotron-gym-instruction-following-freeform-v2",
        "regex_count",
    ),
    DatasetSpec(
        "laion__nemotron-gym-instruction-following-structured-v2",
        "laion__nemotron-gym-instruction-following-structured-v3",
        "structured",
    ),
    DatasetSpec(
        "laion__nemotron-gym-knowledge-mcqa",
        "laion__nemotron-gym-knowledge-mcqa-v2",
        "mcqa",
    ),
    DatasetSpec(
        "laion__nemotron-gym-math-advanced-calculations-v3",
        "laion__nemotron-gym-math-advanced-calculations-v4",
        "math_boxed",
    ),
    DatasetSpec(
        "laion__nemotron-gym-reasoning-gym",
        "laion__nemotron-gym-reasoning-gym-v2",
        "reasoning_gym",
    ),
)

SOURCE_SHA256 = {
    "laion__nemotron-gym-agentic-swe-pivot-v2": "7343310db12b7d3a3649ce0c8b7bbcd300d731e25331ea542de6f4dfc9c996fd",
    "laion__nemotron-gym-arc-agi-python-inductive": "a0b4f47b9c807732d3fad2382f20739064e0334b22e59a52250ffc71207347c2",
    "laion__nemotron-gym-arc-agi-transductive-v2": "a2e800d6e3dda51a467f65237fa537f6ca15602dee1f9ccfed34a4a9743e3f55",
    "laion__nemotron-gym-competitive-coding": "ea3786baa6b30bf086144b0d92579e5e8a0df103120da5837cba731d70e9aba4",
    "laion__nemotron-gym-instruction-following-calendar": "aef469c321980413a9c3c3638dd1e81086758fd8e077b67af2aa14d93d8273f6",
    "laion__nemotron-gym-instruction-following-freeform": "e40201256cc413688fc6564a312200d24d5100403c89bfa93b328acf65eb8bac",
    "laion__nemotron-gym-instruction-following-structured-v2": "48ad790b2e0904c382ce297640b7ec7a659690ea8e76d990cbbbbd49eb79e587",
    "laion__nemotron-gym-knowledge-mcqa": "8af7008b187c08341f9b58657a46509b64627d289fafdf1f89221c3139779076",
    "laion__nemotron-gym-math-advanced-calculations-v3": "784b1ab5b76f640bb5bcc1c254b20742d7fb20fa9fc41b954eb1f348f5dfc624",
    "laion__nemotron-gym-reasoning-gym": "ea67aea7fb0d538deb24f3e966d2c9dc9beae69879e1a30aabf0129f448a7af1",
}

TEST_SH = r"""#!/bin/bash
set -euo pipefail

APP_DIR=${APP_DIR:-/app}
TESTS_DIR=${TESTS_DIR:-/tests}
LOGS_DIR=${LOGS_DIR:-/logs/verifier}
REWARD="$LOGS_DIR/reward.txt"
mkdir -p "$LOGS_DIR"
rm -f "$REWARD"

# Dataset package validation is infrastructure. Any failure leaves no reward.
python3 "$TESTS_DIR/validate_verifier_data.py" "$TESTS_DIR/verifier_data.json" \
  >> "$LOGS_DIR/test-stdout.txt" 2>&1
python3 "$TESTS_DIR/verifier.py" >> "$LOGS_DIR/test-stdout.txt" 2>&1

test -s "$REWARD"
grep -Eq '^(0|1)$' "$REWARD"
"""

VALIDATOR_TEMPLATE = r"""#!/usr/bin/env python3
import json
import pathlib
import re
import sys

FAMILY = __FAMILY__


def require(condition, message):
    if not condition:
        raise ValueError(message)


data = json.loads(pathlib.Path(sys.argv[1]).read_text())
require(isinstance(data, dict), "verifier data must be an object")
if FAMILY == "swe_tool_call":
    value = data.get("expected")
    require(isinstance(value, list) and value, "expected calls missing")
    require(all(isinstance(call, dict) and isinstance(call.get("name"), str) for call in value), "invalid expected call")
elif FAMILY == "grid_transform":
    value = data.get("test_cases")
    require(isinstance(value, list) and value, "test cases missing")
    require(all(isinstance(case, dict) and isinstance(case.get("input"), list) and isinstance(case.get("output"), list) for case in value), "invalid test case")
elif FAMILY == "grid_match":
    value = data.get("expected_output")
    require(isinstance(value, list) and value and all(isinstance(row, list) for row in value), "invalid expected grid")
elif FAMILY == "stdio_diff":
    inputs, outputs = data.get("inputs"), data.get("outputs")
    require(isinstance(inputs, list) and inputs and isinstance(outputs, list) and len(inputs) == len(outputs), "invalid stdin/stdout tests")
    require(all(isinstance(value, str) for value in inputs + outputs), "stdin/stdout tests must be strings")
elif FAMILY == "calendar":
    events = data.get("expected_events")
    require(isinstance(events, dict) and events, "calendar events missing")
    require(all(isinstance(event, dict) and isinstance(event.get("duration"), int) and isinstance(event.get("event_id"), int) and isinstance(event.get("min_time"), str) and isinstance(event.get("max_time"), str) and (event.get("constraint") is None or isinstance(event.get("constraint"), str)) for event in events.values()), "invalid calendar event")
elif FAMILY == "regex_count":
    regexes = data.get("verify_regex")
    require(isinstance(regexes, list) and regexes and all(isinstance(value, str) for value in regexes), "regex list missing")
    require(isinstance(data.get("verify_min_matches"), int) and data["verify_min_matches"] >= 0, "invalid match threshold")
    for pattern in regexes:
        re.compile(pattern)
elif FAMILY == "structured":
    require(isinstance(data.get("schema"), dict), "schema missing")
    require(data.get("schema_type") in {"json", "yaml", "toml", "xml", "csv"}, "invalid schema type")
elif FAMILY == "mcqa":
    require(isinstance(data.get("expected_answer"), str) and data["expected_answer"], "expected answer missing")
    require(isinstance(data.get("output_regex", ""), str), "output regex invalid")
    re.compile(data.get("output_regex") or r"Answer\s*:\s*(?!Answer)\s*([A-Za-z0-9])\s*")
elif FAMILY == "math_boxed":
    boxed = isinstance(data.get("expected_answer"), str)
    numeric = isinstance(data.get("expected_value"), (int, float))
    require(boxed or numeric, "math expectation invalid")
    if numeric:
        require(isinstance(data.get("tolerance_abs", 1e-6), (int, float)), "absolute tolerance invalid")
        require(isinstance(data.get("tolerance_rel", 1e-6), (int, float)), "relative tolerance invalid")
        require(data.get("tolerance_abs", 1e-6) >= 0, "absolute tolerance negative")
        require(data.get("tolerance_rel", 1e-6) >= 0, "relative tolerance negative")
elif FAMILY == "reasoning_gym":
    require(isinstance(data.get("answer"), str), "answer invalid")
    metadata = data.get("metadata")
    require(isinstance(metadata, dict) and isinstance(metadata.get("source_dataset"), str) and metadata["source_dataset"], "Reasoning Gym source missing")
else:
    raise ValueError(f"unknown verifier family: {FAMILY}")
"""

FOOTER_RE = re.compile(
    r'if __name__ == ["\']__main__["\']:\n'
    r"    score = 0\n"
    r"    try:\n"
    r"        score = main\(\)\n"
    r"    except Exception as e:\n"
    r'        print\(f"verifier exception: \{e\}", file=sys\.stderr\)\n'
    r"        score = 0\n"
    r"    _write_reward\(score\)\n?$",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def peak_rss_bytes() -> int:
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return rss if sys.platform == "darwin" else rss * 1024


def archive(task_binary: bytes) -> tuple[list[tarfile.TarInfo], dict[str, bytes]]:
    members: list[tarfile.TarInfo] = []
    files: dict[str, bytes] = {}
    names: set[str] = set()
    with tarfile.open(fileobj=io.BytesIO(task_binary), mode="r:*") as source:
        for member in source.getmembers():
            if (
                member.name.startswith("/")
                or ".." in Path(member.name).parts
                or member.issym()
                or member.islnk()
            ):
                raise ValueError(f"unsafe archive member: {member.name}")
            if member.name in names:
                raise ValueError(f"duplicate archive member: {member.name}")
            names.add(member.name)
            members.append(member)
            if member.isfile():
                handle = source.extractfile(member)
                if handle is None:
                    raise ValueError(f"cannot read archive member: {member.name}")
                files[member.name] = handle.read()
    return members, files


def write_archive(members: list[tarfile.TarInfo], files: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    existing = {member.name for member in members}
    with gzip.GzipFile(fileobj=output, mode="wb", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w") as target:
            for original in members:
                member = tarfile.TarInfo(original.name)
                for attribute in (
                    "mode",
                    "uid",
                    "gid",
                    "mtime",
                    "type",
                    "linkname",
                    "uname",
                    "gname",
                    "devmajor",
                    "devminor",
                    "pax_headers",
                ):
                    setattr(member, attribute, getattr(original, attribute))
                content = files.get(member.name, b"") if original.isfile() else None
                member.size = len(content) if content is not None else original.size
                target.addfile(
                    member, io.BytesIO(content) if content is not None else None
                )
            for name in sorted(set(files) - existing):
                content = files[name]
                member = tarfile.TarInfo(name)
                member.size = len(content)
                member.mode = (
                    0o755 if name.endswith(".py") or name.endswith(".sh") else 0o644
                )
                member.mtime = 0
                target.addfile(member, io.BytesIO(content))
    return output.getvalue()


def patch_verifier(source: str, family: str) -> str:
    source, count = FOOTER_RE.subn(
        'if __name__ == "__main__":\n    _write_reward(main())\n', source
    )
    if count != 1:
        raise ValueError(f"{family}: unexpected verifier footer")
    if family in {"grid_transform", "stdio_diff"}:
        source, timeout_count = re.subn(
            r"        except subprocess\.TimeoutExpired:\n(?:            .*\n)+?            (?:continue|return 0)\n",
            "        except subprocess.TimeoutExpired:\n            raise\n",
            source,
        )
        source, execution_count = re.subn(
            r"        except Exception as e:\n(?:            .*\n)+?            (?:continue|return 0)\n",
            "        except Exception:\n            raise\n",
            source,
        )
        if timeout_count != 1 or execution_count != 1:
            raise ValueError(
                f"{family}: expected one timeout and one execution-error substitution, "
                f"got {timeout_count} and {execution_count}"
            )
    if family == "structured":
        expected_yaml_count = int("import yaml" in source)
        expected_tomli_count = int("import tomli as tomllib" in source)
        source, jsonschema_count = re.subn(
            r'    except ImportError as e:(?:  # pragma: no cover)?\n        print\(f"jsonschema unavailable: \{e\}", file=sys\.stderr\)\n        return 0\n',
            "    except ImportError:  # pragma: no cover\n        raise\n",
            source,
        )
        source, yaml_count = re.subn(
            r'    except ImportError as e:\n        print\(f"pyyaml unavailable: \{e\}", file=sys\.stderr\)\n        return 0\n',
            "    except ImportError:\n        raise\n",
            source,
        )
        source, tomli_count = re.subn(
            r'        except ImportError as e:\n            print\(f"tomllib/tomli unavailable: \{e\}", file=sys\.stderr\)\n            return 0\n',
            "        except ImportError:\n            raise\n",
            source,
        )
        if (jsonschema_count, yaml_count, tomli_count) != (
            1,
            expected_yaml_count,
            expected_tomli_count,
        ):
            raise ValueError(
                f"structured: dependency substitutions drifted: "
                f"{jsonschema_count}, {yaml_count}, {tomli_count}"
            )
    if family == "math_boxed":
        expected_dependency_count = int("sympy unavailable" in source)
        source, dependency_count = re.subn(
            r'    except Exception as e:\n        print\(f"sympy unavailable \(\{e\}\); falling back to string compare only"\)\n        return 0\n',
            "    except ImportError:\n        raise\n",
            source,
        )
        if dependency_count != expected_dependency_count:
            raise ValueError(
                "math_boxed: dependency substitution drifted: "
                f"expected {expected_dependency_count}, got {dependency_count}"
            )
    if family == "reasoning_gym":
        source, import_count = re.subn(
            re.escape(
                "    except ImportError:\n        return None\n",
            ),
            "    except ImportError:\n        raise\n",
            source,
        )
        source, factory_count = re.subn(
            r'        except Exception as e:\n            print\(f"reasoning_gym\.[^\n]+\n            return None\n',
            "        except Exception:\n            raise\n",
            source,
        )
        source, scorer_count = re.subn(
            r'    except Exception as e:\n        print\(f"score_fn call failed: \{e\}"\)\n        return None\n',
            "    except Exception:\n        raise\n",
            source,
        )
        source, api_count = re.subn(
            r'    else:\n        print\("reasoning_gym has neither get_score_answer_fn nor get_scorer"\)\n        return None\n',
            '    else:\n        raise RuntimeError("reasoning_gym has no supported scorer API")\n',
            source,
        )
        source, result_count = re.subn(
            r"    return None\n\n\ndef main\(\) -> int:",
            '    raise TypeError("Reasoning Gym scorer returned a non-numeric result")\n\n\ndef main() -> int:',
            source,
        )
        if (import_count, factory_count, scorer_count, api_count, result_count) != (
            1,
            2,
            1,
            1,
            1,
        ):
            raise ValueError(
                "reasoning_gym: internal fallback substitutions drifted: "
                f"{import_count}, {factory_count}, {scorer_count}, "
                f"{api_count}, {result_count}"
            )
    compile(source, f"{family}/verifier.py", "exec")
    return source


def validate_verifier_data(content: bytes, family: str) -> None:
    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError(f"{family}: verifier data must be an object")
    if family == "swe_tool_call":
        expected = data.get("expected")
        valid = (
            isinstance(expected, list)
            and bool(expected)
            and all(
                isinstance(call, dict) and isinstance(call.get("name"), str)
                for call in expected
            )
        )
    elif family == "grid_transform":
        cases = data.get("test_cases")
        valid = (
            isinstance(cases, list)
            and bool(cases)
            and all(
                isinstance(case, dict)
                and isinstance(case.get("input"), list)
                and isinstance(case.get("output"), list)
                for case in cases
            )
        )
    elif family == "grid_match":
        expected = data.get("expected_output")
        valid = (
            isinstance(expected, list)
            and bool(expected)
            and all(isinstance(row, list) for row in expected)
        )
    elif family == "stdio_diff":
        inputs, outputs = data.get("inputs"), data.get("outputs")
        valid = (
            isinstance(inputs, list)
            and bool(inputs)
            and isinstance(outputs, list)
            and len(inputs) == len(outputs)
            and all(isinstance(value, str) for value in inputs + outputs)
        )
    elif family == "calendar":
        events = data.get("expected_events")
        valid = (
            isinstance(events, dict)
            and bool(events)
            and all(
                isinstance(event, dict)
                and isinstance(event.get("duration"), int)
                and isinstance(event.get("event_id"), int)
                and isinstance(event.get("min_time"), str)
                and isinstance(event.get("max_time"), str)
                and (
                    event.get("constraint") is None
                    or isinstance(event.get("constraint"), str)
                )
                for event in events.values()
            )
        )
    elif family == "regex_count":
        regexes = data.get("verify_regex")
        valid = (
            isinstance(regexes, list)
            and bool(regexes)
            and all(isinstance(value, str) for value in regexes)
            and isinstance(data.get("verify_min_matches"), int)
            and data["verify_min_matches"] >= 0
        )
        if valid:
            for pattern in regexes:
                re.compile(pattern)
    elif family == "structured":
        valid = isinstance(data.get("schema"), dict) and data.get("schema_type") in {
            "json",
            "yaml",
            "toml",
            "xml",
            "csv",
        }
    elif family == "mcqa":
        valid = (
            isinstance(data.get("expected_answer"), str)
            and bool(data["expected_answer"])
            and isinstance(data.get("output_regex", ""), str)
        )
        if valid:
            re.compile(
                data.get("output_regex")
                or r"Answer\s*:\s*(?!Answer)\s*([A-Za-z0-9])\s*"
            )
    elif family == "math_boxed":
        boxed = isinstance(data.get("expected_answer"), str)
        numeric = isinstance(data.get("expected_value"), (int, float))
        valid = boxed or (
            numeric
            and isinstance(data.get("tolerance_abs", 1e-6), (int, float))
            and isinstance(data.get("tolerance_rel", 1e-6), (int, float))
            and data.get("tolerance_abs", 1e-6) >= 0
            and data.get("tolerance_rel", 1e-6) >= 0
        )
    elif family == "reasoning_gym":
        metadata = data.get("metadata")
        valid = (
            isinstance(data.get("answer"), str)
            and isinstance(metadata, dict)
            and isinstance(metadata.get("source_dataset"), str)
            and bool(metadata["source_dataset"])
        )
    else:
        raise ValueError(f"unknown verifier family: {family}")
    if not valid:
        raise ValueError(f"{family}: invalid verifier data")


def patched_task(task_binary: bytes, spec: DatasetSpec) -> tuple[bytes, set[str]]:
    members, files = archive(task_binary)
    validate_verifier_data(files["tests/verifier_data.json"], spec.family)
    TaskConfig.model_validate_toml(files["task.toml"].decode())
    original = dict(files)
    files["tests/test.sh"] = TEST_SH.encode()
    files["tests/verifier.py"] = patch_verifier(
        files["tests/verifier.py"].decode(), spec.family
    ).encode()
    files["tests/validate_verifier_data.py"] = VALIDATOR_TEMPLATE.replace(
        "__FAMILY__", repr(spec.family)
    ).encode()
    changed = {
        name
        for name in set(original) | set(files)
        if original.get(name) != files.get(name)
    }
    allowed = {"tests/test.sh", "tests/verifier.py", "tests/validate_verifier_data.py"}
    if changed != allowed:
        raise ValueError(f"{spec.source}: unexpected changed members: {changed}")
    return write_archive(members, files), changed


def source_path(stage: Path, spec: DatasetSpec, revision: str) -> Path:
    local = stage / "sources" / spec.source / "tasks.parquet"
    if local.is_file():
        return local
    return Path(
        hf_hub_download(
            REPO_ID,
            f"{spec.source}/tasks.parquet",
            repo_type="dataset",
            revision=revision,
            local_dir=stage / "sources",
        )
    )


def rows(path: Path) -> Iterator[tuple[str, bytes]]:
    if path.parent.name == "laion__nemotron-gym-knowledge-mcqa":
        temporary = path.parent / ".duckdb-spill"
        temporary.mkdir(exist_ok=True)
        connection = duckdb.connect(
            config={
                "threads": "1",
                "memory_limit": "256MB",
                "temp_directory": str(temporary),
                "preserve_insertion_order": "true",
            }
        )
        try:
            reader = connection.execute(
                "SELECT path, task_binary FROM read_parquet(?)", [str(path)]
            ).to_arrow_reader(batch_size=8)
            for batch in reader:
                for task_path, task_binary in zip(
                    batch.column(0).to_pylist(),
                    batch.column(1).to_pylist(),
                    strict=True,
                ):
                    yield task_path, task_binary
                del batch
        finally:
            connection.close()
        return
    parquet = pq.ParquetFile(path)
    if parquet.schema_arrow != TASK_SCHEMA:
        raise ValueError(f"unexpected schema: {path}")
    for batch in parquet.iter_batches(batch_size=BATCH_SIZE):
        for task_path, task_binary in zip(
            batch.column(0).to_pylist(), batch.column(1).to_pylist(), strict=True
        ):
            yield task_path, task_binary
        del batch
        gc.collect()
        pa.default_memory_pool().release_unused()


def mcqa_rows(path: Path, offset: int, limit: int) -> Iterator[tuple[str, bytes]]:
    temporary = path.parent / ".duckdb-spill"
    temporary.mkdir(exist_ok=True)
    connection = duckdb.connect(
        config={
            "threads": "1",
            "memory_limit": "256MB",
            "temp_directory": str(temporary),
            "preserve_insertion_order": "true",
        }
    )
    try:
        reader = connection.execute(
            "SELECT path, task_binary FROM read_parquet(?) LIMIT ? OFFSET ?",
            [str(path), limit, offset],
        ).to_arrow_reader(batch_size=8)
        for batch in reader:
            for task_path, task_binary in zip(
                batch.column(0).to_pylist(),
                batch.column(1).to_pylist(),
                strict=True,
            ):
                yield task_path, task_binary
    finally:
        connection.close()


def build_dataset(stage: Path, spec: DatasetSpec, revision: str) -> dict[str, object]:
    if spec.family == "mcqa":
        return build_mcqa_dataset(stage, spec, revision)
    source = source_path(stage, spec, revision)
    output = stage / "datasets" / spec.target / "tasks.parquet"
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = pq.ParquetWriter(output, TASK_SCHEMA, compression="zstd")
    count = 0
    paths: set[str] = set()
    pending_paths: list[str] = []
    pending_tasks: list[bytes] = []
    try:
        for task_path, task_binary in rows(source):
            if task_path in paths:
                raise ValueError(f"duplicate task path: {task_path}")
            paths.add(task_path)
            repaired, _ = patched_task(task_binary, spec)
            pending_paths.append(task_path)
            pending_tasks.append(repaired)
            count += 1
            if len(pending_paths) == BATCH_SIZE:
                writer.write_batch(
                    pa.record_batch(
                        [pa.array(pending_paths), pa.array(pending_tasks)],
                        schema=TASK_SCHEMA,
                    )
                )
                pending_paths.clear()
                pending_tasks.clear()
                gc.collect()
                pa.default_memory_pool().release_unused()
        if pending_paths:
            writer.write_batch(
                pa.record_batch(
                    [pa.array(pending_paths), pa.array(pending_tasks)],
                    schema=TASK_SCHEMA,
                )
            )
    finally:
        writer.close()
    if count < MIN_TASKS:
        raise ValueError(
            f"standing-order minimum violated: {spec.target} has {count} tasks"
        )
    source_hash = sha256_file(source)
    if source_hash != SOURCE_SHA256[spec.source]:
        raise ValueError(f"source hash mismatch for exact v4 dataset: {spec.source}")
    return {
        "source_dataset": spec.source,
        "output_dataset": spec.target,
        "family": spec.family,
        "rows": count,
        "source_sha256": source_hash,
        "output_sha256": sha256_file(output),
        "output": str(output.relative_to(stage)),
    }


def build_mcqa_dataset(
    stage: Path, spec: DatasetSpec, revision: str
) -> dict[str, object]:
    source = source_path(stage, spec, revision)
    output = stage / "datasets" / spec.target / "tasks.parquet"
    output.parent.mkdir(parents=True, exist_ok=True)
    shards = stage / "mcqa-shards"
    count = pq.ParquetFile(source).metadata.num_rows
    shard_count = (count + MCQA_SHARD_ROWS - 1) // MCQA_SHARD_ROWS
    existing_shards = sorted(shards.glob("tasks-*.parquet")) if shards.exists() else []
    reusable = (
        len(existing_shards) == shard_count
        and sum(pq.ParquetFile(path).metadata.num_rows for path in existing_shards)
        == count
    )
    if shards.exists() and not reusable:
        shutil.rmtree(shards)
    shards.mkdir(exist_ok=True)

    built_rows = count if reusable else 0
    resource_file = shards / "resource.json"
    shard_peaks: list[int] = []
    if reusable and resource_file.is_file():
        shard_peaks.append(json.loads(resource_file.read_text())["max_peak_rss_bytes"])
    if not reusable:
        for shard_index in range(shard_count):
            completed = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--stage",
                    str(stage),
                    "--revision",
                    revision,
                    "--worker-mcqa-shard",
                    str(shard_index),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            payload = json.loads(completed.stdout)
            built_rows += payload["rows"]
            shard_peaks.append(payload["peak_rss_bytes"])
        resource_file.write_text(
            json.dumps({"max_peak_rss_bytes": max(shard_peaks)}, sort_keys=True) + "\n"
        )
    if not shard_peaks:
        raise ValueError("MCQA reusable shards are missing their resource measurement")

    if count < MIN_TASKS or built_rows != count:
        raise ValueError(
            f"standing-order minimum violated: {spec.target} has {count} tasks"
        )
    completed = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--stage",
            str(stage),
            "--revision",
            revision,
            "--worker-mcqa-merge",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    merge = json.loads(completed.stdout)
    shutil.rmtree(shards)
    source_hash = sha256_file(source)
    if source_hash != SOURCE_SHA256[spec.source]:
        raise ValueError(f"source hash mismatch for exact v4 dataset: {spec.source}")
    verification = duckdb.connect(
        config={
            "threads": "1",
            "memory_limit": "256MB",
            "temp_directory": str(stage / "duckdb-merge-spill"),
        }
    )
    try:
        output_rows, distinct_paths = verification.execute(
            "SELECT count(*), count(DISTINCT path) FROM read_parquet(?)", [str(output)]
        ).fetchone()
    finally:
        verification.close()
    if output_rows != count or distinct_paths != count:
        raise ValueError(f"MCQA merge row-count mismatch: {spec.target}")
    return {
        "source_dataset": spec.source,
        "output_dataset": spec.target,
        "family": spec.family,
        "rows": count,
        "source_sha256": source_hash,
        "output_sha256": sha256_file(output),
        "output": str(output.relative_to(stage)),
        "shards": shard_count,
        "max_shard_peak_rss_bytes": max(shard_peaks),
        "merge_process_peak_rss_bytes": merge["peak_rss_bytes"],
    }


def build_mcqa_merge(stage: Path) -> dict[str, int]:
    spec = next(spec for spec in SPECS if spec.family == "mcqa")
    output = stage / "datasets" / spec.target / "tasks.parquet"
    shard_paths = sorted(
        str(path) for path in (stage / "mcqa-shards").glob("tasks-*.parquet")
    )
    if not shard_paths:
        raise ValueError("MCQA merge has no input shards")
    temporary = stage / "duckdb-merge-spill"
    temporary.mkdir(exist_ok=True)
    connection = duckdb.connect(
        config={
            "threads": "1",
            "memory_limit": "320MB",
            "temp_directory": str(temporary),
            "preserve_insertion_order": "true",
        }
    )
    try:
        output.unlink(missing_ok=True)
        output_literal = str(output).replace("'", "''")
        connection.execute(
            f"COPY (SELECT path, task_binary FROM read_parquet(?)) "
            f"TO '{output_literal}' "
            "(FORMAT PARQUET, COMPRESSION ZSTD, ROW_GROUP_SIZE 8192)",
            [shard_paths],
        )
    finally:
        connection.close()
    rss = peak_rss_bytes()
    if rss >= MAX_RSS_BYTES:
        output.unlink(missing_ok=True)
        raise MemoryError(f"peak RSS {rss} exceeds {MAX_RSS_BYTES}")
    return {"peak_rss_bytes": rss}


def build_mcqa_shard(stage: Path, revision: str, shard_index: int) -> dict[str, int]:
    spec = next(spec for spec in SPECS if spec.family == "mcqa")
    source = source_path(stage, spec, revision)
    output = stage / "mcqa-shards" / f"tasks-{shard_index:05d}.parquet"
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = pq.ParquetWriter(output, TASK_SCHEMA, compression="zstd")
    offset = shard_index * MCQA_SHARD_ROWS
    pending_paths: list[str] = []
    pending_tasks: list[bytes] = []
    paths: set[str] = set()
    count = 0
    try:
        for task_path, task_binary in mcqa_rows(source, offset, MCQA_SHARD_ROWS):
            if task_path in paths:
                raise ValueError(f"duplicate task path in MCQA shard: {task_path}")
            paths.add(task_path)
            repaired, _ = patched_task(task_binary, spec)
            pending_paths.append(task_path)
            pending_tasks.append(repaired)
            count += 1
            if len(pending_paths) == BATCH_SIZE:
                writer.write_batch(
                    pa.record_batch(
                        [pa.array(pending_paths), pa.array(pending_tasks)],
                        schema=TASK_SCHEMA,
                    )
                )
                pending_paths.clear()
                pending_tasks.clear()
        if pending_paths:
            writer.write_batch(
                pa.record_batch(
                    [pa.array(pending_paths), pa.array(pending_tasks)],
                    schema=TASK_SCHEMA,
                )
            )
    finally:
        writer.close()
    rss = peak_rss_bytes()
    if rss >= MAX_RSS_BYTES:
        raise MemoryError(f"peak RSS {rss} exceeds {MAX_RSS_BYTES}")
    return {"rows": count, "peak_rss_bytes": rss}


def existing_result(
    stage: Path, spec: DatasetSpec, revision: str
) -> dict[str, object] | None:
    source = stage / "sources" / spec.source / "tasks.parquet"
    output = stage / "datasets" / spec.target / "tasks.parquet"
    if not source.is_file() or not output.is_file():
        return None
    source_hash = sha256_file(source)
    if source_hash != SOURCE_SHA256[spec.source]:
        raise ValueError(f"source hash mismatch for exact v4 dataset: {spec.source}")
    parquet = pq.ParquetFile(output)
    source_rows = pq.ParquetFile(source).metadata.num_rows
    if (
        parquet.schema_arrow != TASK_SCHEMA
        or parquet.metadata.num_rows < MIN_TASKS
        or parquet.metadata.num_rows != source_rows
    ):
        return None
    source_first = next(rows(source))[1]
    output_first = next(rows(output))[1]
    if patched_task(source_first, spec)[0] != output_first:
        return None
    return {
        "source_dataset": spec.source,
        "output_dataset": spec.target,
        "family": spec.family,
        "rows": parquet.metadata.num_rows,
        "source_sha256": source_hash,
        "output_sha256": sha256_file(output),
        "output": str(output.relative_to(stage)),
    }


def wrapper_contract_cases(files: dict[str, bytes], family: str) -> dict[str, bool]:
    validator = files["tests/validate_verifier_data.py"]
    valid_data = files["tests/verifier_data.json"]
    outcomes: dict[str, bool] = {}
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        tests = root / "tests"
        logs = root / "logs"
        app = root / "app"
        tests.mkdir()
        logs.mkdir()
        app.mkdir()
        (tests / "validate_verifier_data.py").write_bytes(validator)
        (tests / "verifier_data.json").write_bytes(valid_data)
        script = root / "test.sh"
        script.write_bytes(files["tests/test.sh"])
        script.chmod(0o755)
        env = os.environ | {
            "TESTS_DIR": str(tests),
            "LOGS_DIR": str(logs),
            "APP_DIR": str(app),
        }
        for name, body, expected_status, expected_reward in (
            (
                "positive",
                f'import pathlib\npathlib.Path({str(logs / "reward.txt")!r}).write_text("1")\n',
                0,
                "1",
            ),
            (
                "negative",
                f'import pathlib\npathlib.Path({str(logs / "reward.txt")!r}).write_text("0")\n',
                0,
                "0",
            ),
            ("infra", 'raise RuntimeError("injected verifier failure")\n', 1, None),
        ):
            (tests / "verifier.py").write_text(body)
            (logs / "reward.txt").unlink(missing_ok=True)
            result = subprocess.run(["bash", str(script)], env=env, capture_output=True)
            reward = (
                (logs / "reward.txt").read_text()
                if (logs / "reward.txt").exists()
                else None
            )
            outcomes[name] = (
                result.returncode == expected_status
                if expected_status == 0
                else result.returncode != 0
            ) and reward == expected_reward
        (tests / "verifier_data.json").write_text("{")
        (tests / "verifier.py").write_text(
            f'import pathlib\npathlib.Path({str(logs / "reward.txt")!r}).write_text("0")\n'
        )
        (logs / "reward.txt").unlink(missing_ok=True)
        result = subprocess.run(["bash", str(script)], env=env, capture_output=True)
        outcomes["corrupt_data"] = (
            result.returncode != 0 and not (logs / "reward.txt").exists()
        )
        (tests / "verifier_data.json").unlink()
        result = subprocess.run(["bash", str(script)], env=env, capture_output=True)
        outcomes["missing_data"] = (
            result.returncode != 0 and not (logs / "reward.txt").exists()
        )
        (tests / "verifier_data.json").write_bytes(valid_data)
        (tests / "verifier.py").write_text(
            "import tasktrove_injected_missing_dependency\n"
        )
        result = subprocess.run(["bash", str(script)], env=env, capture_output=True)
        outcomes["missing_dependency"] = (
            result.returncode != 0 and not (logs / "reward.txt").exists()
        )
    if not all(outcomes.values()):
        raise ValueError(f"{family}: wrapper contract failure: {outcomes}")
    return outcomes


def docker_case(
    image: str,
    tests: Path,
    app: Path,
    logs: Path,
    *,
    expect_reward: str | None,
) -> bool:
    result = subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "--volume",
            f"{tests}:/tests",
            "--volume",
            f"{app}:/app",
            "--volume",
            f"{logs}:/logs/verifier",
            image,
            "bash",
            "/tests/test.sh",
        ],
        capture_output=True,
    )
    reward_path = logs / "reward.txt"
    reward = reward_path.read_text() if reward_path.exists() else None
    expected_exit = (
        result.returncode == 0 if expect_reward is not None else result.returncode != 0
    )
    return expected_exit and reward == expect_reward


def exact_image_contracts(
    representatives: dict[str, dict[str, bytes]],
) -> dict[str, object]:
    dockerfiles: dict[str, bytes] = {}
    families_by_image: dict[str, list[str]] = {}
    for family, files in representatives.items():
        dockerfile = files["environment/Dockerfile"]
        digest = hashlib.sha256(dockerfile).hexdigest()
        dockerfiles[digest] = dockerfile
        families_by_image.setdefault(digest, []).append(family)
    if len(dockerfiles) > 20:
        raise ValueError(f"Batch B requires {len(dockerfiles)} images; maximum is 20")

    outcomes: dict[str, dict[str, bool]] = {}
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for digest, dockerfile in dockerfiles.items():
            image = f"tasktrove-batch-b:{digest[:16]}"
            subprocess.run(
                ["docker", "build", "--quiet", "--tag", image, "-"],
                input=dockerfile,
                check=True,
            )
            try:
                for family in families_by_image[digest]:
                    files = representatives[family]
                    family_root = root / family
                    tests = family_root / "tests"
                    app = family_root / "app"
                    logs = family_root / "logs"
                    tests.mkdir(parents=True)
                    app.mkdir()
                    logs.mkdir()
                    for name in (
                        "tests/test.sh",
                        "tests/verifier.py",
                        "tests/verifier_data.json",
                        "tests/validate_verifier_data.py",
                    ):
                        (family_root / name).write_bytes(files[name])
                    original_verifier = files["tests/verifier.py"]
                    original_data = files["tests/verifier_data.json"]
                    family_outcomes: dict[str, bool] = {}

                    family_outcomes["negative"] = docker_case(
                        image, tests, app, logs, expect_reward="0"
                    )
                    (tests / "verifier.py").write_text(
                        'import pathlib\npathlib.Path("/logs/verifier/reward.txt").write_text("1")\n'
                    )
                    family_outcomes["positive"] = docker_case(
                        image, tests, app, logs, expect_reward="1"
                    )
                    (tests / "verifier.py").write_text(
                        'raise RuntimeError("injected unexpected verifier failure")\n'
                    )
                    family_outcomes["unexpected_exception"] = docker_case(
                        image, tests, app, logs, expect_reward=None
                    )
                    (tests / "verifier.py").write_text(
                        "import tasktrove_injected_missing_dependency\n"
                    )
                    family_outcomes["missing_dependency"] = docker_case(
                        image, tests, app, logs, expect_reward=None
                    )
                    (tests / "verifier.py").write_bytes(original_verifier)
                    (tests / "verifier_data.json").write_text("{")
                    family_outcomes["corrupt_data"] = docker_case(
                        image, tests, app, logs, expect_reward=None
                    )
                    (tests / "verifier_data.json").unlink()
                    family_outcomes["missing_data"] = docker_case(
                        image, tests, app, logs, expect_reward=None
                    )
                    (tests / "verifier_data.json").write_bytes(original_data)
                    if not all(family_outcomes.values()):
                        raise ValueError(
                            f"{family}: exact-image contract failure: {family_outcomes}"
                        )
                    outcomes[family] = family_outcomes
            finally:
                subprocess.run(
                    ["docker", "image", "rm", image],
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
    return {
        "unique_images": len(dockerfiles),
        "image_hashes": sorted(dockerfiles),
        "families": outcomes,
    }


def validate_dataset(
    stage: Path, spec: DatasetSpec, expected: dict[str, object]
) -> dict[str, object]:
    source = stage / "sources" / spec.source / "tasks.parquet"
    output = stage / expected["output"]
    if spec.family == "mcqa":
        connection = duckdb.connect(config={"threads": "1", "memory_limit": "256MB"})
        try:
            count, distinct_paths = connection.execute(
                "SELECT count(*), count(DISTINCT path) FROM read_parquet(?)",
                [str(output)],
            ).fetchone()
        finally:
            connection.close()
        if count != expected["rows"] or distinct_paths != count:
            raise ValueError(f"MCQA validation count mismatch: {count}")
        first_binary = next(rows(output))[1]
        first_files = archive(first_binary)[1]
        TaskConfig.model_validate_toml(first_files["task.toml"].decode())
        subprocess.run(["bash", "-n"], input=first_files["tests/test.sh"], check=True)
        if sha256_file(output) != expected["output_sha256"]:
            raise ValueError(f"output hash changed: {spec.target}")
        return {
            "rows": count,
            "distinct_paths": distinct_paths,
            "validated_during_shard_build": count,
            "contract_cases": wrapper_contract_cases(first_files, spec.family),
        }
    source_iter = rows(source)
    output_iter = rows(output)
    count = 0
    first_files: dict[str, bytes] | None = None
    seen: set[str] = set()
    for (source_name, source_binary), (output_name, output_binary) in zip(
        source_iter, output_iter, strict=True
    ):
        if source_name != output_name or output_name in seen:
            raise ValueError(f"path mismatch or duplicate: {output_name}")
        seen.add(output_name)
        source_members, source_files = archive(source_binary)
        _, output_files = archive(output_binary)
        expected_binary, changed = patched_task(source_binary, spec)
        if output_binary != expected_binary:
            raise ValueError(f"non-deterministic output: {output_name}")
        for name, content in source_files.items():
            if name not in changed and output_files.get(name) != content:
                raise ValueError(f"unrelated member changed: {output_name}/{name}")
        TaskConfig.model_validate_toml(output_files["task.toml"].decode())
        subprocess.run(["bash", "-n"], input=output_files["tests/test.sh"], check=True)
        compile(
            output_files["tests/verifier.py"].decode(),
            f"{output_name}/verifier.py",
            "exec",
        )
        compile(
            output_files["tests/validate_verifier_data.py"].decode(),
            f"{output_name}/validate_verifier_data.py",
            "exec",
        )
        if first_files is None:
            first_files = output_files
        count += 1
    if count != expected["rows"] or count < MIN_TASKS or len(seen) != count:
        raise ValueError(f"row validation failed for {spec.target}: {count}")
    if sha256_file(output) != expected["output_sha256"]:
        raise ValueError(f"output hash changed: {spec.target}")
    if first_files is None:
        raise ValueError(f"empty dataset: {spec.target}")
    return {
        "rows": count,
        "contract_cases": wrapper_contract_cases(first_files, spec.family),
    }


def build(
    stage: Path, revision: str, validate_only: bool, validate_images: bool
) -> dict[str, object]:
    if revision != TASKTROVE_V4_REVISION:
        raise ValueError(
            f"Batch B must use exact TaskTrove v4 revision {TASKTROVE_V4_REVISION}"
        )
    stage.mkdir(parents=True, exist_ok=True)
    manifest_path = stage / "manifest.json"
    if validate_only and not manifest_path.is_file():
        raise FileNotFoundError(f"validation manifest missing: {manifest_path}")
    datasets = []
    validation = {}
    worker_peaks = {}
    for spec in SPECS:
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--stage",
            str(stage),
            "--revision",
            revision,
            "--worker-dataset",
            spec.source,
        ]
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
        payload = json.loads(completed.stdout)
        datasets.append(payload["dataset"])
        validation[payload["dataset"]["output_dataset"]] = payload["validation"]
        worker_peaks[spec.source] = payload["peak_rss_bytes"]
    manifest = {
        "source_repo": REPO_ID,
        "source_revision": revision,
        "target_version": "4.1",
        "batch_size": BATCH_SIZE,
        "datasets": datasets,
        "worker_peak_rss_bytes": worker_peaks,
    }
    representatives: dict[str, dict[str, bytes]] = {}
    for spec, item in zip(SPECS, datasets, strict=True):
        first = next(rows(stage / item["output"]))[1]
        representatives[spec.family] = archive(first)[1]
    if validate_images:
        manifest["exact_image_validation"] = exact_image_contracts(representatives)
    rss = peak_rss_bytes()
    if rss >= MAX_RSS_BYTES:
        raise MemoryError(f"peak RSS {rss} exceeds {MAX_RSS_BYTES}")
    manifest["validation"] = validation
    manifest["peak_rss_bytes"] = rss
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def build_worker(stage: Path, revision: str, source_dataset: str) -> dict[str, object]:
    by_source = {spec.source: spec for spec in SPECS}
    spec = by_source[source_dataset]
    dataset = existing_result(stage, spec, revision) or build_dataset(
        stage, spec, revision
    )
    validation = validate_dataset(stage, spec, dataset)
    rss = peak_rss_bytes()
    if rss >= MAX_RSS_BYTES:
        raise MemoryError(f"peak RSS {rss} exceeds {MAX_RSS_BYTES}")
    return {"dataset": dataset, "validation": validation, "peak_rss_bytes": rss}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--revision", default=TASKTROVE_V4_REVISION)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--validate-images", action="store_true")
    parser.add_argument("--clear-source-cache", action="store_true")
    parser.add_argument("--worker-dataset", choices=[spec.source for spec in SPECS])
    parser.add_argument("--worker-mcqa-shard", type=int)
    parser.add_argument("--worker-mcqa-merge", action="store_true")
    args = parser.parse_args()
    if args.worker_mcqa_merge:
        print(json.dumps(build_mcqa_merge(args.stage), sort_keys=True))
        return
    if args.worker_mcqa_shard is not None:
        print(
            json.dumps(
                build_mcqa_shard(args.stage, args.revision, args.worker_mcqa_shard),
                sort_keys=True,
            )
        )
        return
    if args.worker_dataset:
        print(
            json.dumps(
                build_worker(args.stage, args.revision, args.worker_dataset),
                sort_keys=True,
            )
        )
        return
    manifest = build(
        args.stage, args.revision, args.validate_only, args.validate_images
    )
    if args.clear_source_cache and not args.validate_only:
        shutil.rmtree(args.stage / "sources")
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()

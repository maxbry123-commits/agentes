#!/usr/bin/env python3
"""Build the bounded Stack PHP/Pytest repairs from the v4.0 survey."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import warnings
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from harbor.models.task.config import TaskConfig
from huggingface_hub import hf_hub_download

from data.tasktrove.rewardkit_migration import _archive_files, _write_archive

REPO_ID = "open-thoughts/TaskTrove"
BATCH_SIZE = 32
EXPECTED_SCHEMA = pa.schema(
    [pa.field("path", pa.string()), pa.field("task_binary", pa.binary())]
)

PYTEST_SOURCE = "laion__exp_rpt_stack-pytest-large-v2"
PYTEST_TARGET = "laion__exp_rpt_stack-pytest-large-v3"
PHP_SOURCE = "laion__exp_rpt_stack-php-large-v6"
PHP_TARGET = "laion__exp_rpt_stack-php-large-v7"

PYTEST_RISK_PATTERNS = {
    "absolute_home": re.compile(r"/home/|/Users/|C:\\\\Users", re.IGNORECASE),
    "docker_or_service": re.compile(
        r"docker|/var/run/docker\.sock|ClickHouseCluster", re.IGNORECASE
    ),
    "external_process": re.compile(
        r"subprocess\.|os\.system|Popen\(|check_output\(|check_call\(",
        re.IGNORECASE,
    ),
    "fixture_reference": re.compile(
        r"(?:fixtures?|resources?|test_data|data)/[^\s'\"]+"
        r"|\.(?:csv|json|png|jpg|jpeg|ya?ml)['\"]",
        re.IGNORECASE,
    ),
    "network_or_browser": re.compile(
        r"https?://|requests\.|urllib\.|socket\.|selenium|boto3|paramiko",
        re.IGNORECASE,
    ),
    "skip_capable": re.compile(
        r"pytest\.mark\.skip|pytest\.skip\(|@unittest\.skip", re.IGNORECASE
    ),
}

PHP_ALLOWED_IMPORT_PREFIXES = ("PHPUnit\\",)
PHP_ALLOWED_IMPORTS = {
    "ArrayObject",
    "Closure",
    "DateTime",
    "DateTimeImmutable",
    "DateTimeInterface",
    "DomainException",
    "Exception",
    "Generator",
    "InvalidArgumentException",
    "LogicException",
    "RuntimeException",
    "TestCase",
    "Throwable",
    "stdClass",
}
PHP_RISK_PATTERNS = {
    "absolute_home": re.compile(r"/home/|/Users/|C:\\Users", re.IGNORECASE),
    "fixture_reference": re.compile(
        r"(?:fixtures?|resources?|test_data|data)/[^\s'\"]+", re.IGNORECASE
    ),
    "network_or_service": re.compile(
        r"https?://|curl_|Guzzle|new[ \t]+Client[ \t]*\(", re.IGNORECASE
    ),
    "skip_capable": re.compile(
        r"@requires|markTestSkipped|->markTestSkipped", re.IGNORECASE
    ),
    "test_trait": re.compile(
        r"^[ \t]+use[ \t]+[A-Za-z_\\][A-Za-z0-9_\\]*[ \t]*;", re.MULTILINE
    ),
}

PYTEST_TEST_SH = r"""#!/bin/bash
set -euo pipefail

LOGS_DIR=/logs/verifier
REWARD="$LOGS_DIR/reward.txt"
mkdir -p "$LOGS_DIR"
rm -f "$REWARD"

# Dependency setup is infrastructure. Leave no reward if it fails so Harbor retries.
source /app/.venv/bin/activate
if [ -s /tests/requirements.txt ]; then
    pip install --quiet --disable-pip-version-check -r /tests/requirements.txt
fi
python3 -m pytest --version >/dev/null
python3 - <<'PY'
import ast
import pathlib

ast.parse(pathlib.Path("/tests/test_solution.py").read_text())
PY

export PYTHONPATH="/app${PYTHONPATH:+:$PYTHONPATH}"
cd /app
set +e
pytest /tests/test_solution.py -v --tb=short \
    --junitxml="$LOGS_DIR/pytest.xml" 2>&1 | tee "$LOGS_DIR/pytest_output.txt"
PYTEST_EXIT=${PIPESTATUS[0]}

SUMMARY=$(python3 - <<'PY'
import pathlib
import xml.etree.ElementTree as ET

report = pathlib.Path("/logs/verifier/pytest.xml")
if not report.is_file():
    raise SystemExit(2)
root = ET.parse(report).getroot()
cases = root.findall(".//testcase")
print(len(cases), sum(case.find("skipped") is not None for case in cases))
PY
)
SUMMARY_EXIT=$?
set -e

if [ "$SUMMARY_EXIT" -ne 0 ]; then
    rm -f "$REWARD"
    exit "$SUMMARY_EXIT"
fi
read -r TOTAL SKIPPED <<< "$SUMMARY"
if [ "$TOTAL" -lt 1 ]; then
    rm -f "$REWARD"
    exit 2
fi
if [ "$PYTEST_EXIT" -ne 0 ] && [ "$PYTEST_EXIT" -ne 1 ]; then
    rm -f "$REWARD"
    exit "$PYTEST_EXIT"
fi

if [ "$PYTEST_EXIT" -eq 0 ] && [ "$TOTAL" -ge 1 ] && [ "$SKIPPED" -eq 0 ]; then
    echo 1 > "$REWARD"
    exit 0
fi
echo 0 > "$REWARD"
exit 1
"""

PYTEST_DOCKERFILE = """FROM python:3.12-slim-bookworm

WORKDIR /app
RUN mkdir -p /output && chmod 777 /output
RUN apt-get update \\
    && apt-get install -y --no-install-recommends bsdutils git \\
    && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /app/.venv \\
    && /app/.venv/bin/pip install --no-cache-dir pytest
ENV PATH=/app/.venv/bin:$PATH
"""


@dataclass(frozen=True)
class DatasetSpec:
    source: str
    target: str


SPECS = (
    DatasetSpec(PHP_SOURCE, PHP_TARGET),
    DatasetSpec(PYTEST_SOURCE, PYTEST_TARGET),
)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pytest_drop_reasons(files: dict[str, bytes]) -> list[str]:
    source = files["tests/test_solution.py"].decode(errors="replace")
    reasons = []
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            tree = ast.parse(source)
    except SyntaxError:
        return ["syntax_error"]
    tests = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test")
    ]
    if not tests:
        reasons.append("no_tests")
    reasons.extend(
        name for name, pattern in PYTEST_RISK_PATTERNS.items() if pattern.search(source)
    )
    return reasons


def php_drop_reasons(files: dict[str, bytes]) -> list[str]:
    test = files["tests/TestSolution.php"].decode(errors="replace")
    instruction = files["instruction.md"].decode(errors="replace")
    reasons = [
        name for name, pattern in PHP_RISK_PATTERNS.items() if pattern.search(test)
    ]
    for imported in re.findall(r"^use\s+([^;{]+);", test, re.MULTILINE):
        imported = imported.strip()
        short_name = imported.rsplit("\\", 1)[-1]
        if imported.startswith(PHP_ALLOWED_IMPORT_PREFIXES):
            continue
        if short_name in PHP_ALLOWED_IMPORTS:
            continue
        if re.search(rf"\b{re.escape(short_name)}\b", instruction, re.IGNORECASE):
            continue
        reasons.append("unmentioned_import")
        break
    return reasons


def patch_pytest(files: dict[str, bytes]) -> dict[str, bytes]:
    output = dict(files)
    output.pop("tests/__pycache__/test_solution.cpython-312.pyc", None)
    output["environment/Dockerfile"] = PYTEST_DOCKERFILE.encode()
    output["tests/test.sh"] = PYTEST_TEST_SH.encode()
    return output


def patch_php(files: dict[str, bytes]) -> dict[str, bytes]:
    output = dict(files)
    script = output["tests/test.sh"].decode()
    old_start = (
        "set +e\n"
        "mkdir -p /logs/verifier\n"
        'echo "0" > /logs/verifier/reward.txt\n'
        "cd /app\n"
    )
    new_start = (
        "set +e\n"
        "mkdir -p /logs/verifier\n"
        'REWARD="/logs/verifier/reward.txt"\n'
        'rm -f "$REWARD"\n'
        "if ! command -v php >/dev/null 2>&1; then exit 2; fi\n"
        "if [ ! -r /usr/local/bin/phpunit ]; then exit 2; fi\n"
        "if ! php -r \"require '/usr/local/bin/phpunit'; exit(class_exists('PHPUnit\\\\Framework\\\\TestCase') ? 0 : 2);\"; then exit 2; fi\n"
        "cd /app\n"
    )
    if script.count(old_start) != 1:
        raise ValueError("PHP verifier does not contain the expected startup block")
    script = script.replace(old_start, new_start, 1)
    start = "// 6. Catch-all autoloader for unresolved symbols.\n"
    end = "// 7. Snapshot existing classes.\n"
    if start not in script or end not in script:
        raise ValueError("PHP verifier does not contain the expected catch-all block")
    before, remainder = script.split(start, 1)
    _, after = remainder.split(end, 1)
    script = before + end + after
    old_execution = (
        'echo "Running PHPUnit tests (v6 harness)..."\n'
        "php /app/run_tests.php 2>&1 | tee /logs/verifier/test_output.txt\n"
    )
    new_execution = (
        'if ! php -l /app/run_tests.php >/dev/null; then rm -f "$REWARD"; exit 2; fi\n'
        'if ! php -l /tests/TestSolution.php >/dev/null; then rm -f "$REWARD"; exit 2; fi\n'
        'echo "Running PHPUnit tests (v6 harness)..."\n'
        "php /app/run_tests.php 2>&1 | tee /logs/verifier/test_output.txt\n"
    )
    if script.count(old_execution) != 1:
        raise ValueError("PHP verifier does not contain the expected execution block")
    script = script.replace(old_execution, new_execution, 1)

    lifecycle_replacements = {
        "catch (\\Throwable $t) { /* note */ }": (
            'catch (\\Throwable $t) { $errors++; $failureMsgs[] = "setUpBeforeClass failed: " . $t->getMessage(); continue; }'
        ),
        "catch (\\Throwable $t) { /* fall back to no-args */ }": (
            'catch (\\Throwable $t) { $tests++; $errors++; $failureMsgs[] = "test reflection failed: " . $t->getMessage(); continue; }'
        ),
        "catch (\\Throwable $t) { /* don't double-count */ }": (
            'catch (\\Throwable $t) { $errors++; $failureMsgs[] = "tearDown failed: " . $t->getMessage(); }'
        ),
        "try { $cls::tearDownAfterClass(); } catch (\\Throwable $t) { /* ignore */ }": (
            'try { $cls::tearDownAfterClass(); } catch (\\Throwable $t) { $errors++; $failureMsgs[] = "tearDownAfterClass failed: " . $t->getMessage(); }'
        ),
    }
    for old, new in lifecycle_replacements.items():
        if script.count(old) != 1:
            raise ValueError(f"PHP verifier does not contain lifecycle block: {old}")
        script = script.replace(old, new, 1)
    old_php_gate = (
        "if ($failures > 0 || $errors > 0 || $tests === 0 || $assertions === 0) {"
    )
    new_php_gate = "if ($failures > 0 || $errors > 0 || $skipped > 0 || $tests === 0 || $assertions === 0) {"
    if script.count(old_php_gate) != 1:
        raise ValueError("PHP verifier does not contain the expected in-process gate")
    script = script.replace(old_php_gate, new_php_gate, 1)
    old_summary = (
        "detail_line=$(grep -oE 'Tests: [0-9]+, Assertions: [0-9]+, Failures: [0-9]+, Errors: [0-9]+' \\\n"
        "    /logs/verifier/test_output.txt | tail -1)"
    )
    new_summary = (
        "detail_line=$(grep -oE 'Tests: [0-9]+, Assertions: [0-9]+, Failures: [0-9]+, Errors: [0-9]+, Skipped: [0-9]+' \\\n"
        "    /logs/verifier/test_output.txt | tail -1)"
    )
    if script.count(old_summary) != 1:
        raise ValueError("PHP verifier does not contain the expected summary parser")
    script = script.replace(old_summary, new_summary, 1)
    parsed_summary = (
        new_summary + '\nif [ -z "$detail_line" ]; then rm -f "$REWARD"; exit 2; fi'
    )
    script = script.replace(new_summary, parsed_summary, 1)
    old_parse = (
        "errors=0\n"
        'if [ -n "$detail_line" ]; then\n'
        "    tests_run=$(echo \"$detail_line\" | grep -oE 'Tests: [0-9]+' | grep -oE '[0-9]+' | head -1)\n"
        "    assertions_run=$(echo \"$detail_line\" | grep -oE 'Assertions: [0-9]+' | grep -oE '[0-9]+' | head -1)\n"
        "    failures=$(echo \"$detail_line\" | grep -oE 'Failures: [0-9]+' | grep -oE '[0-9]+' | head -1)\n"
        "    errors=$(echo \"$detail_line\"   | grep -oE 'Errors: [0-9]+'   | grep -oE '[0-9]+' | head -1)\n"
        "fi\n"
        "tests_run=${tests_run:-0}\n"
        "assertions_run=${assertions_run:-0}\n"
        "failures=${failures:-0}\n"
        "errors=${errors:-0}\n"
    )
    new_parse = (
        old_parse.replace(
            "errors=0\n",
            "errors=0\nskipped=0\n",
            1,
        )
        .replace(
            "    errors=$(echo \"$detail_line\"   | grep -oE 'Errors: [0-9]+'   | grep -oE '[0-9]+' | head -1)\n",
            "    errors=$(echo \"$detail_line\"   | grep -oE 'Errors: [0-9]+'   | grep -oE '[0-9]+' | head -1)\n"
            "    skipped=$(echo \"$detail_line\"  | grep -oE 'Skipped: [0-9]+'  | grep -oE '[0-9]+' | head -1)\n",
            1,
        )
        .replace(
            "errors=${errors:-0}\n",
            "errors=${errors:-0}\nskipped=${skipped:-0}\n",
            1,
        )
    )
    if script.count(old_parse) != 1:
        raise ValueError("PHP verifier does not contain the expected counter parser")
    script = script.replace(old_parse, new_parse, 1)
    old_shell_gate = (
        '        && [ "$failures" -eq 0 ] \\\n        && [ "$errors" -eq 0 ]; then'
    )
    new_shell_gate = (
        '        && [ "$failures" -eq 0 ] \\\n'
        '        && [ "$errors" -eq 0 ] \\\n'
        '        && [ "$skipped" -eq 0 ]; then'
    )
    if script.count(old_shell_gate) != 1:
        raise ValueError("PHP verifier does not contain the expected shell gate")
    output["tests/test.sh"] = script.replace(old_shell_gate, new_shell_gate, 1).encode()
    return output


def task_result(
    spec: DatasetSpec, task_binary: bytes
) -> tuple[bytes | None, list[str], set[str]]:
    members, files = _archive_files(task_binary)
    if spec.source == PYTEST_SOURCE:
        reasons = pytest_drop_reasons(files)
        if reasons:
            return None, reasons, set()
        patched = patch_pytest(files)
    elif spec.source == PHP_SOURCE:
        reasons = php_drop_reasons(files)
        if reasons:
            return None, reasons, set()
        patched = patch_php(files)
    else:
        raise ValueError(f"unsupported dataset: {spec.source}")
    changed = {
        name
        for name in set(files) | set(patched)
        if files.get(name) != patched.get(name)
    }
    return _write_archive(members, patched), [], changed


def build_dataset(spec: DatasetSpec, source: Path, output: Path) -> dict[str, object]:
    parquet = pq.ParquetFile(source)
    if parquet.schema_arrow != EXPECTED_SCHEMA:
        raise ValueError(f"unexpected schema: {source}")
    output.parent.mkdir(parents=True, exist_ok=True)
    writer = pq.ParquetWriter(output, EXPECTED_SCHEMA, compression="zstd")
    source_rows = 0
    kept_rows = 0
    paths: set[str] = set()
    drop_reasons: Counter[str] = Counter()
    changed_members: Counter[str] = Counter()
    dropped_paths: list[str] = []
    try:
        for batch in parquet.iter_batches(batch_size=BATCH_SIZE):
            output_paths: list[str] = []
            output_tasks: list[bytes] = []
            for path, task_binary in zip(
                batch.column(0).to_pylist(),
                batch.column(1).to_pylist(),
                strict=True,
            ):
                source_rows += 1
                if path in paths:
                    raise ValueError(f"duplicate path: {path}")
                paths.add(path)
                repaired, reasons, changed = task_result(spec, task_binary)
                if repaired is None:
                    dropped_paths.append(path)
                    drop_reasons.update(set(reasons))
                    continue
                output_paths.append(path)
                output_tasks.append(repaired)
                changed_members.update(changed)
                kept_rows += 1
            if output_paths:
                writer.write_batch(
                    pa.record_batch(
                        [pa.array(output_paths), pa.array(output_tasks)],
                        schema=EXPECTED_SCHEMA,
                    )
                )
    finally:
        writer.close()
    if kept_rows < 300:
        raise ValueError(f"standing-order minimum violated: {spec.target}={kept_rows}")
    dropped_file = output.parent / "dropped_paths.txt"
    dropped_file.write_text("".join(f"{path}\n" for path in dropped_paths))
    return {
        "source_dataset": spec.source,
        "output_dataset": spec.target,
        "source_rows": source_rows,
        "kept_rows": kept_rows,
        "dropped_rows": source_rows - kept_rows,
        "drop_reasons": dict(sorted(drop_reasons.items())),
        "changed_members": dict(sorted(changed_members.items())),
        "source_sha256": file_sha256(source),
        "output_sha256": file_sha256(output),
        "dropped_paths_sha256": file_sha256(dropped_file),
    }


def parquet_rows(path: Path):
    parquet = pq.ParquetFile(path)
    if parquet.schema_arrow != EXPECTED_SCHEMA:
        raise ValueError(f"unexpected schema: {path}")
    for batch in parquet.iter_batches(batch_size=BATCH_SIZE):
        yield from zip(
            batch.column(0).to_pylist(),
            batch.column(1).to_pylist(),
            strict=True,
        )


def validate_retained_task(
    spec: DatasetSpec, path: str, task_binary: bytes, expected_changed: set[str]
) -> None:
    _, files = _archive_files(task_binary)
    TaskConfig.model_validate_toml(files["task.toml"].decode())
    script = files["tests/test.sh"].decode()
    subprocess.run(["bash", "-n"], input=script.encode(), check=True)
    if spec.source == PYTEST_SOURCE:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            ast.parse(files["tests/test_solution.py"].decode())
        allowed = {
            "environment/Dockerfile",
            "tests/test.sh",
            "tests/__pycache__/test_solution.cpython-312.pyc",
        }
        required_fragments = (
            'rm -f "$REWARD"',
            "python3 -m pytest --version",
            'ast.parse(pathlib.Path("/tests/test_solution.py").read_text())',
            'if [ "$PYTEST_EXIT" -ne 0 ] && [ "$PYTEST_EXIT" -ne 1 ]',
            'echo 0 > "$REWARD"',
        )
    else:
        allowed = {"tests/test.sh"}
        required_fragments = (
            'rm -f "$REWARD"',
            "command -v php",
            "class_exists('PHPUnit\\\\Framework\\\\TestCase')",
            "php -l /app/run_tests.php",
            "php -l /tests/TestSolution.php",
            'if [ -z "$detail_line" ]; then rm -f "$REWARD"; exit 2; fi',
        )
        forbidden_fragments = ("/* note */", "/* don't double-count */", "/* ignore */")
        if any(fragment in script for fragment in forbidden_fragments):
            raise ValueError(f"PHP lifecycle exception is still swallowed: {path}")
    if any(fragment not in script for fragment in required_fragments):
        raise ValueError(f"fail-closed verifier invariant missing: {path}")
    if not expected_changed <= allowed:
        raise ValueError(
            f"unexpected changed member in {path}: {expected_changed - allowed}"
        )


def validate_dataset(
    spec: DatasetSpec, source: Path, output: Path, expected: dict[str, object]
) -> None:
    output_iterator = iter(parquet_rows(output))
    output_row = next(output_iterator, None)
    source_paths: set[str] = set()
    output_paths: set[str] = set()
    dropped_paths: list[str] = []
    drop_reasons: Counter[str] = Counter()
    changed_members: Counter[str] = Counter()
    source_count = 0
    kept_count = 0
    for path, original in parquet_rows(source):
        source_count += 1
        if path in source_paths:
            raise ValueError(f"duplicate source path: {path}")
        source_paths.add(path)
        expected_binary, reasons, expected_changed = task_result(spec, original)
        if expected_binary is None:
            dropped_paths.append(path)
            drop_reasons.update(set(reasons))
            continue
        if output_row is None:
            raise ValueError(f"retained source row missing from output: {path}")
        output_path, task_binary = output_row
        if output_path != path:
            raise ValueError(
                f"output order/path mismatch: expected {path}, found {output_path}"
            )
        if output_path in output_paths:
            raise ValueError(f"duplicate output path: {output_path}")
        output_paths.add(output_path)
        if expected_binary != task_binary:
            raise ValueError(f"non-reproducible archive: {path}")
        validate_retained_task(spec, path, task_binary, expected_changed)
        changed_members.update(expected_changed)
        kept_count += 1
        output_row = next(output_iterator, None)
    if output_row is not None:
        raise ValueError(f"output contains path absent from source: {output_row[0]}")
    if source_count != expected["source_rows"] or kept_count != expected["kept_rows"]:
        raise ValueError(f"row-count mismatch for {spec.target}")
    if source_count - kept_count != expected["dropped_rows"]:
        raise ValueError(f"dropped-row mismatch for {spec.target}")
    if dict(sorted(drop_reasons.items())) != expected["drop_reasons"]:
        raise ValueError(f"drop-reason mismatch for {spec.target}")
    if dict(sorted(changed_members.items())) != expected["changed_members"]:
        raise ValueError(f"changed-member mismatch for {spec.target}")
    dropped_file = output.parent / "dropped_paths.txt"
    if dropped_file.read_text().splitlines() != dropped_paths:
        raise ValueError(f"dropped-path ledger mismatch for {spec.target}")
    if file_sha256(source) != expected["source_sha256"]:
        raise ValueError(f"source hash changed: {spec.source}")
    if file_sha256(output) != expected["output_sha256"]:
        raise ValueError(f"output hash changed: {spec.target}")
    if file_sha256(dropped_file) != expected["dropped_paths_sha256"]:
        raise ValueError(f"dropped-path hash changed: {spec.target}")


def representative_files(stage: Path, spec: DatasetSpec) -> dict[str, bytes]:
    output = stage / "datasets" / spec.target / "tasks.parquet"
    first_batch = next(pq.ParquetFile(output).iter_batches(batch_size=1))
    _, files = _archive_files(first_batch.column(1).to_pylist()[0])
    return files


def build_gate_image(dockerfile: bytes, root: Path) -> str:
    context = root / "context"
    context.mkdir()
    (context / "Dockerfile").write_bytes(dockerfile)
    image_id = root / "image-id"
    subprocess.run(
        [
            "docker",
            "build",
            "--progress=plain",
            "--iidfile",
            str(image_id),
            str(context),
        ],
        check=True,
    )
    return image_id.read_text().strip()


def run_gate_case(
    image: str,
    wrapper: str,
    test_name: str,
    test_source: str,
    requirements: str,
    command: str,
) -> tuple[int, str | None]:
    with tempfile.TemporaryDirectory(
        prefix="tasktrove-a2-gate-"
    ) as temporary_directory:
        root = Path(temporary_directory)
        tests = root / "tests"
        logs = root / "logs"
        tests.mkdir()
        logs.mkdir()
        (tests / "test.sh").write_text(wrapper)
        (tests / test_name).write_text(test_source)
        (tests / "requirements.txt").write_text(requirements)
        result = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "--volume",
                f"{tests}:/tests:ro",
                "--volume",
                f"{logs}:/logs/verifier",
                image,
                "bash",
                "-lc",
                command,
            ],
            capture_output=True,
            check=False,
            text=True,
        )
        reward_path = logs / "reward.txt"
        reward = reward_path.read_text().strip() if reward_path.is_file() else None
        return result.returncode, reward


def require_gate(result: tuple[int, str | None], reward: str | None, name: str) -> None:
    returncode, observed_reward = result
    expected_success = reward == "1"
    if observed_reward != reward or (returncode == 0) != expected_success:
        raise ValueError(
            f"image gate {name} failed: returncode={returncode}, reward={observed_reward}, expected={reward}"
        )


def run_pytest_image_gates(files: dict[str, bytes], root: Path) -> dict[str, int]:
    image = build_gate_image(files["environment/Dockerfile"], root)
    wrapper = files["tests/test.sh"].decode()
    cases = {
        "positive": (
            "def test_result():\n    assert True\n",
            "bash /tests/test.sh",
            "1",
        ),
        "negative": (
            "def test_result():\n    assert False\n",
            "bash /tests/test.sh",
            "0",
        ),
        "skip": (
            "import pytest\ndef test_result():\n    pytest.skip('gate')\n",
            "bash /tests/test.sh",
            "0",
        ),
        "collection": (
            "import missing_verifier_dependency\ndef test_result():\n    assert True\n",
            "bash /tests/test.sh",
            None,
        ),
        "syntax": ("def test_result(:\n    pass\n", "bash /tests/test.sh", None),
        "missing_dependency": (
            "def test_result():\n    assert True\n",
            "rm -f /app/.venv/bin/pytest; rm -rf /app/.venv/lib/python*/site-packages/pytest /app/.venv/lib/python*/site-packages/_pytest; bash /tests/test.sh",
            None,
        ),
    }
    passed = 0
    try:
        for name, (test_source, command, reward) in cases.items():
            require_gate(
                run_gate_case(
                    image, wrapper, "test_solution.py", test_source, "", command
                ),
                reward,
                f"pytest_{name}",
            )
            passed += 1
        parser_failure = wrapper.replace(
            "import xml.etree.ElementTree as ET",
            "raise RuntimeError('injected report parser failure')\nimport xml.etree.ElementTree as ET",
        )
        require_gate(
            run_gate_case(
                image,
                parser_failure,
                "test_solution.py",
                "def test_result():\n    assert True\n",
                "",
                "bash /tests/test.sh",
            ),
            None,
            "pytest_report_parse",
        )
        passed += 1
        require_gate(
            run_gate_case(
                image,
                "#!/bin/bash\nthis is ( malformed\n",
                "test_solution.py",
                "def test_result():\n    assert True\n",
                "",
                "bash /tests/test.sh",
            ),
            None,
            "pytest_malformed_harness",
        )
        passed += 1
    finally:
        subprocess.run(
            ["docker", "image", "rm", image], capture_output=True, check=False
        )
    return {"pytest_image_gate_attempts": passed, "pytest_image_gate_passes": passed}


def run_php_image_gates(files: dict[str, bytes], root: Path) -> dict[str, int]:
    image = build_gate_image(files["environment/Dockerfile"], root)
    wrapper = files["tests/test.sh"].decode()
    prefix = "<?php\nuse PHPUnit\\Framework\\TestCase;\n"
    cases = {
        "positive": (
            prefix
            + "class SyntheticTest extends TestCase { public function testResult(): void { $this->assertTrue(true); } }\n",
            "bash /tests/test.sh",
            "1",
        ),
        "negative": (
            prefix
            + "class SyntheticTest extends TestCase { public function testResult(): void { $this->assertTrue(false); } }\n",
            "bash /tests/test.sh",
            "0",
        ),
        "skip": (
            prefix
            + "class SyntheticTest extends TestCase { public function testResult(): void { $this->markTestSkipped('gate'); } }\n",
            "bash /tests/test.sh",
            "0",
        ),
        "syntax": (
            "<?php class SyntheticTest extends {\n",
            "bash /tests/test.sh",
            None,
        ),
        "missing_dependency": (
            prefix
            + "class SyntheticTest extends TestCase { public function testResult(): void { $this->assertTrue(true); } }\n",
            "rm -f /usr/local/bin/phpunit; bash /tests/test.sh",
            None,
        ),
        "setup_error": (
            prefix
            + "class SyntheticTest extends TestCase { public static function setUpBeforeClass(): void { throw new Exception('gate'); } public function testResult(): void { $this->assertTrue(true); } }\n",
            "bash /tests/test.sh",
            "0",
        ),
        "teardown_error": (
            prefix
            + "class SyntheticTest extends TestCase { protected function tearDown(): void { throw new Exception('gate'); } public function testResult(): void { $this->assertTrue(true); } }\n",
            "bash /tests/test.sh",
            "0",
        ),
    }
    passed = 0
    try:
        for name, (test_source, command, reward) in cases.items():
            require_gate(
                run_gate_case(
                    image, wrapper, "TestSolution.php", test_source, "", command
                ),
                reward,
                f"php_{name}",
            )
            passed += 1
        require_gate(
            run_gate_case(
                image,
                "#!/bin/bash\nthis is ( malformed\n",
                "TestSolution.php",
                prefix + "class SyntheticTest extends TestCase {}\n",
                "",
                "bash /tests/test.sh",
            ),
            None,
            "php_malformed_harness",
        )
        passed += 1
    finally:
        subprocess.run(
            ["docker", "image", "rm", image], capture_output=True, check=False
        )
    return {"php_image_gate_attempts": passed, "php_image_gate_passes": passed}


def run_image_gates(stage: Path) -> dict[str, int]:
    with tempfile.TemporaryDirectory(
        prefix="tasktrove-a2-images-"
    ) as temporary_directory:
        root = Path(temporary_directory)
        php_root = root / "php"
        pytest_root = root / "pytest"
        php_root.mkdir()
        pytest_root.mkdir()
        php = run_php_image_gates(representative_files(stage, SPECS[0]), php_root)
        pytest = run_pytest_image_gates(
            representative_files(stage, SPECS[1]), pytest_root
        )
    return {**php, **pytest}


def build(stage: Path, revision: str, *, validate_only: bool) -> dict[str, object]:
    manifest_path = stage / "manifest.json"
    if validate_only:
        manifest = json.loads(manifest_path.read_text())
    else:
        datasets = []
        for spec in SPECS:
            source = Path(
                hf_hub_download(
                    REPO_ID,
                    f"{spec.source}/tasks.parquet",
                    repo_type="dataset",
                    revision=revision,
                    local_dir=stage / "sources",
                )
            )
            output = stage / "datasets" / spec.target / "tasks.parquet"
            datasets.append(build_dataset(spec, source, output))
        manifest = {
            "source_repo": REPO_ID,
            "source_revision": revision,
            "target_version": "4.1",
            "datasets": datasets,
        }
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    by_name = {spec.source: spec for spec in SPECS}
    for dataset in manifest["datasets"]:
        spec = by_name[dataset["source_dataset"]]
        validate_dataset(
            spec,
            stage / "sources" / spec.source / "tasks.parquet",
            stage / "datasets" / spec.target / "tasks.parquet",
            dataset,
        )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--clear-source-cache", action="store_true")
    parser.add_argument("--run-image-gates", action="store_true")
    args = parser.parse_args()
    manifest = build(args.stage, args.revision, validate_only=args.validate_only)
    if args.clear_source_cache and not args.validate_only:
        shutil.rmtree(args.stage / "sources")
    image_gates = run_image_gates(args.stage) if args.run_image_gates else {}
    print(
        json.dumps(
            {"datasets": manifest["datasets"], "image_gates": image_gates},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()

"""Migrate embedded TaskTrove LLM judges to Harbor RewardKit.

The migration is deliberately archive-local: task instructions, verifier data,
and unrelated task members remain unchanged. Judgeable output is normalized to
``/app/response.txt`` and evaluated by a root-level RewardKit TOML rubric.
"""

from __future__ import annotations

import copy
import gzip
import io
import json
import re
import tarfile
from dataclasses import dataclass

REWARDKIT_PACKAGE = "harbor-rewardkit==0.1.4"
DEFAULT_JUDGE = "openai/gpt-4o-mini"

DATASET_VERSION_MAP = {
    "laion__glaive-code-assistant-sandboxes-verified": "laion__glaive-code-assistant-sandboxes-verified-v2",
    "laion__magicoder-v2": "laion__magicoder-v3",
    "laion__nemotron-gym-agentic-function-calling-pivot-v2": "laion__nemotron-gym-agentic-function-calling-pivot-v3",
    "laion__nemotron-gym-cfbench-v2": "laion__nemotron-gym-cfbench-v3",
    "laion__nemotron-gym-identity-following-v3": "laion__nemotron-gym-identity-following-v4",
    "laion__nemotron-gym-instruction-following-adversarial-v3": "laion__nemotron-gym-instruction-following-adversarial-v4",
    "laion__nemotron-gym-instruction-following-multiturnchat-v2": "laion__nemotron-gym-instruction-following-multiturnchat-v3",
    "laion__nemotron-gym-inverse-ifeval-v2": "laion__nemotron-gym-inverse-ifeval-v3",
    "laion__nemotron-gym-knowledge-openqa-v2": "laion__nemotron-gym-knowledge-openqa-v3",
    "laion__nemotron-gym-multichallenge-advanced-v2": "laion__nemotron-gym-multichallenge-advanced-v3",
    "laion__nemotron-gym-multichallenge-vanilla-v2": "laion__nemotron-gym-multichallenge-vanilla-v3",
    "laion__nemotron-gym-safety-v2": "laion__nemotron-gym-safety-v3",
    "laion__nemotron-gym-science-so-openq": "laion__nemotron-gym-science-so-openq-v2",
    "laion__nemotron-gym-sysbench-v2": "laion__nemotron-gym-sysbench-v3",
    "laion__qasper-v2": "laion__qasper-v3",
    "laion__stackexchange-codereview-sandboxes-verified": "laion__stackexchange-codereview-sandboxes-verified-v2",
    "laion__stackexchange-overflow-sandboxes-verified": "laion__stackexchange-overflow-sandboxes-verified-v2",
    "laion__stackexchange-superuser-sandboxes-verified": "laion__stackexchange-superuser-sandboxes-verified-v2",
    "laion__stackexchange-tezos-sandboxes-verified": "laion__stackexchange-tezos-sandboxes-verified-v2",
    "laion__stackexchange-unix-sandboxes-verified": "laion__stackexchange-unix-sandboxes-verified-v2",
    "laion__staqc-v3": "laion__staqc-v4",
    "laion__wizardlm-orca-v3": "laion__wizardlm-orca-v4",
}

REWARDKIT_TEST_SH = r"""#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier
rm -f /logs/verifier/reward.json /logs/verifier/reward.txt

if [[ ! -s /app/response.txt && ! -s /app/answer.txt ]]; then
  printf '{"reward": 0.0}\n' > /logs/verifier/reward.json
  exit 0
fi

if [[ ! -s /app/response.txt ]]; then
  cp /app/answer.txt /app/response.txt
fi

if [[ -f /tests/deterministic_gate ]]; then
  set +e
  REWARDKIT_DETERMINISTIC_ONLY=1 python3 /tests/deterministic_gate \
    >> /logs/verifier/test-stdout.txt 2>&1
  gate_status=$?
  set -e
  if [[ ${gate_status} -eq 1 ]]; then
    printf '{"reward": 0.0}\n' > /logs/verifier/reward.json
    exit 0
  fi
  if [[ ${gate_status} -ne 0 ]]; then
    exit "${gate_status}"
  fi
fi

if [[ -f /tests/judge.toml ]]; then
  export LITELLM_DROP_PARAMS=1
  rewardkit /tests --max-concurrent-llm 1 \
    >> /logs/verifier/test-stdout.txt 2>&1
else
  printf '{"reward": 1.0}\n' > /logs/verifier/reward.json
fi
"""


@dataclass(frozen=True)
class ArchiveMigration:
    family: str
    has_judge: bool
    has_deterministic_gate: bool


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _rubric_text(items: object) -> str:
    if not isinstance(items, list):
        return "(none)"
    lines = []
    for item in items:
        if not isinstance(item, dict):
            continue
        identifier = item.get("id", item.get("uid", "?"))
        criterion = item.get("criteria", item.get("question", item.get("content", "")))
        lines.append(f"[{identifier}] {criterion}")
    return "\n".join(lines) if lines else "(none)"


def classify_judge(files: dict[str, bytes]) -> tuple[str, str] | None:
    """Return ``(family, judge_member)`` for an embedded hand-written judge."""
    for member in ("tests/verifier.py", "tests/test_state.py"):
        source = files.get(member, b"")
        if b"litellm" not in source:
            continue
        if b"det_constraints" in source and b"judge_questions" in source:
            return "hybrid", member
        if b"scientifically equivalent" in source and b"reference_answer" in source:
            return "equivalence", member
        if b"Multi-turn rubric" in source or b"multi-criterion YES/NO rubric" in source:
            return "multiturn", member
        if b"Inverse-IFEval" in source or b"Multi-criterion YES/NO" in source:
            return "multi_criterion", member
        if b"heuristic safety" in source or b"Safety principle" in source:
            return "safety", member
        return "generic", member
    return None


def _base_judge_lines(*, mode: str = "batched") -> list[str]:
    return [
        "[judge]",
        f"judge = {_toml_string(DEFAULT_JUDGE)}",
        'files = ["/app/response.txt"]',
        f"mode = {_toml_string(mode)}",
        "timeout = 300",
        "",
    ]


def _generic_description(data: dict, *, safety: bool = False) -> str:
    instruction = str(data.get("instruction", ""))
    system = str(data.get("judge_system_prompt", ""))
    template = str(data.get("judge_prompt_template", ""))
    principle = str(data.get("principle", ""))
    rubric = _rubric_text(data.get("rubric"))
    task_kind = "safety and policy compliance" if safety else "task satisfaction"
    return (
        f"Evaluate the candidate response for {task_kind}. Score 0.0 when it does not "
        "satisfy the task and 1.0 when it fully satisfies the task; use intermediate "
        "values for partial satisfaction.\n\n"
        f"Original judge policy:\n{system}\n\n"
        f"Task instruction:\n{instruction}\n\n"
        f"Rubric:\n{rubric}\n\n"
        f"Principle:\n{principle}\n\n"
        f"Original prompt template:\n{template}"
    )


def render_judge_toml(family: str, data: dict) -> str | None:
    """Render a root-level RewardKit judge preserving the source aggregation."""
    lines: list[str]
    if family in {"generic", "safety"}:
        lines = _base_judge_lines()
        lines.extend(
            [
                "[[criterion]]",
                'name = "reward"',
                f"description = {_toml_string(_generic_description(data, safety=family == 'safety'))}",
                'type = "numeric"',
                "min = 0.0",
                "max = 1.0",
            ]
        )
        return "\n".join(lines) + "\n"

    if family == "equivalence":
        description = (
            "Determine whether the candidate response is scientifically equivalent to the "
            "reference answer. Equivalent phrasing and notation pass; a wrong mechanism, "
            "wrong result, contradiction, or omission of the key point fails. Consider the "
            "candidate's final boxed answer when present.\n\n"
            f"Question:\n{data.get('instruction', '')}\n\n"
            f"Reference answer:\n{data.get('reference_answer', '')}\n\n"
            f"Original judge policy:\n{data.get('judge_system_prompt', '')}\n\n"
            f"Original prompt template:\n{data.get('judge_prompt_template', '')}"
        )
        lines = _base_judge_lines()
        lines.extend(
            [
                "[[criterion]]",
                'name = "equivalent"',
                f"description = {_toml_string(description)}",
                'type = "binary"',
            ]
        )
        return "\n".join(lines) + "\n"

    if family in {"multi_criterion", "multiturn"}:
        criteria = data.get("criteria")
        if not isinstance(criteria, list) or not criteria:
            raise ValueError(f"{family} verifier_data has no criteria")
        lines = _base_judge_lines(mode="individual")
        conversation = str(data.get("conversation", data.get("instruction", "")))
        for index, criterion in enumerate(criteria):
            if not isinstance(criterion, dict):
                raise ValueError(f"criterion {index} is not an object")
            source = criterion.get("content", criterion.get("question", ""))
            expected = str(criterion.get("pass_criteria", "YES")).upper()
            description = (
                "Judge the candidate response against the original requirement below. "
                f"This criterion passes only when the original required verdict is {expected}.\n\n"
                f"Conversation or instruction:\n{conversation}\n\n"
                f"Original requirement:\n{source}"
            )
            lines.extend(
                [
                    "[[criterion]]",
                    f"name = {_toml_string(f'criterion_{index:04d}')}",
                    f"description = {_toml_string(description)}",
                    'type = "binary"',
                    "",
                ]
            )
        lines.extend(["[scoring]", 'aggregation = "all_pass"'])
        return "\n".join(lines) + "\n"

    if family == "hybrid":
        questions = data.get("judge_questions") or []
        if not questions:
            return None
        if not isinstance(questions, list):
            raise ValueError("hybrid judge_questions is not a list")
        instruction = str(data.get("instruction", ""))
        lines = _base_judge_lines()
        for index, question in enumerate(questions):
            description = (
                "The candidate response must satisfy this requirement for the task below. "
                "Be literal and conservative.\n\n"
                f"Task instruction:\n{instruction}\n\nRequirement:\n{question}"
            )
            lines.extend(
                [
                    "[[criterion]]",
                    f"name = {_toml_string(f'requirement_{index:04d}')}",
                    f"description = {_toml_string(description)}",
                    'type = "binary"',
                    "",
                ]
            )
        lines.extend(["[scoring]", 'aggregation = "all_pass"'])
        return "\n".join(lines) + "\n"

    raise ValueError(f"unsupported judge family: {family}")


def render_hybrid_gate(source: str) -> str:
    """Turn the existing hybrid verifier into a deterministic-only gate."""
    marker = "    # --- judge portion ---\n"
    if marker not in source:
        raise ValueError("hybrid verifier lacks judge marker")
    source = source.replace(
        marker,
        '    if os.environ.get("REWARDKIT_DETERMINISTIC_ONLY") == "1":\n'
        '        print(f"det_ok={det_ok} (RewardKit deterministic gate)")\n'
        "        return 1 if det_ok else 0\n\n" + marker,
        1,
    )
    main_marker = 'if __name__ == "__main__":\n'
    if main_marker not in source:
        raise ValueError("hybrid verifier lacks main block")
    source = (
        source[: source.index(main_marker)]
        + r"""if __name__ == "__main__":
    if os.environ.get("REWARDKIT_DETERMINISTIC_ONLY") != "1":
        print("deterministic_gate must be run with REWARDKIT_DETERMINISTIC_ONLY=1", file=sys.stderr)
        raise SystemExit(2)
    try:
        score = main()
    except Exception as error:
        print(f"deterministic gate exception: {error}", file=sys.stderr)
        raise SystemExit(2) from error
    raise SystemExit(0 if score else 1)
"""
    )
    return source


def patch_dockerfile(dockerfile: str) -> str:
    """Install RewardKit at build time without changing the task's other tools."""
    if REWARDKIT_PACKAGE in dockerfile:
        return dockerfile
    dockerfile = re.sub(
        r"^RUN pip install --no-cache-dir litellm==1\.51\.3\s*$\n?",
        "",
        dockerfile,
        count=1,
        flags=re.MULTILINE,
    )
    dockerfile = dockerfile.replace(
        "    && rm -rf /var/lib/apt/lists/* \\\n"
        "    && pip3 install --no-cache-dir --break-system-packages "
        "litellm==1.51.3 openai",
        "    && rm -rf /var/lib/apt/lists/*",
    )
    dockerfile = dockerfile.replace(
        "RUN pip3 install --break-system-packages openai pytest litellm",
        "RUN pip3 install --break-system-packages pytest",
    )
    if re.search(r"^FROM python:3\.11-slim-bookworm\s*$", dockerfile, re.MULTILINE):
        dockerfile = re.sub(
            r"^FROM python:3\.11-slim-bookworm\s*$",
            "FROM python:3.12-slim-bookworm",
            dockerfile,
            count=1,
            flags=re.MULTILINE,
        )
    if re.search(r"^FROM ubuntu:24\.04\s*$", dockerfile, re.MULTILINE):
        if "python3-pip" not in dockerfile:
            raise ValueError("Ubuntu judge image does not install python3-pip")
        install = (
            "RUN python3 -m pip install --no-cache-dir --break-system-packages "
            f"{REWARDKIT_PACKAGE}"
        )
    elif re.search(r"^FROM python:3\.12", dockerfile, re.MULTILINE):
        install = f"RUN python3 -m pip install --no-cache-dir {REWARDKIT_PACKAGE}"
    else:
        raise ValueError(
            "judge image must provide Python 3.12 through a supported base"
        )
    return dockerfile.rstrip() + "\n" + install + "\n"


def patch_task_toml(task_toml: str) -> str:
    """Expose provider routing to RewardKit while preserving existing settings."""
    additions = {
        "REWARDKIT_JUDGE": "${JUDGE_MODEL:-openai/gpt-4o-mini}",
    }
    inline = re.search(r"(?m)^\s*env\s*=\s*\{(.*)\}\s*$", task_toml)
    if inline:
        body = inline.group(1).strip()
        for key, value in additions.items():
            if re.search(rf"\b{re.escape(key)}\s*=", body):
                continue
            body = f'{body}, {key} = "{value}"' if body else f'{key} = "{value}"'
        replacement = f"env = {{ {body} }}"
        return task_toml[: inline.start()] + replacement + task_toml[inline.end() :]

    section = re.search(r"(?m)^\s*\[verifier\.env\]\s*$", task_toml)
    lines = [
        f'{key} = "{value}"'
        for key, value in additions.items()
        if not re.search(rf"(?m)^\s*{key}\s*=", task_toml)
    ]
    if not lines:
        return task_toml
    if section:
        insert_at = task_toml.find("\n[", section.end())
        if insert_at < 0:
            insert_at = len(task_toml)
        return (
            task_toml[:insert_at].rstrip()
            + "\n"
            + "\n".join(lines)
            + "\n"
            + task_toml[insert_at:].lstrip("\n")
        )
    return task_toml.rstrip() + "\n\n[verifier.env]\n" + "\n".join(lines) + "\n"


def _archive_files(
    task_binary: bytes,
) -> tuple[list[tarfile.TarInfo], dict[str, bytes]]:
    members: list[tarfile.TarInfo] = []
    files: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(task_binary), mode="r:*") as archive:
        for member in archive.getmembers():
            if member.name.startswith("/") or ".." in member.name.split("/"):
                raise ValueError(f"unsafe archive member: {member.name}")
            if member.issym() or member.islnk():
                raise ValueError(
                    f"links are not allowed in task archives: {member.name}"
                )
            members.append(copy.copy(member))
            if member.isfile():
                extracted = archive.extractfile(member)
                if extracted is None:
                    raise ValueError(f"could not read archive member: {member.name}")
                files[member.name] = extracted.read()
    return members, files


def _write_archive(members: list[tarfile.TarInfo], files: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with gzip.GzipFile(fileobj=output, mode="wb", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w") as archive:
            existing = set()
            for original in members:
                if original.name not in files or not original.isfile():
                    if original.isfile():
                        continue
                    archive.addfile(original)
                    continue
                content = files[original.name]
                member = copy.copy(original)
                member.size = len(content)
                member.mtime = 0
                archive.addfile(member, io.BytesIO(content))
                existing.add(original.name)
            for name in sorted(set(files) - existing):
                content = files[name]
                member = tarfile.TarInfo(name)
                member.size = len(content)
                member.mtime = 0
                member.mode = (
                    0o755
                    if name in {"tests/test.sh", "tests/deterministic_gate"}
                    else 0o644
                )
                archive.addfile(member, io.BytesIO(content))
    return output.getvalue()


def migrate_task_binary(task_binary: bytes) -> tuple[bytes, ArchiveMigration | None]:
    """Migrate one task archive; return the original bytes when no judge exists."""
    members, files = _archive_files(task_binary)
    classified = classify_judge(files)
    if classified is None:
        return task_binary, None
    family, judge_member = classified
    data = json.loads(files.get("tests/verifier_data.json", b"{}"))
    judge_toml = render_judge_toml(family, data)
    gate = None
    if family == "hybrid":
        gate = render_hybrid_gate(files[judge_member].decode("utf-8"))

    files.pop("tests/verifier.py", None)
    files.pop("tests/test_state.py", None)
    files["tests/test.sh"] = REWARDKIT_TEST_SH.encode("utf-8")
    files["environment/Dockerfile"] = patch_dockerfile(
        files["environment/Dockerfile"].decode("utf-8")
    ).encode("utf-8")
    files["task.toml"] = patch_task_toml(files["task.toml"].decode("utf-8")).encode(
        "utf-8"
    )
    if judge_toml is not None:
        files["tests/judge.toml"] = judge_toml.encode("utf-8")
    if gate is not None:
        files["tests/deterministic_gate"] = gate.encode("utf-8")

    return _write_archive(members, files), ArchiveMigration(
        family=family,
        has_judge=judge_toml is not None,
        has_deterministic_gate=gate is not None,
    )

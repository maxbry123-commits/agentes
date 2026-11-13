"""Core adapter: HarborTask dataclass, sanitizers, tarball builder.

Security invariants enforced by this module:
  1. No untrusted string is ever interpolated into Dockerfile / bash / Python
     source. Verifier inputs are written to /tests/verifier_data.json (JSON) and
     read by the embedded verifier at runtime.
  2. Base images come from a name-pinned registry (PINNED_BASE_IMAGES);
     optional sha256 digests can be populated to upgrade to digest-pinned.
  3. All text inputs pass through `sanitize_text()` which strips control
     characters (except whitespace) and enforces length caps.
  4. setup_files / extra_files paths are validated against
     `_SAFE_PATH_RE` (no `..`, no absolute paths, no NUL bytes).
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import tarfile
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import PurePosixPath

from data.tasktrove.rewardkit_migration import migrate_task_binary


# Name-pinned base image registry. Values are the expected sha256 digest if
# known; None means "name-pinned only". A digest may be added later by running
# `docker manifest inspect <image>` and populating the value; once non-None,
# `_assert_pinned_image` will require the Dockerfile FROM to use the
# `image@sha256:<digest>` form and the digest to match.
PINNED_BASE_IMAGES: dict[str, str | None] = {
    "python:3.11-slim-bookworm": None,
}


_SAFE_PATH_RE = re.compile(r"^[A-Za-z0-9_./\-]+$")
_MAX_TEXT_LEN = 256 * 1024
_MAX_PATH_LEN = 512


class SanitizationError(ValueError):
    """Raised when dataset content fails security validation."""


def sanitize_text(
    value: object, *, field_name: str, max_len: int = _MAX_TEXT_LEN
) -> str:
    """Coerce to str, strip C0/C1 control chars except \\t \\n \\r, cap length.

    Anything that isn't a string is rejected — the caller is expected to do
    type coercion explicitly so we don't paper over schema drift.
    """
    if not isinstance(value, str):
        raise SanitizationError(
            f"{field_name}: expected str, got {type(value).__name__}"
        )
    if len(value) > max_len:
        raise SanitizationError(
            f"{field_name}: length {len(value)} exceeds cap {max_len}"
        )
    out_chars = []
    for ch in value:
        if ch in ("\t", "\n", "\r"):
            out_chars.append(ch)
            continue
        if unicodedata.category(ch)[0] == "C":
            continue
        out_chars.append(ch)
    return "".join(out_chars)


def validate_path(path: str) -> str:
    if not isinstance(path, str):
        raise SanitizationError(f"path must be str, got {type(path).__name__}")
    if not path or len(path) > _MAX_PATH_LEN:
        raise SanitizationError(f"path length out of range: {len(path)}")
    if "\x00" in path:
        raise SanitizationError("path contains NUL")
    p = PurePosixPath(path)
    if p.is_absolute():
        raise SanitizationError(f"path must be relative: {path!r}")
    if any(part == ".." for part in p.parts):
        raise SanitizationError(f"path traversal not allowed: {path!r}")
    if not _SAFE_PATH_RE.match(path):
        raise SanitizationError(f"path contains unsafe chars: {path!r}")
    return path


def _json_safe(value):
    """Recursively check that `value` is JSON-serializable via a dry-run dump."""
    json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True)
    return value


@dataclass(frozen=True)
class HarborTask:
    """A Harbor-format task ready to serialize as a tarball.

    Fields mirror the file layout the Harbor runtime expects:
      - instruction.md
      - environment/Dockerfile
      - tests/test.sh
      - tests/verifier.py            (from `verifier_py`)
      - tests/verifier_data.json     (from `verifier_data`)
      - metadata.json                (from `metadata`)
      - task.toml                    (from `task_toml`)
      - setup_files/<...>            (mounted at trial start by Harbor)
      - <extra_files>                (free-form additional files at task root)
    """

    task_id: str
    instruction_md: str
    dockerfile: str
    test_sh: str
    verifier_py: str
    verifier_data: dict
    metadata: dict
    task_toml: str = ""
    setup_files: dict[str, bytes] = field(default_factory=dict)
    extra_files: dict[str, bytes] = field(default_factory=dict)

    def __post_init__(self):
        sanitize_text(self.task_id, field_name="task_id", max_len=256)
        sanitize_text(self.instruction_md, field_name="instruction_md")
        sanitize_text(self.dockerfile, field_name="dockerfile")
        sanitize_text(self.test_sh, field_name="test_sh")
        sanitize_text(self.verifier_py, field_name="verifier_py")
        sanitize_text(self.task_toml, field_name="task_toml")
        _json_safe(self.verifier_data)
        _json_safe(self.metadata)
        for p in list(self.setup_files) + list(self.extra_files):
            validate_path(p)
        self._assert_pinned_image()

    def _assert_pinned_image(self) -> None:
        m = re.search(r"^\s*FROM\s+([^\s]+)", self.dockerfile, flags=re.MULTILINE)
        if not m:
            raise SanitizationError("Dockerfile missing FROM directive")
        image = m.group(1)
        bare, _, dgst = image.partition("@")
        if bare not in PINNED_BASE_IMAGES:
            raise SanitizationError(
                f"Dockerfile base image {bare!r} not in pinned registry: "
                f"{sorted(PINNED_BASE_IMAGES)}"
            )
        expected = PINNED_BASE_IMAGES[bare]
        if expected is not None:
            if not dgst:
                raise SanitizationError(
                    f"image {bare!r} requires digest-pinned form @sha256:..."
                )
            if dgst != expected:
                raise SanitizationError(
                    f"image {bare!r} digest mismatch: got {dgst!r}, expected {expected!r}"
                )

    def to_tarball(self) -> bytes:
        """Serialize this task as a deterministic gzipped tar.

        Deterministic = sorted file entries, mtime=0, uid/gid=0,
        uname/gname empty. This makes upload hashes reproducible.
        """
        buf = io.BytesIO()
        entries: list[tuple[str, bytes]] = []

        def add(path: str, content: bytes | str) -> None:
            validate_path(path)
            if isinstance(content, str):
                content = content.encode("utf-8")
            entries.append((path, content))

        add("instruction.md", self.instruction_md)
        add("environment/Dockerfile", self.dockerfile)
        add("tests/test.sh", self.test_sh)
        add("tests/verifier.py", self.verifier_py)
        add(
            "tests/verifier_data.json",
            json.dumps(
                self.verifier_data,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                indent=2,
            ),
        )
        add(
            "metadata.json",
            json.dumps(
                self.metadata,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                indent=2,
            ),
        )
        add("task.toml", self.task_toml or DEFAULT_TASK_TOML)
        for p, content in self.setup_files.items():
            add(f"setup_files/{p}", content)
        for p, content in self.extra_files.items():
            add(p, content)

        entries.sort(key=lambda kv: kv[0])

        with tarfile.open(fileobj=buf, mode="w:gz", compresslevel=6) as tar:
            for path, content in entries:
                info = tarfile.TarInfo(name=path)
                info.size = len(content)
                info.mtime = 0
                info.uid = 0
                info.gid = 0
                info.uname = ""
                info.gname = ""
                info.mode = 0o644
                tar.addfile(info, io.BytesIO(content))
        task_binary = buf.getvalue()
        if "litellm" not in self.verifier_py:
            return task_binary

        # Normalize legacy hand-written LLM judges at the serialization boundary.
        # RewardKit preserves judge failures as infrastructure failures instead of
        # turning them into scoreable zero rewards.
        migrated, migration = migrate_task_binary(task_binary)
        if migration is None:
            raise ValueError(
                "LLM judge verifier was not recognized for RewardKit migration"
            )
        return migrated


def task_id_for(prefix: str, payload: str | bytes) -> str:
    """Deterministic short task ID from a dataset slug + row payload."""
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()[:12]
    return f"{prefix}-{digest}"


PINNED_DOCKERFILE_HEADER = (
    "# DO NOT EDIT — generated by nemotron_gym adapter.\n"
    "# Base image is restricted by adapter.PINNED_BASE_IMAGES.\n"
)


def render_dockerfile(
    *,
    base: str,
    pip_packages: tuple[str, ...] = (),
    apt_packages: tuple[str, ...] = (),
) -> str:
    """Build a Dockerfile pinned against the adapter's image registry.

    pip_packages must be a tuple of pre-validated package specs (no shell
    metacharacters). We re-validate here anyway as a belt-and-braces check.

    apt_packages must be a tuple of Debian package names (alphanumeric, with
    `+`, `-`, `.`, and `:` allowed for things like `g++` and `libfoo-dev:amd64`).
    When non-empty, the rendered Dockerfile runs `apt-get update && apt-get
    install -y --no-install-recommends ...` before the pip step so that pip can
    build sdists that need compilers/headers (e.g. `pycosat`).
    """
    if base not in PINNED_BASE_IMAGES:
        raise SanitizationError(f"base image not pinned: {base!r}")
    pip_re = re.compile(
        r"^[A-Za-z0-9._\-]+(\[[A-Za-z0-9._\-,]+\])?(==[A-Za-z0-9._\-+]+)?$"
    )
    for pkg in pip_packages:
        if not pip_re.match(pkg):
            raise SanitizationError(f"unsafe pip package spec: {pkg!r}")
    apt_re = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.+\-:]*$")
    for pkg in apt_packages:
        if not apt_re.match(pkg):
            raise SanitizationError(f"unsafe apt package spec: {pkg!r}")
    lines = [
        PINNED_DOCKERFILE_HEADER,
        f"FROM {base}",
        "ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1",
        "RUN mkdir -p /app /tests /logs/verifier && chmod 755 /app /tests",
    ]
    if apt_packages:
        joined_apt = " ".join(apt_packages)
        lines.append(
            "RUN apt-get update "
            f"&& apt-get install -y --no-install-recommends {joined_apt} "
            "&& rm -rf /var/lib/apt/lists/*"
        )
    if pip_packages:
        joined = " ".join(pip_packages)
        lines.append(f"RUN pip install --no-cache-dir {joined}")
    lines.append("WORKDIR /app")
    return "\n".join(lines) + "\n"


STANDARD_TEST_SH = """#!/bin/bash
# DO NOT EDIT — generated by nemotron_gym adapter.
# Reads /tests/verifier_data.json + agent output from /app, writes
# /logs/verifier/reward.txt (one of "0" / "1").
set -euo pipefail
mkdir -p /logs/verifier
rm -f /logs/verifier/reward.txt
python3 /tests/verifier.py >> /logs/verifier/test-stdout.txt 2>&1
test -s /logs/verifier/reward.txt
grep -Eq '^(0|1)$' /logs/verifier/reward.txt
"""


def answer_delivery_guidance(
    path: str = "/app/answer.txt", *, what: str = "your answer"
) -> str:
    """Canonical instruction block teaching a TERMINAL agent how to submit.

    Root cause this fixes: the validate harness runs `terminus-2` (a tmux/shell
    agent). Its chat reply is NOT read by the verifier — only files inside the
    sandbox are. Tasks that merely said "write to /app/answer.txt" without
    showing HOW saw ~100% "answer.txt missing -> reward 0" because the model
    emitted the answer as its response instead of running a shell command.
    The proven fix (validated by the science task, which dropped to ~16% miss)
    is to show the heredoc explicitly + tell the agent to verify + note that a
    missing file scores 0. Pass the exact path your verifier reads.
    """
    return (
        "\n\n## Submitting your answer (IMPORTANT)\n"
        "You are a terminal agent. Your chat reply is NOT graded — the grader "
        f"only reads the file `{path}` inside the sandbox. You MUST write {what} "
        f"to `{path}` by RUNNING A SHELL COMMAND, e.g. a heredoc:\n\n"
        f"    cat > {path} <<'EOF'\n"
        f"    <{what} here>\n"
        "    EOF\n\n"
        f"Then confirm it with `cat {path}`. An empty or missing `{path}` "
        "scores 0 regardless of what you wrote in your reply.\n"
    )


# Mirrors the structure of Harbor's src/harbor/cli/template-task/task.toml.
# Converters may override via HarborTask.task_toml; if empty, this default is
# emitted at serialization time.
DEFAULT_TASK_TOML = """version = "1.0"

[metadata]
adapter = "nemotron_gym"

[verifier]
timeout_sec = 600.0

[agent]
timeout_sec = 900.0

[environment]
build_timeout_sec = 600.0
cpus = 1
memory_mb = 4096
storage_mb = 10240
"""


# Variant for LLM-judge tasks: same as DEFAULT_TASK_TOML, but with
# `[verifier.env]` propagating OPENAI_API_KEY / JUDGE_MODEL / OPENAI_BASE_URL
# from the Harbor host into the verifier container. Without this, the embedded
# litellm-based judge inside the verifier sandbox has no credentials and every
# call fails with "Missing credentials. Please pass an `api_key`...", causing a
# universal 0.0 reward across every task. Matches the Harbor convention used
# by adapters/strongreject/src/strongreject/task-template/task.toml.
#
# OPENAI_API_KEY is REQUIRED (no default) — if unset on the host, the trial
# raises a clear ValueError at verify time instead of silently scoring 0.0.
# JUDGE_MODEL / OPENAI_BASE_URL use empty `${VAR:-}` defaults so trials run
# fine without them (the verifier falls back to gpt-4o-mini + default base).
LLM_JUDGE_TASK_TOML = """version = "1.0"

[metadata]
adapter = "nemotron_gym"

[verifier]
timeout_sec = 600.0
env = { OPENAI_API_KEY = "${OPENAI_API_KEY}", JUDGE_MODEL = "${JUDGE_MODEL:-}" }

[agent]
timeout_sec = 900.0

[environment]
build_timeout_sec = 600.0
cpus = 1
memory_mb = 4096
storage_mb = 10240
"""


_now = int(time.time())


def render_metadata(
    *, source_dataset: str, source_uuid: str | None, extra: dict | None = None
) -> dict:
    base = {
        "source": "nemotron_gym",
        "source_dataset": source_dataset,
        "adapter_version": 1,
        "adapter_built_at": _now,
    }
    if source_uuid is not None:
        base["source_uuid"] = source_uuid
    if extra:
        base.update(extra)
    return base

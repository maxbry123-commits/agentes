"""YAIWES ABI adapter for yaiwes.loop.temporal_python. Does not execute vendor source during registration."""
from pathlib import Path
import hashlib

PLUGIN_ID = 'yaiwes.loop.temporal_python'
ROLE = 'durable_execution_replay'
SOURCE_PATH = 'Agente Yaiwes principal/execution-orchestration/state-machine-executor/temporal-python-sdk/SOURCE_COMMIT.txt'
SOURCE_KIND = 'marker'
EXPECTED = '22a9e41fd857261ee0a9bb5ce57f439d93e7f88d'

def _git_blob_sha(path):
    data = path.read_bytes()
    return hashlib.sha1((f"blob {len(data)}\0").encode() + data).hexdigest()

def health(repo_root):
    p = Path(repo_root) / SOURCE_PATH
    if not p.is_file():
        return False
    if SOURCE_KIND == "marker":
        return p.read_text(encoding="utf-8").strip() == EXPECTED
    return _git_blob_sha(p) == EXPECTED

def descriptor():
    return {"plugin_id": PLUGIN_ID, "role": ROLE, "source_path": SOURCE_PATH, "source_kind": SOURCE_KIND, "expected": EXPECTED}

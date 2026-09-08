"""YAIWES ABI adapter for yaiwes.loop.hatchet_python. Does not execute vendor source during registration."""
from pathlib import Path
import hashlib

PLUGIN_ID = 'yaiwes.loop.hatchet_python'
ROLE = 'durable_task_orchestration'
SOURCE_PATH = 'Agente Yaiwes principal/execution-orchestration/dag-executor/hatchet-python-sdk/SOURCE_COMMIT.txt'
SOURCE_KIND = 'marker'
EXPECTED = '086a63f2245416296de288a944aad1b8357e63e9'

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

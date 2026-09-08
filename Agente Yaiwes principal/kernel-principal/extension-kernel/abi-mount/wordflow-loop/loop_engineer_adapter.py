"""YAIWES ABI adapter for yaiwes.loop.loop_engineer. Does not execute vendor source during registration."""
from pathlib import Path
import hashlib

PLUGIN_ID = 'yaiwes.loop.loop_engineer'
ROLE = 'serial_loop_runtime_recovery'
SOURCE_PATH = 'Agente Yaiwes principal/execution-orchestration/deterministic-execution/loop-engineer/SOURCE_COMMIT.txt'
SOURCE_KIND = 'marker'
EXPECTED = '0ca97d7c7e8a2e20e986d18e273c6171a2684d30'

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

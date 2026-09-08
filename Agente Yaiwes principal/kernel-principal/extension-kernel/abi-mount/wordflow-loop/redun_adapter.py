"""YAIWES ABI adapter for yaiwes.loop.redun. Does not execute vendor source during registration."""
from pathlib import Path
import hashlib

PLUGIN_ID = 'yaiwes.loop.redun'
ROLE = 'dag_scheduler_cache'
SOURCE_PATH = 'Agente Yaiwes principal/execution-orchestration/dag-executor/redun/SOURCE_COMMIT.txt'
SOURCE_KIND = 'marker'
EXPECTED = '49a299b223bc345b999aaa40daa6876f105089e1'

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

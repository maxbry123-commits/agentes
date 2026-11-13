"""YAIWES ABI adapter for yaiwes.runtime.instance_pool. Does not execute vendor source during registration."""
from pathlib import Path
import hashlib

PLUGIN_ID = 'yaiwes.runtime.instance_pool'
ROLE = 'execution_instance_pool'
SOURCE_PATH = 'Agente Yaiwes principal/execution-engine-pool/instance_pool.py'
SOURCE_KIND = 'gitblob'
EXPECTED = 'cf537a34515baac2cc9919c59ca40c4c09da0672'

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

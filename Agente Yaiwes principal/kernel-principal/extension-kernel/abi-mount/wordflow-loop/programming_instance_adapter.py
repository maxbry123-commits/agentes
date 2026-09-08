"""YAIWES ABI adapter for yaiwes.runtime.programming_instance. Does not execute vendor source during registration."""
from pathlib import Path
import hashlib

PLUGIN_ID = 'yaiwes.runtime.programming_instance'
ROLE = 'programming_pipeline_instance'
SOURCE_PATH = 'Agente Yaiwes principal/execution-orchestration/programming-pipeline/programming_instance.py'
SOURCE_KIND = 'gitblob'
EXPECTED = '1dd88384765a182f1f299bfeb119d42ac00ec324'

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

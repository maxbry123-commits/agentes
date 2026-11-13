"""YAIWES ABI adapter for yaiwes.runtime.capability_registration. Does not execute vendor source during registration."""
from pathlib import Path
import hashlib

PLUGIN_ID = 'yaiwes.runtime.capability_registration'
ROLE = 'capability_registry_registration'
SOURCE_PATH = 'Agente Yaiwes principal/kernel-principal/extension-kernel/capability-registry/capability_registration.py'
SOURCE_KIND = 'gitblob'
EXPECTED = 'd205e86d0379844162e612317b2737ed8b62ece9'

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

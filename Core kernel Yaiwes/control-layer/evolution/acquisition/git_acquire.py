"""Git acquire determinista · pin ref + tree sha256."""
from __future__ import annotations
import hashlib, json, subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

@dataclass
class GitAcquireResult:
    ok: bool
    path: str
    repo_url: str
    ref: str
    commit: str
    tree_sha256: str
    error: str = ""
    def to_dict(self):
        return asdict(self)

class GitAcquire:
    def __init__(self, cache_dir="evolution/sources"):
        self.cache = Path(cache_dir)
        self.cache.mkdir(parents=True, exist_ok=True)

    def acquire(self, *, repo_url, ref, dest_id, expected_tree_sha256="", depth=1):
        dest = self.cache / dest_id
        if dest.exists():
            import shutil
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(["git", "clone", "--depth", str(depth), "--branch", ref, repo_url, str(dest)], check=True, capture_output=True, text=True, timeout=120)
        except subprocess.CalledProcessError as e:
            try:
                subprocess.run(["git", "clone", "--depth", str(depth), repo_url, str(dest)], check=True, capture_output=True, text=True, timeout=120)
                subprocess.run(["git", "-C", str(dest), "checkout", ref], check=True, capture_output=True, text=True, timeout=60)
            except Exception as e2:
                return GitAcquireResult(False, str(dest), repo_url, ref, "", "", str(e2) or str(e))
        except Exception as e:
            return GitAcquireResult(False, str(dest), repo_url, ref, "", "", str(e))
        commit = self._rev_parse(dest)
        tree_hash = self._tree_hash(dest)
        if expected_tree_sha256 and expected_tree_sha256 != tree_hash:
            return GitAcquireResult(False, str(dest), repo_url, ref, commit, tree_hash, "tree_sha256_mismatch")
        (dest / "SOURCE_RECEIPT.json").write_text(json.dumps({"repo_url": repo_url, "ref": ref, "commit": commit, "tree_sha256": tree_hash}, indent=2), encoding="utf-8")
        return GitAcquireResult(True, str(dest), repo_url, ref, commit, tree_hash)

    def _rev_parse(self, path):
        try:
            r = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
            return r.stdout.strip()
        except Exception:
            return ""

    def _tree_hash(self, root):
        h = hashlib.sha256()
        for p in sorted(root.rglob("*")):
            if p.is_file() and ".git" not in p.parts and p.name != "SOURCE_RECEIPT.json":
                h.update(p.relative_to(root).as_posix().encode())
                try:
                    h.update(p.read_bytes()[:65536])
                except OSError:
                    pass
        return h.hexdigest()

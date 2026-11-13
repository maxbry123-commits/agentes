"""Source Store · sources/ separado de runtime/extensions."""
from __future__ import annotations
import hashlib, json, shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

@dataclass
class SourceReceipt:
    id: str
    path: str
    sha256_tree: str
    ref: str = ""
    repo_url: str = ""
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

class SourceStore:
    def __init__(self, base: str | Path = "evolution/sources") -> None:
        self.base = Path(base)
        self.base.mkdir(parents=True, exist_ok=True)

    def register_local(self, source_id: str, local_path: str | Path, *, ref: str = "", repo_url: str = "") -> SourceReceipt:
        src = Path(local_path)
        dest = self.base / source_id
        if dest.exists():
            shutil.rmtree(dest)
        if src.is_dir():
            shutil.copytree(src, dest, ignore=shutil.ignore_patterns(".git", "node_modules", "venv", ".venv", "__pycache__"))
        else:
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest / src.name)
        digest = self._tree_hash(dest)
        receipt = SourceReceipt(source_id, str(dest), digest, ref, repo_url)
        (dest / "SOURCE_RECEIPT.json").write_text(json.dumps(receipt.to_dict(), indent=2), encoding="utf-8")
        return receipt

    def _tree_hash(self, root: Path) -> str:
        h = hashlib.sha256()
        for p in sorted(root.rglob("*")):
            if p.is_file() and p.name != "SOURCE_RECEIPT.json":
                h.update(p.relative_to(root).as_posix().encode())
                h.update(p.read_bytes()[:65536])
        return h.hexdigest()

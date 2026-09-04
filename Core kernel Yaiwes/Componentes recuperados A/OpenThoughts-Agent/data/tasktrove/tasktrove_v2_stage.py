"""Download each of the 96 v2 datasets into tasktrove_v2/<org>__<name>/.

Resumable: skips datasets whose target dir already has a non-empty README.md
or any *.parquet file. Logs per-dataset success/failure to staging.log.
"""

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tasktrove_v2_datasets import ALL

from huggingface_hub import snapshot_download
from huggingface_hub.utils import HfHubHTTPError, RepositoryNotFoundError

ROOT = Path("/Users/benjaminfeuer/Documents/scaling_laws_papers/tasktrove_v2")
LOG = ROOT / "staging.log"
ROOT.mkdir(exist_ok=True, parents=True)


def log(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with LOG.open("a") as fh:
        fh.write(line + "\n")


def already_done(target: Path) -> bool:
    if not target.exists():
        return False
    has_parquet = any(p.suffix == ".parquet" for p in target.rglob("*"))
    return has_parquet


def stage_one(repo_id: str, difficulty: str) -> tuple[str, str]:
    org, name = repo_id.split("/", 1)
    safe = f"{org}__{name}"
    target = ROOT / safe
    if already_done(target):
        return ("skip", safe)
    target.mkdir(parents=True, exist_ok=True)
    try:
        snapshot_download(
            repo_id=repo_id,
            repo_type="dataset",
            local_dir=str(target),
            allow_patterns=[
                "*.parquet",
                "*.json",
                "*.md",
                "*.txt",
                "*.yaml",
                "*.yml",
                ".gitattributes",
            ],
            max_workers=4,
        )
        return ("ok", safe)
    except RepositoryNotFoundError as e:
        return ("missing", f"{safe}: {e}")
    except HfHubHTTPError as e:
        return ("http_error", f"{safe}: {e}")
    except Exception as e:
        return ("error", f"{safe}: {e}")


def main():
    log(f"Staging {len(ALL)} datasets into {ROOT}")
    counts = {"ok": 0, "skip": 0, "missing": 0, "http_error": 0, "error": 0}
    for i, (repo_id, diff) in enumerate(ALL, start=1):
        log(f"[{i}/{len(ALL)}] {repo_id} ({diff})")
        status, msg = stage_one(repo_id, diff)
        counts[status] += 1
        log(f"    -> {status}: {msg}")
    log(f"DONE counts={counts}")


if __name__ == "__main__":
    main()

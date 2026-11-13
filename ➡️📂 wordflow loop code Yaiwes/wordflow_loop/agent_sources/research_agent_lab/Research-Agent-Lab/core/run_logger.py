from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json


class RunLogger:
    def write(self, run_dir: Path, event: str, payload: dict[str, Any] | None = None) -> None:
        run_dir.mkdir(parents=True, exist_ok=True)
        row = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "payload": payload or {},
        }
        with (run_dir / "run_log.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

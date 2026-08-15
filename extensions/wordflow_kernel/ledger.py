import hashlib
import json
import time
from pathlib import Path


class MissionLedger:
    """Hash-chained append-only mission ledger."""

    def __init__(self, root="state/ledger"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def append(self, mission_id, event: dict):
        path = self.root / f"{mission_id}.jsonl"
        previous = ""
        if path.exists():
            lines = path.read_text(encoding="utf-8").splitlines()
            if lines:
                previous = json.loads(lines[-1]).get("hash", "")
        body = {"timestamp": time.time(), "previous_hash": previous, **event}
        body["hash"] = hashlib.sha256(
            json.dumps(body, sort_keys=True, default=str).encode()
        ).hexdigest()
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(body, sort_keys=True, default=str) + "\n")
        return body

    def verify(self, mission_id):
        path = self.root / f"{mission_id}.jsonl"
        if not path.exists():
            return True
        previous = ""
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row["previous_hash"] != previous:
                return False
            supplied = row.pop("hash")
            expected = hashlib.sha256(
                json.dumps(row, sort_keys=True, default=str).encode()
            ).hexdigest()
            if supplied != expected:
                return False
            previous = supplied
        return True

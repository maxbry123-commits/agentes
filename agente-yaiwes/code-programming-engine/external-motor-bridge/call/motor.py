"""CallMotor — T0.2 native. Llama code/tools de otros repos multi-cuenta con trazabilidad."""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

@dataclass
class CallRequest:
    owner: str
    repo: str
    path: str
    ref: str = "main"
    credential_ref: Optional[str] = None

class CallMotor:
    def __init__(self):
        self.name = "call_motor"
        self.trace: List[Dict] = []

    def execute(self, req: CallRequest) -> Dict[str, Any]:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "req": req.__dict__,
            "action": "get_file_contents"
        }
        self.trace.append(entry)
        return {
            "status": "READY",
            "motor": self.name,
            "trace_id": len(self.trace),
            "target": f"{req.owner}/{req.repo}:{req.path}@{req.ref}",
            "next": "github___get_file_contents + append trace",
            "note": "Trazabilidad completa en self.trace"
        }

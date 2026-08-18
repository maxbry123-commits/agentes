"""CallMotor — T0.2 native. Llama code/tools de otros repos multi-cuenta con trazabilidad."""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

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
        self.trace.append({"ts": "now", "req": req.__dict__})
        return {
            "status": "PENDING",
            "motor": self.name,
            "trace_id": len(self.trace),
            "next": "github___get_file_contents + trazabilidad"
        }

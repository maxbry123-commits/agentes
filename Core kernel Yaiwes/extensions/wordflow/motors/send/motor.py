"""SendMotor — T0.1 native kernel extension.
Envía documentos/code a repos de otras cuentas GitHub vía Actions + credential_ref.
No almacena PAT en git. Usa EXTERNAL_GH_B_TOKEN secret.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class SendRequest:
    source_path: str
    target_owner: str
    target_repo: str
    target_path: str
    credential_ref: str = "EXTERNAL_GH_B_TOKEN"
    content: Optional[str] = None  # si None → leer source_path

class SendMotor:
    """Motor nativo: push/create file cross-account via bridge."""
    def __init__(self, connector_cfg: Optional[Dict] = None):
        self.cfg = connector_cfg or {}
        self.name = "send_motor"

    def execute(self, req: SendRequest) -> Dict[str, Any]:
        # Deterministic path: github___create_or_update_file o workflow_dispatch
        # credential_ref resuelve secret sin escribir PAT en repo
        return {
            "status": "READY",
            "motor": self.name,
            "req": {
                "source_path": req.source_path,
                "target": f"{req.target_owner}/{req.target_repo}:{req.target_path}",
                "credential_ref": req.credential_ref
            },
            "next": "github___create_or_update_file | Actions bridge",
            "note": "No PAT in git. EXTERNAL_GH_B_TOKEN only via secret."
        }

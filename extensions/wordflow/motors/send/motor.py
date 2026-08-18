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

class SendMotor:
    """Motor nativo: push/create file cross-account via bridge workflow."""
    def __init__(self, connector_cfg: Optional[Dict] = None):
        self.cfg = connector_cfg or {}
        self.name = "send_motor"

    def execute(self, req: SendRequest) -> Dict[str, Any]:
        return {
            "status": "PENDING_BRIDGE",
            "motor": self.name,
            "req": req.__dict__,
            "next": "call github___create_or_update_file or Actions"
        }

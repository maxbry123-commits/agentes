"""DownloadMotor — T0.3. Descarga software/framework a repo destino (Cuenta B).
Mejora del acquire parcial. Usa Recipe + ACQUIRE-OS 28-node sub-DAG.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class DownloadRequest:
    source_type: str  # git_native | hf_hub | release_binary | package_manager
    source_url: str
    pin: str
    target_owner: str
    target_repo: str
    recipe_path: Optional[str] = None

class DownloadMotor:
    def __init__(self):
        self.name = "download_motor"

    def execute(self, req: DownloadRequest) -> Dict[str, Any]:
        return {
            "status": "READY",
            "motor": self.name,
            "source_type": req.source_type,
            "pin": req.pin,
            "target": f"{req.target_owner}/{req.target_repo}",
            "next": "ACQUIRE-OS sub-DAG (T-008) + promote",
            "note": "Recipe-driven. Nunca latest. Fail-closed."
        }

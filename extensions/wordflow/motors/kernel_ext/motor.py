"""KernelExtMotor — T0.4. Une los 3 motors + recepción/conversión como extensión nativa kernel.
Agente sabe usar cada motor. Sub-Wordflow.
Knowledge: si se pierde enlace reception → regenerar o devolver desde KNOWLEDGE_RECEPTION_LINKS.md
"""
from typing import Dict, Any
from ..send.motor import SendMotor, SendRequest
from ..call.motor import CallMotor, CallRequest
from ..download.motor import DownloadMotor, DownloadRequest

class KernelExtMotor:
    def __init__(self):
        self.name = "kernel_ext_motor"
        self.send = SendMotor()
        self.call = CallMotor()
        self.download = DownloadMotor()
        self.reception_links = {
            "agentes": "https://github.com/maxbry123-commits/agentes/blob/main/extensions/wordflow/reception/RECEPTION_agentes.md",
            "osquestador-auditor": "https://github.com/maxbry123-commits/osquestador-auditor/blob/main/RECEPTION_osquestador-auditor.md",
            "comand-Center": "https://github.com/maxbry123-commits/comand-Center/blob/main/RECEPTION_comand-Center.md",
        }

    def get_reception_link(self, repo: str) -> str:
        """Si el usuario pierde el enlace, el agente usa este método."""
        return self.reception_links.get(repo, f"Crear RECEPTION_{repo}.md y devolver enlace nuevo")

    def dispatch(self, motor: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if motor == "send":
            return self.send.execute(SendRequest(**payload))
        if motor == "call":
            return self.call.execute(CallRequest(**payload))
        if motor == "download":
            return self.download.execute(DownloadRequest(**payload))
        if motor == "reception_link":
            return {"status": "OK", "link": self.get_reception_link(payload.get("repo", "agentes"))}
        return {"status": "UNKNOWN_MOTOR", "motor": motor}

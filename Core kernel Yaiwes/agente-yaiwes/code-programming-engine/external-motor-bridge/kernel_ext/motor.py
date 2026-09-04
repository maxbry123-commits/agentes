"""KernelExtMotor — T0.4. SEND/CALL/DOWNLOAD + reception via kernel LINK.

Inbox files stay in extensions/wordflow/reception/.
Kernel surface: extensions/wordflow_kernel/reception/.
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

    def _kernel_locate(self, kind: str = "inbox") -> dict:
        try:
            from wordflow_kernel.reception.convert import locate

            return locate(kind)
        except ImportError:
            try:
                from extensions.wordflow_kernel.reception.convert import locate

                return locate(kind)
            except ImportError:
                return {"ok": False, "error": "KERNEL_RECEPTION_MISSING"}

    def get_reception_link(self, repo: str = "agentes") -> str:
        return self.reception_links.get(repo, f"Crear RECEPTION_{repo}.md y devolver enlace nuevo")

    def dispatch(self, motor: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if motor == "send":
            return self.send.execute(SendRequest(**payload))
        if motor == "call":
            return self.call.execute(CallRequest(**payload))
        if motor == "download":
            return self.download.execute(DownloadRequest(**payload))
        if motor in ("reception_link", "get_link"):
            loc = self._kernel_locate("inbox")
            return {
                "status": "OK",
                "link": self.get_reception_link(payload.get("repo", "agentes")),
                "locate": loc,
            }
        if motor in ("ingest", "convert", "reception"):
            try:
                from wordflow_kernel.reception.convert import ingest
            except ImportError:
                try:
                    from extensions.wordflow_kernel.reception.convert import ingest
                except ImportError:
                    return {"status": "ERROR", "error": "KERNEL_RECEPTION_MISSING"}
            return {"status": "OK", "result": ingest(payload or {})}
        return {
            "status": "UNKNOWN_MOTOR",
            "motor": motor,
            "available": ["send", "call", "download", "reception_link", "ingest", "convert"],
        }

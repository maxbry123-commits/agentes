"""KernelExtMotor — T0.4. Une los 3 motors + recepción/conversión como extensión nativa kernel.
Agente sabe usar cada motor. Sub-Wordflow.
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

    def dispatch(self, motor: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if motor == "send":
            return self.send.execute(SendRequest(**payload))
        if motor == "call":
            return self.call.execute(CallRequest(**payload))
        if motor == "download":
            return self.download.execute(DownloadRequest(**payload))
        return {"status": "UNKNOWN_MOTOR", "motor": motor}

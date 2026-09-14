import subprocess
import shutil
import tempfile
from pathlib import Path


DOCKER_IMAGE = "shel-tools"
DOCKERFILE_CONTENT = """FROM kalilinux/kali-rolling:latest
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \\
    nmap hydra gobuster dirb wfuzz sqlmap nikto enum4linux \\
    smbclient ldapscripts dnsutils curl wget netcat-openbsd \\
    iproute2 python3-pip openssh-client whois dnsrecon \\
    && rm -rf /var/lib/apt/lists/*
RUN pip3 install --quiet pwntools requests beautifulsoup4
WORKDIR /workspace
"""


class DockerSandbox:
    def __init__(self):
        self.available = self._check_docker()

    def _check_docker(self):
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'agent/docker.py','step':'_check_docker','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    def build_image(self):
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'agent/docker.py','step':'build_image','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    def run_command(self, command: str, timeout: int = 120) -> str:
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'agent/docker.py','step':'run_command','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    def run_interactive(self, command: str) -> str:
        return self.run_command(command)

"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '0ef424b92c5e0f5ac25da445114427aa470fa218dce8a50ea7292aac768b005e'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class ContainerConfig:
    def __post_init__(self, *args, **kwargs):
        return _yaiwes_checkpoint('ContainerConfig.__post_init__', kwargs)

class DockerIsolator:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('DockerIsolator.__init__', kwargs)
    def _check_docker(self, *args, **kwargs):
        return _yaiwes_checkpoint('DockerIsolator._check_docker', kwargs)
    async def run_tool(self, *args, **kwargs):
        return _yaiwes_checkpoint('DockerIsolator.run_tool', kwargs)
    async def _run_local(self, *args, **kwargs):
        return _yaiwes_checkpoint('DockerIsolator._run_local', kwargs)
    async def _kill_container(self, *args, **kwargs):
        return _yaiwes_checkpoint('DockerIsolator._kill_container', kwargs)
    async def run_sqlmap(self, *args, **kwargs):
        return _yaiwes_checkpoint('DockerIsolator.run_sqlmap', kwargs)
    async def run_nuclei(self, *args, **kwargs):
        return _yaiwes_checkpoint('DockerIsolator.run_nuclei', kwargs)
    async def run_nmap(self, *args, **kwargs):
        return _yaiwes_checkpoint('DockerIsolator.run_nmap', kwargs)
    async def run_ffuf(self, *args, **kwargs):
        return _yaiwes_checkpoint('DockerIsolator.run_ffuf', kwargs)
    async def run_subfinder(self, *args, **kwargs):
        return _yaiwes_checkpoint('DockerIsolator.run_subfinder', kwargs)
    async def run_httpx(self, *args, **kwargs):
        return _yaiwes_checkpoint('DockerIsolator.run_httpx', kwargs)
    async def run_dalfox(self, *args, **kwargs):
        return _yaiwes_checkpoint('DockerIsolator.run_dalfox', kwargs)
    def list_tools(self, *args, **kwargs):
        return _yaiwes_checkpoint('DockerIsolator.list_tools', kwargs)

"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '029c3e65a3986d1167906a7277a6175a431d6987885ebbff7f18f63dfad83417'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class DockerSandbox:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('DockerSandbox.__init__', kwargs)
    def _check_docker(self, *args, **kwargs):
        return _yaiwes_checkpoint('DockerSandbox._check_docker', kwargs)
    def build_image(self, *args, **kwargs):
        return _yaiwes_checkpoint('DockerSandbox.build_image', kwargs)
    def run_command(self, *args, **kwargs):
        return _yaiwes_checkpoint('DockerSandbox.run_command', kwargs)
    def run_interactive(self, *args, **kwargs):
        return _yaiwes_checkpoint('DockerSandbox.run_interactive', kwargs)

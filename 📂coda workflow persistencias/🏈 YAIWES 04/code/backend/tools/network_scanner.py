"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'c6bff9530ad930098a69587d566e765cdba5c9b335d5ed930c58c180411fced7'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class NetworkScanner:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('NetworkScanner.__init__', kwargs)
    def execute(self, *args, **kwargs):
        return _yaiwes_checkpoint('NetworkScanner.execute', kwargs)
    def _build_command(self, *args, **kwargs):
        return _yaiwes_checkpoint('NetworkScanner._build_command', kwargs)
    def parse_output(self, *args, **kwargs):
        return _yaiwes_checkpoint('NetworkScanner.parse_output', kwargs)
    def _parse_host(self, *args, **kwargs):
        return _yaiwes_checkpoint('NetworkScanner._parse_host', kwargs)
    def _parse_text_output(self, *args, **kwargs):
        return _yaiwes_checkpoint('NetworkScanner._parse_text_output', kwargs)
    def scan_ports(self, *args, **kwargs):
        return _yaiwes_checkpoint('NetworkScanner.scan_ports', kwargs)
    def detect_os(self, *args, **kwargs):
        return _yaiwes_checkpoint('NetworkScanner.detect_os', kwargs)
    def scan_vulns(self, *args, **kwargs):
        return _yaiwes_checkpoint('NetworkScanner.scan_vulns', kwargs)

class MasscanScanner:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('MasscanScanner.__init__', kwargs)
    def execute(self, *args, **kwargs):
        return _yaiwes_checkpoint('MasscanScanner.execute', kwargs)
    def parse_output(self, *args, **kwargs):
        return _yaiwes_checkpoint('MasscanScanner.parse_output', kwargs)
    def _guess_service(self, *args, **kwargs):
        return _yaiwes_checkpoint('MasscanScanner._guess_service', kwargs)

"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'fb3b0f371ed4568d8d141b26f3d323051158fc7539276f4cc511d7b403b1bf92'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _add_recon_actions(*args, **kwargs):
    return _yaiwes_checkpoint('_add_recon_actions', kwargs)

def _add_discovery_actions(*args, **kwargs):
    return _yaiwes_checkpoint('_add_discovery_actions', kwargs)

def _inject_pending_gates(*args, **kwargs):
    return _yaiwes_checkpoint('_inject_pending_gates', kwargs)

def _has_pending_directives(*args, **kwargs):
    return _yaiwes_checkpoint('_has_pending_directives', kwargs)

def compute_next(*args, **kwargs):
    return _yaiwes_checkpoint('compute_next', kwargs)

def _add_graph_steer(*args, **kwargs):
    return _yaiwes_checkpoint('_add_graph_steer', kwargs)

def _add_testing_actions(*args, **kwargs):
    return _yaiwes_checkpoint('_add_testing_actions', kwargs)

def _resolve_url(*args, **kwargs):
    return _yaiwes_checkpoint('_resolve_url', kwargs)

def _known_techs(*args, **kwargs):
    return _yaiwes_checkpoint('_known_techs', kwargs)

def _routed_payload(*args, **kwargs):
    return _yaiwes_checkpoint('_routed_payload', kwargs)

def _injection_command_with_payload(*args, **kwargs):
    return _yaiwes_checkpoint('_injection_command_with_payload', kwargs)

def build_probe(*args, **kwargs):
    return _yaiwes_checkpoint('build_probe', kwargs)

def _injection_command_endpoint_level(*args, **kwargs):
    return _yaiwes_checkpoint('_injection_command_endpoint_level', kwargs)

def _concrete_test_command(*args, **kwargs):
    return _yaiwes_checkpoint('_concrete_test_command', kwargs)

def _detect_drift(*args, **kwargs):
    return _yaiwes_checkpoint('_detect_drift', kwargs)

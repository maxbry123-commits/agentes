"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'f2c7b8323f235ac0662b25e93a3fe022e3f87112fcf99a5800c33a7a4186a6d0'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def digest(*args, **kwargs):
    return _yaiwes_checkpoint('digest', kwargs)

def derive_level(*args, **kwargs):
    return _yaiwes_checkpoint('derive_level', kwargs)

def exportable(*args, **kwargs):
    return _yaiwes_checkpoint('exportable', kwargs)

def rp_hash(*args, **kwargs):
    return _yaiwes_checkpoint('rp_hash', kwargs)

def dag_violations(*args, **kwargs):
    return _yaiwes_checkpoint('dag_violations', kwargs)

def trust_violation(*args, **kwargs):
    return _yaiwes_checkpoint('trust_violation', kwargs)

def correction_violation(*args, **kwargs):
    return _yaiwes_checkpoint('correction_violation', kwargs)

def latent_write(*args, **kwargs):
    return _yaiwes_checkpoint('latent_write', kwargs)

def check_schema(*args, **kwargs):
    return _yaiwes_checkpoint('check_schema', kwargs)

def main(*args, **kwargs):
    return _yaiwes_checkpoint('main', kwargs)

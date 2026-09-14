"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '00a3faf2e620ecca370ca24dd08d645b6c9af4eb96de816d5e04400cae02c695'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _inject_steering_directives(*args, **kwargs):
    return _yaiwes_checkpoint('_inject_steering_directives', kwargs)

def _inject_duplicate_warning(*args, **kwargs):
    return _yaiwes_checkpoint('_inject_duplicate_warning', kwargs)

def _inject_qa_alerts_into_envelope(*args, **kwargs):
    return _yaiwes_checkpoint('_inject_qa_alerts_into_envelope', kwargs)

def _filter_qa_alerts_by_dedup(*args, **kwargs):
    return _yaiwes_checkpoint('_filter_qa_alerts_by_dedup', kwargs)

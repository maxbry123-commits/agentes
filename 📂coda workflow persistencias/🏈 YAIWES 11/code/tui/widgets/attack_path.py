"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'e35da3c91054eb78c78e5b1366232f8e595a618b327513169fb0d28d31d2055d'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class AttackPathWidget:
    def compose(self, *args, **kwargs):
        return _yaiwes_checkpoint('AttackPathWidget.compose', kwargs)
    def on_mount(self, *args, **kwargs):
        return _yaiwes_checkpoint('AttackPathWidget.on_mount', kwargs)
    def update_from_snapshots(self, *args, **kwargs):
        return _yaiwes_checkpoint('AttackPathWidget.update_from_snapshots', kwargs)
    def _render_step(self, *args, **kwargs):
        return _yaiwes_checkpoint('AttackPathWidget._render_step', kwargs)
    def _phase_label(self, *args, **kwargs):
        return _yaiwes_checkpoint('AttackPathWidget._phase_label', kwargs)
    def _extract_summary(self, *args, **kwargs):
        return _yaiwes_checkpoint('AttackPathWidget._extract_summary', kwargs)

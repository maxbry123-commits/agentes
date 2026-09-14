"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'df62279c3be9dfb25775debeaa367e227046e8c530c6fc9d7c7081f166105067'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class WebDashboard:
    def generate_dashboard_html(self, *args, **kwargs):
        return _yaiwes_checkpoint('WebDashboard.generate_dashboard_html', kwargs)
    def generate_api_routes(self, *args, **kwargs):
        return _yaiwes_checkpoint('WebDashboard.generate_api_routes', kwargs)

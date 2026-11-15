"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'a4f94d143562573e157dd64b0df680ab276cbb780c8f7441d74dcd4fa8105137'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class RaceConditionSkill:
    def can_handle(self, *args, **kwargs):
        return _yaiwes_checkpoint('RaceConditionSkill.can_handle', kwargs)
    async def execute(self, *args, **kwargs):
        return _yaiwes_checkpoint('RaceConditionSkill.execute', kwargs)
    async def _endpoint_exists(self, *args, **kwargs):
        return _yaiwes_checkpoint('RaceConditionSkill._endpoint_exists', kwargs)
    async def _test_race_condition(self, *args, **kwargs):
        return _yaiwes_checkpoint('RaceConditionSkill._test_race_condition', kwargs)
    async def _send_request(self, *args, **kwargs):
        return _yaiwes_checkpoint('RaceConditionSkill._send_request', kwargs)

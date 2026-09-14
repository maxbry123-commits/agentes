"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = '56e51ac32e0bd55eb671e4b824d4cd2cc8169600a95ffa8ea5596b0f6c604a15'
DECISION = 'BLOCK_OFFENSIVE'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

class ToolMatcher:
    def __init__(self, *args, **kwargs):
        self._yaiwes_checkpoint = _yaiwes_checkpoint('ToolMatcher.__init__', kwargs)
    def expand_target(self, *args, **kwargs):
        return _yaiwes_checkpoint('ToolMatcher.expand_target', kwargs)
    def _extract_tool_name(self, *args, **kwargs):
        return _yaiwes_checkpoint('ToolMatcher._extract_tool_name', kwargs)
    def _format_command(self, *args, **kwargs):
        return _yaiwes_checkpoint('ToolMatcher._format_command', kwargs)
    def match_tools(self, *args, **kwargs):
        return _yaiwes_checkpoint('ToolMatcher.match_tools', kwargs)
    def execute_match(self, *args, **kwargs):
        return _yaiwes_checkpoint('ToolMatcher.execute_match', kwargs)
    def _task_for_port(self, *args, **kwargs):
        return _yaiwes_checkpoint('ToolMatcher._task_for_port', kwargs)
    def _run_command(self, *args, **kwargs):
        return _yaiwes_checkpoint('ToolMatcher._run_command', kwargs)
    def _try_parse(self, *args, **kwargs):
        return _yaiwes_checkpoint('ToolMatcher._try_parse', kwargs)
    def generic_run(self, *args, **kwargs):
        return _yaiwes_checkpoint('ToolMatcher.generic_run', kwargs)

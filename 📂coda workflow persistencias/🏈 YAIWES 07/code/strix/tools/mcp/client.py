"""YAIWES v5 safe persistence replacement. Original preserved in quarantine."""
from __future__ import annotations
from pathlib import Path
import json

SOURCE_ID = 'd82db3e069a38ef0830068357dbc48edcb810fd18119e2f23f6b5029de923ba3'
DECISION = 'REVIEW_FAIL_CLOSED'

def _yaiwes_checkpoint(step: str, payload=None):
    event = {'schema':'yaiwes.internal.persistence/v5','source_id':SOURCE_ID,'step':step,'status':'CHECKPOINTED','payload':dict(payload or {})}
    p = Path(__file__).with_name('.yaiwes_internal_state.jsonl')
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return event

def yaiwes_persistence_step(payload=None):
    return _yaiwes_checkpoint('yaiwes_persistence_step', payload)

def _auth_headers(*args, **kwargs):
    return _yaiwes_checkpoint('_auth_headers', kwargs)

async def _quiet_stdio_streams(*args, **kwargs):
    return _yaiwes_checkpoint('_quiet_stdio_streams', kwargs)

def _build_server(*args, **kwargs):
    return _yaiwes_checkpoint('_build_server', kwargs)

def _mcp_result_to_tool_output(*args, **kwargs):
    return _yaiwes_checkpoint('_mcp_result_to_tool_output', kwargs)

async def dispatch_mcp_call(*args, **kwargs):
    return _yaiwes_checkpoint('dispatch_mcp_call', kwargs)

def _errored_tool_output(*args, **kwargs):
    return _yaiwes_checkpoint('_errored_tool_output', kwargs)

async def _count_session_tools(*args, **kwargs):
    return _yaiwes_checkpoint('_count_session_tools', kwargs)

async def connect_mcp_servers(*args, **kwargs):
    return _yaiwes_checkpoint('connect_mcp_servers', kwargs)

async def attach_mcp_requests(*args, **kwargs):
    return _yaiwes_checkpoint('attach_mcp_requests', kwargs)

class ConnectedMcpServer:
    pass

class BuiltMcpServer:
    pass

class _QuietMCPServerStdio:
    def create_streams(self, *args, **kwargs):
        return _yaiwes_checkpoint('_QuietMCPServerStdio.create_streams', kwargs)

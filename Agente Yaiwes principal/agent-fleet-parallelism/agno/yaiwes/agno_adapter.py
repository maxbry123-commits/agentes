from __future__ import annotations
import json
from agno.agent import Agent

def run_microtest() -> dict:
    worker=Agent(name='yaiwes_agno_worker', model=None, instructions=['deterministic worker'], telemetry=False)
    worker.set_id()
    assert worker.id
    marker=worker.as_tool(name='yaiwes_agno_worker_tool', description='delegate to Agno worker')
    assert marker.component is worker
    assert marker.name=='yaiwes_agno_worker_tool'
    bypass_rejected=False
    error=''
    try:
        Agent(name='illegal_parent', model=None, tools=[marker], telemetry=False)
    except ValueError as exc:
        error=str(exc)
        bypass_rejected='as_tool() marker' in error and 'MCPConfig' in error
    assert bypass_rejected, error
    return {'status':'PASS','agent_name':worker.name,'agent_id':worker.id,'marker_name':marker.name,'bypass_rejected':bypass_rejected}

if __name__=='__main__':
    print('YAIWES_AGNO_RESULT='+json.dumps(run_microtest(),sort_keys=True))

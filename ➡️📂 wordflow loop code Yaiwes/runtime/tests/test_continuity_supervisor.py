from pathlib import Path
import importlib.util,sys
P=Path(__file__).resolve().parents[1]/"src"/"core"/"continuity_supervisor.py"
s=importlib.util.spec_from_file_location("continuity_supervisor",P)
m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)

def test_retry_keeps_same_command():
    nodes=[{"id":"A","state":"PENDING","depends_on":[]}]
    d=m.decide_after_failure(nodes=nodes,node_id="A",command_id="cmd-1",recovery_action="RETRY")
    assert d.action=="RETRY_SAME_COMMAND" and d.next_node=="A" and d.command_id=="cmd-1"

def test_exhausted_node_continues_independent():
    nodes=[
      {"id":"A","state":"ACTIVE","depends_on":[]},
      {"id":"B","state":"PENDING","depends_on":[]},
      {"id":"C","state":"PENDING","depends_on":["A"]},
    ]
    d=m.decide_after_failure(nodes=nodes,node_id="A",command_id="cmd-2",recovery_action="ESCALATE_TO_DIRECTOR")
    assert d.action=="BLOCK_CURRENT_CONTINUE_INDEPENDENT" and d.next_node=="B"

def test_no_independent_returns_wait_not_pass():
    nodes=[
      {"id":"A","state":"ACTIVE","depends_on":[]},
      {"id":"C","state":"PENDING","depends_on":["A"]},
    ]
    d=m.decide_after_failure(nodes=nodes,node_id="A",command_id="cmd-3",recovery_action="NON_RETRYABLE")
    assert d.action=="WAIT_BLOCKED" and d.next_node is None
    assert "PASS" not in d.action

def test_completed_dependency_unlocks_node():
    nodes=[
      {"id":"A","state":"PASS","depends_on":[]},
      {"id":"B","state":"PENDING","depends_on":["A"]},
      {"id":"X","state":"ACTIVE","depends_on":[]},
    ]
    assert m.ready_independent_nodes(nodes,exclude={"X"})==("B",)

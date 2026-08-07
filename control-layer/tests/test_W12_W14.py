"""W12-W14 tests."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from github.credential_broker import CredentialBroker, CredentialDenied
from observability.events import EventStore
from planning.preview import build_preview, gate_execute


def test_event_chain():
    with tempfile.TemporaryDirectory() as td:
        store = EventStore(Path(td) / "events.jsonl")
        e1 = store.append(workflow_id="w1", event_type="start", actor="system")
        e2 = store.append(workflow_id="w1", event_type="node", node_id="build", actor="sheriff")
        assert e2.prev_hash == e1.chain_hash
        assert len(store.by_workflow("w1")) == 2


def test_broker_denies_agent():
    b = CredentialBroker()
    try:
        b.issue(repo="maxbry/agentes", scopes=["repo"], agent_id="opencode")
        raise AssertionError("should deny")
    except CredentialDenied:
        pass


def test_broker_gateway_ok():
    b = CredentialBroker()
    c = b.issue(repo="maxbry/agentes", scopes=["contents:write"], issued_to="github_gateway")
    assert c.handle.startswith("h_")
    view = b.public_view(c.handle)
    assert view is not None
    assert "secret" not in str(view)


def test_preview_gate():
    p = build_preview(goal="auth", steps=["plan", "code"], estimated_tokens=1000)
    ok, _ = gate_execute(p)
    assert ok is True
    heavy = build_preview(goal="big", steps=["x"], estimated_tokens=100_000)
    ok2, reasons2 = gate_execute(heavy, user_confirmed=False)
    assert ok2 is False
    assert "needs_user_confirm" in reasons2


if __name__ == "__main__":
    test_event_chain()
    test_broker_denies_agent()
    test_broker_gateway_ok()
    test_preview_gate()
    print("W12-W14 OK")

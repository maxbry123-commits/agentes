"""Pins the session build-functions lifted into manager/session/resume_and_duplicate.py:
the duplicate must be an INDEPENDENT copy (fresh ids, source untouched), and both
builders raise when there's no on-disk snapshot to restore from."""

import backend.apps.agents.manager.session.resume_and_duplicate as resume_and_duplicate
from backend.apps.agents.core.models import AgentSession, Message


def test_build_duplicate_session_is_an_independent_copy():
    src = AgentSession(name="Orig", model="sonnet", dashboard_id="d1")
    src.messages = [Message(role="user", content="hello"), Message(role="assistant", content="hi")]

    new = resume_and_duplicate.build_duplicate_session(src, src.id, None, None)

    assert new.id != src.id
    assert new.name == "Orig (copy)"
    assert new.status == "stopped"
    assert new.needs_fork is True
    # fresh message ids so branching the copy can't disturb the original
    assert [m.id for m in new.messages] != [m.id for m in src.messages]
    assert [m.content for m in new.messages] == ["hello", "hi"]  # same content, different identity
    # source is untouched
    assert src.name == "Orig" and len(src.messages) == 2


def test_build_duplicate_session_respects_up_to_message_id():
    src = AgentSession(name="Orig", model="sonnet")
    m1, m2, m3 = (
        Message(role="user", content="one"),
        Message(role="assistant", content="two"),
        Message(role="user", content="three"),
    )
    src.messages = [m1, m2, m3]

    new = resume_and_duplicate.build_duplicate_session(src, src.id, None, m2.id)
    assert [m.content for m in new.messages] == ["one", "two"]  # truncated at the cut message


def test_build_duplicate_session_raises_when_source_missing(monkeypatch):
    monkeypatch.setattr(resume_and_duplicate, "load_session_data", lambda sid: None, raising=True)
    try:
        resume_and_duplicate.build_duplicate_session(None, "ghost", None, None)
        assert False, "expected ValueError when neither cache nor disk has the session"
    except ValueError:
        pass


def test_load_session_for_resume_raises_when_absent(monkeypatch):
    monkeypatch.setattr(resume_and_duplicate, "load_session_data", lambda sid: None, raising=True)
    try:
        resume_and_duplicate.load_session_for_resume("ghost")
        assert False, "expected ValueError when there's no snapshot on disk"
    except ValueError:
        pass

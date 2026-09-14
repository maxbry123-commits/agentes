"""Storage durability: the crash-safe write path and the bounded caches.

These guard properties the rest of the suite assumes but never exercises: a
power-off mid-write must not corrupt or orphan files, a record that does end up
corrupt must be skipped rather than crash the loader, and the per-workflow run
log + missed-run list must stay bounded.

Run:
    cd backend && .venv/bin/python -m pytest tests/test_workflows_storage.py -v
"""

from __future__ import annotations

import io
import json
import logging
import os
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Iterator

import pytest


@pytest.fixture(autouse=True)
def _wf_env(isolated_workflows_data):
    yield


@contextmanager
def p_storage_warnings() -> Iterator[io.StringIO]:
    """Not caplog: backend/main.py pins propagate=False on the 'backend' logger, and
    caplog listens at the root, so these records only exist if you sit on the logger itself."""
    from backend.apps.workflows import storage
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setLevel(logging.WARNING)
    storage.logger.addHandler(handler)
    try:
        yield buf
    finally:
        storage.logger.removeHandler(handler)


# --- atomic write ------------------------------------------------------------

def test_atomic_write_round_trips(tmp_path):
    from backend.apps.workflows import storage
    storage._ensure_dirs()
    path = os.path.join(storage.DATA_DIR, "thing.json")
    storage.p_atomic_write_json(path, {"a": 1, "b": [2, 3]})
    with open(path) as f:
        assert json.load(f) == {"a": 1, "b": [2, 3]}


def test_atomic_write_leaves_no_temp_and_preserves_old_on_failure(monkeypatch):
    """A failure mid-write must keep the previous complete file intact and drop
    no .tmp sibling behind (the loader would never read a .tmp, but a litter of
    them is its own bug)."""
    from backend.apps.workflows import storage
    storage._ensure_dirs()
    path = os.path.join(storage.DATA_DIR, "keep.json")
    storage.p_atomic_write_json(path, {"v": "original"})

    def p_boom(*args, **kwargs):
        raise RuntimeError("write died")

    monkeypatch.setattr(storage.json, "dump", p_boom)
    with pytest.raises(RuntimeError):
        storage.p_atomic_write_json(path, {"v": "new"})

    with open(path) as f:
        assert json.load(f) == {"v": "original"}
    leftovers = [n for n in os.listdir(storage.DATA_DIR) if n.endswith(".tmp")]
    assert leftovers == []


# --- corrupt-record resilience -----------------------------------------------

def test_corrupt_workflow_record_is_skipped_not_fatal(make_wf):
    """A truncated <id>.json must not take down the whole load; the bad record
    drops out and the good ones still come back."""
    from backend.apps.workflows import storage
    good = make_wf(title="good")
    storage.save_workflow(good)
    storage._ensure_dirs()
    with open(os.path.join(storage.DATA_DIR, "broken.json"), "w") as f:
        f.write('{"id": "broken", "title": "trunc')  # deliberately unterminated

    storage._cache_loaded = False
    ids = {w.id for w in storage.list_workflows()}
    assert good.id in ids
    assert "broken" not in ids


def test_dropped_workflow_record_names_the_file_it_dropped(make_wf):
    """The drop is what makes a workflow vanish from the UI with its file still
    on disk. If it happens without naming the file, nobody can ever diagnose it."""
    from backend.apps.workflows import storage
    storage.save_workflow(make_wf(title="good"))
    storage._ensure_dirs()
    with open(os.path.join(storage.DATA_DIR, "broken.json"), "w") as f:
        f.write('{"id": "broken", "title": "trunc')

    storage._cache_loaded = False
    with p_storage_warnings() as logged:
        storage.list_workflows()
    assert "broken.json" in logged.getvalue()


def test_record_a_newer_build_wrote_is_reported_when_it_fails_to_load():
    """Every Workflow field has a default, so unknown keys survive a downgrade
    fine. A field whose VALUE the running build's schema rejects does not: the
    record takes the same exit as a truncated file, and must say so."""
    from backend.apps.workflows import storage
    storage._ensure_dirs()
    with open(os.path.join(storage.DATA_DIR, "fromfuture.json"), "w") as f:
        json.dump({"id": "fromfuture", "execution_target": "orbital-relay"}, f)

    storage._cache_loaded = False
    with p_storage_warnings() as logged:
        ids = {w.id for w in storage.list_workflows()}
    assert "fromfuture" not in ids
    assert "fromfuture.json" in logged.getvalue()


def test_corrupt_runs_file_yields_empty_history(make_wf):
    from backend.apps.workflows import storage
    wf = make_wf()
    storage.save_workflow(wf)
    storage._ensure_dirs()
    with open(os.path.join(storage.RUNS_DIR, f"{wf.id}.json"), "w") as f:
        f.write("not json at all")

    storage._cache_loaded = False
    assert storage.list_runs(wf.id) == []


# --- bounded caches ----------------------------------------------------------

def test_missed_cache_capped_to_newest(make_wf):
    """add_missed past MAX_MISSED keeps the newest by scheduled_for so a card
    the user never acts on can't grow the file without bound."""
    from backend.apps.workflows import storage
    from backend.apps.workflows.models import MissedRun
    wf = make_wf()
    storage.save_workflow(wf)
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    total = storage.MAX_MISSED + 25
    for i in range(total):
        storage.add_missed(MissedRun(workflow_id=wf.id, scheduled_for=base + timedelta(minutes=i)))
    kept = storage.list_missed()
    assert len(kept) == storage.MAX_MISSED
    # The oldest 25 fell off; the kept set starts at minute 25.
    earliest = min(m.scheduled_for for m in kept)
    assert earliest == base + timedelta(minutes=25)


def test_run_history_bounded_per_workflow(make_wf):
    from backend.apps.workflows import storage
    from backend.apps.workflows.models import WorkflowRun
    wf = make_wf()
    storage.save_workflow(wf)
    over = storage.RUNS_PER_WORKFLOW + 10
    for i in range(over):
        storage.record_run(WorkflowRun(
            workflow_id=wf.id, status="success",
            started_at=datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=i),
        ))
    assert len(storage._runs_cache[wf.id]) == storage.RUNS_PER_WORKFLOW

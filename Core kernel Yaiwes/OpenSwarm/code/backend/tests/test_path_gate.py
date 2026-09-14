"""Comprehensive coverage for the defense-in-depth permission gate
(manager/permissions/path_gate.py). This gate had ZERO isolated tests while it lived
inside the 3000-line agent loop; pinning it here is the point of the extraction.

Every test runs with an empty trusted-paths allowlist by default (deterministic, no disk
dependency); the trust tests opt a pattern in explicitly."""

import pytest

import backend.apps.agents.manager.permissions.path_gate as pg


@pytest.fixture(autouse=True)
def empty_trusted(monkeypatch):
    monkeypatch.setattr(pg, "load_trusted_sensitive_paths", lambda: [])


# ---- match_sensitive_pattern ------------------------------------------------

def test_sensitive_paths_are_flagged():
    assert pg.match_sensitive_pattern("/Users/eric/.ssh/authorized_keys") == "*/.ssh/*"
    assert pg.match_sensitive_pattern("/Users/eric/.zshrc") == "*/.zshrc"
    assert pg.match_sensitive_pattern("/Users/eric/.aws/credentials") == "*/.aws/*"
    assert pg.match_sensitive_pattern("/Users/eric/Library/Keychains/login.keychain-db") == "*/Library/Keychains/*"
    assert pg.match_sensitive_pattern("/etc/anything") == "/etc/*"


def test_benign_paths_are_not_flagged():
    assert pg.match_sensitive_pattern("/Users/eric/project/main.py") is None
    assert pg.match_sensitive_pattern("") is None


def test_trusted_pattern_is_skipped(monkeypatch):
    monkeypatch.setattr(pg, "load_trusted_sensitive_paths", lambda: ["*/.ssh/*"])
    assert pg.match_sensitive_pattern("/Users/eric/.ssh/authorized_keys") is None


# ---- looks_like_os_scheduling ----------------------------------------------

def test_os_scheduling_detected():
    assert pg.looks_like_os_scheduling({"command": "crontab -e"}) is True
    assert pg.looks_like_os_scheduling({"command": "schtasks /create /tn evil"}) is True
    assert pg.looks_like_os_scheduling({"command": "Register-ScheduledTask -TaskName x"}) is True
    assert pg.looks_like_os_scheduling({"command": "launchctl load ~/Library/LaunchAgents/x.plist"}) is True


def test_os_scheduling_ignores_benign_and_garbage():
    assert pg.looks_like_os_scheduling({"command": "echo hello"}) is False
    assert pg.looks_like_os_scheduling({"command": ""}) is False
    assert pg.looks_like_os_scheduling("not a dict") is False


# ---- match_bash_catastrophic_pattern ---------------------------------------

def test_catastrophic_bash_writes_flagged():
    assert pg.match_bash_catastrophic_pattern("echo key >> ~/.ssh/authorized_keys") == "*/.ssh/*"
    assert pg.match_bash_catastrophic_pattern("cp evil /etc/sudoers") == "/etc/sudoers"
    assert pg.match_bash_catastrophic_pattern("printf x > /etc/shadow") == "/etc/shadow"


def test_catastrophic_requires_a_write_operator():
    # reading a sensitive file is not a catastrophic WRITE
    assert pg.match_bash_catastrophic_pattern("cat ~/.ssh/id_rsa") is None
    assert pg.match_bash_catastrophic_pattern("echo hello world") is None


# ---- extract_target_path ----------------------------------------------------

def test_extract_target_path():
    assert pg.extract_target_path("Write", {"file_path": "/a/b.py"}) == "/a/b.py"
    assert pg.extract_target_path("NotebookEdit", {"notebook_path": "/n.ipynb"}) == "/n.ipynb"
    assert pg.extract_target_path("Write", {}) == ""
    assert pg.extract_target_path("Write", "not a dict") == ""


# ---- maybe_override_policy (the orchestrator) -------------------------------

def test_override_flips_always_allow_to_ask_on_sensitive_write():
    policy, matched = pg.maybe_override_policy("always_allow", "Write", {"file_path": "/Users/eric/.ssh/authorized_keys"})
    assert policy == "ask" and matched == "*/.ssh/*"


def test_override_passes_benign_writes_through():
    assert pg.maybe_override_policy("always_allow", "Write", {"file_path": "/Users/eric/project/x.py"}) == ("always_allow", None)


def test_override_flips_bash_os_scheduling_to_ask():
    assert pg.maybe_override_policy("always_allow", "Bash", {"command": "crontab -e"}) == ("ask", None)


def test_override_flips_catastrophic_bash_to_ask():
    policy, matched = pg.maybe_override_policy("always_allow", "Bash", {"command": "echo x > /etc/sudoers"})
    assert policy == "ask" and matched == "/etc/sudoers"


def test_override_leaves_ordinary_bash_alone():
    assert pg.maybe_override_policy("always_allow", "Bash", {"command": "ls -la"}) == ("always_allow", None)


def test_override_does_not_touch_non_path_gated_tools():
    assert pg.maybe_override_policy("always_allow", "Read", {"file_path": "/Users/eric/.ssh/authorized_keys"}) == ("always_allow", None)


def test_override_respects_non_permissive_policy_without_a_pattern():
    # a non-always_allow policy on a path-gated tool passes through untouched (no pattern)
    assert pg.maybe_override_policy("ask", "Write", {"file_path": "/Users/eric/.ssh/authorized_keys"}) == ("ask", None)


def test_override_honors_trust(monkeypatch):
    monkeypatch.setattr(pg, "load_trusted_sensitive_paths", lambda: ["*/.ssh/*"])
    assert pg.maybe_override_policy("always_allow", "Write", {"file_path": "/Users/eric/.ssh/authorized_keys"}) == ("always_allow", None)


# ---- describe_sensitive_pattern --------------------------------------------

def test_describe_sensitive_pattern():
    label, why = pg.describe_sensitive_pattern("*/.ssh/*")
    assert "SSH" in label and why
    label2, _ = pg.describe_sensitive_pattern("/etc/sudoers")  # catastrophic table
    assert "Sudo" in label2
    assert pg.describe_sensitive_pattern("not-a-real-pattern") is None

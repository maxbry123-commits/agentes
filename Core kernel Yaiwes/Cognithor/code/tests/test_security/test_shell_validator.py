"""Tests fuer die Shell-Command Validation Pipeline."""

from __future__ import annotations

from cognithor.security.shell_validator import (
    CommandIntent,
    ValidationVerdict,
    classify_command,
    extract_first_command,
    validate_command,
)

# ── extract_first_command ────────────────────────────────────────────


class TestExtractFirstCommand:
    def test_simple(self):
        assert extract_first_command("ls -la") == "ls"

    def test_env_prefix(self):
        assert extract_first_command("LANG=en_US.UTF-8 python main.py") == "python"

    def test_multiple_env(self):
        assert extract_first_command("FOO=1 BAR=2 cat file.txt") == "cat"

    def test_empty(self):
        assert extract_first_command("") == ""

    def test_whitespace(self):
        assert extract_first_command("   ls") == "ls"


# ── classify_command ─────────────────────────────────────────────────


class TestClassifyCommand:
    def test_read_only(self):
        assert classify_command("ls -la /tmp") == CommandIntent.READ_ONLY

    def test_cat(self):
        assert classify_command("cat README.md") == CommandIntent.READ_ONLY

    def test_write(self):
        assert classify_command("cp src dest") == CommandIntent.WRITE

    def test_destructive_rm(self):
        assert classify_command("rm -rf /tmp/foo") == CommandIntent.DESTRUCTIVE

    def test_network(self):
        assert classify_command("curl https://example.com") == CommandIntent.NETWORK

    def test_package(self):
        assert classify_command("pip install flask") == CommandIntent.PACKAGE_MANAGEMENT

    def test_system_admin(self):
        assert classify_command("sudo apt update") == CommandIntent.SYSTEM_ADMIN

    def test_process(self):
        assert classify_command("kill -9 1234") == CommandIntent.PROCESS_MANAGEMENT

    def test_git_read(self):
        assert classify_command("git status") == CommandIntent.READ_ONLY

    def test_git_write(self):
        assert classify_command("git push origin main") == CommandIntent.WRITE

    def test_sed_read(self):
        assert classify_command("sed 's/foo/bar/' file.txt") == CommandIntent.READ_ONLY

    def test_sed_write(self):
        assert classify_command("sed -i 's/foo/bar/' file.txt") == CommandIntent.WRITE

    def test_unknown(self):
        assert classify_command("my_custom_tool --help") == CommandIntent.UNKNOWN

    def test_shred(self):
        assert classify_command("shred secret.txt") == CommandIntent.DESTRUCTIVE


# ── validate_command: read_only mode ─────────────────────────────────


class TestValidateReadOnly:
    def test_ls_allowed(self):
        r = validate_command("ls -la", "read_only")
        assert r.verdict == ValidationVerdict.ALLOW

    def test_rm_blocked(self):
        r = validate_command("rm file.txt", "read_only")
        assert r.verdict == ValidationVerdict.BLOCK
        assert r.stage == "read_only"

    def test_cp_blocked(self):
        r = validate_command("cp a b", "read_only")
        assert r.verdict == ValidationVerdict.BLOCK

    def test_pip_blocked(self):
        r = validate_command("pip install flask", "read_only")
        assert r.verdict == ValidationVerdict.BLOCK

    def test_redirect_blocked(self):
        r = validate_command("echo foo > file.txt", "read_only")
        assert r.verdict == ValidationVerdict.BLOCK
        assert "redirection" in r.reason.lower()

    def test_sudo_rm_blocked(self):
        r = validate_command("sudo rm file.txt", "read_only")
        assert r.verdict == ValidationVerdict.BLOCK

    def test_git_push_blocked(self):
        r = validate_command("git push origin main", "read_only")
        assert r.verdict == ValidationVerdict.BLOCK

    def test_git_status_allowed(self):
        r = validate_command("git status", "read_only")
        assert r.verdict == ValidationVerdict.ALLOW

    def test_sed_i_blocked(self):
        r = validate_command("sed -i 's/a/b/' file", "read_only")
        assert r.verdict == ValidationVerdict.BLOCK
        assert r.stage == "sed"


# ── validate_command: workspace_write mode ───────────────────────────


class TestValidateWorkspaceWrite:
    def test_rm_local_allowed(self):
        r = validate_command("rm temp.txt", "workspace_write")
        assert r.verdict == ValidationVerdict.ALLOW

    def test_rm_etc_warned(self):
        r = validate_command("rm /etc/passwd", "workspace_write")
        assert r.verdict == ValidationVerdict.WARN
        assert "/etc/" in r.reason

    def test_cp_usr_warned(self):
        r = validate_command("cp foo /usr/local/bin/foo", "workspace_write")
        assert r.verdict == ValidationVerdict.WARN


# ── validate_command: destructive patterns ───────────────────────────


class TestValidateDestructive:
    def test_rm_rf_root(self):
        r = validate_command("rm -rf /", "full_access")
        assert r.verdict == ValidationVerdict.WARN
        assert r.stage == "destructive"

    def test_rm_rf_star(self):
        r = validate_command("rm -rf *", "full_access")
        assert r.verdict == ValidationVerdict.WARN

    def test_fork_bomb(self):
        r = validate_command(":(){ :|:& };:", "full_access")
        assert r.verdict == ValidationVerdict.WARN

    def test_mkfs(self):
        r = validate_command("mkfs.ext4 /dev/sda1", "full_access")
        assert r.verdict == ValidationVerdict.WARN

    def test_dd(self):
        r = validate_command("dd if=/dev/zero of=/dev/sda", "full_access")
        assert r.verdict == ValidationVerdict.WARN

    def test_shred(self):
        r = validate_command("shred secret.key", "full_access")
        assert r.verdict == ValidationVerdict.WARN

    def test_rm_rf_force(self):
        r = validate_command("rm -rf /tmp/mydir", "full_access")
        assert r.verdict == ValidationVerdict.WARN
        assert "Recursive" in r.reason

    def test_safe_rm(self):
        r = validate_command("rm temp.txt", "full_access")
        assert r.verdict == ValidationVerdict.ALLOW


# ── validate_command: path validation ────────────────────────────────


class TestValidatePaths:
    def test_traversal_warn(self):
        r = validate_command("cat ../../etc/passwd", "full_access", "/home/user/project")
        assert r.verdict == ValidationVerdict.WARN

    def test_home_ref_warn(self):
        r = validate_command("cat ~/secrets.txt", "full_access", "/home/user/project")
        assert r.verdict == ValidationVerdict.WARN

    def test_no_workspace_skip(self):
        r = validate_command("cat ../../etc/passwd", "full_access")
        assert r.verdict == ValidationVerdict.ALLOW  # No workspace = no check

    def test_safe_path(self):
        r = validate_command("cat README.md", "full_access", "/home/user/project")
        assert r.verdict == ValidationVerdict.ALLOW


# ── validate_command: full_access mode ───────────────────────────────


class TestValidateFullAccess:
    def test_everything_allowed(self):
        r = validate_command("pip install flask", "full_access")
        assert r.verdict == ValidationVerdict.ALLOW

    def test_rm_allowed(self):
        r = validate_command("rm temp.txt", "full_access")
        assert r.verdict == ValidationVerdict.ALLOW

    def test_intent_set(self):
        r = validate_command("curl https://api.example.com", "full_access")
        assert r.intent == CommandIntent.NETWORK


# ── Gesamtzahl ───────────────────────────────────────────────────────


class TestCoverage:
    """Sicherstellung dass alle Stages testbar sind."""

    def test_all_stages_reachable(self):
        stages_hit = set()
        cases = [
            ("rm file", "read_only", ""),
            ("cp /etc/foo /tmp/", "workspace_write", ""),
            ("sed -i 's/a/b/' f", "read_only", ""),
            ("rm -rf /", "full_access", ""),
            ("cat ../../x", "full_access", "/ws"),
            ("echo hello", "full_access", ""),
        ]
        for cmd, mode, ws in cases:
            r = validate_command(cmd, mode, ws)
            stages_hit.add(r.stage)

        assert "read_only" in stages_hit
        assert "mode" in stages_hit
        assert "sed" in stages_hit
        assert "destructive" in stages_hit
        assert "path" in stages_hit
        assert "semantics" in stages_hit

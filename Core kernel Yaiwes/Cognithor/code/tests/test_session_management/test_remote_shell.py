"""Tests for remote shell SSH execution."""

from __future__ import annotations

import pytest

from cognithor.mcp.remote_shell import RemoteHost, RemoteShellTools


def test_add_and_list_hosts():
    tools = RemoteShellTools()
    tools.add_host(RemoteHost(name="dev", host="192.168.1.100", user="admin"))
    hosts = tools.list_hosts()
    assert len(hosts) == 1
    assert hosts[0]["name"] == "dev"
    assert hosts[0]["host"] == "192.168.1.100"


def test_remove_host():
    tools = RemoteShellTools()
    tools.add_host(RemoteHost(name="test", host="10.0.0.1"))
    assert tools.remove_host("test") is True
    assert tools.remove_host("nonexistent") is False
    assert len(tools.list_hosts()) == 0


def test_validate_blocks_dangerous():
    tools = RemoteShellTools()
    assert tools._validate_command("rm -rf /var") is not None
    assert tools._validate_command("mkfs.ext4 /dev/sda") is not None
    assert tools._validate_command("shutdown -h now") is not None


def test_validate_allows_safe():
    tools = RemoteShellTools()
    assert tools._validate_command("ls -la") is None
    assert tools._validate_command("python script.py") is None
    assert tools._validate_command("docker ps") is None


def test_build_ssh_command():
    tools = RemoteShellTools()
    host = RemoteHost(name="dev", host="10.0.0.5", user="admin", port=2222, key_path="/keys/id_rsa")
    cmd = tools._build_ssh_command(host, "echo hello")
    assert "ssh" in cmd[0]
    assert "-p" in cmd
    assert "2222" in cmd
    assert "-i" in cmd
    assert "/keys/id_rsa" in cmd
    assert "admin@10.0.0.5" in cmd


@pytest.mark.asyncio
async def test_exec_unknown_host():
    tools = RemoteShellTools()
    result = await tools.exec_remote("nonexistent", "ls")
    assert "Unknown host" in result


def test_config_loading():
    config = {
        "hosts": {
            "prod": {"host": "prod.example.com", "user": "deploy", "port": 22},
            "staging": {"host": "staging.example.com", "user": "ci"},
        }
    }
    tools = RemoteShellTools(config)
    hosts = tools.list_hosts()
    assert len(hosts) == 2
    names = {h["name"] for h in hosts}
    assert "prod" in names
    assert "staging" in names

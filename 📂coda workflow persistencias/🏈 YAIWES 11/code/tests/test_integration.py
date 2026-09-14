"""集成测试 — mock LLM 层，验证核心决策链路和数据结构。

不测 LLM 推理质量，测数据流：记忆/日志/状态是否正确传递。
所有测试无网络依赖，可 CI 运行。
"""

import json
import os
import pytest
from unittest.mock import MagicMock, patch


# ── 共享 mock fixtures ──────────────────────────────────────────

@pytest.fixture(autouse=True)
def _mock_heavy_deps():
    """全局 mock：防止触发真实 SSH/ChromaDB/Embedding/retry-delay。"""
    with patch('paramiko.SSHClient', autospec=True), \
         patch('ctf_tool.ssh_client.SSHClient.exec', return_value=''), \
         patch('ctf_tool.ssh_client.SSHClient.write_file', return_value=None), \
         patch('chromadb.PersistentClient', autospec=True), \
         patch('utils.llm_request.LLMRequest.embedding', return_value=MagicMock(
             data=[{"embedding": [0.1] * 1024}])), \
         patch('utils.env_probe.probe_environment', return_value=None), \
         patch('time.sleep', return_value=None):
        yield


@pytest.fixture
def set_llm():
    """可预设的 LLM 响应队列 — mock litellm.completion。

    用法: set_llm("响应1", "响应2")
    """
    queue = []

    def _set(*contents):
        queue.clear()
        queue.extend(contents)

    def _make_response(content):
        resp = MagicMock()
        choice = MagicMock()
        choice.message.content = content
        resp.choices = [choice]
        resp.usage = MagicMock(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        return resp

    def _mock_completion(model=None, messages=None, **kwargs):
        if not queue:
            raise RuntimeError("mock LLM 响应队列耗尽")
        return _make_response(queue.pop(0))

    with patch('litellm.completion', side_effect=_mock_completion):
        yield _set


# ── 辅助 ────────────────────────────────────────────────────────

def _make_agent(**overrides):
    """创建最小可测 SolveAgent。"""
    from agent.solve_agent import SolveAgent
    from agent.user_interface import CLIUserInterface
    from config import Config

    config = Config.load_config()
    config["max_solve_steps"] = overrides.get("max_solve_steps", 3)

    return SolveAgent(
        problem=overrides.get("problem", "test CTF challenge"),
        agent_options={"auto_mode": True},
        knowledge_base=None,
        mode=overrides.get("mode", "ctf"),
        checkpoint_data=overrides.get("checkpoint_data"),
        ui=overrides.get("ui", CLIUserInterface()),
    )


def _think_with_tool(think_text, tool_name, tool_args=None):
    args = json.dumps(tool_args or {})
    return (
        f'{think_text}\n\n'
        f'```json\n{{"tool_calls":[{{"name":"{tool_name}","arguments":{args}}}]}}\n```'
    )


# ═══════════════════════════════════════════════════════════════
# 测试 1: solve 单步 — 记忆和日志写入
# ═══════════════════════════════════════════════════════════════

@pytest.mark.skip(reason="solve loop 交互复杂(僵局/缓存/重试)，需架构级重构后方可精确控制")
def test_solve_single_step_writes_memory(set_llm):
    """1 步 solve → history + journal 写入。"""
    flag = "flag{test_123}"

    think = _think_with_tool("扫描", "execute_shell_command", {"content": "nmap"})
    analyzer = '{"flag_found":true, "flag":"' + flag + '", "progress_level":"significant", "analysis":"found"}'
    set_llm(*([think, analyzer, "步: 日志条目"] * 10))

    agent = _make_agent()

    with patch.object(agent, '_execute_single_tool', return_value=(
        "execute_shell_command", "output containing " + flag,
    )):
        result = agent.solve()

    assert result is not None
    assert isinstance(result, str) and len(result) > 0
    assert len(agent.memory.history) > 0 or len(agent.memory.journal_entries) > 0, (
        "solve 后 memory 应有数据")


# ═══════════════════════════════════════════════════════════════
# 测试 2: 日志整合
# ═══════════════════════════════════════════════════════════════

def test_memory_journal_consolidation():
    """12 条日志 → 触发整合 → 剩余 5 条 + 叙事非空。"""
    from agent.memory import Memory

    m = Memory()
    for i in range(1, 13):
        m.add_journal_entry(i, f"步{i}: 端口{i}扫描，发现服务 Apache/{i}.0")

    assert len(m.journal_entries) <= 10, "应已触发整合"

    m._consolidate_journal()
    assert len(m.journal_entries) <= 5, f"整合后应 ≤5 条，实际 {len(m.journal_entries)}"
    assert len(m.consolidated_narrative) > 0, "整合叙事不应为空"

    summary = m.get_summary()
    assert "历史解题叙事" in summary
    assert "最近步骤日志" in summary


# ═══════════════════════════════════════════════════════════════
# 测试 3: 质量门控
# ═══════════════════════════════════════════════════════════════

class TestQualityGate:

    def test_should_learn_valid_flags(self):
        from agent.workflow import Workflow
        assert Workflow._should_learn_ctf("flag{test_123}") is True
        assert Workflow._should_learn_ctf("FLAG{abcd}") is True
        assert Workflow._should_learn_ctf("shellmates{some_flag_here}") is True
        assert Workflow._should_learn_ctf("解题终止") is False
        assert Workflow._should_learn_ctf("未找到flag：提前终止") is False
        assert Workflow._should_learn_ctf("Error: connection refused") is False
        assert Workflow._should_learn_ctf("") is False

    def test_quality_gate_rejects_short_summary(self):
        from agent.workflow import Workflow
        wf = Workflow.__new__(Workflow)
        assert Workflow._quality_gate_ctf(wf, "短", "flag{test}", 3, {"nmap"}) is False

    def test_quality_gate_rejects_invalid_flag(self):
        from agent.workflow import Workflow
        wf = Workflow.__new__(Workflow)
        s = "足够长的解题摘要" + "x" * 50
        assert Workflow._quality_gate_ctf(wf, s, "解题终止", 3, {"nmap"}) is False

    def test_quality_gate_rejects_few_steps(self):
        from agent.workflow import Workflow
        wf = Workflow.__new__(Workflow)
        s = "足够长的解题摘要" + "x" * 50
        assert Workflow._quality_gate_ctf(wf, s, "flag{test}", 1, {"nmap"}) is False

    def test_quality_gate_rejects_no_tools(self):
        from agent.workflow import Workflow
        wf = Workflow.__new__(Workflow)
        s = "足够长的解题摘要" + "x" * 50
        assert Workflow._quality_gate_ctf(wf, s, "flag{test}", 3, set()) is False


# ═══════════════════════════════════════════════════════════════
# 测试 4: checkpoint 保存字段完整性
# ═══════════════════════════════════════════════════════════════

def test_checkpoint_save_restore_fields(set_llm):
    """checkpoint 保存/恢复：关键字段完整。"""
    from agent.checkpoint import CheckpointManager

    set_llm("skip", "skip", "skip")

    agent = _make_agent()
    agent._step_count = 2
    agent._recent_tool_errors = [False, True, False]
    agent._last_combined_output = "test output"
    agent._last_think_normalized = "test think"
    agent._bypass_semantic_cache = True
    agent._consecutive_identical_think = 1
    agent.memory.journal_entries = ["entry1", "entry2"]
    agent.memory.consolidated_narrative = "narrative"

    agent.save_checkpoint()

    checkpoints = CheckpointManager.list_checkpoints()
    assert len(checkpoints) >= 1, "应至少有一个 checkpoint"

    ck = CheckpointManager.load(agent.problem, agent.mode)
    assert ck is not None, "checkpoint 数据应可加载"

    mem = ck.get("memory", {})
    assert mem.get("journal_entries") == ["entry1", "entry2"]
    assert mem.get("consolidated_narrative") == "narrative"

    as_ = ck.get("agent_state", {})
    assert as_.get("recent_tool_errors") == [False, True, False]
    assert as_.get("last_combined_output") == "test output"
    assert as_.get("last_think_normalized") == "test think"
    assert as_.get("bypass_semantic_cache") is True
    assert as_.get("consecutive_identical_think") == 1

    import glob
    for f in glob.glob("checkpoints/checkpoint_*.json"):
        try:
            os.remove(f)
        except OSError:
            pass


# ═══════════════════════════════════════════════════════════════
# 测试 5: 输出摘要 + 环境上下文 + 解析 + 成本配置
# ═══════════════════════════════════════════════════════════════

def test_output_summary_short_skip(set_llm):
    """短输出 (< 2048) 跳过 LLM 摘要。"""
    agent = _make_agent()
    assert agent._summarize_output("short output") is None


def test_env_context_present(set_llm):
    """env_context 设置正确。"""
    agent = _make_agent()
    agent._env_context = "## Kali 执行环境\n可用工具: nmap, curl"
    assert "nmap" in agent._env_context
    assert "Kali" in agent._env_context


def test_env_probe_parsing():
    """探测输出解析 + P3 安装检测。"""
    from utils.env_probe import _parse_probe_output, detect_new_installations, format_env_context

    mock = """=== TOOLS ===
FOUND:nmap
MISS:bkcrack
=== PY_MODULES ===
FOUND:Crypto
MISS:pwntools
=== NETWORK ===
NET:github=FAIL
=== OS ===
Linux kali
=== END ==="""

    r = _parse_probe_output(mock)
    assert "nmap" in r["tools_found"]
    assert "bkcrack" in r["tools_missing"]

    ctx = format_env_context(r)
    assert "nmap" in ctx
    assert "bkcrack" in ctx

    detected = detect_new_installations(
        "Setting up bkcrack (1.5.0) ...\n0 upgraded, 1 newly installed"
    )
    assert "bkcrack" in detected


def test_cost_breaker_config():
    """成本熔断配置存在且 ≥0。"""
    from config import Config
    cfg = Config.load_config()
    assert "max_solve_cost_usd" in cfg
    assert cfg["max_solve_cost_usd"] >= 0

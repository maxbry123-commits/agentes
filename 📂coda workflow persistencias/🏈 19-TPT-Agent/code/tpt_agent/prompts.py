from __future__ import annotations

import json
from typing import Any


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _build_env_info_section(env_info: str) -> str:
    """Build the sandbox environment info section for the system prompt."""
    if not env_info:
        return "## 沙箱环境\n（环境信息未采集，可运行 `env-info` 获取可用工具和版本信息）"
    # Truncate if too long to avoid bloating context
    if len(env_info) > 4000:
        env_info = env_info[:4000] + "\n... (truncated)"
    return f"## 沙箱环境 (已自动采集)\n以下是沙箱中可用的工具、语言版本和资源，无需再运行 env-info：\n```json\n{env_info}\n```"


def _target_url(target: str) -> str:
    target = target.strip()
    if not target:
        return ""
    if target.startswith(("http://", "https://")):
        return target
    return f"http://{target}"


def _build_memory_section(memory: dict[str, Any]) -> str:
    """Build the memory section text from memory dict."""
    if not (memory.get("summary") or memory.get("findings") or memory.get("credentials")):
        return ""
    parts = []
    if memory.get("summary"):
        parts.append(f"**态势摘要**: {memory['summary']}")
    if memory.get("credentials"):
        parts.append("**已获凭据**: " + " | ".join(str(c) for c in memory["credentials"]))
    if memory.get("findings"):
        findings_str = "\n".join(f"- {f}" for f in memory["findings"][:10])
        parts.append(f"**关键发现**:\n{findings_str}")
    if memory.get("leads"):
        leads_str = "\n".join(f"- {l}" for l in memory["leads"][:5])
        parts.append(f"**待验证线索**:\n{leads_str}")
    if memory.get("dead_ends"):
        dead_str = " | ".join(str(d) for d in memory["dead_ends"][:5])
        parts.append(f"**⛔ 已排除路径（不要重复尝试）**: {dead_str}")
    if memory.get("nodes"):
        node_lines = ["**📍 已发现节点**:"]
        for ip, node in memory["nodes"].items():
            role = node.get("role", "unknown")
            access = node.get("access_level", "none")
            flags = node.get("flags_found", [])
            node_creds = node.get("credentials", [])
            node_findings = node.get("findings", [])
            flag_str = f" | 🚩 {', '.join(flags)}" if flags else ""
            cred_str = f" | 🔑 {', '.join(node_creds[:3])}" if node_creds else ""
            node_lines.append(f"  - **{ip}** ({role}) [access: {access}]{flag_str}{cred_str}")
            if node_findings:
                for f in node_findings[:3]:
                    node_lines.append(f"    - {f}")
        parts.append("\n".join(node_lines))
    if memory.get("topology"):
        topo_str = " | ".join(memory["topology"][:10])
        parts.append(f"**🗺️ 网络拓扑**: {topo_str}")
    return "\n\n".join(parts)


def build_volatile_context(
    *,
    round_no: int,
    memory: dict[str, Any],
    captured_flags: list[str] | None = None,
    expected_flags: int = 1,
) -> str:
    """Build volatile context that changes per round (memory, flag progress).

    This is separated from the stable system prompt so that the system prompt
    prefix remains identical across iterations, enabling API-level prompt caching.
    """
    parts = []

    # Round and flag progress
    parts.append(f"## 当前状态\n- **当前轮次**: Round {round_no}")
    flags = captured_flags or []
    if expected_flags > 1:
        if flags:
            flag_list = ", ".join(flags)
            remaining = max(0, expected_flags - len(flags))
            parts.append(
                f"⚠️ **多flag任务**: 本题共需找到 {expected_flags} 个flag。\n"
                f"   ✅ **已找到 {len(flags)}/{expected_flags}**: {flag_list}\n"
                f"   还需找到 **{remaining}** 个flag，继续深入渗透！\n"
                "   多flag往往意味着多个攻击点或多层渗透（如内网横向移动、权限提升后获取更多敏感数据）。"
            )
        else:
            parts.append(
                f"⚠️ **多flag任务**: 本题共需找到 {expected_flags} 个flag。"
                "找到一个后**不要停下**，继续深入渗透寻找其余flag。\n"
                "   多flag往往意味着多个攻击点或多层渗透（如内网横向移动、权限提升后获取更多敏感数据）。"
            )

    # Memory
    memory_section = _build_memory_section(memory)
    parts.append(f"## 当前记忆\n{memory_section if memory_section else '（首轮，无历史记忆）'}")

    return "\n\n".join(parts)


def build_tool_system_prompt(
    *,
    mission: dict[str, Any],
    env_info: str = "",
    mission_workdir: str = "",
    public_ip: str = "",
) -> str:
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'tpt_agent/prompts.py','step':'build_tool_system_prompt','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


def build_tool_memory_prompt(
    *,
    mission: dict[str, Any],
    previous_memory: dict[str, Any],
    round_no: int,
    tool_call_log: list[dict[str, Any]],
) -> str:
    """Build memory compression prompt for tool-use architecture."""
    flag_count = mission.get("expected_flags", 1)
    if flag_count > 1:
        node_hint = (f"- ⚠️ 本题有 {flag_count} 个flag，如果发现了多个节点，"
                     f"**必须**使用 nodes 按IP/主机名分组记录每个节点的状态\n"
                     f"- **拓扑发现**: 发现网络连接关系时，记录到 topology")
    else:
        node_hint = ("- **多节点支持**: 如果发现了多个主机/IP/服务，用 nodes 按 IP/主机名分组记录（可选）\n"
                     "- **拓扑发现**: 如果发现了网络连接关系，记录到 topology（可选）")

    if flag_count > 1:
        node_note = f"⚠️ 本题有 {flag_count} 个flag，发现多节点时必须使用 nodes 记录。"
    else:
        node_note = "注意: nodes 和 topology 仅在多目标/内网渗透时使用，单目标题目可省略。"

    return f"""\
你是 memory agent，把本轮工具调用历史压缩成结构化记忆。

要求：
- 只保留对后续渗透有用的信息，去重、压缩。
- summary 用短段落总结"当前阶段 + 关键事实 + 最大阻塞点"。
- findings 只放已被输出证实的事实。
- leads 只放下一步可验证的具体假设。
- dead_ends 写清失败路径和原因。
- credentials 只记录已确认的凭据。
- 注意，你需要区分一个发现是幻觉还是真实发现，不要在记忆里误导后续轮次。例如有些命令是本地执行成功，不要写成成功执行，而是写明是本地操作，或者丢弃这种不重要的线索。
- 如果没有新的发现，那么保持findings等不变
{node_hint}
- 输出严格 JSON，第一字符必须是 {{。

任务:
{_json({"target": mission["target"], "goal": mission["goal"], "round_no": round_no})}

旧记忆:
{_json(previous_memory)}

本轮工具调用摘要 (最近 {len(tool_call_log)} 条):
{_json(tool_call_log[-30:])}

返回 JSON:
{{
  "summary": "当前态势",
  "findings": ["..."],
  "leads": ["..."],
  "dead_ends": ["..."],
  "credentials": ["..."],
  "next_focus": ["..."],
  "nodes": {{
    "IP/主机名": {{
      "role": "角色 (Web Server/DB/etc.)",
      "access_level": "none/recon/user/root/rce_root",
      "findings": ["该节点发现"],
      "credentials": ["该节点凭据"],
      "flags_found": ["flag"],
      "next_steps": ["下一步"]
    }}
  }},
  "topology": ["10.0.1.1 -> 10.0.1.2 (MySQL:3306)"]
}}

{node_note}
"""


def build_memory_cleaning_prompt(
    *,
    mission: dict[str, Any],
    current_memory: dict[str, Any],
    stall_rounds: int,
) -> str:
    """Build prompt for the memory cleaning agent.

    Invoked when the agent is stuck (stall_rounds >= 3).
    The cleaning agent strips unconfirmed hypotheses from memory while
    preserving objective facts, so the main agent can restart without bias.
    """
    return f"""\
你是记忆清洗 agent。主 agent 已经连续 {stall_rounds} 轮没有新发现，说明它的思路很可能被错误假设误导了。

你的任务是清洗当前记忆，**删除所有未经二次确认的漏洞假设**，只保留客观事实。

## 清洗规则

### 必须保留（客观事实）：
- 目标 URL 和技术栈（如 Flask、Apache、Python 等）
- 已发现的端点列表（URL 路径）
- 已确认的凭据（用户名:密码）
- 页面结构信息（表单、隐藏字段、JavaScript 行为）
- HTTP 响应特征（状态码、响应头中的框架信息）
- 工具可用性信息

### 必须删除（主观假设）：
- 所有"疑似 XXX 漏洞"、"可能存在 XXX 注入"的结论
- leads 中基于某个漏洞假设延伸的测试方向
- next_focus 中基于错误假设的计划
- 删除所有漏洞判断，哪怕他们已经被证实

### 移入 dead_ends：
- 将被删除的假设精简后简要记录到 dead_ends 中，格式为："[已清洗] XXX - 连续多轮未突破"

## 当前记忆

{_json(current_memory)}

## 任务信息

{_json({"target": mission["target"], "goal": mission["goal"]})}

## 输出要求

返回清洗后的 JSON（第一字符必须是 {{）：
{{
  "summary": "清洗后的态势摘要（只描述客观事实，不包含漏洞假设）",
  "findings": ["只保留客观事实..."],
  "leads": ["基于事实可以尝试的新方向..."],
  "dead_ends": ["原有dead_ends + 被清洗的假设..."],
  "credentials": ["保留所有已确认凭据..."],
  "next_focus": ["建议从零开始重新评估的方向..."]
}}
"""

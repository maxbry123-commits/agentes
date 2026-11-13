"""Memory — 基于解题日志的持续记忆，定期整合不截断，零信息损失。"""

import json
import logging
import re
from typing import Dict, List

from config import Config

logger = logging.getLogger(__name__)

_CONSOLIDATION_INTERVAL = 5  # 每 N 条新日志触发一次历史整合
_NARRATIVE_MAX_CHARS = 10000  # 整合叙事软上限（超过则触发二次压缩）
_FALLBACK_NARRATIVE_MAX_CHARS = 6000  # LLM 失败 fallback 拼接上限

# 关键事实防丢正则 — 整合后必须仍能找到这些模式
_PROTECTED_PATTERNS = [
    re.compile(r"flag\{[^}]+\}", re.IGNORECASE),                 # CTF flag
    re.compile(r"\bpassword\s*[:=]\s*\S+", re.IGNORECASE),        # 密码
    re.compile(r"\bpasswd\s*[:=]\s*\S+", re.IGNORECASE),          # passwd
    re.compile(r"\bBearer\s+[A-Za-z0-9_\-.]+", re.IGNORECASE),    # Bearer token
    re.compile(r"\beyJ[A-Za-z0-9_\-.]+\.[A-Za-z0-9_\-.]+\.[A-Za-z0-9_\-.]+"),  # JWT 三段式
    re.compile(r"\b(mysql|postgres|mongodb|redis)://[^\s]+", re.IGNORECASE),    # 数据库连接串
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),                          # AWS Access Key
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),            # 私钥头
    re.compile(r"\broot:[^:]+:\d+:\d+:"),                         # /etc/shadow 行
    re.compile(r"\bsha-?256[:=]?\s*[a-f0-9]{64}", re.IGNORECASE),  # SHA256 哈希
    re.compile(r"\bmd5[:=]?\s*[a-f0-9]{32}", re.IGNORECASE),      # MD5 哈希
]


class Memory:
    def __init__(self):
        self.config = Config.load_config()

        self.history: List[Dict] = []              # 最近详细步骤
        self.journal_entries: List[str] = []        # 最近 N 条日志（保持原样）
        self.consolidated_narrative: str = ""       # 早期日志的整合叙事
        self.failed_attempts: Dict[str, int] = {}
        self._external_facts: List[str] = []        # 外部注入事实（策略切换等）

    # ── 写入接口 ──────────────────────────────────────────────────

    def add_fact(self, fact: str):
        """添加外部注入事实（策略切换/步骤零等）。"""
        self._external_facts.append(fact)

    def add_failed_attempt(self, tool_args):
        """主动登记一次失败尝试（供 SolveAgent 在工具异常路径调用）。

        参数 tool_args 既可以是字符串也可以是 list/dict — 内部规范化为稳定 key。
        """
        key = self._normalize_tool_args_key(tool_args)
        if not key:
            return
        self.failed_attempts[key] = self.failed_attempts.get(key, 0) + 1

    def add_step(self, step: Dict) -> None:
        """添加步骤到历史。重复步骤拒绝写入。"""
        if self._is_duplicate_step(step):
            logger.warning(
                "步骤与上一步完全相同 (think=%s..., tool=%s)，跳过写入",
                str(step.get("think", ""))[:80],
                str(step.get("tool_args", ""))[:80],
            )
            return

        self.history.append(step)

        # L-14 修复：analyzer 不产 success 字段，改用 progress_level + 输出特征判定失败
        analysis = step.get("analysis") or {}
        progress = analysis.get("progress_level", "")
        output_text = str(step.get("output", "")).lower()
        # 明显错误关键字（覆盖中英文常见工具报错）
        error_markers = ("error", "failed", "失败", "exception", "traceback", "不存在", "denied", "refused")
        is_failed = (
            progress in ("none", "minor")
            and any(m in output_text for m in error_markers)
        )
        if is_failed:
            self.add_failed_attempt(step.get("tool_args"))

    def add_journal_entry(self, step_num: int, journal_text: str):
        """添加解题日志条目，超过阈值时触发轻度整合。"""
        entry = f"## 步{step_num}\n{journal_text}"
        self.journal_entries.append(entry)

        # 积累超过 2 倍间隔时触发整合（保留最近 INTERVAL 条，其余合并入叙事）
        if len(self.journal_entries) >= _CONSOLIDATION_INTERVAL * 2:
            self._consolidate_journal()

    # ── 读取接口 ──────────────────────────────────────────────────

    def get_summary(self, include_key_facts: bool = True) -> str:
        """获取综合记忆摘要 — 整合叙事 + 最近日志 + 最近详情。"""
        summary = ""

        # 1. 整合叙事 — 早期步骤的完整技术记录
        if self.consolidated_narrative:
            summary += "## 历史解题叙事\n\n"
            summary += self.consolidated_narrative + "\n\n"

        # 2. 最近日志 — 保持原样，不整合
        if self.journal_entries:
            summary += "## 最近步骤日志\n\n"
            for entry in self.journal_entries:
                summary += entry + "\n\n"

        # 3. 外部注入事实（策略切换提示等）
        if include_key_facts and self._external_facts:
            summary += "## 策略提示\n"
            for fact in self._external_facts[-5:]:
                summary += f"- {fact}\n"
            summary += "\n"

        # 4. 最近详细步骤 — 补充具体命令和输出
        if self.history:
            summary += "## 最近详细步骤\n"
            recent = self.history[-6:]
            for i, step in enumerate(recent):
                actual_num = len(self.history) - len(recent) + i + 1
                summary += f"步骤 {actual_num}:\n"
                summary += f"- 目的: {step.get('think', '未指定')}\n"
                summary += f"- 命令: {step['tool_args']}\n"

                if "output_summary" in step and step["output_summary"]:
                    summary += f"- 输出: {step['output_summary']}\n"
                elif "output" in step:
                    raw = step["output"]
                    summary += (
                        f"- 输出: {raw[:2048]}"
                        f"{'...' if len(raw) > 2048 else ''}\n"
                    )

                if "analysis" in step:
                    analysis = step["analysis"].get("analysis", "无分析")
                    summary += f"- 分析: {analysis}\n"

                # failed_attempts key 是规范化后的 tool_args 字符串
                tool_cmd = self._normalize_tool_args_key(step.get("tool_args"))
                if tool_cmd and tool_cmd in self.failed_attempts:
                    summary += (
                        f"- 历史失败次数: {self.failed_attempts[tool_cmd]}\n"
                    )

                summary += "\n"

        return summary if summary else "无历史记录"

    # ── 内部：日志整合 ────────────────────────────────────────────

    def _consolidate_journal(self):
        """将早期日志整合进叙事，保留最近 N 条原样。

        整合不是截断 — LLM 语义提炼，但必须保留所有技术细节。
        压缩度小：宁可叙事稍长，不可丢失任何端口/路径/凭据/payload/失败记录。
        """
        # 取出要整合的条目（保留最近 INTERVAL 条）
        to_consolidate = self.journal_entries[:-_CONSOLIDATION_INTERVAL]
        self.journal_entries = self.journal_entries[-_CONSOLIDATION_INTERVAL:]

        new_entries_text = "\n\n".join(to_consolidate)
        prev_narrative = self.consolidated_narrative or "（首次整合，无历史叙事）"

        prompt = (
            "你是一个CTF解题日志整合器。请将历史叙事和新日志条目合并为一个连贯的技术叙事。\n\n"
            "## 整合原则（非常重要）\n"
            "1. **宁可长，不可丢** — 所有技术细节必须保留\n"
            "2. 以下信息一个都不能少：IP地址/端口号/服务版本/URL路径/文件名/返回码\n"
            "3. 具体命令和有效 payload 必须保留原文\n"
            "4. 发现的凭据/哈希/flag/敏感文件内容必须完整保留\n"
            "5. 失败尝试也要保留，注明失败原因（避免后人踩坑）\n"
            "6. 重复信息合并为一条，但不要因此删除任何独特细节\n"
            "7. 按时间线组织，用 Markdown 格式输出\n\n"
            f"## 历史叙事\n{prev_narrative}\n\n"
            f"## 新日志条目\n{new_entries_text}\n\n"
            "## 整合后叙事\n请输出整合后的完整叙事（Markdown，不要JSON包裹）："
        )

        try:
            from utils.llm_request import LLMRequest
            from utils.text import optimize_text
            llm = LLMRequest("solve_agent")
            response = llm.text_completion(
                prompt=optimize_text(prompt), json_check=False, use_cache=False,
            )
            new_narrative = response.choices[0].message.content.strip()
            # M-15 修复：成功路径也加长度上限 — 超长触发二次压缩
            if len(new_narrative) > _NARRATIVE_MAX_CHARS:
                new_narrative = self._compress_narrative(new_narrative)
            self.consolidated_narrative = new_narrative
            logger.info(
                "日志整合完成: %d 条 → 叙事 %d 字",
                len(to_consolidate), len(self.consolidated_narrative),
            )
        except Exception as e:
            # 降级：M-15 修复 — 不再无脑拼接全文，避免叙事无界增长
            logger.warning("日志整合 LLM 调用失败，使用降级拼接: %s", e)
            self.consolidated_narrative = self._fallback_consolidate(
                prev_narrative, new_entries_text
            )

        # M-14 修复：后置校验 — 整合后扫描受保护模式，缺失则强制追加
        self._ensure_protected_facts(new_entries_text)

    def _fallback_consolidate(self, prev_narrative: str, new_entries_text: str) -> str:
        """LLM 失败时的降级整合 — 只保留标题行 + 关键事实，控制长度。"""
        # 提取每条日志的标题行（## 步N）作为骨架
        title_lines = []
        for line in new_entries_text.split("\n"):
            stripped = line.strip()
            if stripped.startswith("## 步"):
                title_lines.append(stripped)
        skeleton = "\n".join(title_lines)

        # 保留 prev_narrative 头部（如有）
        prev_part = ""
        if prev_narrative and prev_narrative != "（首次整合，无历史叙事）":
            prev_part = prev_narrative[:_FALLBACK_NARRATIVE_MAX_CHARS // 2]
            if len(prev_narrative) > _FALLBACK_NARRATIVE_MAX_CHARS // 2:
                prev_part += "\n...（早期叙事已截断，详见 checkpoint）\n"

        parts = []
        if prev_part:
            parts.append(prev_part)
        parts.append("## 本批次步骤骨架（LLM 整合失败，仅保留标题）\n" + skeleton)

        result = "\n\n".join(parts)
        # 兜底硬截断
        if len(result) > _FALLBACK_NARRATIVE_MAX_CHARS:
            result = result[:_FALLBACK_NARRATIVE_MAX_CHARS] + "\n...（降级叙事已达上限）"
        return result

    def _compress_narrative(self, narrative: str) -> str:
        """叙事超长时的二次压缩 — 调 LLM 提炼要点。"""
        try:
            from utils.llm_request import LLMRequest
            llm = LLMRequest("solve_agent")
            prompt = (
                "以下 CTF 解题叙事过长，请压缩到 6000 字以内，但必须保留：\n"
                "1. 所有凭据/flag/哈希/敏感文件原文\n"
                "2. 关键 IP/端口/服务版本/URL 路径\n"
                "3. 成功 payload 原文\n"
                "4. 失败尝试的原因（可压缩描述）\n\n"
                f"## 原叙事\n{narrative}\n\n"
                "## 压缩后叙事（Markdown）："
            )
            resp = llm.text_completion(prompt=prompt, json_check=False, use_cache=False)
            compressed = resp.choices[0].message.content.strip()
            return compressed if compressed else narrative
        except Exception:
            # LLM 不可用 — 硬截断保头尾
            head = narrative[: _NARRATIVE_MAX_CHARS // 2]
            tail = narrative[-(_NARRATIVE_MAX_CHARS // 2):]
            return f"{head}\n...（中段已省略 {len(narrative) - _NARRATIVE_MAX_CHARS} 字）...\n{tail}"

    def _ensure_protected_facts(self, source_text: str) -> None:
        """M-14 修复 — 扫描源文本中的关键事实，确保整合叙事包含它们。

        若 LLM 整合遗漏了凭据/flag/哈希等，则强制以"关键事实（防丢）"形式追加。
        """
        if not source_text:
            return
        # 从本次待整合的源文本中提取所有受保护事实
        found_facts: List[str] = []
        seen = set()
        for pattern in _PROTECTED_PATTERNS:
            for match in pattern.finditer(source_text):
                fact = match.group(0).strip()
                if fact and fact not in seen:
                    seen.add(fact)
                    found_facts.append(fact)

        if not found_facts:
            return

        # 检查哪些缺失
        missing = [f for f in found_facts if f not in self.consolidated_narrative]
        if not missing:
            return

        # 强制追加到叙事末尾
        block = "\n\n## 关键事实（防丢）\n"
        for f in missing:
            block += f"- `{f}`\n"
        self.consolidated_narrative += block
        logger.warning(
            "记忆整合防丢：检测到 %d 个关键事实未在叙事中，已强制追加",
            len(missing),
        )

    # ── 内部：去重 ────────────────────────────────────────────────

    @staticmethod
    def _normalize_tool_args_key(tool_args) -> str:
        """L-13/L-14 修复 — 把 tool_args 规范化为稳定的字符串 key。

        - list：每个元素先规范化为 json 字符串，再对 list 排序后 join，
                消除 list 元素顺序差异（相同元素不同顺序 → 相同 key）
        - dict：直接 json.dumps(sort_keys=True)
        - str/其他：原样返回
        """
        if tool_args is None:
            return ""
        if isinstance(tool_args, str):
            return tool_args
        if isinstance(tool_args, list):
            # 每个元素转规范化字符串后排序，消除顺序差异
            parts = []
            for item in tool_args:
                if isinstance(item, (dict, list)):
                    try:
                        parts.append(json.dumps(item, sort_keys=True, ensure_ascii=False))
                    except (TypeError, ValueError):
                        parts.append(str(item))
                else:
                    parts.append(str(item))
            return "[" + ",".join(sorted(parts)) + "]"
        if isinstance(tool_args, dict):
            try:
                return json.dumps(tool_args, sort_keys=True, ensure_ascii=False)
            except (TypeError, ValueError):
                return str(tool_args)
        return str(tool_args)

    def _is_duplicate_step(self, step: Dict) -> bool:
        if not self.history:
            return False
        last = self.history[-1]
        # L-13 修复：用 json.dumps(sort_keys=True) 替代 str()，
        # 消除 list 元素顺序与 dict key 顺序导致的去重失效
        same_think = (
            json.dumps(step.get("think", ""), sort_keys=True, ensure_ascii=False)[:200]
            == json.dumps(last.get("think", ""), sort_keys=True, ensure_ascii=False)[:200]
        )
        same_tool = (
            self._normalize_tool_args_key(step.get("tool_args", ""))
            == self._normalize_tool_args_key(last.get("tool_args", ""))
        )
        same_output = (
            json.dumps(step.get("output", ""), sort_keys=True, ensure_ascii=False)[:500]
            == json.dumps(last.get("output", ""), sort_keys=True, ensure_ascii=False)[:500]
        )
        return same_think and same_tool and same_output

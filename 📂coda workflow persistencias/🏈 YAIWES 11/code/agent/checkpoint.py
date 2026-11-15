"""断点续跑 — Checkpoint 存档/读档系统。

保存和恢复 SolveAgent 的完整运行时状态，支持意外中断后从断点继续。
"""

import hashlib
import json
import logging
import os
import shutil
import time
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_CHECKPOINT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "checkpoints")


class CheckpointManager:
    """Checkpoint 管理器 — 以 problem 内容哈希为键，存档/恢复 agent 状态。"""

    @staticmethod
    def _ensure_dir():
        os.makedirs(_CHECKPOINT_DIR, exist_ok=True)

    @staticmethod
    def _problem_key(problem: str, mode: str) -> str:
        """生成存档键：mode + problem 原文的 MD5 前 12 位。"""
        h = hashlib.md5(problem.encode("utf-8")).hexdigest()[:12]
        return f"{mode}_{h}"

    @classmethod
    def save(cls, agent, step_count: int, problem: str, mode: str,
             extra: Optional[dict] = None) -> Optional[str]:
        """将 SolveAgent 当前状态保存到 checkpoint 文件。

        Args:
            agent: SolveAgent 实例
            step_count: 当前步数
            problem: 预处理后的题目文本
            mode: "ctf" 或 "pentest"
            extra: 额外状态（如攻击面数据），会合并到 agent_state 中

        Returns:
            checkpoint 文件路径，失败返回 None
        """
        cls._ensure_dir()
        key = cls._problem_key(problem, mode)
        # 保留最近 3 个同 key checkpoint，用时间戳区分
        timestamp = int(time.time())
        filename = f"checkpoint_{key}_{timestamp}.json"
        filepath = os.path.join(_CHECKPOINT_DIR, filename)

        # 构建结构化摘要
        phase = getattr(agent, 'current_phase', 'unknown')
        findings_count = "?"
        targets_count = "?"
        if hasattr(agent, 'attack_surface') and agent.attack_surface:
            findings_count = str(len(agent.attack_surface.findings))
            targets_count = str(len(agent.attack_surface.targets))
        summary = (
            f"[{mode.upper()}] 阶段: {phase} | "
            f"步数: {step_count} | "
            f"发现: {findings_count} | "
            f"目标: {targets_count}"
        )

        data = {
            "meta": {
                "mode": mode,
                "problem_key": key,
                "step_count": step_count,
                "created_at": timestamp,
                "problem_text": problem,
                "phase": phase,
                "summary": summary,
                "__checkpoint_format__": "v2",  # 结构化版本标识
            },
            "agent_state": {
                "auto_mode": agent.auto_mode,
                "stuck_counter": agent._stuck_counter,
                "recent_tools": agent._recent_tools,
                "recent_output_samples": agent._recent_output_samples,
                "tried_strategies": agent._tried_strategies,
                "strategy_switch_count": agent._strategy_switch_count,
                "recent_thoughts": agent._recent_thoughts,
                "consecutive_none_progress": agent._consecutive_none_progress,
                "recent_tool_errors": agent._recent_tool_errors,
                "last_combined_output": agent._last_combined_output,
                "last_think_normalized": agent._last_think_normalized,
                "bypass_semantic_cache": agent._bypass_semantic_cache,
                "consecutive_identical_think": agent._consecutive_identical_think,
                "llm_failure_count": agent._llm_failure_count,
                "current_phase": agent.current_phase,
                **(extra or {}),
            },
            "memory": {
                "history": agent.memory.history,
                "journal_entries": agent.memory.journal_entries,
                "consolidated_narrative": agent.memory.consolidated_narrative,
                "external_facts": agent.memory._external_facts,
                "failed_attempts": agent.memory.failed_attempts,
            },
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("Checkpoint 已保存: %s (步数 %d)", filepath, step_count)
            cls._cleanup_old(key, keep=3)
            return filepath
        except Exception as e:
            logger.warning("Checkpoint 保存失败: %s", e)
            return None

    @classmethod
    def load(cls, problem: str, mode: str) -> Optional[dict]:
        """查找并加载匹配的 checkpoint。

        Args:
            problem: 题目/授权范围原文（未预处理）
            mode: "ctf" 或 "pentest"

        Returns:
            包含 checkpoint 数据的 dict，未找到返回 None
        """
        cls._ensure_dir()
        key = cls._problem_key(problem, mode)
        candidates = cls._find_files(key)
        if not candidates:
            return None

        latest = candidates[-1]  # 按 mtime 排序后最晚的
        try:
            with open(latest, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info("Checkpoint 已加载: %s (步数 %d)", latest, data["meta"]["step_count"])
            return data
        except Exception as e:
            logger.warning("Checkpoint 加载失败: %s: %s", latest, e)
            return None

    @classmethod
    def list_checkpoints(cls) -> List[Dict]:
        """列出所有 checkpoint。"""
        cls._ensure_dir()
        results = []
        for fname in os.listdir(_CHECKPOINT_DIR):
            if not fname.startswith("checkpoint_") or not fname.endswith(".json"):
                continue
            fpath = os.path.join(_CHECKPOINT_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    meta = json.load(f).get("meta", {})
                results.append({
                    "file": fname,
                    "path": fpath,
                    "mode": meta.get("mode", "?"),
                    "step_count": meta.get("step_count", 0),
                    "phase": meta.get("phase", ""),
                    "summary": meta.get("summary", ""),
                    "created_at": meta.get("created_at", 0),
                })
            except Exception:
                continue
        results.sort(key=lambda x: x["created_at"], reverse=True)
        return results

    @classmethod
    def remove(cls, filepath: str):
        """删除指定 checkpoint 文件。"""
        try:
            os.remove(filepath)
            logger.debug("Checkpoint 已删除: %s", filepath)
        except Exception as e:
            logger.warning("Checkpoint 删除失败: %s: %s", filepath, e)

    @classmethod
    def clear_key(cls, problem: str, mode: str):
        """清除某个 problem 的所有 checkpoint（解题成功后调用）。"""
        key = cls._problem_key(problem, mode)
        for fpath in cls._find_files(key):
            cls.remove(fpath)

    # ── 内部辅助 ───────────────────────────────────────────────────

    @classmethod
    def _find_files(cls, key: str) -> List[str]:
        """查找匹配指定 key 的 checkpoint 文件，按修改时间升序。"""
        cls._ensure_dir()
        matches = []
        for fname in os.listdir(_CHECKPOINT_DIR):
            if fname.startswith(f"checkpoint_{key}_") and fname.endswith(".json"):
                fpath = os.path.join(_CHECKPOINT_DIR, fname)
                matches.append(fpath)
        matches.sort(key=lambda p: os.path.getmtime(p))
        return matches

    @classmethod
    def _cleanup_old(cls, key: str, keep: int = 3):
        """保留最近 keep 个 checkpoint，删除更旧的。"""
        files = cls._find_files(key)
        while len(files) > keep:
            old = files.pop(0)
            cls.remove(old)

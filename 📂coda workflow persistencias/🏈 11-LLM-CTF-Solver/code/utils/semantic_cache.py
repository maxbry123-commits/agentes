"""
LLM 语义缓存 —— 基于 prompt 向量相似度复用历史响应。

两层缓存:
  L1: 精确匹配 (MD5 hash) — 零开销，命中重试请求
  L2: 语义匹配 (cosine similarity > threshold) — 命中语义相近的请求

配置文件 config.json 中添加:
  "semantic_cache": {
      "enabled": true,
      "similarity_threshold": 0.92,
      "max_entries": 500
  }
"""

import atexit
import hashlib
import json
import logging
import os
import re
import threading
import time
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

_CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "semantic_cache.json")
_DEFAULT_THRESHOLD = 0.92
_DEFAULT_MAX = 500

# L2 语义缓存双阈值: 高分直接命中，低分需关键词校验
# v3: 放宽阈值以匹配 LLM 循环中语义相似但关键词变化的情况
_L2_HIGH = 0.92
_L2_LOW = 0.78


class SemanticCache:
    _instance: Optional["SemanticCache"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_ready"):
            return
        self._ready = True
        self._rwlock = threading.RLock()
        self.entries: list[dict] = []       # [{embedding, prompt_hash, response, ts}]
        self.hash_index: dict[str, int] = {}  # prompt_hash -> index in entries
        self._embedding_llm = None           # 延迟初始化，避免循环导入
        self._dirty_count = 0                # 未写入磁盘的新条目数
        self._batch_save_threshold = 5       # 每 N 个新条目写一次磁盘
        self._load()

    # ---- 公开接口 --------------------------------------------------------

    @staticmethod
    def _normalize_for_cache(prompt: str) -> str:
        """归一化 prompt，减少瞬态信息（步骤编号/时间戳/临时路径）对缓存的干扰。"""
        normalized = prompt
        normalized = re.sub(r'步骤\s*\d+', '步骤 N', normalized)
        normalized = re.sub(r'第\s*\d+\s*(步|行|次|轮)', r'第 N 步', normalized)
        normalized = re.sub(r'已进行\s*\d+\s*步', '已进行 N 步', normalized)
        normalized = re.sub(r'[Ss]tep\s*\d+', 'Step N', normalized)
        normalized = re.sub(r'\d{2}:\d{2}:\d{2}', '', normalized)
        normalized = re.sub(r'/tmp/[a-zA-Z0-9_/.\-]+', '/tmp/FILE', normalized)
        return normalized

    @staticmethod
    def _keyword_overlap(a: str, b: str) -> float:
        """计算两个字符串的关键词重叠率 (0.0 ~ 1.0)。"""
        words_a = set(re.findall(r'[\w一-鿿]+', a.lower()))
        words_b = set(re.findall(r'[\w一-鿿]+', b.lower()))
        if not words_a or not words_b:
            return 0.0
        return len(words_a & words_b) / max(len(words_a), len(words_b))

    @property
    def embedding_llm(self):
        """延迟导入 LLMRequest，避免循环依赖"""
        if self._embedding_llm is None:
            from utils.llm_request import LLMRequest
            self._embedding_llm = LLMRequest("embedding")
        return self._embedding_llm

    def lookup(self, prompt: str, threshold: float = _DEFAULT_THRESHOLD,
               fingerprint: str = None) -> Optional[str]:
        """查询缓存 — 返回命中的响应文本，未命中返回 None。

        Args:
            prompt: 完整 prompt 文本（用于 L1 MD5 + 关键词校验）
            fingerprint: 语义指纹文本（用于 L2 embedding，None 则用 prompt）
            长 prompt (>6000 字) 的 embedding 会触发 API 400 错误，fingerprint
            只提取 prompt 中真正变化的"语义核心"，稳定在 1000-1500 字。
        """
        cfg = self._load_config()
        if not cfg.get("enabled", True):
            return None

        threshold = threshold if threshold != _DEFAULT_THRESHOLD else cfg.get(
            "similarity_threshold", _DEFAULT_THRESHOLD
        )
        normalized = self._normalize_for_cache(prompt)
        prompt_hash = hashlib.md5(normalized.encode("utf-8")).hexdigest()

        with self._rwlock:
            # L1: 精确匹配（归一化后）
            if prompt_hash in self.hash_index:
                idx = self.hash_index[prompt_hash]
                logger.info("语义缓存 L1 命中 (精确匹配)")
                return self.entries[idx]["response"]

            if not self.entries:
                return None

            # threshold >= 1.0 表示仅 L1 精确匹配（JSON 模式），跳过 L2 语义匹配
            if threshold >= 1.0:
                return None

            # L2: 语义匹配 — 使用 fingerprint 做 embedding（若提供），避免长文本超限
            try:
                embed_text = fingerprint if fingerprint else prompt
                embedding = self._embed(embed_text)
            except Exception:
                logger.debug("获取 embedding 失败，跳过 L2 缓存查询")
                return None

            best_sim, best_idx = -1.0, -1
            entries = self.entries
            for i, entry in enumerate(entries):
                sim = self._cosine_sim(embedding, entry["embedding"])
                if sim > best_sim:
                    best_sim, best_idx = sim, i

            if best_idx < 0:
                return None

            # L2 高分（>= threshold）直接命中
            if best_sim >= threshold:
                logger.info("语义缓存 L2 命中 (高分, 相似度=%.3f)", best_sim)
                return entries[best_idx]["response"]

            # L2 低分（>= 0.78）需关键词校验 (v3: 重叠率降到 0.3)
            if best_sim >= _L2_LOW:
                stored_prompt = entries[best_idx].get("prompt", "")
                overlap = self._keyword_overlap(prompt, stored_prompt)
                if overlap >= 0.3:
                    logger.info("语义缓存 L2 命中 (低分+校验, 相似度=%.3f, 重叠率=%.2f)",
                                best_sim, overlap)
                    return entries[best_idx]["response"]
                else:
                    logger.debug("L2 候选被关键词校验拒绝 (相似度=%.3f, 重叠率=%.2f)",
                                 best_sim, overlap)

        return None

    def store(self, prompt: str, response: str, fingerprint: str = None):
        """存储 prompt→response 映射（若已存在则跳过）。

        Args:
            fingerprint: 用于 L2 embedding 的语义指纹（None 则用 prompt 全文）
        """
        normalized = self._normalize_for_cache(prompt)
        prompt_hash = hashlib.md5(normalized.encode("utf-8")).hexdigest()

        with self._rwlock:
            if prompt_hash in self.hash_index:
                return  # 已存在，不重复存储

            try:
                embed_text = fingerprint if fingerprint else prompt
                embedding = self._embed(embed_text)
            except Exception:
                logger.debug("获取 embedding 失败，跳过缓存存储")
                return

            entry = {
                "embedding": embedding,
                "prompt_hash": prompt_hash,
                "prompt": prompt[:500],  # 保存原文前500字符，用于 L2 关键词校验
                "response": response,
                "ts": time.time(),
            }
            self.entries.append(entry)
            self.hash_index[prompt_hash] = len(self.entries) - 1

            # 超量裁剪
            cfg = self._load_config()
            max_entries = cfg.get("max_entries", _DEFAULT_MAX)
            if len(self.entries) > max_entries:
                removed = self.entries.pop(0)
                self.hash_index.pop(removed["prompt_hash"], None)
                self._rebuild_index()

            # 延迟写入：每 N 个新条目写一次磁盘
            self._dirty_count += 1
            if self._dirty_count >= self._batch_save_threshold:
                self._save()
                self._dirty_count = 0

    # ---- 内部 -----------------------------------------------------------

    def _embed(self, text: str) -> list[float]:
        """调用 embedding API 获取向量。"""
        response = self.embedding_llm.embedding(text)
        return response.data[0]["embedding"]

    @staticmethod
    def _cosine_sim(a: list[float], b: list[float]) -> float:
        """余弦相似度 (numpy)。"""
        va = np.array(a, dtype=np.float32)
        vb = np.array(b, dtype=np.float32)
        dot = float(np.dot(va, vb))
        na = float(np.linalg.norm(va))
        nb = float(np.linalg.norm(vb))
        if na == 0.0 or nb == 0.0:
            return 0.0
        return dot / (na * nb)

    def _rebuild_index(self):
        self.hash_index = {e["prompt_hash"]: i for i, e in enumerate(self.entries)}

    @staticmethod
    def _load_config() -> dict:
        try:
            from config import Config
            return Config.load_config().get("semantic_cache", {})
        except Exception:
            return {}

    # ---- 持久化 ---------------------------------------------------------

    def _load(self):
        if not os.path.exists(_CACHE_FILE):
            return
        try:
            with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.entries = data.get("entries", [])
            self._rebuild_index()
            logger.info("语义缓存加载完成 (%d 条记录)", len(self.entries))
        except Exception as e:
            logger.warning("加载语义缓存失败: %s", e)
            self.entries = []
            self.hash_index = {}

    def flush(self):
        """强制写入磁盘（程序退出前调用）。"""
        with self._rwlock:
            self._save()

    def reset_session(self):
        """清除全部缓存并持久化到磁盘 — 新任务启动时调用，防止跨会话污染。

        跨会话场景:
          - 同一题目重试: 上次跑崩了/sigterm 退出，缓存中残留错误推理链
          - 不同题目切换: 旧题目的 LLM 响应可能被 L2 语义匹配误命中

        此方法会立即写入磁盘使清理生效，即使后续任务崩溃也不会残留旧数据。
        """
        with self._rwlock:
            count = len(self.entries)
            self.entries.clear()
            self.hash_index.clear()
            self._dirty_count = 0
            self._save()
        if count:
            logger.info("语义缓存已重置 (%d 条记录已清除)", count)

    def _save(self, _open=open):
        try:
            with _open(_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({"entries": self.entries}, f, ensure_ascii=False)
        except Exception as e:
            logger.warning("保存语义缓存失败: %s", e)

    def __del__(self):
        try:
            self.flush()
        except Exception:
            pass


def get_cache() -> SemanticCache:
    """获取语义缓存单例。"""
    return SemanticCache()


def reset_session_cache():
    """清除语义缓存 — 新任务启动时调用，防止跨会话污染。"""
    get_cache().reset_session()

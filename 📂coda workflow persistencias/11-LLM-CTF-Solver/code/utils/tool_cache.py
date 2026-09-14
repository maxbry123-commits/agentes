"""工具结果缓存 — 相同参数的工具调用在 TTL 内直接返回缓存结果。
防重放: 同一 key 连续命中 2 次后自动绕行，避免缓存锁死 Agent。
"""

import json
import time
import hashlib
import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)

_MAX_CONSECUTIVE_HITS = 2  # 同一 key 连续命中上限，超限自动绕过


class ToolCache:
    """工具结果缓存。

    缓存键 = MD5(tool_name + sorted(arguments))
    默认 TTL 300 秒，可配置。
    防重放机制: 同一 key 连续命中超过 _MAX_CONSECUTIVE_HITS 次后返回 None，
    强制重新执行以避免"缓存死锁"。
    """

    def __init__(self, ttl_seconds: int = 300):
        self._cache: Dict[str, Dict[str, Tuple[float, str]]] = {}
        self._ttl = ttl_seconds
        self._hit_counts: Dict[str, int] = {}  # key → 连续命中次数
        self._last_key: Optional[str] = None    # 上一次命中的 key

    def _make_key(self, tool_name: str, arguments: dict) -> str:
        key_str = json.dumps(
            {tool_name: arguments}, sort_keys=True, ensure_ascii=False,
        )
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, tool_name: str, arguments: dict) -> Optional[str]:
        """获取缓存结果，过期或不存在返回 None。
        同一 key 连续命中超过上限后自动绕过缓存。"""
        tool_cache = self._cache.get(tool_name)
        if not tool_cache:
            return None
        key = self._make_key(tool_name, arguments)
        entry = tool_cache.get(key)
        if entry and (time.time() - entry[0]) < self._ttl:
            # 连续命中检测
            if key == self._last_key:
                self._hit_counts[key] = self._hit_counts.get(key, 0) + 1
                if self._hit_counts[key] >= _MAX_CONSECUTIVE_HITS:
                    logger.warning(
                        "工具缓存连续命中 %d 次 (%s)，强制绕过以打破死循环",
                        self._hit_counts[key], tool_name,
                    )
                    return None
            else:
                self._hit_counts[key] = 1
                self._last_key = key
            logger.debug("工具缓存命中: %s (连续=%d)", tool_name, self._hit_counts[key])
            return entry[1]
        return None

    def set(self, tool_name: str, arguments: dict, output: str):
        """写入缓存结果，并重置该 key 的命中计数。"""
        key = self._make_key(tool_name, arguments)
        if tool_name not in self._cache:
            self._cache[tool_name] = {}
        self._cache[tool_name][key] = (time.time(), output)
        # 新写入意味着结果已变化，重置命中计数
        if key in self._hit_counts:
            self._hit_counts[key] = 0

    def invalidate(self, tool_name: str):
        """清除指定工具的全部缓存及命中计数。"""
        self._cache.pop(tool_name, None)
        # 清除对应命中计数
        keys_to_drop = [k for k in self._hit_counts if k.startswith(tool_name)]
        for k in keys_to_drop:
            self._hit_counts.pop(k, None)
        logger.info("工具缓存已清除: %s", tool_name)

    def clear(self):
        """清除全部工具缓存。"""
        count = sum(len(v) for v in self._cache.values())
        self._cache.clear()
        self._hit_counts.clear()
        self._last_key = None
        if count:
            logger.info("工具缓存已全部清除 (%d 条)", count)

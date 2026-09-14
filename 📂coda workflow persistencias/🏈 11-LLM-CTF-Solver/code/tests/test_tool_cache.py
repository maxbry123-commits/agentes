"""tool_cache.py 测试 — 缓存命中/过期/清除逻辑。"""

import time
import pytest
from utils.tool_cache import ToolCache


class TestToolCache:
    """工具结果缓存的核心行为。"""

    def setup_method(self):
        self.cache = ToolCache(ttl_seconds=60)

    def test_set_and_get(self):
        self.cache.set("nmap", {"target": "127.0.0.1"}, "open ports: 80")
        result = self.cache.get("nmap", {"target": "127.0.0.1"})
        assert result == "open ports: 80"

    def test_miss_on_different_args(self):
        self.cache.set("nmap", {"target": "A"}, "result A")
        result = self.cache.get("nmap", {"target": "B"})
        assert result is None

    def test_miss_on_different_tool(self):
        self.cache.set("tool_a", {}, "result")
        result = self.cache.get("tool_b", {})
        assert result is None

    def test_miss_after_expiry(self):
        cache = ToolCache(ttl_seconds=0)  # 立即过期
        cache.set("x", {}, "data")
        time.sleep(0.01)
        assert cache.get("x", {}) is None

    def test_invalidate_single_tool(self):
        self.cache.set("a", {}, "1")
        self.cache.set("b", {}, "2")
        self.cache.invalidate("a")
        assert self.cache.get("a", {}) is None
        assert self.cache.get("b", {}) == "2"

    def test_clear_all(self):
        self.cache.set("a", {}, "1")
        self.cache.set("b", {}, "2")
        self.cache.clear()
        assert self.cache.get("a", {}) is None
        assert self.cache.get("b", {}) is None

    def test_cache_key_order_independent(self):
        """相同参数不同顺序应命中同一缓存。"""
        self.cache.set("x", {"b": 2, "a": 1}, "result")
        assert self.cache.get("x", {"a": 1, "b": 2}) == "result"

    def test_cache_key_type_stable(self):
        """int 1 和 str '1' 是不同缓存键。"""
        self.cache.set("x", {"port": 1}, "int")
        result = self.cache.get("x", {"port": "1"})
        # 取决于 json.dumps 行为，int 1 → "1", str "1" → "\"1\""
        # 它们应该是不同的键才对
        assert result is None

    def test_invalidate_nonexistent(self):
        """清除不存在的工具不应报错。"""
        self.cache.invalidate("nonexistent")  # 不应抛异常

    def test_clear_empty(self):
        """清空空缓存不应报错。"""
        cache = ToolCache()
        cache.clear()  # 不应抛异常

    def test_get_nonexistent_tool(self):
        assert self.cache.get("nonexistent", {}) is None

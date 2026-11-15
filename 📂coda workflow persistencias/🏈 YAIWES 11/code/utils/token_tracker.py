"""Token 用量追踪器 — 线程安全的全局 LLM Token 计数器。"""
import threading
import time

# 常见模型定价 ($/1M tokens)，用于成本估算
_MODEL_PRICING = {
    "gpt-4o":                     (2.50, 10.00),
    "gpt-4o-mini":                (0.15,  0.60),
    "gpt-4-turbo":                (10.00, 30.00),
    "gpt-4":                      (30.00, 60.00),
    "gpt-3.5-turbo":              (0.50,  1.50),
    "claude-3-opus":              (15.00, 75.00),
    "claude-3.5-sonnet":          (3.00, 15.00),
    "claude-3.5-haiku":           (0.80,  4.00),
    "claude-4-opus":              (15.00, 75.00),
    "claude-4-sonnet":            (3.00, 15.00),
    "claude-haiku-4-5":           (0.80,  4.00),
    "deepseek-v3":                (0.27,  1.10),
    "deepseek-r1":                (0.55,  2.19),
    "deepseek-chat":              (0.27,  1.10),
    "deepseek-reasoner":          (0.55,  2.19),
    "qwen-plus":                  (0.40,  1.20),
    "qwen-max":                   (2.00,  6.00),
    "glm-4":                      (1.00,  1.00),
    "moonshot-v1":                (0.60,  1.20),
}


def _match_model_price(model_id: str) -> tuple:
    """模糊匹配模型定价（输入/输出 $/1M tokens）。"""
    model_lower = model_id.lower().replace("_", "-")
    for key, price in _MODEL_PRICING.items():
        if key in model_lower or model_lower in key:
            return price
    return (0.0, 0.0)


class TokenTracker:
    """线程安全的 Token 用量累加器（单例）。"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    obj = super().__new__(cls)
                    obj._mtx = threading.Lock()
                    obj._reset()
                    cls._instance = obj
        return cls._instance

    def _reset(self):
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.total_tokens: int = 0
        self.call_count: int = 0
        self.model_id: str = ""
        self._start_time: float = time.time()
        self._input_price: float = 0.0
        self._output_price: float = 0.0

    def record(self, model_id: str, prompt_tokens: int,
               completion_tokens: int, total_tokens: int = 0):
        """记录一次 LLM 调用的用量。"""
        if not model_id:
            return
        with self._mtx:
            if not self.model_id:
                self.model_id = model_id
                self._input_price, self._output_price = _match_model_price(model_id)
            self.prompt_tokens += prompt_tokens
            self.completion_tokens += completion_tokens
            self.total_tokens += total_tokens or (prompt_tokens + completion_tokens)
            self.call_count += 1

    def snapshot(self) -> dict:
        """获取当前累计用量快照（线程安全）。"""
        with self._mtx:
            cost = (self.prompt_tokens / 1_000_000 * self._input_price +
                    self.completion_tokens / 1_000_000 * self._output_price)
            return {
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens,
                "call_count": self.call_count,
                "cost": round(cost, 4),
                "elapsed_s": round(time.time() - self._start_time, 1),
            }

    def reset(self):
        with self._mtx:
            self._reset()


def get_token_tracker() -> TokenTracker:
    return TokenTracker()

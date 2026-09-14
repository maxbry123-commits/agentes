import hashlib
import json
import litellm
import logging
import threading
import time
from config import Config
from utils.text import optimize_text
from litellm.utils import ModelResponse, CustomStreamWrapper
from litellm.types.utils import Choices, Message
from typing import Union, List

logger = logging.getLogger(__name__)

_REQUEST_TIMEOUT = 120  # 单次请求超时（秒）
_MAX_RETRIES = 2        # 最大重试次数
_RETRY_DELAY = 3        # 重试间隔（秒）
_json_schema_lock = threading.Lock()  # 保护 litellm 全局状态


class LLMRequest:
    def __init__(self, model: str):
        config: dict = Config.load_config()
        self.llm_config = config["llm"][model]

    def text_completion(
        self, prompt: str, json_check: bool, use_cache: bool = True,
        cache_fingerprint: str = None, **kwargs
    ) -> Union[ModelResponse, CustomStreamWrapper]:
        optimized = optimize_text(prompt)
        message = litellm.Message(role="user", content=optimized)
        cache_key = self._cache_key(optimized, kwargs)

        # ── 语义缓存查询 ──
        if use_cache:
            try:
                from utils.semantic_cache import get_cache
                cache = get_cache()
                # JSON 模式仅用 L1 精确匹配，避免语义相近但 JSON 结构不同
                if json_check:
                    cached = cache.lookup(optimized, threshold=1.0, fingerprint=cache_fingerprint)
                else:
                    cached = cache.lookup(optimized, fingerprint=cache_fingerprint)
            except Exception:
                cached = None
            if cached is not None:
                logger.debug("LLM 语义缓存命中")
                return _build_cached_response(cached)

        last_exception = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                with _json_schema_lock:
                    _old = litellm.enable_json_schema_validation
                    if json_check is True:
                        litellm.enable_json_schema_validation = True

                try:
                    response = litellm.completion(
                        model=self.llm_config["model"],
                        api_key=self.llm_config["api_key"],
                        api_base=self.llm_config["api_base"],
                        messages=[message],
                        timeout=_REQUEST_TIMEOUT,
                        **kwargs
                    )
                finally:
                    with _json_schema_lock:
                        litellm.enable_json_schema_validation = _old

                content = response.choices[0].message.content
                logger.debug(f"LLM Response Message: {content}")

                if use_cache:
                    # 纯 tool_calls 响应（content 为空）时，将 tool_calls 序列化为文本
                    # 存入缓存，命中后由文本提取层（layer 2）解析，保持一致的命中路径
                    cache_content = content
                    if not cache_content:
                        msg = response.choices[0].message
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            try:
                                tc_list = []
                                for tc in msg.tool_calls:
                                    args = tc.function.arguments
                                    if isinstance(args, str):
                                        try:
                                            args = json.loads(args)
                                        except json.JSONDecodeError:
                                            args = {}
                                    elif not isinstance(args, dict):
                                        args = {}
                                    tc_list.append({
                                        "tool_name": tc.function.name,
                                        "arguments": args,
                                    })
                                cache_content = json.dumps(
                                    {"tool_calls": tc_list}, ensure_ascii=False,
                                )
                            except Exception:
                                pass
                    if cache_content:
                        try:
                            from utils.semantic_cache import get_cache
                            get_cache().store(optimized, cache_content, fingerprint=cache_fingerprint)
                        except Exception:
                            pass

                # 记录 Token 用量
                try:
                    usage = getattr(response, 'usage', None)
                    if usage:
                        from utils.token_tracker import get_token_tracker
                        get_token_tracker().record(
                            model_id=self.llm_config.get("model", ""),
                            prompt_tokens=getattr(usage, 'prompt_tokens', 0) or 0,
                            completion_tokens=getattr(usage, 'completion_tokens', 0) or 0,
                            total_tokens=getattr(usage, 'total_tokens', 0) or 0,
                        )
                except Exception:
                    pass

                return response
            except Exception as e:
                last_exception = e
                logger.warning(f"LLM 请求失败 (第{attempt + 1}次): {e}")
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_DELAY)
                continue

        raise RuntimeError(f"LLM 请求失败，已重试{_MAX_RETRIES}次") from last_exception

    @staticmethod
    def _cache_key(prompt: str, kwargs: dict) -> str:
        """生成缓存键 — prompt + 关键参数哈希。"""
        key_params = {k: v for k, v in kwargs.items()
                      if k in ("temperature", "top_p", "response_format", "tools")}
        raw = prompt + json.dumps(key_params, sort_keys=True)
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def embedding(
        self, text: Union[str, List[str]], **kwargs
    ) -> Union[ModelResponse, CustomStreamWrapper]:
        if isinstance(text, str):
            text = [text]

        last_exception = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                response = litellm.embedding(
                    model=self.llm_config["model"],
                    api_key=self.llm_config["api_key"],
                    api_base=self.llm_config["api_base"],
                    input=text,
                    timeout=_REQUEST_TIMEOUT,
                    **kwargs
                )
                return response
            except Exception as e:
                last_exception = e
                logger.warning(f"Embedding 请求失败 (第{attempt + 1}次): {e}")
                if attempt < _MAX_RETRIES:
                    time.sleep(_RETRY_DELAY)
                continue

        raise RuntimeError(f"Embedding 请求失败，已重试{_MAX_RETRIES}次") from last_exception


def _build_cached_response(content: str) -> ModelResponse:
    """从缓存文本重建 ModelResponse（兼容 litellm >=1.55）。"""
    return ModelResponse(
        id="cache-hit",
        choices=[Choices(
            finish_reason="stop",
            index=0,
            message=Message(content=content, role="assistant"),
        )],
    )

"""WebUIInterface — 将同步 SolveAgent 桥接到 Redis WebSocket 消息总线。

模式与 TextualUserInterface 完全一致:
  - display()  → 非阻塞 publish SystemMessage 到 Redis
  - confirm()  → 阻塞轮询 Redis 等待前端 WebSocket 传回决策
  - choose()   → 同上
  - prompt_text() → 同上

使用 redis-py 同步客户端（线程安全），运行在 SolveAgent 的 worker 线程中。
"""
import json
import logging
import threading
import uuid
from typing import List

import redis

from agent.user_interface import UserInterface
from backend.app.schemas.messages import SystemMessage, ApprovalMessage
from backend.app.services.redis_manager import redis_manager, save_message_to_file_sync

logger = logging.getLogger(__name__)

REDIS_URL = "redis://localhost:6379/0"
_APPROVAL_TIMEOUT = 300  # 默认 HIL 决策超时（秒）


class WebUIInterface(UserInterface):
    """Web UI 版 UserInterface — 通过 Redis 与 WebSocket 前端通信。"""

    def __init__(self, task_id: str):
        self._task_id = task_id
        self._sync_redis = redis.Redis.from_url(REDIS_URL, decode_responses=True, protocol=2)
        self._event = threading.Event()
        self._decision_result: dict | None = None

    def display(self, message: str):
        """非阻塞：发布 SystemMessage 到 Redis + 持久化到文件。"""
        try:
            msg = SystemMessage(content=message)
            self._sync_redis.publish(f"task:{self._task_id}:messages", msg.model_dump_json())
            save_message_to_file_sync(redis_manager.messages_dir, self._task_id, msg)
        except Exception as e:
            logger.warning("WebUIInterface.display 失败: %s", e)

    def display_separator(self, char: str = "=", length: int = 48):
        self.display(char * length)

    def confirm(self, prompt: str, yes_label: str = "y", no_label: str = "n") -> bool:
        """阻塞：发布 ApprovalMessage，轮询 Redis 等待用户决策。"""
        return self._await_decision(prompt, "confirm", [yes_label, no_label]) == yes_label

    def choose(self, prompt: str, options: List[str]) -> str:
        """阻塞：发布 ApprovalMessage，轮询 Redis 等待用户选择。"""
        result = self._await_decision(prompt, "choose", options)
        return result if isinstance(result, str) else (options[0] if options else "")

    def prompt_text(self, prompt: str) -> str:
        """阻塞：发布 ApprovalMessage，等待用户文本输入。"""
        result = self._await_decision(prompt, "prompt_text", [])
        return result if isinstance(result, str) else ""

    # ── 内部 ──────────────────────────────────────────────────────

    def _await_decision(self, prompt: str, checkpoint_type: str, options: list) -> str | None:
        """发布审批消息 → 阻塞轮询 Redis → 返回用户决策。"""
        checkpoint_id = str(uuid.uuid4())
        approval = ApprovalMessage(
            checkpoint_id=checkpoint_id,
            prompt={"message": prompt, "type": checkpoint_type},
            options=options,
            timeout=_APPROVAL_TIMEOUT,
        )
        redis_key = f"state:checkpoint:{self._task_id}:{checkpoint_id}"

        try:
            # 1. 发布审批消息 + 持久化到文件
            self._sync_redis.publish(
                f"task:{self._task_id}:messages",
                approval.model_dump_json(),
            )
            save_message_to_file_sync(redis_manager.messages_dir, self._task_id, approval)
        except Exception as e:
            logger.error("发布 ApprovalMessage 失败: %s", e)
            return options[0] if options else None

        # 2. 阻塞轮询 Redis（每 1s，最长 300s）
        self._event.clear()
        self._decision_result = None
        elapsed = 0
        while elapsed < _APPROVAL_TIMEOUT:
            if self._event.wait(timeout=1.0):
                # 被外部信号唤醒（预留扩展点）
                break
            elapsed += 1
            try:
                raw = self._sync_redis.get(redis_key)
                if raw:
                    decision = json.loads(raw)
                    self._decision_result = decision
                    # 消费后删除
                    self._sync_redis.delete(redis_key)
                    break
            except Exception:
                pass

        result = self._decision_result
        if result is None:
            logger.warning("HIL 决策超时 (%ss)，使用默认值", _APPROVAL_TIMEOUT)
            return options[0] if options else None

        action = result.get("action", "")
        content = result.get("content", "")
        if checkpoint_type == "confirm":
            return action  # 返回 yes_label/no_label
        elif checkpoint_type == "choose":
            return action  # 返回选项文本
        else:
            return content  # prompt_text 返回内容

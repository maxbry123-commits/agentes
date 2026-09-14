import re
import json
import logging
from json_repair import repair_json


logger = logging.getLogger(__name__)


def fix_json_with_llm(json_str: str, err_content: str) -> str:
    """
    使用LLM修复格式错误的JSON
    :param json_str: 格式错误的JSON字符串
    :param err_content: 错误信息
    :return: 修复后的JSON字符串
    :raises ValueError: 超过最大重试次数仍无法修复
    """
    from utils.llm_request import LLMRequest
    pre_processor = LLMRequest("pre_processor")
    max_retries = 3

    for attempt in range(max_retries):
        # 先尝试 repair_json 修复
        try:
            repaired = repair_json(json_str)
            if json.loads(repaired):
                return repaired
        except Exception:
            pass

        # 调用 LLM 修复
        prompt = (
            "以下是一个格式错误的JSON字符串，请修复它使其成为有效的JSON。"
            "只返回修复后的JSON，不要包含任何其他内容。"
            "确保保留所有原始键值对，不要改动里面的内容\n\n"
            f"错误JSON: {json_str}"
            f"错误信息: {err_content}"
        )
        try:
            response = pre_processor.text_completion(prompt, json_check=False)
            json_str = response.choices[0].message.content.strip()
        except Exception:
            if attempt == max_retries - 1:
                raise ValueError(f"无法修复JSON格式，已重试{max_retries}次: {json_str[:200]}")
            continue

    raise ValueError(f"无法修复JSON格式，已重试{max_retries}次: {json_str[:200]}")


def optimize_text(text: str) -> str:
    """
    缩减 Prompt：
    压缩连续空格和制表符，但保留换行符结构（段落分隔等重要格式）。
    """
    text = re.sub(r"[ \t]{2,}", " ", text)     # 连续空格/制表符 → 单个空格
    text = re.sub(r"\n{4,}", "\n\n\n", text)   # 过多连续换行 → 最多保留2个空行
    return text.strip()



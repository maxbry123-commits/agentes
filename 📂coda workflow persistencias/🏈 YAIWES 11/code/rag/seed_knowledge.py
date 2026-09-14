"""CTF 知识种子加载器 — 将预置知识导入 ChromaDB。"""

import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

_SEED_DIR = os.path.join(os.path.dirname(__file__), "seed_data")


def load_seed_files() -> Dict[str, List[Dict]]:
    """加载所有种子数据文件，按分类返回。"""
    if not os.path.isdir(_SEED_DIR):
        logger.warning(f"种子数据目录不存在: {_SEED_DIR}")
        return {}

    categories = {}
    for fname in sorted(os.listdir(_SEED_DIR)):
        if fname.endswith(".json"):
            fpath = os.path.join(_SEED_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                cat = fname[:-5]  # 去掉 .json
                categories[cat] = data
                logger.info(f"已加载种子数据: {fname} ({len(data)} 条)")
            except Exception as e:
                logger.error(f"加载 {fname} 失败: {e}")
    return categories


def seed_knowledge_base(knowledge_base) -> Dict[str, int]:
    """将种子数据导入知识库。返回各分类的导入数量。"""
    categories = load_seed_files()
    if not categories:
        return {}

    stats = {}
    total = 0

    for category, items in categories.items():
        count = 0
        for item in items:
            try:
                # 构建知识条目内容
                content_parts = [item.get("title", ""), item.get("content", "")]
                content = "\n".join(content_parts)

                # 提取标签（兼容 str 和 list 两种格式）
                tags = item.get("tags", category)
                if isinstance(tags, list):
                    tags_str = ",".join(str(t).strip() for t in tags if str(t).strip())
                elif isinstance(tags, str):
                    tags_str = ",".join(t.strip() for t in tags.split(",") if t.strip())
                else:
                    tags_str = str(tags)

                metadata = {
                    "type": "seed_knowledge",
                    "category": category,
                    "tags": tags_str,
                    "title": item.get("title", "")[:200],
                    "tools": item.get("tools", ""),
                    "checklist": item.get("checklist", ""),
                    "timestamp": datetime.now().isoformat(),
                }

                # 使用 knowledge_base 的 add_general_knowledge 方法
                knowledge_base.add_general_knowledge(content, [t.strip() for t in tags.split(",") if t.strip()])
                count += 1
                total += 1

            except Exception as e:
                logger.warning(f"添加知识条目失败 [{category}]: {e}")

        stats[category] = count
        logger.info(f"已导入 {category}: {count} 条")

    stats["total"] = total
    return stats


def get_seed_stats() -> Dict:
    """获取种子数据统计信息（不导入）。"""
    categories = load_seed_files()
    stats = {}
    for cat, items in categories.items():
        stats[cat] = {
            "count": len(items),
            "titles": [i.get("title", "") for i in items],
        }
    stats["total"] = sum(v["count"] for v in stats.values())
    return stats

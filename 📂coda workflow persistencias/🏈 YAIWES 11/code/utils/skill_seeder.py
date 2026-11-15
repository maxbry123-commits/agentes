"""技能知识库种子加载器 — 将 skills/ 目录的 SKILL.md 导入 ChromaDB。"""

import logging
from typing import Dict
from utils.skill_loader import load_all_skills

logger = logging.getLogger(__name__)

# 技能名 → 额外标签的映射，提升检索召回率
_TAG_MAP = {
    "sqli": "sql-injection",
    "xss": "xss",
    "ssrf": "ssrf",
    "cmdi": "command-injection",
    "csrf": "csrf",
    "cors": "cors",
    "idor": "idor",
    "jwt": "jwt",
    "oauth": "oauth",
    "ssti": "ssti",
    "xxe": "xxe",
    "lfi": "lfi",
    "nosql": "nosql-injection",
    "saml": "saml",
    "jndi": "jndi-injection",
    "crlf": "crlf-injection",
    "graphql": "graphql",
    "prototype": "prototype-pollution",
    "deserialization": "deserialization",
    "upload": "file-upload",
    "path-traversal": "path-traversal",
    "request-smuggling": "request-smuggling",
    "race-condition": "race-condition",
    "business-logic": "business-logic",
    "dependency-confusion": "dependency-confusion",
    "clickjacking": "clickjacking",
    "open-redirect": "open-redirect",
    "websocket": "websocket",
    "cache": "web-cache",
    "type-juggling": "type-juggling",
    "xslt": "xslt-injection",
    "csv": "csv-formula",
    "expression": "expression-language",
    "parameter-pollution": "parameter-pollution",
    "auth": "authentication",
    "recon": "recon",
    "api": "api-security",
    "hack": "router",
    "injection-checking": "injection",
}


def _extract_tags(name: str) -> list:
    """从技能名称中提取检索标签。"""
    tags = ["skill", name]
    for keyword, tag in _TAG_MAP.items():
        if keyword in name.lower():
            tags.append(tag)
    return tags


def seed_skills(knowledge_base) -> Dict[str, int]:
    """将所有 SKILL.md 技能导入知识库。返回 {'imported': N}。"""
    skills = load_all_skills()
    if not skills:
        logger.warning("未找到任何技能文件")
        return {"imported": 0}

    count = 0
    for skill in skills:
        name = skill["name"]
        content = f"【安全技能】{name}\n{skill['description']}\n\n{skill['body']}"
        tags = _extract_tags(name)

        try:
            knowledge_base.add_general_knowledge(content, tags=tags)
            count += 1
        except Exception as e:
            logger.warning(f"导入技能 {name} 失败: {e}")

    logger.info(f"技能知识库种子导入完成: {count} 条")
    return {"imported": count}

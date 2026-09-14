import logging
import time
import hashlib
from datetime import datetime
from rag.rag_service import BaseVectorStore
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class KnowledgeBase(BaseVectorStore):
    """知识库系统 - 存储通用的、可复用的知识，如工具用法和解题模式"""

    def __init__(self):
        super().__init__(
            collection_name="ctf_knowledge",
            collection_description="存储CTF通用知识、工具用法和最佳实践"
        )

    def add_tool_knowledge(
        self,
        tool_name: str,
        usage_examples: List[str],
        best_practices: List[str] = None,
    ) -> str:
        """添加工具使用知识"""
        content = f"工具: {tool_name}\n使用示例: {'; '.join(usage_examples)}"
        if best_practices:
            content += f"\n最佳实践: {'; '.join(best_practices)}"
        
        metadata = {
            "type": "tool_knowledge",
            "tool_name": tool_name,
            "examples_count": len(usage_examples),
            "timestamp": datetime.now().isoformat(),
        }
        
        doc_id = hashlib.md5((content + str(time.time_ns())).encode()).hexdigest()
        self._add(contents=[content], metadatas=[metadata], ids=[doc_id])
        return doc_id

    def add_general_knowledge(self, content: str, tags: List[str] = None) -> str:
        """添加通用的CTF知识或技巧"""
        # ChromaDB metadata 不支持列表，需要转换为字符串
        tags_str = ",".join(tags) if tags else ""
        metadata = {
            "type": "general_knowledge",
            "tags": tags_str,  # 转换为逗号分隔的字符串
            "timestamp": datetime.now().isoformat(),
        }
        doc_id = hashlib.md5((content + str(time.time_ns())).encode()).hexdigest()
        self._add(contents=[content], metadatas=[metadata], ids=[doc_id])
        return doc_id

    def search_knowledge(self, query: str, n_results: int = 3, filters: Dict[str, Any] = None,
                         hybrid: bool = True, use_reranker: bool = False) -> List[Dict[str, Any]]:
        """从知识库中搜索相关知识。

        Args:
            query: 查询文本
            n_results: 返回结果数
            filters: 元数据过滤条件
            hybrid: 是否使用混合检索（BM25 + 向量），默认开启
            use_reranker: 是否使用 LLM 重排序（默认关闭，速度较慢）
        """
        try:
            if hybrid:
                return self._hybrid_search(query, n_results, filters, use_reranker=use_reranker)
            return self._search(query, n_results, filters)
        except Exception as e:
            logger.warning(f"知识库搜索失败 (不影响核心流程): {e}")
            return []

    def get_relevant_knowledge(self, query: str, n_results: int = 3) -> str:
        """获取格式化的相关知识，用于构建提示"""
        try:
            logger.debug("查询： %s", query)
            results = self.search_knowledge(query, n_results, hybrid=True)
            if not results:
                return "从知识库中未找到相关信息。"

            knowledge_text = "相关知识仅供参考:\n"
            for i, result in enumerate(results, 1):
                knowledge_text += f"{i}. {result['content']}\n"
            return knowledge_text
        except Exception as e:
            logger.warning(f"获取相关知识失败 (不影响核心流程): {e}")
            return "从知识库中未找到相关信息。"
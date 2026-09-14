import hashlib
import time
import logging
from datetime import datetime
from rag.rag_service import BaseVectorStore
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class MemorySystem(BaseVectorStore):
    """记忆系统 - 存储解题过程中的步骤、观察和结论，供长期复用。"""

    def __init__(self, persist_directory: str = "./rag_db"):
        self.persist_directory = persist_directory
        super().__init__(
            collection_name="agent_memory",
            collection_description="存储智能体在任务执行过程中的记忆和经验",
        )
        logger.info(f"记忆系统已就绪，集合 '{self.collection_name}' 存在，"
                     f"当前文档数: {self.collection.count() if self.collection else '?'}")

    def add_problem_solution_memory(
        self,
        problem: str,
        solution: str,
        problem_type: str,
    ) -> str:
        """记录一个已完成问题的完整解决方案作为长期记忆"""
        content = f"问题: {problem}\n解决方案: {solution}"
        metadata = {
            "type": "problem_solution",
            "problem_type": problem_type,
            "timestamp": datetime.now().isoformat(),
        }
        doc_id = hashlib.md5((content + str(time.time_ns())).encode()).hexdigest()
        self._add(contents=[content], metadatas=[metadata], ids=[doc_id])
        return doc_id

    def add_step_memory(
        self, step: int, action: str, observation: str, thought: str
    ) -> str:
        """记录任务执行过程中的单步记忆"""
        content = f"步骤 {step}:\n思考: {thought}\n行动: {action}\n观察: {observation}"
        metadata = {
            "type": "step_memory",
            "step": step,
            "timestamp": datetime.now().isoformat(),
        }
        doc_id = hashlib.md5((content + str(time.time_ns())).encode()).hexdigest()
        self._add(contents=[content], metadatas=[metadata], ids=[doc_id])
        return doc_id

    def search_memories(
        self, query: str, n_results: int = 3, filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """从记忆中搜索相关事件"""
        try:
            return self._search(query, n_results, filters)
        except Exception as e:
            logger.warning(f"记忆搜索失败 (不影响核心流程): {e}")
            return []

    def get_relevant_memories_for_prompt(
        self, current_problem: str, n_results: int = 3
    ) -> str:
        """获取与当前问题相关的过往记忆，用于构建提示"""
        try:
            results = self.search_memories(
                f"与 '{current_problem}' 类似的问题", n_results
            )
            if not results:
                return "从记忆中未找到相关记忆。"

            memory_text = "相关过往记忆:\n"
            for i, result in enumerate(results, 1):
                content = result.get("content", "内容未知")
                memory_text += f"{i}. {content}\n"
            logger.debug(memory_text)
            return memory_text
        except Exception as e:
            logger.warning(f"获取相关记忆失败 (不影响核心流程): {e}")
            return "从记忆中未找到相关记忆。"

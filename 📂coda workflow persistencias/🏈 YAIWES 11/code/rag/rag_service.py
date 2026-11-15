import chromadb
import logging
import math
import re
from collections import Counter
from config import Config
from chromadb.config import Settings
from chromadb import ClientAPI
from typing import List, Dict, Any, Optional, Callable
from utils.llm_request import LLMRequest

logger = logging.getLogger(__name__)


# ── BM25 轻量实现 ────────────────────────────────────────────────

class _BM25Scorer:
    """轻量 BM25 评分器，不需要 rank_bm25 库。"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_freqs: List[Counter] = []
        self.doc_count = 0
        self.avg_doc_len = 0.0
        self.idf: Dict[str, float] = {}

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    def fit(self, documents: List[str]):
        """从文档中学习 IDF 和文档长度统计。"""
        self.doc_count = len(documents)
        total_len = 0
        df: Counter = Counter()  # 文档频率

        for doc in documents:
            tokens = self._tokenize(doc)
            total_len += len(tokens)
            unique_tokens = set(tokens)
            for token in unique_tokens:
                df[token] += 1
            self.doc_freqs.append(Counter(tokens))

        self.avg_doc_len = total_len / self.doc_count if self.doc_count else 1

        # 计算 IDF
        for token, doc_freq in df.items():
            self.idf[token] = math.log(
                (self.doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1
            )

    def score(self, query: str, doc_idx: int) -> float:
        """计算单个文档的 BM25 分数。"""
        query_tokens = self._tokenize(query)
        doc_freqs = self.doc_freqs[doc_idx]
        doc_len = sum(doc_freqs.values())

        score = 0.0
        for token in query_tokens:
            if token not in self.idf:
                continue
            tf = doc_freqs.get(token, 0)
            idf = self.idf[token]
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len)
            score += idf * numerator / denominator

        return score

    def search(self, query: str, documents: List[str]) -> List[float]:
        """返回每个文档的 BM25 分数。"""
        if not self.doc_freqs:
            self.fit(documents)
        scores = []
        for i in range(len(documents)):
            scores.append(self.score(query, i))
        return scores


# ── 主类 ──────────────────────────────────────────────────────────

class BaseVectorStore:
    """向量存储的基类，处理与ChromaDB的通用交互"""

    def __init__(self, collection_name: str, collection_description: str):
        self.config = Config.load_config()
        self.persist_directory = self.config.get("persist_directory", "./rag_db")
        self.embedding_llm = LLMRequest("embedding")
        self.solve_llm = LLMRequest("solve_agent")  # 用于 reranker
        self.client = None
        self.collection: Optional[chromadb.Collection] = None
        self.collection_name = collection_name
        self.collection_description = collection_description
        self._initialize_database()

    def _initialize_database(self):
        """初始化向量数据库并获取指定的集合"""
        try:
            # 抑制 ChromaDB PostHog 遥测兼容性错误（capture() 参数不匹配）
            logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)
            self.client: ClientAPI = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False),
            )
            # 根据子类提供的名称创建或获取集合
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": self.collection_description},
            )
            logger.info(f"向量存储集合 '{self.collection_name}' 初始化完成")
        except Exception as e:
            logger.error(f"向量存储 '{self.collection_name}' 初始化失败: {str(e)}")
            self.collection = None

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """获取文本的嵌入向量"""
        try:
            response = self.embedding_llm.embedding(text=texts)
            return [item["embedding"] for item in response.data]
        except Exception as e:
            logger.error(f"获取嵌入向量失败: {e}")
            return []

    def _add(
        self, contents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]
    ):
        """向集合中添加文档（底层方法）。向量存储不可用或 LLM 失败时静默跳过。"""
        if self.collection is None:
            logger.warning(f"向量存储集合 '{self.collection_name}' 未初始化，跳过添加")
            return
        try:
            embeddings = self.get_embeddings(contents)
            if not embeddings or len(embeddings) != len(contents):
                logger.warning("获取嵌入向量失败，跳过添加")
                return
            self.collection.add(
                documents=contents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )
            logger.info(
                f"成功向集合 '{self.collection_name}' 添加了 {len(contents)} 条目"
            )
        except Exception as e:
            logger.error(f"向集合 '{self.collection_name}' 添加条目失败: {str(e)}")

    def _search(
        self, query: str, n_results: int = 3, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """在集合中搜索相关文档（底层方法，纯向量检索）。"""
        if self.collection is None:
            logger.warning(f"集合 '{self.collection_name}' 未初始化，跳过搜索")
            return []
        try:
            query_embedding = self.get_embeddings([query])[0]
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results * 2,  # 多取一些给 reranker 筛选
                where=filters,
                include=["documents", "metadatas", "distances"],
            )
            # 格式化结果
            formatted_results = []
            if not results or not results.get("documents"):
                return []

            for i in range(len(results["documents"][0])):
                formatted_results.append(
                    {
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i],
                        "relevance_score": 1 - results["distances"][0][i],
                    }
                )
            return formatted_results
        except Exception as e:
            logger.error(f"在集合 '{self.collection_name}' 中搜索失败: {str(e)}")
            return []

    def _hybrid_search(
        self, query: str, n_results: int = 3, filters: Optional[Dict[str, Any]] = None,
        bm25_weight: float = 0.3, use_reranker: bool = False
    ) -> List[Dict[str, Any]]:
        """混合检索：向量检索 + BM25，可选 LLM 重排序。

        Args:
            query: 查询文本
            n_results: 返回结果数
            filters: ChromaDB 元数据过滤
            bm25_weight: BM25 分数权重 (0-1), 向量权重为 1-bm25_weight
            use_reranker: 是否使用 LLM 重排序
        """
        if self.collection is None:
            logger.warning(f"集合 '{self.collection_name}' 未初始化，跳过混合检索")
            return []

        # 1. 向量检索（取更多结果用于融合）
        vector_n = max(n_results * 3, 10)
        vector_results = self._search(query, n_results=vector_n, filters=filters)
        if not vector_results:
            return []

        # 2. BM25 检索
        documents = [r["content"] for r in vector_results]
        try:
            bm25 = _BM25Scorer()
            bm25_scores = bm25.search(query, documents)
        except Exception as e:
            logger.warning(f"BM25 评分失败，回退到纯向量检索: {e}")
            bm25_scores = [0.0] * len(documents)

        # 3. 融合评分
        max_vector = max(r["relevance_score"] for r in vector_results) or 1
        max_bm25 = max(bm25_scores) or 1

        for i, result in enumerate(vector_results):
            vector_score = result["relevance_score"] / max_vector
            bm25_score = bm25_scores[i] / max_bm25 if max_bm25 > 0 else 0
            result["hybrid_score"] = (
                (1 - bm25_weight) * vector_score + bm25_weight * bm25_score
            )
            result["vector_score"] = vector_score
            result["bm25_score"] = bm25_score

        # 4. 按融合分数排序
        vector_results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        top_results = vector_results[:n_results * 2]

        # 5. 可选 LLM 重排序
        if use_reranker:
            top_results = self._rerank(query, top_results)

        return top_results[:n_results]

    def _rerank(self, query: str, results: List[Dict], max_rerank: int = 6) -> List[Dict]:
        """LLM 重排序：用 LLM 评估每个结果与查询的相关性（限制重排序数量以控制成本）。"""
        if not results:
            return results

        # 仅对前 max_rerank 个结果进行 LLM 重排序
        to_rerank = results[:max_rerank]
        rest = results[max_rerank:]

        scored = []
        for result in to_rerank:
            content = result["content"][:500]  # 截断以免超出 LLM 上下文
            prompt = (
                "你是一个检索重排序模型。请评估以下搜索结果与用户查询的相关性。\n"
                f"用户查询: {query}\n\n"
                f"搜索结果: {content}\n\n"
                "请只返回一个 0-10 的整数分数（0=完全不相关, 10=高度相关），不要有其他文字:"
            )
            try:
                response = self.solve_llm.text_completion(
                    prompt=prompt, json_check=False
                )
                score_text = response.choices[0].message.content.strip()
                # 提取数字
                score_match = re.search(r"(\d+)", score_text)
                if score_match:
                    llm_score = int(score_match.group(1)) / 10.0
                else:
                    llm_score = result.get("hybrid_score", result.get("relevance_score", 0.5))
            except Exception:
                llm_score = result.get("hybrid_score", result.get("relevance_score", 0.5))

            result["rerank_score"] = llm_score
            scored.append(result)

        # 未参与重排序的结果直接追加（用 hybrid_score 作为 rerank_score）
        for result in rest:
            result["rerank_score"] = result.get("hybrid_score", result.get("relevance_score", 0.5))
            scored.append(result)

        scored.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored

    def delete_collection(self):
        """删除整个集合"""
        if self.client is None:
            logger.warning("向量存储客户端未初始化，跳过删除")
            return
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info(f"集合 '{self.collection_name}' 已被删除")
        except Exception as e:
            logger.error(f"删除集合 '{self.collection_name}' 失败: {str(e)}")

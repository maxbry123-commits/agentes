"""知识库管理路由 — 增删改查。"""
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/kb", tags=["knowledge_base"])
logger = logging.getLogger(__name__)

_KB = None  # 延迟初始化


def _get_kb():
    global _KB
    if _KB is None:
        from rag.knowledge_base import KnowledgeBase
        _KB = KnowledgeBase()
    return _KB


class AddRequest(BaseModel):
    content: str
    tags: list[str] = []


class SearchRequest(BaseModel):
    query: str
    n_results: int = 10


class DeleteRequest(BaseModel):
    ids: list[str]


# ── 查询 ──────────────────────────────────────────────────────────

class UpdateRequest(BaseModel):
    content: str
    tags: list[str] = []


@router.get("/stats")
async def kb_stats():
    """获取知识库统计信息。"""
    kb = _get_kb()
    try:
        count = kb.collection.count()
        # peek 前 5 条获取样例
        sample = kb.collection.peek(limit=5)
        return {
            "total": count,
            "collection": kb.collection_name,
            "sample_tags": _extract_tags(sample),
        }
    except Exception as e:
        return {"total": 0, "error": str(e)}


@router.get("/{item_id}")
async def kb_get(item_id: str):
    """获取单条知识全文。"""
    kb = _get_kb()
    try:
        result = kb.collection.get(ids=[item_id], include=["documents", "metadatas"])
        if not result["ids"]:
            raise HTTPException(status_code=404, detail="条目不存在")
        return {
            "id": result["ids"][0],
            "content": result["documents"][0] or "",
            "type": (result["metadatas"][0] or {}).get("type", ""),
            "tags": (result["metadatas"][0] or {}).get("tags", ""),
            "timestamp": (result["metadatas"][0] or {}).get("timestamp", ""),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{item_id}")
async def kb_update(item_id: str, req: UpdateRequest):
    """更新知识条目（删除旧记录 + 新增）。"""
    kb = _get_kb()
    try:
        kb.collection.delete(ids=[item_id])
        new_id = kb.add_general_knowledge(req.content, tags=req.tags)
        return {"status": "ok", "id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def kb_list(offset: int = 0, limit: int = 500):
    """分页列出知识库条目。"""
    kb = _get_kb()
    try:
        total = kb.collection.count()
        if total == 0:
            return {"total": 0, "items": []}
        result = kb.collection.get(
            limit=limit,
            offset=offset,
            include=["documents", "metadatas"],
        )
        items = []
        for i, (id_, doc, meta) in enumerate(zip(
            result.get("ids", []),
            result.get("documents", []),
            result.get("metadatas", []),
        )):
            items.append({
                "id": id_,
                "content": (doc or ""),
                "type": (meta or {}).get("type", ""),
                "tags": (meta or {}).get("tags", ""),
                "timestamp": (meta or {}).get("timestamp", ""),
            })
        return {"total": total, "items": items}
    except Exception as e:
        return {"total": 0, "items": [], "error": str(e)}


@router.post("/search")
async def kb_search(req: SearchRequest):
    """搜索知识库。"""
    kb = _get_kb()
    try:
        results = kb.search_knowledge(req.query, n_results=req.n_results)
        return {
            "query": req.query,
            "count": len(results),
            "results": [
                {
                    "id": r.get("id", ""),
                    "content": str(r.get("content", ""))[:500],
                    "score": round(r.get("relevance_score", 0), 4) if "relevance_score" in r else None,
                    "type": (r.get("metadata") or {}).get("type", ""),
                }
                for r in results
            ],
        }
    except Exception as e:
        return {"query": req.query, "count": 0, "error": str(e)}


# ── 增删 ──────────────────────────────────────────────────────────

@router.post("/add")
async def kb_add(req: AddRequest):
    """添加知识条目。"""
    kb = _get_kb()
    try:
        doc_id = kb.add_general_knowledge(req.content, tags=req.tags)
        return {"status": "ok", "id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete")
async def kb_delete(req: DeleteRequest):
    """批量删除知识条目。"""
    kb = _get_kb()
    try:
        kb.collection.delete(ids=req.ids)
        return {"status": "ok", "deleted": len(req.ids)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def kb_reset():
    """清空并重新种子知识库。"""
    from rag.seed_knowledge import seed_knowledge_base
    from utils.skill_seeder import seed_skills
    kb = _get_kb()
    try:
        kb.delete_collection()
        # 重建 collection
        kb._init_collection()
        stats = seed_knowledge_base(kb)
        skill_stats = seed_skills(kb)
        return {
            "status": "ok",
            "seeded": stats.get("total", 0) if stats else 0,
            "skills": skill_stats.get("imported", 0) if skill_stats else 0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _extract_tags(sample: dict) -> list[str]:
    tags = set()
    for meta in (sample.get("metadatas") or []):
        if meta and meta.get("tags"):
            for t in str(meta["tags"]).split(","):
                if t.strip():
                    tags.add(t.strip())
    return sorted(tags)[:20]

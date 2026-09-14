"""
上下文信息 API 端点
提供Token使用统计等信息
"""
from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.database import get_db
from app.models.task import Message

router = APIRouter()


class ContextInfoResponse(BaseModel):
    """上下文信息响应"""
    total_messages: int
    current_messages: int
    compression_events: int
    tokens_saved: int
    current_tokens: int
    max_tokens: int
    memory_type: str
    langchain_active: bool
    attack_stage: str
    found_vectors: List[str]
    successful_attacks: List[str]
    flags_found: List[str]


@router.get("/context/info", response_model=ContextInfoResponse)
async def get_context_info(
    task_id: str = Query(..., description="任务ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定任务的上下文信息
    
    主要用于前端显示Token使用率
    """
    try:
        # 获取该任务的所有消息
        result = await db.execute(
            select(Message)
            .where(Message.task_id == task_id)
            .order_by(Message.created_at.asc())
        )
        messages = result.scalars().all()
        
        # 估算token数量（简化算法）
        total_tokens = 0
        for msg in messages:
            content = msg.content or ''
            # 简化的token计算：中文1字符≈1.5token，英文1字符≈0.25token
            chinese_chars = len([c for c in content if '\u4e00' <= c <= '\u9fff'])
            other_chars = len(content) - chinese_chars
            tokens = int(chinese_chars * 1.5 + other_chars * 0.25)
            total_tokens += tokens
        
        # 返回统计信息
        return ContextInfoResponse(
            total_messages=len(messages),
            current_messages=len(messages),
            compression_events=0,  # 暂不支持
            tokens_saved=0,  # 暂不支持
            current_tokens=total_tokens,
            max_tokens=120000,  # 120K token限制
            memory_type="database",
            langchain_active=True,
            attack_stage="running",
            found_vectors=[],
            successful_attacks=[],
            flags_found=[]
        )
        
    except Exception as e:
        # 出错时返回默认值
        return ContextInfoResponse(
            total_messages=0,
            current_messages=0,
            compression_events=0,
            tokens_saved=0,
            current_tokens=0,
            max_tokens=120000,
            memory_type="none",
            langchain_active=False,
            attack_stage="error",
            found_vectors=[],
            successful_attacks=[],
            flags_found=[]
        )

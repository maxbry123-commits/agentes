"""
Conversations API - 对话历史接口
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db, AsyncSession
from app.models.task import Conversation
from sqlalchemy import select

router = APIRouter()


@router.get("/tasks/{task_id}/conversations")
async def get_task_conversations(
    task_id: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    获取任务的对话历史
    
    Args:
        task_id: 任务ID
        skip: 跳过数量
        limit: 限制数量
    """
    query = select(Conversation).where(Conversation.task_id == task_id)
    query = query.order_by(Conversation.created_at.asc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    conversations = result.scalars().all()
    
    return [
        {
            'id': conv.id,
            'task_id': conv.task_id,
            'role': conv.role,
            'content': conv.content,
            'round': conv.round,
            'created_at': conv.created_at.isoformat()
        }
        for conv in conversations
    ]

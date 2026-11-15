"""
Messages API - 消息查询接口（HTTP轮询备份）
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db, AsyncSession
from app.models.task import Message
from sqlalchemy import select

router = APIRouter()


@router.get("/tasks/{task_id}/messages")
async def get_task_messages(
    task_id: str,
    skip: int = 0,
    limit: int = 100,
    msg_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取任务的消息列表（用于HTTP轮询）
    
    Args:
        task_id: 任务ID
        skip: 跳过数量
        limit: 限制数量
        msg_type: 消息类型过滤
    """
    query = select(Message).where(Message.task_id == task_id)
    
    # 类型过滤
    if msg_type:
        query = query.where(Message.type == msg_type)
    
    # 排序和分页 - 🔥 改为升序，确保Round 1在前，Round 8在后
    query = query.order_by(Message.created_at.asc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    messages = result.scalars().all()
    
    return [
        {
            'id': msg.id,
            'task_id': msg.task_id,
            'type': msg.type,
            'content': msg.content,
            'metadata': msg.msg_metadata,  # 使用msg_metadata
            'round': msg.round,
            'timestamp': msg.created_at.isoformat()  # 🔥 前端期期timestamp字段
        }
        for msg in messages
    ]


@router.get("/tasks/{task_id}/messages/latest")
async def get_latest_messages(
    task_id: str,
    since: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    获取最新消息（增量轮询）
    
    Args:
        task_id: 任务ID
        since: ISO格式时间戳，获取此时间之后的消息
    """
    query = select(Message).where(Message.task_id == task_id)
    
    # 时间过滤
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace('Z', '+00:00'))
            query = query.where(Message.created_at > since_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的时间格式")
    
    # 排序
    query = query.order_by(Message.created_at.asc()).limit(100)
    
    result = await db.execute(query)
    messages = result.scalars().all()
    
    return [
        {
            'id': msg.id,
            'task_id': msg.task_id,
            'type': msg.type,
            'content': msg.content,
            'metadata': msg.msg_metadata,  # 使用msg_metadata
            'round': msg.round,
            'timestamp': msg.created_at.isoformat()  # 🔥 前端期期timestamp字段
        }
        for msg in messages
    ]

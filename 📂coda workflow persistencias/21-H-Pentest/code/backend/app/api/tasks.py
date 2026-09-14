"""
Tasks API - 任务管理接口
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
from datetime import datetime
import asyncio

from app.db.database import get_db, AsyncSession
from app.models.task import Task, TaskStatus
from app.services.process_manager import process_manager
from app.services.message_consumer import message_consumer
from sqlalchemy import select

router = APIRouter()


async def cleanup_task_resources(task_id: str):
    """
    🔥🔥🔥 清理任务资源（Docker容器）
    
    在任务停止/删除/失败时调用
    """
    try:
        import docker
        client = docker.from_env()
        
        # 查找并删除沙箱容器
        container_name = f"pentest-sandbox-{task_id}"
        
        try:
            container = client.containers.get(container_name)
            print(f"🗑️  API: 删除容器 {container_name}")
            container.stop(timeout=3)
            container.remove(force=True)
            print(f"✅ API: 容器已删除")
        except docker.errors.NotFound:
            print(f"ℹ️  API: 容器不存在 {container_name}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ API清理资源失败: {e}")


# Pydantic模型
class CreateTaskRequest(BaseModel):
    target_url: str
    mode: str = "ctf"
    max_rounds: int = 10
    model: Optional[str] = None  # 🔥🔥🔥 不硬编码，从config读取
    
    # 🔥 自定义目标
    custom_objective: Optional[str] = None
    
    # 🔥 CTF配置
    flag_submit_url: Optional[str] = None
    flag_submit_method: str = "POST"
    token: Optional[str] = None
    challenge_code: Optional[str] = None
    
    # RealWorld配置
    scope_file: Optional[str] = None
    compliance: str = "OWASP"
    stealth: bool = False
    stealth_profile: str = "balanced"


class TaskResponse(BaseModel):
    id: str
    target_url: str
    mode: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None  # 别名
    max_rounds: int = 10
    current_round: int = 0
    flags_found: List[str] = []
    flags: List[str] = []  # 别名
    vulnerabilities: List[dict] = []
    report: Optional[dict] = None
    task_plan: Optional[dict] = None


class InterventionRequest(BaseModel):
    """人工干预请求"""
    action: str = Field(..., description="操作类型: pause, resume, inject, force_stop")
    instruction: Optional[str] = Field(None, description="自定义指令（action=inject时必填）")
    priority: Optional[str] = Field('high', description="指令优先级: low, medium, high, critical")


@router.post("/", response_model=TaskResponse)
async def create_task(
    request: CreateTaskRequest,
    db: AsyncSession = Depends(get_db)
):
    """创建新任务"""
    task_id = str(uuid.uuid4())
    
    # 创建任务记录
    task = Task(
        id=task_id,
        target_url=request.target_url,
        mode=request.mode,
        status=TaskStatus.PENDING,
        created_at=datetime.utcnow()
    )
    
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    # 启动任务进程
    # 🔥🔥🔥 从config.json获取模型
    from app.core.config import settings
    model_to_use = request.model or settings.WORKER_MODEL
    
    config = {
        'max_rounds': request.max_rounds,
        'model': model_to_use,  # 🔥 使用config中的模型
        # 🔥 自定义目标
        'custom_objective': request.custom_objective,
        # 🔥 FLAG提交配置
        'flag_submit_url': request.flag_submit_url,
        'flag_submit_method': request.flag_submit_method,
        'token': request.token,
        'challenge_code': request.challenge_code,
        # RealWorld配置
        'scope_file': request.scope_file,
        'compliance': request.compliance,
        'stealth': request.stealth,
        'stealth_profile': request.stealth_profile
    }
    
    success, message_queue = await process_manager.start_task(
        task_id=task_id,
        target_url=request.target_url,
        mode=request.mode,
        config=config
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="启动任务失败")
    
    # 开始消费消息
    await message_consumer.start_consuming(task_id, message_queue)
    
    # 更新状态
    task.status = TaskStatus.RUNNING
    task.started_at = datetime.utcnow()  # 设置开始时间
    await db.commit()
    
    return TaskResponse(
        id=task.id,
        target_url=task.target_url,
        mode=task.mode,
        status=task.status.value,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        finished_at=task.completed_at,
        max_rounds=task.max_rounds,
        current_round=task.current_round,
        flags_found=task.flags_found or [],
        flags=task.flags_found or [],
        vulnerabilities=task.vulnerabilities or [],
        report=task.report,
        task_plan=task.task_plan
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取任务详情"""
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return TaskResponse(
        id=task.id,
        target_url=task.target_url,
        mode=task.mode,
        status=task.status.value,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        finished_at=task.completed_at,
        max_rounds=task.max_rounds,
        current_round=task.current_round,
        flags_found=task.flags_found or [],
        flags=task.flags_found or [],
        vulnerabilities=task.vulnerabilities or [],
        report=task.report,
        task_plan=task.task_plan
    )


@router.get("/")
async def list_tasks(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """获取任务列表"""
    result = await db.execute(
        select(Task)
        .order_by(Task.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    tasks = result.scalars().all()
    
    return [
        TaskResponse(
            id=task.id,
            target_url=task.target_url,
            mode=task.mode,
            status=task.status.value,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            finished_at=task.completed_at,
            max_rounds=task.max_rounds,
            current_round=task.current_round,
            flags_found=task.flags_found or [],
            flags=task.flags_found or [],
            vulnerabilities=task.vulnerabilities or [],
            report=task.report,
            task_plan=task.task_plan
        )
        for task in tasks
    ]


@router.post("/{task_id}/intervention")
async def task_intervention(
    task_id: str,
    request: InterventionRequest,
    db: AsyncSession = Depends(get_db)
):
    """人工干预 - 暂停/恢复/注入指令"""
    # 检查任务是否存在
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if request.action == 'pause':
        # 暂停任务
        if task.status != TaskStatus.RUNNING:
            raise HTTPException(status_code=400, detail="只有运行中的任务可以暂停")
        
        # 🔥 更新数据库状态（Agent会轮询检查）
        task.status = TaskStatus.PAUSED
        await db.commit()
        
        return {"message": "任务已暂停", "task_id": task_id, "status": "PAUSED"}
    
    elif request.action == 'resume':
        # 🔥🔥🔥 恢复任务（只更新数据库状态，让原进程恢复）
        if task.status != TaskStatus.PAUSED:
            raise HTTPException(status_code=400, detail="只有暂停的任务可以恢复")
        
        # 🔥 只需更新数据库状态，Agent会自动从_check_pause_state中恢复
        task.status = TaskStatus.RUNNING
        await db.commit()
        
        return {
            "message": f"任务已恢复，从第{task.current_round}轮继续",
            "task_id": task_id,
            "status": "RUNNING",
            "current_round": task.current_round
        }
    
    elif request.action == 'inject':
        # 注入自定义指令
        if not request.instruction:
            raise HTTPException(status_code=400, detail="指令不能为空")
        
        if task.status != TaskStatus.RUNNING:
            raise HTTPException(status_code=400, detail="只有运行中的任务可以注入指令")
        
        # 🔥 写入messages表，Agent会读取并注入
        from app.models.task import Message
        
        intervention_msg = Message(
            id=str(uuid.uuid4()),
            task_id=task_id,
            type='intervention',
            content=request.instruction,
            msg_metadata={
                'priority': request.priority,
                'action': 'inject',
                'timestamp': datetime.utcnow().isoformat(),
                'processed': False  # 🔥 标记未处理
            },
            created_at=datetime.utcnow()
        )
        db.add(intervention_msg)
        await db.commit()
        
        return {
            "message": "指令已注入，Agent将在下一轮读取",
            "task_id": task_id,
            "instruction": request.instruction,
            "priority": request.priority
        }
    
    elif request.action == 'force_stop':
        # 强制停止（与force stop接口一致）
        success = await process_manager.stop_task(task_id, timeout=0.5)
        if success:
            await message_consumer.stop_consuming(task_id)
            task.status = TaskStatus.STOPPED
            await db.commit()
            return {"message": "任务已强制停止", "task_id": task_id}
        else:
            raise HTTPException(status_code=404, detail="任务不存在或已停止")
    
    else:
        raise HTTPException(status_code=400, detail=f"不支持的操作: {request.action}")


@router.post("/{task_id}/stop")
async def stop_task(
    task_id: str,
    force: bool = False,  # 强制停止
    db: AsyncSession = Depends(get_db)
):
    """停止任务（支持强制停止）"""
    # 停止进程
    if force:
        # 强制停止（kill）
        success = await process_manager.stop_task(task_id, timeout=0.5)
    else:
        # 优雅停止
        success = await process_manager.stop_task(task_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="任务不存在或已停止")
    
    # 🔥🔥🔥 CRITICAL: 清理Docker资源
    try:
        await cleanup_task_resources(task_id)
    except Exception as e:
        print(f"⚠️  清理资源失败: {e}")
    
    # 停止消息消费
    await message_consumer.stop_consuming(task_id)
    
    # 更新数据库
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if task:
        task.status = TaskStatus.STOPPED
        await db.commit()
    
    return {"message": "任务已停止", "task_id": task_id}


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """删除任务"""
    # 先停止任务
    await process_manager.stop_task(task_id)
    await message_consumer.stop_consuming(task_id)
    
    # 🔥🔥🔥 CRITICAL: 清理Docker资源
    try:
        await cleanup_task_resources(task_id)
    except Exception as e:
        print(f"⚠️  清理资源失败: {e}")
    
    # 删除数据库记录
    result = await db.execute(
        select(Task).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    await db.delete(task)
    await db.commit()
    
    return {"message": "任务已删除", "task_id": task_id}

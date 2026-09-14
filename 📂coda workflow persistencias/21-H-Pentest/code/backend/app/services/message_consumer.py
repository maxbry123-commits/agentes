"""
Message Consumer - 从Queue消费消息并转发到WebSocket和数据库
"""
import asyncio
from multiprocessing import Queue
from typing import Optional
import uuid
from datetime import datetime, timezone

from app.db.database import AsyncSessionLocal
from app.models.task import Message, Task, TaskStatus
from sqlalchemy import select


class MessageConsumer:
    """消息消费者 - 消费子进程的消息队列"""
    
    def __init__(self):
        self.active_consumers = {}  # task_id -> asyncio.Task
    
    async def start_consuming(self, task_id: str, message_queue: Queue):
        """
        开始消费指定任务的消息队列
        
        Args:
            task_id: 任务ID
            message_queue: 消息队列
        """
        # 创建消费任务
        consumer_task = asyncio.create_task(
            self._consume_loop(task_id, message_queue)
        )
        self.active_consumers[task_id] = consumer_task
        print(f"✅ 开始消费消息: task_id={task_id}")
    
    async def stop_consuming(self, task_id: str):
        """停止消费"""
        if task_id in self.active_consumers:
            self.active_consumers[task_id].cancel()
            del self.active_consumers[task_id]
            print(f"⏹️  停止消费: task_id={task_id}")
    
    async def _consume_loop(self, task_id: str, message_queue: Queue):
        """
        消费循环 - 持续从队列读取消息
        """
        empty_count = 0  # 🔥 记录连续空队列次数
        
        try:
            while True:
                try:
                    # 非阻塞读取队列
                    message = await asyncio.to_thread(
                        message_queue.get,
                        timeout=0.5
                    )
                    
                    if message:
                        # 处理消息
                        await self._process_message(task_id, message)
                        empty_count = 0  # 🔥 重置空计数
                    else:
                        empty_count += 1
                
                except Exception as e:
                    # 队列为空或超时
                    if "Empty" in str(type(e).__name__):
                        empty_count += 1
                        
                        # 🔥 如果连续60秒没有消息，检查任务状态
                        if empty_count > 120:  # 60秒 (0.5s * 120)
                            await self._check_task_status(task_id)
                            empty_count = 0
                    else:
                        raise
                
        except asyncio.CancelledError:
            print(f"✅ 消费循环被取消: {task_id}")
        except Exception as e:
            print(f"❌ 消费循环异常: {task_id} - {e}")
    
    async def _process_message(self, task_id: str, message: dict):
        """
        处理单条消息：广播到WebSocket + 保存到数据库
        
        Args:
            task_id: 任务ID
            message: 消息字典
        """
        try:
            msg_type = message.get('type', 'unknown')
            
            # 1. 广播到WebSocket
            await self._broadcast_to_websocket(task_id, message)
            
            # 2. 保存到数据库
            await self._save_to_database(task_id, message)
            
            # 3. 处理特殊消息类型（更新Task表）
            await self._update_task_on_message(task_id, message)
            
        except Exception as e:
            print(f"⚠️  处理消息失败: {e}")
    
    async def _broadcast_to_websocket(self, task_id: str, message: dict):
        """广播消息到WebSocket（简化版 - 仅打印日志）"""
        msg_type = message.get('type')
        data = message.get('data', {})
        
        # 简化版：只打印重要消息
        if msg_type in ['flag', 'vulnerability', 'error', 'report']:
            print(f"📢 [{msg_type}] {data}")
    
    async def _save_to_database(self, task_id: str, message: dict):
        """保存消息到数据库"""
        try:
            msg_type = message.get('type', 'unknown')
            data = message.get('data', {})
            
            # 🔥🔥🔥 根据消息类型正确提取content
            if msg_type == 'llm_thinking':
                content = data.get('content', '')
            elif msg_type == 'conversation_message':
                # 🔥🔥🔥 新增：对话消息（user/assistant/tool）
                role = data.get('role', 'unknown')
                content = data.get('content', '')
                # 保持conversation_message类型，但在metadata中保存role
                msg_type = 'conversation_message'
            elif msg_type == 'tool_execution':
                # 工具执行：显示工具名 + 参数 + 结果
                tool_name = data.get('tool_name', '')
                args = data.get('args', {})
                result = data.get('result', '')
                content = f"🔧 {tool_name}\n参数: {args}\n结果: {result}"
            elif msg_type == 'log':
                content = data.get('content', '')
            elif msg_type == 'plan':
                # 🔥🔥🔥 计划：前端期望task_plan类型
                msg_type = 'task_plan'
                import json
                content = json.dumps(data, ensure_ascii=False, indent=2)
            elif msg_type == 'meta_supervision':
                # 🔥🔥🔥 Meta洞察：前端期望meta_supervision类型
                # content保存insights文本，metadata保存完整data
                insights = data.get('insights', [])
                content = "\n".join(insights)
                # 🔥 保持msg_type不变，完整data已在msg_metadata中
            elif msg_type == 'strategic':
                # 🔥🔥🔥 战略分析：前端期望strategic_analysis类型
                msg_type = 'strategic_analysis'
                import json
                content = json.dumps(data, ensure_ascii=False, indent=2)
            elif msg_type == 'payload_guidance':
                # 🔥🔥🔥 Payload大师：前端期望payload_guidance类型
                # content保存evolution_note，metadata保存完整data
                content = data.get('evolution_note', '')
                # 🔥 保持msg_type不变，完整data已在msg_metadata中
            elif msg_type == 'llm_stream':
                # 流式输出：只是chunk，不保存到数据库
                return
            elif msg_type == 'vulnerability':
                # 🔥🔥🔥 漏洞发现：保存为vulnerability_found类型
                msg_type = 'vulnerability_found'
                vuln = data.get('vulnerability', {})
                content = vuln.get('description', '')
                # 完整漏洞数据在metadata中
            else:
                content = str(data.get('content', str(data)))
            
            async with AsyncSessionLocal() as session:
                msg = Message(
                    id=str(uuid.uuid4()),
                    task_id=task_id,
                    type=msg_type,  # 🔥 使用转换后的msg_type
                    content=content,  # 🔥 使用正确提取的content
                    msg_metadata=data,  # 保存完整的data
                    round=data.get('round'),
                    created_at=datetime.now(timezone.utc)  # 🔥 使用timezone-aware
                )
                
                session.add(msg)
                await session.commit()
                
                # 🔥 移除打印，避免与流式输出重复
        
        except Exception as e:
            print(f"⚠️  保存消息失败: {e}")
    
    async def _update_task_on_message(self, task_id: str, message: dict):
        """根据消息类型更新Task表"""
        try:
            msg_type = message.get('type')
            data = message.get('data', {})
            
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Task).where(Task.id == task_id)
                )
                task = result.scalar_one_or_none()
                
                if not task:
                    return
                
                # 处理FLAG
                if msg_type == 'flag':
                    flag_value = data.get('flag', '')
                    if flag_value and flag_value not in (task.flags_found or []):
                        flags = task.flags_found or []
                        flags.append(flag_value)
                        task.flags_found = flags
                        print(f"🚩 发现FLAG: {flag_value}")
                
                # 处理漏洞
                elif msg_type == 'vulnerability':
                    vuln_data = {
                        'type': data.get('type', 'unknown'),
                        'severity': data.get('severity', 'MEDIUM'),
                        'description': data.get('description', ''),
                        'found_at': datetime.now(timezone.utc).isoformat()  # 🔥 使用timezone-aware
                    }
                    vulns = task.vulnerabilities or []
                    vulns.append(vuln_data)
                    task.vulnerabilities = vulns
                    print(f"🔓 发现漏洞: {vuln_data['type']}")
                
                # 处理进度
                elif msg_type == 'progress':
                    current = data.get('current', 0)
                    task.current_round = current
                
                # 处理报告（任务完成）
                elif msg_type == 'report':
                    task.report = data
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.now(timezone.utc)  # 🔥 使用timezone-aware
                    print(f"✅ 任务完成: {task_id}")
                
                # 处理错误（🔥 立即更新为FAILED）
                elif msg_type == 'error':
                    task.status = TaskStatus.FAILED
                    task.completed_at = datetime.now(timezone.utc)  # 🔥
                    # 保存错误信息到report
                    task.report = task.report or {}
                    task.report['error'] = {
                        'message': data.get('content', '未知错误'),
                        'type': data.get('error_type', 'Unknown'),
                        'timestamp': datetime.now(timezone.utc).isoformat()  # 🔥
                    }
                    print(f"❌ 任务失败: {task_id} - {data.get('content', '')}")
                
                await session.commit()
        
        except Exception as e:
            print(f"⚠️  更新Task失败: {e}")
    
    async def _check_task_status(self, task_id: str):
        """🔥 检查任务状态，如果进程已退出但没有发送完成消息，则标记为FAILED"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(Task).where(Task.id == task_id)
                )
                task = result.scalar_one_or_none()
                
                if task and task.status == TaskStatus.RUNNING:
                    # 如果还是RUNNING但长时间没消息，可能进程崩溃
                    from app.services.process_manager import process_manager
                    if not process_manager.is_running(task_id):
                        task.status = TaskStatus.FAILED
                        task.completed_at = datetime.now(timezone.utc)  # 🔥
                        task.report = task.report or {}
                        task.report['error'] = {
                            'message': '进程异常退出，未发送完成消息',
                            'type': 'ProcessExited',
                            'timestamp': datetime.now(timezone.utc).isoformat()  # 🔥
                        }
                        await session.commit()
                        print(f"❌ 检测到进程已退出，标记任务为FAILED: {task_id}")
        except Exception as e:
            print(f"⚠️  检查任务状态失败: {e}")


# 全局实例
message_consumer = MessageConsumer()

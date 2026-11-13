"""
进程管理器 - 管理Agent子进程
"""
import asyncio
from multiprocessing import Process, Queue, Event
from typing import Dict, Optional, Tuple
from datetime import datetime


class ProcessManager:
    """进程管理器 - 简化版"""
    
    def __init__(self):
        self.processes: Dict[str, Process] = {}
        self.queues: Dict[str, Queue] = {}
        self.events: Dict[str, Event] = {}
    
    async def start_task(
        self,
        task_id: str,
        target_url: str,
        mode: str,
        config: dict
    ) -> Tuple[bool, Optional[Queue]]:
        """
        启动任务进程
        
        Args:
            task_id: 任务ID
            target_url: 目标URL
            mode: 模式
            config: 配置
        
        Returns:
            (是否成功, 消息队列)
        """
        if task_id in self.processes:
            print(f"⚠️  任务 {task_id} 已存在")
            return False, None
        
        try:
            # 创建进程间通信组件
            message_queue = Queue()
            stop_event = Event()
            
            # 导入runner
            from agent.runner import run_agent
            
            # 创建进程
            process = Process(
                target=run_agent,
                args=(task_id, target_url, mode, config, message_queue, stop_event),
                name=f"Task-{task_id[:8]}"
            )
            
            # 启动进程
            process.start()
            
            # 保存
            self.processes[task_id] = process
            self.queues[task_id] = message_queue
            self.events[task_id] = stop_event
            
            print(f"✅ 任务 {task_id} 已启动在进程 PID={process.pid}")
            return True, message_queue
            
        except Exception as e:
            print(f"❌ 启动任务进程失败: {e}")
            import traceback
            traceback.print_exc()
            return False, None
    
    async def stop_task(self, task_id: str, timeout: float = 5.0) -> bool:
        """
        停止任务
        
        Args:
            task_id: 任务ID
            timeout: 超时时间
        
        Returns:
            是否成功停止
        """
        if task_id not in self.processes:
            return False
        
        try:
            # 设置停止事件
            if task_id in self.events:
                self.events[task_id].set()
            
            # 等待进程结束
            process = self.processes[task_id]
            process.join(timeout=timeout)
            
            # 如果还在运行，强制终止
            if process.is_alive():
                print(f"⚠️  进程未响应，强制终止...")
                process.terminate()
                process.join(timeout=2.0)
            
            # 清理
            del self.processes[task_id]
            if task_id in self.queues:
                del self.queues[task_id]
            if task_id in self.events:
                del self.events[task_id]
            
            print(f"✅ 任务 {task_id} 已停止")
            return True
            
        except Exception as e:
            print(f"❌ 停止任务失败: {e}")
            return False
    
    def is_running(self, task_id: str) -> bool:
        """检查任务是否在运行"""
        if task_id not in self.processes:
            return False
        return self.processes[task_id].is_alive()
    
    def get_queue(self, task_id: str) -> Optional[Queue]:
        """获取消息队列"""
        return self.queues.get(task_id)


# 全局实例
process_manager = ProcessManager()

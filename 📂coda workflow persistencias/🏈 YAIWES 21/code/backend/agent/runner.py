"""
Agent Runner - 子进程入口点（完全异步）
"""
import asyncio
import sys
from pathlib import Path
from multiprocessing import Queue, Event
from typing import Dict, Any

# 添加当前目录到路径
backend_dir = Path(__file__).parent.parent  # /app/backend
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from agent.core.agent import PentestAgent
from agent.core.output import OutputManager


async def cleanup_docker_resources(task_id: str):
    """
    🔥🔥🔥 清理Docker资源（沙箱容器）
    
    在任务失败/暂停/完成时都必须调用！
    """
    try:
        import docker
        client = docker.from_env()
        
        # 查找并删除与该任务相关的所有容器
        container_name = f"pentest-sandbox-{task_id}"
        
        try:
            container = client.containers.get(container_name)
            print(f"🗑️  删除容器: {container_name}")
            container.stop(timeout=3)
            container.remove(force=True)
            print(f"✅ 容器已删除: {container_name}")
        except docker.errors.NotFound:
            print(f"ℹ️  容器不存在: {container_name}")
        except Exception as e:
            print(f"⚠️  删除容器失败: {e}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ 清理Docker资源失败: {e}")
        import traceback
        traceback.print_exc()


def run_agent(
    task_id: str,
    target_url: str,
    mode: str,
    config: Dict[str, Any],
    message_queue: Queue,
    stop_event: Event
):
    """
    子进程入口 - 运行Agent
    
    Args:
        task_id: 任务ID
        target_url: 目标URL
        mode: 模式（ctf/realworld）
        config: 配置字典
        message_queue: 消息队列（发送到主进程）
        stop_event: 停止事件
    """
    print(f"\n{'='*80}")
    print(f"🚀 Agent进程启动")
    print(f"{'='*80}")
    print(f"PID: {__import__('os').getpid()}")
    print(f"Task ID: {task_id}")
    print(f"Target: {target_url}")
    print(f"Mode: {mode}")
    print(f"{'='*80}\n")
    
    # 运行异步主函数
    try:
        asyncio.run(
            async_main(task_id, target_url, mode, config, message_queue, stop_event)
        )
    except KeyboardInterrupt:
        print("\n⚠️  Agent被中断")
        # 发送中断消息
        message_queue.put({
            'type': 'error',
            'data': {
                'content': "任务被用户中断"
            }
        })
    except Exception as e:
        print(f"\n❌ Agent执行失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 🔥 发送错误消息（会触发FAILED状态）
        message_queue.put({
            'type': 'error',
            'data': {
                'content': f"Agent执行失败: {str(e)}",
                'traceback': traceback.format_exc(),
                'error_type': type(e).__name__
            }
        })
        
        # 🔥 确保消息被消费
        import time
        time.sleep(0.5)
    
    finally:
        # 🔥🔥🔥 CRITICAL: 无论成功失败，都必须清理资源！
        print("\n🧹 开始清理资源...")
        try:
            # 🔥 同步调用清理函数
            asyncio.run(cleanup_docker_resources(task_id))
            print("✅ Docker资源已清理")
        except Exception as cleanup_error:
            print(f"⚠️  清理资源失败: {cleanup_error}")


async def async_main(
    task_id: str,
    target_url: str,
    mode: str,
    config: Dict[str, Any],
    message_queue: Queue,
    stop_event: Event
):
    """
    异步主函数
    """
    # 创建输出管理器
    output_mgr = OutputManager(task_id, message_queue)
    
    # 发送启动消息
    output_mgr.log("info", f"🚀 Agent启动: {target_url}")
    
    try:
        # 创建Agent
        agent = PentestAgent(
            task_id=task_id,
            target_url=target_url,
            mode=mode,
            config=config,
            output_manager=output_mgr,
            stop_event=stop_event
        )
        
        # 运行Agent
        output_mgr.log("info", "▶️  开始渗透测试")
        report = await agent.run()
        
        # 发送完成消息
        output_mgr.log("success", "✅ 渗透测试完成")
        
        # 发送报告
        message_queue.put({
            'type': 'report',
            'data': report
        })
        
        print("\n✅ Agent执行成功")
        
    except Exception as e:
        output_mgr.log("error", f"❌ Agent执行异常: {str(e)}")
        
        # 🔥 发送错误消息到队列（确保状态更新）
        message_queue.put({
            'type': 'error',
            'data': {
                'content': f"Agent执行失败: {str(e)}",
                'error_type': type(e).__name__
            }
        })
        
        raise
    
    finally:
        # 🔥🔥🔥 CRITICAL: 无论成功失败，都清理资源
        print("\n🧹 async_main: 清理资源...")
        try:
            await cleanup_docker_resources(task_id)
        except Exception as cleanup_error:
            print(f"⚠️  async_main清理失败: {cleanup_error}")


if __name__ == "__main__":
    # 用于测试
    import multiprocessing as mp
    
    queue = mp.Queue()
    event = mp.Event()
    
    run_agent(
        task_id="test-001",
        target_url="http://example.com",
        mode="ctf",
        config={"max_rounds": 5},
        message_queue=queue,
        stop_event=event
    )

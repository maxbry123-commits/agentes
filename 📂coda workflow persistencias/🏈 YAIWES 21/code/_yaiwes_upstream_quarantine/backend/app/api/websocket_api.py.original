"""
FastAPI WebSocket端点 - 实时通信
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

router = APIRouter()


@router.websocket("/ws/{task_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    task_id: str,
    token: str = Query(None)
):
    """
    WebSocket端点 - 实时推送任务进度和日志
    
    服务端推送的消息类型:
    - log: 日志消息
    - progress: 进度更新
    - tool_execution: 工具执行
    - llm_thinking: LLM思考内容
    - vulnerability_found: 发现漏洞
    - flag_found: 发现FLAG
    - task_status: 任务状态变更
    """
    try:
        # 建立连接
        await websocket.accept()
        print(f"✅ WebSocket连接成功: task_id={task_id}")
    
        # 发送连接成功消息
        await websocket.send_json({
            "type": "log",
            "log_type": "info",
            "content": f"WebSocket连接已建立,开始接收任务 {task_id} 的实时数据",
            "timestamp": __import__('datetime').datetime.now().isoformat()
        })
    except Exception as e:
        print(f"❌ WebSocket连接失败: {e}")
        import traceback
        traceback.print_exc()
        await websocket.close(code=1008, reason=str(e))
        return
    
    try:
        while True:
            # 接收客户端消息（心跳等）
            data = await websocket.receive_text()
            # 简单的心跳响应
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        print(f"WebSocket断开: task_id={task_id}")
    except Exception as e:
        print(f"WebSocket错误: {e}")

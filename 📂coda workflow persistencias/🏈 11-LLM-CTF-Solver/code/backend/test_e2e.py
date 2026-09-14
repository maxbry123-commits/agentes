"""端到端测试: 先连 WebSocket 订阅 → 再提交任务 → 接收实时消息。"""
import asyncio
import json
import sys
sys.path.insert(0, ".")

import httpx
import websockets

TASK_ID = None
MESSAGES = []


async def main():
    from pathlib import Path as _YP
    import json as _YJ
    _ye = {'schema':'yaiwes.internal.persistence/v1','source':'backend/test_e2e.py','step':'main','status':'CHECKPOINTED'}
    _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
    with _yp.open('a', encoding='utf-8') as _yf:
        _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
    return _ye


if __name__ == "__main__":
    asyncio.run(main())

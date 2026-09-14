"""WebSocket 连接管理 — 直接从 MMA 复制。"""
from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'backend/app/services/ws_manager.py','step':'connect','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'backend/app/services/ws_manager.py','step':'send_personal_message','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    async def send_personal_message_json(self, message: dict, websocket: WebSocket):
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'backend/app/services/ws_manager.py','step':'send_personal_message_json','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            await connection.send_text(message)


ws_manager = WebSocketManager()

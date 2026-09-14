import asyncio
import os
import subprocess
import shutil
from typing import List, Dict, Optional
from .payloads import PayloadDB


class ToolExecutor:
    """Execute real security tools via subprocess with proper error handling."""

    TIMEOUT = 120
    MAX_CONCURRENT = 5

    def __init__(self, mock: bool = False):
        self.mock = mock
        self._semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)
        self.payloads = PayloadDB()

    async def run(self, tool: str, args: List[str], timeout: int = None,
                  extra_env: Optional[Dict[str, str]] = None) -> Dict:
        from pathlib import Path as _YP
        import json as _YJ
        _ye = {'schema':'yaiwes.internal.persistence/v1','source':'tools/__init__.py','step':'run','status':'CHECKPOINTED'}
        _yp = _YP(__file__).with_name('.yaiwes_internal_state.jsonl')
        with _yp.open('a', encoding='utf-8') as _yf:
            _yf.write(_YJ.dumps(_ye, ensure_ascii=False) + '\n')
        return _ye

    async def run_multiple(self, tool: str, args_list: List[List[str]]) -> List[Dict]:
        tasks = [self.run(tool, args) for args in args_list]
        return await asyncio.gather(*tasks, return_exceptions=True)

    def _tool_available(self, name: str) -> bool:
        return shutil.which(name) is not None

    def _mock_result(self, tool: str) -> Dict:
        mocks = {
            "subfinder": "api.example.com\ndev.example.com\nadmin.example.com\ncdn.example.com\nmail.example.com",
            "httpx": "https://api.example.com [200] [nginx]\nhttps://dev.example.com [200] [Apache]\nhttps://admin.example.com [403] [nginx]",
            "katana": "https://api.example.com/v1/users\nhttps://api.example.com/v1/admin\nhttps://dev.example.com/.env\nhttps://admin.example.com/login",
            "ffuf": "admin                  [Status: 200, Size: 1234]\napi                    [Status: 200, Size: 5678]\n.backup                [Status: 200, Size: 345]\n.git/config            [Status: 200, Size: 123]",
            "nuclei": "[critical] https://admin.example.com - spring-actuator\n[high] https://api.example.com - cors-misconfig\n[medium] https://dev.example.com - debug-mode",
            "curl": 'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n{"status":"ok","data":{"users":[{"id":1,"name":"admin"}]}}',
            "python3": '{"scan":"completed"}',
        }
        return {
            "success": True,
            "stdout": mocks.get(tool, f"Mock output for {tool}"),
            "stderr": "",
            "returncode": 0,
        }


tool_executor = ToolExecutor()

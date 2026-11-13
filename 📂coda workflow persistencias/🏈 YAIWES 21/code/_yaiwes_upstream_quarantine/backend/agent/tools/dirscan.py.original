"""
Directory Scanner - 目录扫描工具（Dirsearch）
"""
import asyncio
import subprocess
import json
import os
from typing import Dict, Any
from agent.tools.base import BaseTool


class DirectoryScanner(BaseTool):
    """目录扫描工具"""
    
    name = "directory_scan"
    description = "扫描Web目录和文件，发现隐藏路径、备份文件、敏感信息"
    
    def __init__(self):
        self.dirsearch_path = "/app/tools/dirsearch/dirsearch.py"
        self.wordlist = "/app/tools/dirsearch/db/dicc.txt"  # 默认字典
    
    def get_parameters(self) -> Dict[str, Any]:
        """返回工具参数定义"""
        return {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "目标URL"
                },
                "extensions": {
                    "type": "string",
                    "description": "文件扩展名，逗号分隔，例如: php,html,js",
                    "default": "php,html,js,txt,zip,bak"
                },
                "threads": {
                    "type": "integer",
                    "description": "线程数",
                    "default": 30
                },
                "timeout": {
                    "type": "integer",
                    "description": "超时时间（秒）",
                    "default": 300
                }
            },
            "required": ["target"]
        }
    
    async def initialize(self):
        """初始化检查"""
        if not os.path.exists(self.dirsearch_path):
            raise FileNotFoundError(f"Dirsearch未找到: {self.dirsearch_path}")
    
    async def execute(
        self, 
        target: str,
        extensions: str = "php,asp,aspx,jsp,html,js",
        threads: int = 30,
        timeout: int = 300
    ) -> str:
        """
        执行目录扫描
        
        Args:
            target: 目标URL
            extensions: 文件扩展名，逗号分隔
            threads: 线程数
            timeout: 超时时间（秒）
        
        Returns:
            扫描结果JSON字符串
        """
        cmd = [
            "python3",
            self.dirsearch_path,
            "-u", target,
            "-e", extensions,
            "-t", str(threads),
            "--format=json",
            "--quiet",
            "--random-agent"
        ]
        
        # 如果字典文件存在
        if os.path.exists(self.wordlist):
            cmd.extend(["-w", self.wordlist])
        
        try:
            print(f"📁 目录扫描: {target}")
            print(f"   扩展名: {extensions}")
            print(f"   线程: {threads}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return json.dumps({
                    "status": "timeout",
                    "message": f"扫描超时（{timeout}秒）",
                    "results": []
                })
            
            # 解析结果
            output = stdout.decode('utf-8', errors='ignore')
            
            # Dirsearch输出是每行一个JSON
            results = []
            for line in output.strip().split('\n'):
                if line.strip():
                    try:
                        item = json.loads(line)
                        results.append({
                            "url": item.get("url", ""),
                            "status": item.get("status", 0),
                            "content_length": item.get("content-length", 0),
                            "content_type": item.get("content-type", ""),
                            "redirect": item.get("redirect", "")
                        })
                    except json.JSONDecodeError:
                        continue
            
            # 过滤有效结果（2xx, 3xx状态码）
            valid_results = [
                r for r in results 
                if 200 <= r.get("status", 0) < 400
            ]
            
            result = {
                "status": "success",
                "target": target,
                "total_found": len(valid_results),
                "results": valid_results[:100]  # 限制返回数量
            }
            
            if stderr:
                result["stderr"] = stderr.decode('utf-8', errors='ignore')
            
            print(f"✅ 目录扫描完成: 发现 {len(valid_results)} 个路径")
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e),
                "results": []
            })
    
    async def cleanup(self):
        """清理资源"""
        pass
    
    def to_openai_tool(self) -> Dict[str, Any]:
        """转换为OpenAI工具格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target": {
                            "type": "string",
                            "description": "目标URL，如 http://example.com"
                        },
                        "extensions": {
                            "type": "string",
                            "description": "文件扩展名（逗号分隔），默认: php,asp,aspx,jsp,html,js"
                        },
                        "threads": {
                            "type": "integer",
                            "description": "线程数，默认30"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "超时时间（秒），默认300"
                        }
                    },
                    "required": ["target"]
                }
            }
        }

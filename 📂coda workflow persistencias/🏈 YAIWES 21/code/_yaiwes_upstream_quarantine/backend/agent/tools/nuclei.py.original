"""
Nuclei Tool - Nuclei漏洞扫描器集成
"""
import asyncio
import subprocess
import json
import os
from typing import Dict, Any
from agent.tools.base import BaseTool


class NucleiScanner(BaseTool):
    """Nuclei漏洞扫描器"""
    
    name = "nuclei_scan"
    description = "使用Nuclei进行自动化漏洞扫描，支持11000+模板"
    
    def __init__(self):
        self.nuclei_bin = "nuclei"
        self.templates_path = os.getenv("NUCLEI_TEMPLATES_PATH", "/app/tools/nuclei-templates")
    
    def get_parameters(self) -> Dict[str, Any]:
        """返回工具参数定义"""
        return {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "目标URL"
                },
                "severity": {
                    "type": "string",
                    "description": "严重级别过滤: critical,high,medium,low",
                    "default": "critical,high,medium"
                },
                "tags": {
                    "type": "string",
                    "description": "模板标签过滤（可选），例如: sqli,xss,rce"
                },
                "timeout": {
                    "type": "integer",
                    "description": "扫描超时时间（秒）",
                    "default": 300
                }
            },
            "required": ["target"]
        }
    
    async def initialize(self):
        """初始化检查"""
        # 检查nuclei是否可用
        try:
            result = subprocess.run(
                [self.nuclei_bin, "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✅ Nuclei可用: {result.stdout.strip()}")
            else:
                print(f"⚠️  Nuclei检查异常: {result.stderr}")
        except Exception as e:
            print(f"⚠️  Nuclei初始化失败: {e}")
    
    async def execute(
        self, 
        target: str,
        severity: str = "critical,high,medium",
        tags: str = None,
        timeout: int = 300
    ) -> str:
        """
        执行Nuclei扫描
        
        Args:
            target: 目标URL
            severity: 漏洞严重程度 (critical,high,medium,low,info)
            tags: 标签过滤 (如: cve,sqli,xss)
            timeout: 超时时间（秒）
        
        Returns:
            扫描结果JSON字符串
        """
        cmd = [
            self.nuclei_bin,
            "-u", target,
            "-severity", severity,
            "-json",  # JSON输出
            "-no-color",
            "-timeout", "10",  # 单个请求超时
            "-rate-limit", "150",  # 限速避免封禁
        ]
        
        # 如果指定了标签
        if tags:
            cmd.extend(["-tags", tags])
        
        # 如果模板路径存在
        if os.path.exists(self.templates_path):
            cmd.extend(["-t", self.templates_path])
        
        try:
            print(f"🔍 Nuclei扫描: {target}")
            print(f"   严重程度: {severity}")
            if tags:
                print(f"   标签: {tags}")
            
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
                    "vulnerabilities": []
                })
            
            # 解析结果
            vulnerabilities = []
            for line in stdout.decode('utf-8').strip().split('\n'):
                if line.strip():
                    try:
                        vuln = json.loads(line)
                        vulnerabilities.append({
                            "template_id": vuln.get("template-id", ""),
                            "name": vuln.get("info", {}).get("name", ""),
                            "severity": vuln.get("info", {}).get("severity", ""),
                            "tags": vuln.get("info", {}).get("tags", []),
                            "matched_at": vuln.get("matched-at", ""),
                            "type": vuln.get("type", ""),
                            "curl_command": vuln.get("curl-command", "")
                        })
                    except json.JSONDecodeError:
                        continue
            
            result = {
                "status": "success",
                "target": target,
                "vulnerabilities_found": len(vulnerabilities),
                "vulnerabilities": vulnerabilities
            }
            
            if stderr:
                result["stderr"] = stderr.decode('utf-8')
            
            print(f"✅ Nuclei扫描完成: 发现 {len(vulnerabilities)} 个漏洞")
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e),
                "vulnerabilities": []
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
                        "severity": {
                            "type": "string",
                            "description": "漏洞严重程度过滤，默认: critical,high,medium",
                            "enum": ["critical", "high", "medium", "low", "info", "critical,high", "critical,high,medium"]
                        },
                        "tags": {
                            "type": "string",
                            "description": "标签过滤，如: cve,sqli,xss"
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

"""
Execute Python - Docker沙箱执行Python代码
"""
import docker
import time
import tempfile
import os
from typing import Dict, Any
from .base import BaseTool


class ExecutePython(BaseTool):
    """Python代码沙箱执行器 - Docker隔离"""
    
    def __init__(self, session_id: str = None):
        super().__init__(
            name="execute_python",
            description="Execute Python code in isolated Docker sandbox. Can use requests, beautifulsoup4, etc."
        )
        self.session_id = session_id or f"task-{int(time.time())}"
        self.container_name = f"pentest-sandbox-{self.session_id}"
        self.client = None
        self.container = None
        self.work_dir = None
        self.image_name = "pentest-sandbox:latest"
    
    async def initialize(self):
        """初始化沙箱"""
        try:
            self.client = docker.from_env()
            
            # 确保镜像存在
            await self._ensure_image_exists()
            
            # 启动容器
            await self._start_container()
            
        except Exception as e:
            print(f"❌ 沙箱初始化失败: {e}")
            import traceback
            traceback.print_exc()
            self.client = None
            self.container = None
    
    async def _ensure_image_exists(self):
        """确保沙箱镜像存在"""
        try:
            self.client.images.get(self.image_name)
        except docker.errors.ImageNotFound:
            await self._build_sandbox_image()
    
    async def _build_sandbox_image(self):
        """构建沙箱镜像"""
        dockerfile = """
FROM python:3.11-slim

# 配置清华源
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources && \\
    sed -i 's/security.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \\
    gcc g++ git curl wget \\
    libxml2-dev libxslt1-dev zlib1g-dev \\
    libffi-dev libssl-dev \\
    && rm -rf /var/lib/apt/lists/*

# 配置pip清华源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装核心库
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \\
    pip install --no-cache-dir \\
    requests httpx aiohttp urllib3 \\
    beautifulsoup4 lxml html5lib \\
    pyyaml pycryptodome cryptography \\
    pyjwt chardet flask jinja2 \\
    pymysql redis python-dateutil pytz \\
    colorama tqdm click validators \\
    websocket-client pysocks pillow

# 创建工作目录
WORKDIR /sandbox

# 非root用户
RUN useradd -m -u 1000 sandbox && chown -R sandbox:sandbox /sandbox
USER sandbox

# 环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8

CMD ["python3"]
"""
        
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                dockerfile_path = os.path.join(tmpdir, 'Dockerfile')
                with open(dockerfile_path, 'w') as f:
                    f.write(dockerfile)
                
                print("🔨 构建沙箱镜像（首次需要几分钟）...")
                image, build_logs = self.client.images.build(
                    path=tmpdir,
                    tag=self.image_name,
                    rm=True
                )
                
                print(f"✅ 镜像构建成功: {self.image_name}")
        except Exception as e:
            print(f"❌ 镜像构建失败: {e}")
            raise
    
    async def _start_container(self):
        """启动容器"""
        try:
            self.container = self.client.containers.run(
                image=self.image_name,
                command=['sleep', 'infinity'],
                detach=True,
                mem_limit='512m',
                cpu_quota=100000,
                network_mode='bridge',
                read_only=False,
                remove=False,
                name=self.container_name
            )
        except Exception as e:
            print(f"❌ 容器启动失败: {e}")
            self.container = None
    
    async def execute(self, code: str, timeout: int = 60) -> str:
        """
        执行Python代码
        
        Args:
            code: Python代码
            timeout: 超时（秒）
        
        Returns:
            执行结果（输出+错误）
        """
        if not self.client or not self.container:
            return "❌ 沙箱未初始化"
        
        start_time = time.time()
        
        try:
            # 检查容器状态
            self.container.reload()
            if self.container.status != 'running':
                print("⚠️ 容器已停止，重新启动...")
                await self._start_container()
            
            # 创建工作目录
            if not self.work_dir:
                self.work_dir = f"/sandbox/workspace_{int(time.time())}"
                self.container.exec_run(f"mkdir -p {self.work_dir}")
            
            # 写入代码文件
            script_name = f"script_{int(time.time() * 1000)}.py"
            code_file = f"{self.work_dir}/{script_name}"
            
            write_cmd = f"cat > {code_file} << 'EOF'\n{code}\nEOF"
            self.container.exec_run(['sh', '-c', write_cmd])
            
            # 执行代码
            exec_result = self.container.exec_run(
                cmd=['python3', code_file],
                stdout=True,
                stderr=True,
                demux=False,
                workdir=self.work_dir
            )
            
            execution_time = time.time() - start_time
            
            # 解析结果
            exit_code = exec_result.exit_code
            output = exec_result.output.decode('utf-8', errors='replace') if exec_result.output else ''
            
            # 返回格式化结果
            result = f"Exit Code: {exit_code}\n"
            result += f"Execution Time: {execution_time:.2f}s\n"
            result += f"{'='*60}\n"
            result += f"Output:\n{output[:30000]}"  # 🔥 增加到30000字符，避免JSON截断
            
            return result
            
        except Exception as e:
            error_msg = f"❌ 执行失败: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return error_msg
    
    def get_parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute. Can use requests, beautifulsoup4, etc."
                },
                "timeout": {
                    "type": "integer",
                    "description": "Timeout in seconds",
                    "default": 60
                }
            },
            "required": ["code"]
        }
    
    async def cleanup(self):
        """清理沙箱"""
        try:
            # 清理工作目录
            if self.container and self.work_dir:
                try:
                    self.container.exec_run(f"rm -rf {self.work_dir}")
                    print(f"🗑️ 清理工作目录: {self.work_dir}")
                except:
                    pass
            
            # 停止容器
            if self.container:
                try:
                    container_name = self.container.name
                    self.container.stop(timeout=2)
                    self.container.remove(force=True)
                    print(f"🗑️ 清理容器: {container_name}")
                except:
                    pass
            
            self.container = None
            self.work_dir = None
            
            print(f"✅ 沙箱清理完成: {self.session_id}")
            
        except Exception as e:
            print(f"❌ 清理失败: {e}")
    
    def __del__(self):
        """析构函数 - 自动清理"""
        try:
            import asyncio
            asyncio.create_task(self.cleanup())
        except:
            pass

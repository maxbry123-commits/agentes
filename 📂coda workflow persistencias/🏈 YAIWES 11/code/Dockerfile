# CTF Agent Docker 镜像
# 用法:
#   docker build -t ctf-agent .
#   docker run -it --rm -v ./config.json:/app/config.json ctf-agent --mode ctf
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖（chromadb 需要的编译库 + 可选渗透工具）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# ChromaDB 持久化目录（可挂载卷覆盖）
VOLUME ["/app/rag_db", "/app/logs", "/app/attachments"]

# 默认运行 CTF 模式
ENTRYPOINT ["python", "main.py"]
CMD ["--mode", "ctf"]

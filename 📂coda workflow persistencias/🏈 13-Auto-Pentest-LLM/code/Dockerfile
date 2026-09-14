FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (curl, sshpass, git, gcc for some python libs)
RUN apt-get update && apt-get install -y \
    curl \
    sshpass \
    git \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default command (can be overridden)
ENTRYPOINT ["python", "main.py"]

# Real-Life Test Runner for Cognithor
FROM python:3.13-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . /app/

# Install Cognithor with all extras
RUN pip install --no-cache-dir -e ".[search,documents,cron]" && \
    pip install --no-cache-dir pytest pytest-asyncio httpx

# Test entrypoint
CMD ["pytest", "tests/test_reallife/", "-v", "--tb=short", "-x"]

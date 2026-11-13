FROM python:3.13-slim

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV PORT=8080
EXPOSE 8080

# One worker is fine: the work is IO-bound (Tigris + cloud proxy) and the sandbox
# compute spawns its own subprocess. Scale out via Fly machines, not workers.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]

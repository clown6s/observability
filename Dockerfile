FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 先装依赖层，利用缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 容器内不跑 reload；日志由 main 里 setup_logging() 统一为 JSON
EXPOSE 8000

# 用我们自己的 logging 配置启动 uvicorn，避免 uvicorn 启动时覆盖 uvicorn.access 的 null handler
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--log-config", "app/core/logging.py"]

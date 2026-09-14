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

# 用 python main.py 入口：内部 uvicorn.run(log_config=LOGGING_CONFIG) 采用我们的日志配置
CMD ["python", "main.py"]

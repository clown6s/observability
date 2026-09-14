"""结构化日志（structlog.stdlib）：JSON 输出，uvicorn 启动日志同样结构化。"""

import logging
import logging.config
import sys
import time

import structlog
from fastapi import Request
from structlog.stdlib import BoundLogger

# 访问日志专用 logger 名
ACCESS_LOGGER = "access"

# 可复用给 uvicorn.run(log_config=...) 的 logging 配置，让 reload 主进程日志也结构化
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        # ProcessorFormatter 同时处理 structlog 日志与外部(uvicorn/stdlib)日志
        "json": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(ensure_ascii=False),
            "foreign_pre_chain": [
                structlog.contextvars.merge_contextvars,
                structlog.processors.TimeStamper(fmt="iso", utc=True),
                structlog.stdlib.add_log_level,
            ],
        },
    },
    "handlers": {
        "default": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            # 用字符串引用而非 sys.stdout 对象，避免 uvicorn reload 子进程 pickle 报错
            "stream": "ext://sys.stdout",
        },
        # 丢弃 uvicorn.access 的自带访问日志（比 disabled 更可靠，不依赖 uvicorn flag）
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "loggers": {
        "": {"handlers": ["default"], "level": logging.INFO},
        "uvicorn": {"handlers": ["default"], "level": logging.INFO, "propagate": False},
        "uvicorn.error": {"handlers": ["default"], "level": logging.INFO, "propagate": False},
        "uvicorn.access": {"handlers": ["null"], "level": logging.INFO, "propagate": False},
    },
}


def setup_logging(level: int = logging.INFO) -> None:
    """用 dictConfig 接管 root 与 uvicorn 的日志输出，统一为单行 JSON。"""
    config = dict(LOGGING_CONFIG)
    for logger_cfg in config["loggers"].values():
        logger_cfg["level"] = level
    logging.config.dictConfig(config)

    # 强制关闭 uvicorn 自带 access log（会覆盖我们 middleware 的 JSON 访问日志）。
    # 不依赖 --no-access-log 参数，代码级生效。
    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("uvicorn.access").propagate = False

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> BoundLogger:
    """拿到一个 bound logger，业务代码直接 .info()/.error() 即可。"""
    return structlog.get_logger(name)


async def request_logging_middleware(request: Request, call_next):
    """为每个请求绑定 request_id / client_ip，并记录访问日志。"""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=f"{time.time_ns():x}",
        client_ip=request.client.host if request.client else None,
    )
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    # 探活/指标等高频路径不打访问日志，避免刷屏
    if request.url.path not in {"/metrics"}:
        get_logger(ACCESS_LOGGER).info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration_ms, 3),
        )
    return response
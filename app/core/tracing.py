"""OpenTelemetry 链路追踪：FastAPI 自动埋点，trace 推送到 Tempo，并把 trace_id 注入日志。"""

import os

import structlog
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# 容器内 Tempo 服务名；本地跑可覆盖
OTLP_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://tempo:4317")


def _add_trace_context(logger, method_name, event_dict):
    """把当前 span 的 trace_id/span_id 并入日志事件，实现日志↔追踪联动。"""
    span = trace.get_current_span()
    if span and span.is_recording():
        ctx = span.get_span_context()
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict


def _resource(service_name: str) -> Resource:
    """确保 service.name 明确（兼容不带 get_default 的旧版 SDK）。"""
    name = os.getenv("OTEL_SERVICE_NAME", service_name)
    return Resource.create({SERVICE_NAME: name})


def setup_tracing(app: FastAPI, service_name: str = "fastapi-app") -> None:
    """初始化 TracerProvider + OTLP(→Tempo)，并给 FastAPI 自动埋点。"""
    provider = TracerProvider(resource=_resource(service_name))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=OTLP_ENDPOINT)))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider, excluded_urls="/metrics")

    # 在 structlog processors 链中插入 trace_id 注入（在 wrap_for_formatter 之前）
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            _add_trace_context,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
    )

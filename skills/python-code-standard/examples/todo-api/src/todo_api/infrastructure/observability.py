import logging.config
import os
from dataclasses import dataclass
from typing import Literal

import structlog
from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import MetricReader, PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from structlog.typing import EventDict, WrappedLogger

SERVICE_NAME = "todo-api"

type LogFormat = Literal["json", "console"]


def configure_logging(log_format: LogFormat, level: str = "INFO") -> None:
    """Code logs with stdlib `logging.getLogger(__name__).info("noun.verb", extra={...})`; structlog renders every
    record, uvicorn's included, as one JSON line (or coloured console output locally)."""
    shared: list[structlog.typing.Processor] = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.ExtraAdder(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _add_trace_context,
        _drop_color_message,
    ]
    renderer = structlog.processors.JSONRenderer() if log_format == "json" else structlog.dev.ConsoleRenderer()
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "structlog": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "foreign_pre_chain": shared,
                    "processors": [
                        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                        structlog.processors.format_exc_info,
                        renderer,
                    ],
                }
            },
            "handlers": {"default": {"class": "logging.StreamHandler", "formatter": "structlog"}},
            "root": {"handlers": ["default"], "level": level},
            "loggers": {
                "uvicorn": {"handlers": [], "propagate": True},
                "uvicorn.error": {"handlers": [], "propagate": True},
                "uvicorn.access": {"handlers": [], "propagate": True, "level": "WARNING"},
            },
        }
    )


@dataclass(frozen=True, slots=True)
class Telemetry:
    tracer_provider: TracerProvider
    meter_provider: MeterProvider

    def flush(self) -> None:
        """Called on app shutdown; the providers themselves live as long as the process."""
        self.meter_provider.force_flush()
        self.tracer_provider.force_flush()


def configure_telemetry() -> Telemetry:
    """Install the global tracer and meter providers once per process. Spans always exist (trace ids in logs and
    problem bodies); spans and metrics are exported only when `OTEL_EXPORTER_OTLP_ENDPOINT` is set.
    """
    tracer_provider, meter_provider = trace.get_tracer_provider(), metrics.get_meter_provider()
    if isinstance(tracer_provider, TracerProvider) and isinstance(meter_provider, MeterProvider):
        return Telemetry(tracer_provider, meter_provider)
    resource = Resource.create({"service.name": SERVICE_NAME})
    exporting = bool(os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"))
    provider = TracerProvider(resource=resource)
    if exporting:
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    # Instrument the driver, not SQLAlchemy: opentelemetry-instrumentation-sqlalchemy 0.66b1 refuses SQLAlchemy 2.1.
    AsyncPGInstrumentor().instrument()
    readers: list[MetricReader] = [PeriodicExportingMetricReader(OTLPMetricExporter())] if exporting else []
    meters = MeterProvider(resource=resource, metric_readers=readers)
    metrics.set_meter_provider(meters)
    return Telemetry(provider, meters)


def instrument(app: FastAPI) -> None:
    """Server spans + `http.server.duration` for this app instance; undone with `uninstrument` on shutdown."""
    FastAPIInstrumentor.instrument_app(app, excluded_urls="health/.*")


def uninstrument(app: FastAPI) -> None:
    FastAPIInstrumentor.uninstrument_app(app)


def _add_trace_context(_: WrappedLogger, __: str, event: EventDict) -> EventDict:
    context = trace.get_current_span().get_span_context()
    if context.is_valid:
        event["trace_id"] = format(context.trace_id, "032x")
        event["span_id"] = format(context.span_id, "016x")
    return event


def _drop_color_message(_: WrappedLogger, __: str, event: EventDict) -> EventDict:
    event.pop("color_message", None)
    return event

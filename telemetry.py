import os
import logging

logger = logging.getLogger(__name__)


# Tracing is opt in: it only starts when an OTLP endpoint is configured (or an exporter is passed in),
# so tests and the desktop app never try to send spans anywhere
def setup_tracing(app, engine, span_exporter=None):
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if span_exporter is None and not endpoint:
        return None

    # imported here so the app does not pay for them when tracing is off
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({"service.name": os.getenv("OTEL_SERVICE_NAME", "perfima")})
    provider = TracerProvider(resource=resource)
    # with no arguments the exporter reads OTEL_EXPORTER_OTLP_ENDPOINT and posts to <endpoint>/v1/traces
    provider.add_span_processor(BatchSpanProcessor(span_exporter or OTLPSpanExporter()))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider, excluded_urls="healthCheck")
    SQLAlchemyInstrumentor().instrument(engine=engine, tracer_provider=provider)

    logger.info(f"Tracing enabled for {resource.attributes['service.name']}")
    return provider

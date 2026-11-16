from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from perfima.telemetry import setup_tracing


def test_tracing_is_off_without_endpoint(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    assert setup_tracing(FastAPI(), create_engine("sqlite://")) is None


def test_requests_and_queries_produce_spans():
    app = FastAPI()
    engine = create_engine("sqlite://", poolclass=StaticPool)

    @app.get("/ping")
    def ping():
        with engine.connect() as connection:
            return {"value": connection.execute(text("select 1")).scalar()}

    exporter = InMemorySpanExporter()
    provider = setup_tracing(app, engine, span_exporter=exporter)

    response = TestClient(app).get("/ping")
    assert response.status_code == 200
    provider.force_flush()

    spans = exporter.get_finished_spans()
    request_span = next(s for s in spans if s.name == "GET /ping")
    query_span = next(s for s in spans if s.attributes.get("db.statement") == "select 1")

    # the SQL span is a child of the request, so one trace shows the whole request
    assert query_span.context.trace_id == request_span.context.trace_id
    assert request_span.attributes["http.status_code"] == 200
    assert provider.resource.attributes["service.name"] == "perfima"

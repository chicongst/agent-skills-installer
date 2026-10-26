import logging

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from tests.conftest import SettingsFactory, SigningKey
from tests.integration.conftest import Api, open_api
from todo_api.main import create_app


@pytest.fixture(scope="session")
def spans() -> InMemorySpanExporter:
    provider = trace.get_tracer_provider()
    assert isinstance(provider, TracerProvider), "create_app installs the SDK provider"
    exporter = InMemorySpanExporter()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return exporter


async def test_each_request_logs_one_line_with_route_template_and_status(
    api: Api, caplog: pytest.LogCaptureFixture
) -> None:
    url = await api.create()
    caplog.clear()

    with caplog.at_level(logging.INFO, logger="todo_api.http"):
        await api.send("GET", url)

    [record] = [r for r in caplog.records if r.getMessage() == "http.request"]
    assert (record.method, record.route, record.status) == ("GET", "/v1/todos/{todo_id}", 200)  # type: ignore[attr-defined]
    assert record.duration_ms >= 0  # type: ignore[attr-defined]


@pytest.mark.postgres
async def test_database_statements_are_traced_inside_the_request_span(
    postgres_url: str, make_settings: SettingsFactory, signing_key: SigningKey, spans: InMemorySpanExporter
) -> None:
    async for api in open_api(create_app(make_settings(database_url=postgres_url)), signing_key):
        spans.clear()
        await api.send("GET", "/v1/todos")

    finished = spans.get_finished_spans()
    sql = [span for span in finished if span.attributes and span.attributes.get("db.system") == "postgresql"]
    server = [span for span in finished if span.kind is trace.SpanKind.SERVER]
    assert sql
    assert server
    assert {span.context.trace_id for span in sql} == {server[0].context.trace_id}

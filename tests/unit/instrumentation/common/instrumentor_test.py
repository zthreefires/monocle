import pytest
from unittest.mock import Mock, patch, MagicMock
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import SpanContext
from opentelemetry.context import attach, get_value, set_value, detach, Context
import uuid
import random

from monocle_apptrace.instrumentation.common.instrumentor import (
    MonocleInstrumentor,
    set_tracer_provider,
    get_tracer_provider,
    setup_monocle_telemetry,
    on_processor_start,
    set_context_properties,
    propagate_trace_id,
    propagate_trace_id_from_traceparent,
    stop_propagate_trace_id,
    is_valid_trace_id_uuid,
    start_scope,
    stop_scope,
    monocle_trace_scope,
    monocle_trace_scope_method,
    monocle_trace_http_route,
    FixedIdGenerator
)

@pytest.fixture
def tracer_provider():
    provider = TracerProvider()
    yield provider

@pytest.fixture
def mock_span():
    span = Mock()
    span.get_span_context = Mock(return_value=SpanContext(
        trace_id=123,
        span_id=456,
        is_remote=False,
        trace_flags=1
    ))
    return span

@pytest.fixture
def mock_handler():
    handler = Mock()
    handler.hydrate_span = Mock()
    return handler

def test_set_get_tracer_provider(tracer_provider):
    set_tracer_provider(tracer_provider)
    assert get_tracer_provider() == tracer_provider

def test_monocle_instrumentor_init():
    handlers = {"default": Mock()}
    instrumentor = MonocleInstrumentor(handlers=handlers)
    assert instrumentor.handlers == handlers
    assert instrumentor.user_wrapper_methods == []
    assert instrumentor.union_with_default_methods == True

def test_monocle_instrumentor_init_with_methods():
    handlers = {"default": Mock()}
    methods = [{"package": "test", "method": "test_method"}]
    instrumentor = MonocleInstrumentor(handlers=handlers, user_wrapper_methods=methods)
    assert instrumentor.handlers == handlers
    assert instrumentor.user_wrapper_methods == methods

def test_setup_monocle_telemetry():
    workflow_name = "test_workflow"
    span_processor = Mock(spec=BatchSpanProcessor)

    with patch('monocle_apptrace.instrumentation.common.instrumentor.get_monocle_exporter') as mock_exporter:
        mock_exporter.return_value = [Mock()]

        instrumentor = setup_monocle_telemetry(
            workflow_name=workflow_name,
            span_processors=[span_processor]
        )

        assert isinstance(instrumentor, MonocleInstrumentor)
        assert get_value("workflow_name") == workflow_name

def test_on_processor_start(mock_span):
    test_properties = {"key": "value"}
    set_context_properties(test_properties)

    on_processor_start(mock_span, None)

    mock_span.set_attribute.assert_called_once_with(
        "session.key", "value"
    )

def test_set_context_properties():
    test_props = {"test": "value"}
    set_context_properties(test_props)
    assert get_value("session") == test_props

def test_is_valid_trace_id_uuid():
    valid_id = "550e8400-e29b-41d4-a716-446655440000"
    invalid_id = "not-a-uuid"

    assert is_valid_trace_id_uuid(valid_id) == True
    assert is_valid_trace_id_uuid(invalid_id) == False

def test_fixed_id_generator():
    trace_id = 123456
    generator = FixedIdGenerator(trace_id)

    assert generator.generate_trace_id() == trace_id
    assert isinstance(generator.generate_span_id(), int)

def test_monocle_trace_scope_method_sync():
    @monocle_trace_scope_method("test_scope")
    def test_func():
        return "test_result"

    result = test_func()
    assert result == "test_result"

def test_monocle_trace_http_route_sync():
    @monocle_trace_http_route
    def test_route():
        return "test_response"

    result = test_route()
    assert result == "test_response"

def test_propagate_trace_id_from_traceparent():
    with patch('monocle_apptrace.instrumentation.common.instrumentor.propagate_trace_id') as mock_propagate:
        propagate_trace_id_from_traceparent()
        mock_propagate.assert_called_once_with(use_trace_context=True)

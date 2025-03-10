import json
from os import path
from datetime import datetime
from unittest.mock import mock_open, patch, MagicMock
import pytest
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExportResult
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import SpanContext, TraceFlags
from monocle_apptrace.exporters.file_exporter import FileSpanExporter

@pytest.fixture
def mock_span():
    span = MagicMock(spec=ReadableSpan)
    span.context = SpanContext(
        trace_id=123,
        span_id=456,
        trace_flags=TraceFlags.DEFAULT,
        is_remote=False
    )
    span.resource = Resource({"service.name": "test_service"})
    span.to_json.return_value = json.dumps({"name": "test_span"})
    return span

@pytest.fixture
def exporter(tmp_path):
    exporter = FileSpanExporter(out_path=str(tmp_path))
    yield exporter
    exporter.shutdown()

def test_export_single_span(exporter, mock_span, tmp_path):
    with patch('builtins.open', mock_open()) as mock_file:
        result = exporter.export([mock_span])

        assert result == SpanExportResult.SUCCESS
        mock_file.assert_called_once()
        mock_file().write.assert_called_once()
        mock_file().flush.assert_called_once()

def test_export_multiple_spans_same_trace(exporter, mock_span, tmp_path):
    spans = [mock_span, mock_span]

    with patch('builtins.open', mock_open()) as mock_file:
        result = exporter.export(spans)

        assert result == SpanExportResult.SUCCESS
        assert mock_file().write.call_count == 2
        mock_file().flush.assert_called_once()

def test_export_spans_different_traces(exporter, tmp_path):
    span1 = MagicMock(spec=ReadableSpan)
    span1.context = SpanContext(
        trace_id=123,
        span_id=456,
        trace_flags=TraceFlags.DEFAULT,
        is_remote=False
    )
    span1.resource = Resource({"service.name": "test_service"})

    span2 = MagicMock(spec=ReadableSpan)
    span2.context = SpanContext(
        trace_id=789,
        span_id=101,
        trace_flags=TraceFlags.DEFAULT,
        is_remote=False
    )
    span2.resource = Resource({"service.name": "test_service"})

    with patch('builtins.open', mock_open()) as mock_file:
        result = exporter.export([span1, span2])

        assert result == SpanExportResult.SUCCESS
        assert mock_file.call_count == 2
        assert mock_file().write.call_count == 2

def test_rotate_file(exporter, tmp_path):
    with patch('builtins.open', mock_open()) as mock_file:
        exporter.rotate_file("test_service", 123)

        expected_path = path.join(str(tmp_path),
            f"monocle_trace_test_service_{hex(123)}_{datetime.now().strftime('%Y-%m-%d_%H.%M.%S')}.json")
        mock_file.assert_called_once_with(expected_path, "w", encoding='UTF-8')
        assert exporter.current_trace_id == 123

def test_force_flush(exporter):
    mock_handle = MagicMock()
    exporter.out_handle = mock_handle

    result = exporter.force_flush()

    assert result is True
    mock_handle.flush.assert_called_once()

def test_reset_handle(exporter):
    mock_handle = MagicMock()
    exporter.out_handle = mock_handle

    exporter.reset_handle()

    mock_handle.close.assert_called_once()
    assert exporter.out_handle is None

def test_reset_handle_no_handle(exporter):
    exporter.out_handle = None
    exporter.reset_handle()
    assert exporter.out_handle is None

def test_shutdown(exporter):
    mock_handle = MagicMock()
    exporter.out_handle = mock_handle

    exporter.shutdown()

    mock_handle.close.assert_called_once()
    assert exporter.out_handle is None

def test_shutdown_no_handle(exporter):
    exporter.out_handle = None
    exporter.shutdown()
    assert exporter.out_handle is None

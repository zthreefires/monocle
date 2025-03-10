import pytest
from unittest.mock import Mock, patch, mock_open
import logging
import json
import os
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import NonRecordingSpan, SpanContext, Span
from opentelemetry.context import Context
from monocle_apptrace.instrumentation.common.utils import *
from monocle_apptrace.instrumentation.common.constants import MONOCLE_SCOPE_NAME_PREFIX

@pytest.fixture
def mock_tracer_provider():
    provider = TracerProvider()
    return provider

def test_set_get_tracer_provider(mock_tracer_provider):
    set_tracer_provider(mock_tracer_provider)
    assert get_tracer_provider() == mock_tracer_provider

def test_set_span_attribute():
    mock_span = Mock()
    set_span_attribute(mock_span, "test_key", "test_value")
    mock_span.set_attribute.assert_called_once_with("test_key", "test_value")

    mock_span.reset_mock()
    set_span_attribute(mock_span, "test_key", "")
    mock_span.set_attribute.assert_not_called()

    mock_span.reset_mock()
    set_span_attribute(mock_span, "test_key", None)
    mock_span.set_attribute.assert_not_called()

def test_dont_throw():
    @dont_throw
    def test_func():
        raise ValueError("test error")

    with patch('logging.Logger.warning') as mock_warning:
        test_func()
        mock_warning.assert_called_once_with(
            "Failed to execute %s, error: %s",
            "test_func",
            "test error"
        )

def test_with_tracer_wrapper():
    mock_tracer = Mock()
    mock_handler = Mock()
    mock_to_wrap = Mock()

    @with_tracer_wrapper
    def test_wrapper(tracer, handler, to_wrap, wrapped, instance, args, kwargs):
        return "test"

    wrapper = test_wrapper(mock_tracer, mock_handler, mock_to_wrap)
    result = wrapper(None, None, [], {})
    assert result == "test"

def test_resolve_from_alias():
    test_map = {"key1": "value1", "key2": "value2"}
    assert resolve_from_alias(test_map, ["key1"]) == "value1"
    assert resolve_from_alias(test_map, ["missing"]) is None
    assert resolve_from_alias(test_map, ["key2", "key1"]) == "value2"

def test_set_get_embedding_model():
    set_embedding_model("test_model")
    assert get_embedding_model() == "test_model"

    embedding_model_context.clear()
    assert get_embedding_model() == "unknown"

def test_set_get_attribute():
    token = set_attribute("test_key", "test_value")
    assert get_attribute("test_key") == "test_value"
    detach(token)

def test_flatten_dict():
    nested_dict = {
        "a": 1,
        "b": {
            "c": 2,
            "d": {
                "e": 3
            }
        }
    }
    flattened = flatten_dict(nested_dict)
    assert flattened == {
        "a": 1,
        "b_c": 2,
        "b_d_e": 3
    }

def test_get_fully_qualified_class_name():
    class TestClass:
        pass

    test_obj = TestClass()
    expected = f"{test_obj.__class__.__module__}.{test_obj.__class__.__qualname__}"
    assert get_fully_qualified_class_name(test_obj) == expected
    assert get_fully_qualified_class_name(None) is None

def test_get_nested_value():
    data = {
        "a": {
            "b": {
                "c": "value"
            }
        }
    }
    assert get_nested_value(data, ["a", "b", "c"]) == "value"
    assert get_nested_value(data, ["a", "missing"]) is None

    class TestObj:
        def __init__(self):
            self.attr = "value"

    obj = TestObj()
    assert get_nested_value(obj, ["attr"]) == "value"
    assert get_nested_value(obj, ["missing"]) is None

def test_load_scopes(tmp_path):
    test_data = [
        {"http_header": "test-header", "scope_name": "test-scope"},
        {"method": "test_method"}
    ]

    config_file = tmp_path / "scope_methods.json"
    config_file.write_text(json.dumps(test_data))

    with patch.dict(os.environ, {SCOPE_CONFIG_PATH: str(config_file)}):
        scope_methods = load_scopes()
        assert len(scope_methods) == 1
        assert scope_methods[0]["method"] == "test_method"
        assert "test-header" in http_scopes
        assert http_scopes["test-header"] == "test-scope"

def test_set_get_scopes():
    token = set_scopes({"test_scope": "test_value"})
    scopes = get_scopes()
    assert "test_scope" in scopes
    assert scopes["test_scope"] == "test_value"

    remove_scopes(token)
    assert len(get_scopes()) == 0

def test_extract_http_headers():
    headers = {"test-header": "test-value"}
    http_scopes["test-header"] = "test-scope"

    token = extract_http_headers(headers)
    scopes = get_scopes()
    assert "test-scope" in scopes
    assert "test-header: test-value" in scopes.values()

    clear_http_scopes(token)
    assert len(get_scopes()) == 0

def test_http_route_handler():
    def test_func(*args, **kwargs):
        return "test"

    mock_req = Mock()
    mock_req.headers = {"test-header": "test-value"}

    result = http_route_handler(test_func, req=mock_req)
    assert result == "test"

@pytest.mark.asyncio
async def test_async_wrapper():
    async def test_func():
        return "test"

    result = await async_wrapper(test_func, "test_scope")
    assert result == "test"

    result = await async_wrapper(test_func, headers={"test-header": "test-value"})
    assert result == "test"

def test_option():
    opt = Option(5)
    assert opt.is_some()
    assert not opt.is_none()
    assert opt.unwrap_or(0) == 5

    none_opt = Option(None)
    assert none_opt.is_none()
    assert not none_opt.is_some()
    assert none_opt.unwrap_or(0) == 0

    mapped = opt.map(lambda x: x * 2)
    assert mapped.unwrap_or(0) == 10

    def double_option(x):
        return Option(x * 2)

    chained = opt.and_then(double_option)
    assert chained.unwrap_or(0) == 10

def test_try_option():
    def may_fail(succeed):
        if not succeed:
            raise ValueError()
        return "success"

    success = try_option(may_fail, True)
    assert success.is_some()
    assert success.unwrap_or("failed") == "success"

    failure = try_option(may_fail, False)
    assert failure.is_none()
    assert failure.unwrap_or("failed") == "failed"

import pytest
from monocle_apptrace.instrumentation.common.wrapper_method import WrapperMethod
from monocle_apptrace.instrumentation.common.wrapper import task_wrapper, scope_wrapper
from monocle_apptrace.instrumentation.common.span_handler import SpanHandler
from monocle_apptrace.instrumentation.metamodel.botocore.handlers.botocore_span_handler import BotoCoreSpanHandler

@pytest.fixture
def basic_wrapper_method():
    return WrapperMethod(
        package="test_package",
        object_name="TestObject",
        method="test_method"
    )

@pytest.fixture
def scoped_wrapper_method():
    return WrapperMethod(
        package="test_package",
        object_name="TestObject",
        method="test_method",
        scope_name="test_scope"
    )

@pytest.fixture
def full_wrapper_method():
    return WrapperMethod(
        package="test_package",
        object_name="TestObject",
        method="test_method",
        span_name="test_span",
        output_processor="test_processor",
        wrapper_method=task_wrapper,
        span_handler=BotoCoreSpanHandler,
        scope_name="test_scope"
    )

def test_to_dict_basic(basic_wrapper_method):
    result = basic_wrapper_method.to_dict()
    assert result["package"] == "test_package"
    assert result["object"] == "TestObject"
    assert result["method"] == "test_method"
    assert result["span_name"] is None
    assert result["output_processor"] is None
    assert result["wrapper_method"] == task_wrapper
    assert result["span_handler"] == "default"
    assert result["scope_name"] is None

def test_to_dict_with_scope(scoped_wrapper_method):
    result = scoped_wrapper_method.to_dict()
    assert result["scope_name"] == "test_scope"
    assert result["wrapper_method"] == scope_wrapper

def test_to_dict_full(full_wrapper_method):
    result = full_wrapper_method.to_dict()
    assert result["package"] == "test_package"
    assert result["object"] == "TestObject"
    assert result["method"] == "test_method"
    assert result["span_name"] == "test_span"
    assert result["output_processor"] == "test_processor"
    assert result["wrapper_method"] == scope_wrapper
    assert result["span_handler"] == BotoCoreSpanHandler
    assert result["scope_name"] == "test_scope"

def test_get_span_handler_default():
    method = WrapperMethod(
        package="test_package",
        object_name="TestObject",
        method="test_method",
        span_handler=SpanHandler
    )
    handler = method.get_span_handler()
    assert isinstance(handler, SpanHandler)

def test_get_span_handler_custom():
    method = WrapperMethod(
        package="test_package",
        object_name="TestObject",
        method="test_method",
        span_handler=BotoCoreSpanHandler
    )
    handler = method.get_span_handler()
    assert isinstance(handler, BotoCoreSpanHandler)

def test_wrapper_method_selection():
    # Test with scope name
    method = WrapperMethod("pkg", "obj", "method", scope_name="scope")
    assert method.wrapper_method == scope_wrapper

    # Test without scope name
    method = WrapperMethod("pkg", "obj", "method")
    assert method.wrapper_method == task_wrapper

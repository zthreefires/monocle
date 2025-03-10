import pytest
from unittest.mock import MagicMock, patch
from monocle_apptrace.instrumentation.metamodel.requests._helper import (
    request_pre_task_processor,
    request_skip_span,
    RequestSpanHandler
)

@pytest.fixture
def mock_inject():
    with patch('monocle_apptrace.instrumentation.metamodel.requests._helper.inject') as mock:
        yield mock

def test_request_pre_task_processor_with_existing_headers(mock_inject):
    # Test with existing headers
    kwargs = {'headers': {'existing': 'header'}}
    request_pre_task_processor(kwargs)

    mock_inject.assert_called_once()
    assert 'existing' in kwargs['headers']

def test_request_pre_task_processor_without_headers(mock_inject):
    # Test without existing headers
    kwargs = {}
    request_pre_task_processor(kwargs)

    mock_inject.assert_called_once()
    assert 'headers' in kwargs

def test_request_pre_task_processor_empty_headers(mock_inject):
    # Test with empty headers dict
    kwargs = {'headers': {}}
    request_pre_task_processor(kwargs)

    mock_inject.assert_called_once()
    assert isinstance(kwargs['headers'], dict)

def test_request_skip_span_no_url():
    # Test when no URL is provided
    kwargs = {}
    assert request_skip_span(kwargs) is True

def test_request_skip_span_allowed_url():
    # Test with allowed URL
    kwargs = {'url': 'http://allowed-domain.com'}
    with patch('monocle_apptrace.instrumentation.metamodel.requests._helper.allowed_urls', ['http://allowed-domain.com']):
        assert request_skip_span(kwargs) is False

def test_request_skip_span_not_allowed_url():
    # Test with non-allowed URL
    kwargs = {'url': 'http://other-domain.com'}
    with patch('monocle_apptrace.instrumentation.metamodel.requests._helper.allowed_urls', ['http://allowed-domain.com']):
        assert request_skip_span(kwargs) is True

def test_request_skip_span_empty_allowed_urls():
    # Test with empty allowed URLs list
    kwargs = {'url': 'http://any-domain.com'}
    with patch('monocle_apptrace.instrumentation.metamodel.requests._helper.allowed_urls', []):
        assert request_skip_span(kwargs) is True

def test_request_span_handler_pre_task_processing(mock_inject):
    with patch('monocle_apptrace.instrumentation.common.span_handler.SpanHandler.pre_task_processing') as mock_super:
        handler = RequestSpanHandler()
        to_wrap = MagicMock()
        wrapped = MagicMock()
        instance = MagicMock()
        args = ()
        kwargs = {'headers': {}}
        span = MagicMock()

        handler.pre_task_processing(to_wrap, wrapped, instance, args, kwargs, span)

        mock_inject.assert_called_once_with(kwargs['headers'])
        mock_super.assert_called_once_with(to_wrap, wrapped, instance, args, kwargs, span)

def test_request_span_handler_skip_span():
    with patch('monocle_apptrace.instrumentation.metamodel.requests._helper.request_skip_span') as mock_request_skip:
        handler = RequestSpanHandler()
        to_wrap = MagicMock()
        wrapped = MagicMock()
        instance = MagicMock()
        args = ()
        kwargs = {'url': 'http://test.com'}

        handler.skip_span(to_wrap, wrapped, instance, args, kwargs)

        mock_request_skip.assert_called_once_with(kwargs)

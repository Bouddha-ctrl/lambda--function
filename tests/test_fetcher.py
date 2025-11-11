import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
import json

from src.fetcher import (
    parse_oil_price, 
    parse_exchange_rate, 
    ExtractionError,
    fetch_oil_data,
    fetch_exchange_data,
    _fetch_json,
    _parse_date_string_to_iso
)


def test_parse_oil_price_success():
    resp = {
        "bars": [
            ["Mon Aug 11 00:00:00 2025", 653],
            ["Tue Aug 12 00:00:00 2025", 648.25],
            ["Wed Aug 13 00:00:00 2025", 639.25]
        ],
        "marketId": 5910762
    }
    date_iso, price = parse_oil_price(resp)
    assert date_iso == "2025-08-13"
    assert price == Decimal("639.25")


def test_parse_oil_price_malformed_bars_raises():
    # bars exists but last element malformed
    resp = {
        "bars": [
            ["Mon Aug 11 00:00:00 2025", 653],
            ["bad_entry"]
        ]
    }
    with pytest.raises(ExtractionError):
        parse_oil_price(resp)


def test_parse_oil_price_missing_bars_raises():
    resp = {"no_bars": True}
    with pytest.raises(ExtractionError):
        parse_oil_price(resp)


def test_parse_exchange_rate_success_with_info_rate():
    resp = {
        "date": "2025-04-04",
        "historical": True,
        "info": {"rate": 9.490092, "timestamp": 1743811199},
        "query": {"amount": 1, "from": "USD", "to": "MAD"},
        "result": 9.490092,
        "success": True
    }
    date_iso, rate = parse_exchange_rate(resp)
    assert date_iso == "2025-04-04"
    assert rate == Decimal("9.490092")


def test_parse_exchange_rate_with_timestamp_and_no_date_field():
    resp = {
        "info": {"rate": 3.14, "timestamp": 1712121600},  # 2024-04-02 UTC example
    }
    date_iso, rate = parse_exchange_rate(resp)
    assert rate == Decimal("3.14")
    assert date_iso is not None  # we rely on timestamp to produce a date


def test_parse_exchange_rate_missing_rate_raises():
    resp = {"date": "2025-04-04", "info": {"foo": "bar"}}
    with pytest.raises(ExtractionError):
        parse_exchange_rate(resp)


def test_parse_exchange_rate_missing_date_raises():
    resp = {"result": 1.234}
    # missing date and timestamp -> should raise
    with pytest.raises(ExtractionError):
        parse_exchange_rate(resp)


# Additional tests for parse_oil_price

def test_parse_oil_price_with_integer_price():
    """Test oil price parsing when price is an integer"""
    resp = {
        "bars": [["Wed Aug 13 00:00:00 2025", 640]],
        "marketId": 5910762
    }
    date_iso, price = parse_oil_price(resp)
    assert date_iso == "2025-08-13"
    assert price == Decimal("640")


def test_parse_oil_price_with_float_string():
    """Test oil price parsing when price is a string"""
    resp = {
        "bars": [["Wed Aug 13 00:00:00 2025", "639.99"]],
        "marketId": 5910762
    }
    date_iso, price = parse_oil_price(resp)
    assert date_iso == "2025-08-13"
    assert price == Decimal("639.99")


def test_parse_oil_price_empty_bars_raises():
    """Test that empty bars list raises ExtractionError"""
    resp = {"bars": []}
    with pytest.raises(ExtractionError, match="bars"):
        parse_oil_price(resp)


def test_parse_oil_price_not_dict_raises():
    """Test that non-dict response raises ExtractionError"""
    resp = "not a dict"
    with pytest.raises(ExtractionError, match="not a JSON object"):
        parse_oil_price(resp)


def test_parse_oil_price_bars_not_list_raises():
    """Test that bars as non-list raises ExtractionError"""
    resp = {"bars": "not a list"}
    with pytest.raises(ExtractionError, match="bars"):
        parse_oil_price(resp)


def test_parse_oil_price_invalid_price_raises():
    """Test that invalid price value raises ExtractionError"""
    resp = {
        "bars": [["Wed Aug 13 00:00:00 2025", "not_a_number"]],
        "marketId": 5910762
    }
    with pytest.raises(ExtractionError, match="price"):
        parse_oil_price(resp)


def test_parse_oil_price_single_element_bar_raises():
    """Test that bar with only one element raises ExtractionError"""
    resp = {
        "bars": [["Wed Aug 13 00:00:00 2025"]],
        "marketId": 5910762
    }
    with pytest.raises(ExtractionError, match="malformed"):
        parse_oil_price(resp)


def test_parse_oil_price_unparseable_date_raises():
    """Test that unparseable date raises ExtractionError"""
    resp = {
        "bars": [["invalid date format", 639.25]],
        "marketId": 5910762
    }
    with pytest.raises(ExtractionError, match="unable to parse date"):
        parse_oil_price(resp)


# Additional tests for parse_exchange_rate

def test_parse_exchange_rate_with_result_field():
    """Test exchange rate parsing using result field"""
    resp = {
        "date": "2025-04-04",
        "result": 9.490092,
        "success": True
    }
    date_iso, rate = parse_exchange_rate(resp)
    assert date_iso == "2025-04-04"
    assert rate == Decimal("9.490092")


def test_parse_exchange_rate_with_top_level_rate():
    """Test exchange rate parsing with top-level rate field"""
    resp = {
        "date": "2025-04-04",
        "rate": 9.490092
    }
    date_iso, rate = parse_exchange_rate(resp)
    assert date_iso == "2025-04-04"
    assert rate == Decimal("9.490092")


def test_parse_exchange_rate_not_dict_raises():
    """Test that non-dict response raises ExtractionError"""
    resp = ["not", "a", "dict"]
    with pytest.raises(ExtractionError, match="not a JSON object"):
        parse_exchange_rate(resp)


def test_parse_exchange_rate_rate_priority():
    """Test that info.rate has priority over result"""
    resp = {
        "date": "2025-04-04",
        "info": {"rate": 9.5},
        "result": 9.4,
        "rate": 9.3
    }
    date_iso, rate = parse_exchange_rate(resp)
    assert rate == Decimal("9.5")  # info.rate should be used


def test_parse_exchange_rate_integer_rate():
    """Test exchange rate with integer value"""
    resp = {
        "date": "2025-04-04",
        "info": {"rate": 10}
    }
    date_iso, rate = parse_exchange_rate(resp)
    assert rate == Decimal("10")


def test_parse_exchange_rate_string_rate():
    """Test exchange rate with string value"""
    resp = {
        "date": "2025-04-04",
        "info": {"rate": "9.490092"}
    }
    date_iso, rate = parse_exchange_rate(resp)
    assert rate == Decimal("9.490092")


def test_parse_exchange_rate_invalid_date_format_with_timestamp_fallback():
    """Test that invalid date format falls back to timestamp"""
    resp = {
        "date": "invalid-date-format",
        "info": {"rate": 9.49, "timestamp": 1712121600}
    }
    date_iso, rate = parse_exchange_rate(resp)
    assert date_iso is not None  # Should use timestamp
    assert rate == Decimal("9.49")


def test_parse_exchange_rate_invalid_timestamp_raises():
    """Test that invalid timestamp with no date raises ExtractionError"""
    resp = {
        "info": {"rate": 9.49, "timestamp": "not_a_number"}
    }
    with pytest.raises(ExtractionError, match="unable to extract date"):
        parse_exchange_rate(resp)


# Tests for _parse_date_string_to_iso

def test_parse_date_string_iso_format():
    """Test parsing ISO format date"""
    result = _parse_date_string_to_iso("2025-08-13")
    assert result == "2025-08-13"


def test_parse_date_string_with_time():
    """Test parsing date with time component"""
    result = _parse_date_string_to_iso("Mon Aug 11 00:00:00 2025")
    assert result == "2025-08-11"


def test_parse_date_string_iso_with_time():
    """Test parsing ISO format with time"""
    result = _parse_date_string_to_iso("2025-08-13T14:30:00")
    assert result == "2025-08-13"


def test_parse_date_string_day_month_year():
    """Test parsing date in 'dd Mon yyyy' format"""
    result = _parse_date_string_to_iso("13 Aug 2025")
    assert result == "2025-08-13"


def test_parse_date_string_month_day_year():
    """Test parsing date in 'Mon dd yyyy' format"""
    result = _parse_date_string_to_iso("Aug 13 2025")
    assert result == "2025-08-13"


def test_parse_date_string_non_string_returns_none():
    """Test that non-string input returns None"""
    assert _parse_date_string_to_iso(123) is None
    assert _parse_date_string_to_iso(None) is None
    assert _parse_date_string_to_iso([]) is None


def test_parse_date_string_invalid_format_returns_none():
    """Test that unparseable date string returns None"""
    result = _parse_date_string_to_iso("not a valid date")
    assert result is None


def test_parse_date_string_iso_with_timezone():
    """Test parsing ISO format with timezone (extracts date part)"""
    result = _parse_date_string_to_iso("2025-08-13T14:30:00Z")
    assert result == "2025-08-13"


# Tests for _fetch_json

@patch('src.fetcher.urllib.request.urlopen')
def test_fetch_json_success(mock_urlopen):
    """Test successful JSON fetching"""
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"key": "value"}'
    mock_response.headers.get_content_charset.return_value = "utf-8"
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = None
    mock_urlopen.return_value = mock_response
    
    result = _fetch_json("http://example.com")
    assert result == {"key": "value"}
    # Check that Request object was created and passed to urlopen
    call_args = mock_urlopen.call_args
    assert call_args[1]['timeout'] == 10


@patch('src.fetcher.urllib.request.urlopen')
def test_fetch_json_with_headers(mock_urlopen):
    """Test JSON fetching with custom headers"""
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"key": "value"}'
    mock_response.headers.get_content_charset.return_value = "utf-8"
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = None
    mock_urlopen.return_value = mock_response
    
    headers = {"apikey": "test-key-123", "User-Agent": "TestAgent"}
    result = _fetch_json("http://example.com", headers=headers)
    assert result == {"key": "value"}
    
    # Verify Request object was created with headers
    call_args = mock_urlopen.call_args[0]
    request_obj = call_args[0]
    assert request_obj.get_header('Apikey') == "test-key-123"
    assert request_obj.get_header('User-agent') == "TestAgent"


@patch('src.fetcher.urllib.request.urlopen')
def test_fetch_json_custom_timeout(mock_urlopen):
    """Test JSON fetching with custom timeout"""
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"key": "value"}'
    mock_response.headers.get_content_charset.return_value = "utf-8"
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = None
    mock_urlopen.return_value = mock_response
    
    _fetch_json("http://example.com", timeout=30)
    call_args = mock_urlopen.call_args
    assert call_args[1]['timeout'] == 30


@patch('src.fetcher.urllib.request.urlopen')
def test_fetch_json_with_different_charset(mock_urlopen):
    """Test JSON fetching with different charset"""
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"key": "value"}'
    mock_response.headers.get_content_charset.return_value = "latin-1"
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = None
    mock_urlopen.return_value = mock_response
    
    result = _fetch_json("http://example.com")
    assert result == {"key": "value"}


@patch('src.fetcher.urllib.request.urlopen')
def test_fetch_json_network_error_raises(mock_urlopen):
    """Test that network errors are raised"""
    mock_urlopen.side_effect = Exception("Network error")
    
    with pytest.raises(Exception, match="Network error"):
        _fetch_json("http://example.com")


@patch('src.fetcher.urllib.request.urlopen')
def test_fetch_json_invalid_json_raises(mock_urlopen):
    """Test that invalid JSON raises error"""
    mock_response = MagicMock()
    mock_response.read.return_value = b'not valid json'
    mock_response.headers.get_content_charset.return_value = "utf-8"
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = None
    mock_urlopen.return_value = mock_response
    
    with pytest.raises(json.JSONDecodeError):
        _fetch_json("http://example.com")


# Tests for fetch_oil_data

@patch('src.fetcher._fetch_json')
def test_fetch_oil_data_success(mock_fetch):
    """Test successful oil data fetching"""
    mock_fetch.return_value = {
        "bars": [["Wed Aug 13 00:00:00 2025", 639.25]],
        "marketId": 5910762
    }
    
    date_iso, price = fetch_oil_data("http://oil.example.com")
    assert date_iso == "2025-08-13"
    assert price == Decimal("639.25")
    mock_fetch.assert_called_once_with("http://oil.example.com")


@patch('src.fetcher._fetch_json')
def test_fetch_oil_data_extraction_error(mock_fetch):
    """Test oil data fetching with extraction error"""
    mock_fetch.return_value = {"no_bars": True}
    
    with pytest.raises(ExtractionError):
        fetch_oil_data("http://oil.example.com")


@patch('src.fetcher._fetch_json')
def test_fetch_oil_data_network_error(mock_fetch):
    """Test oil data fetching with network error"""
    mock_fetch.side_effect = Exception("Connection failed")
    
    with pytest.raises(Exception, match="Connection failed"):
        fetch_oil_data("http://oil.example.com")


# Tests for fetch_exchange_data

@patch('src.fetcher._fetch_json')
@patch.dict('os.environ', {}, clear=True)
def test_fetch_exchange_data_success_no_api_key(mock_fetch):
    """Test successful exchange data fetching without API key"""
    mock_fetch.return_value = {
        "date": "2025-11-11",
        "info": {"rate": 9.490092},
        "success": True
    }
    
    date_iso, rate = fetch_exchange_data("http://exchange.example.com?from=USD&to=MAD")
    assert date_iso == "2025-11-11"
    assert rate == Decimal("9.490092")
    
    # Verify URL has date appended and headers are empty
    call_args = mock_fetch.call_args
    assert "date=2025-11-11" in call_args[0][0]
    assert call_args[1]['headers'] == {}


@patch('src.fetcher._fetch_json')
@patch.dict('os.environ', {'EXCHANGE_API_KEY': 'test-key-123'})
def test_fetch_exchange_data_success_with_api_key(mock_fetch):
    """Test successful exchange data fetching with API key from environment"""
    mock_fetch.return_value = {
        "date": "2025-11-11",
        "info": {"rate": 9.490092},
        "success": True
    }
    
    date_iso, rate = fetch_exchange_data("http://exchange.example.com?from=USD&to=MAD")
    assert date_iso == "2025-11-11"
    assert rate == Decimal("9.490092")
    
    # Verify URL has date appended and API key header is set
    call_args = mock_fetch.call_args
    assert "date=2025-11-11" in call_args[0][0]
    assert call_args[1]['headers'] == {"apikey": "test-key-123"}


@patch('src.fetcher._fetch_json')
@patch.dict('os.environ', {}, clear=True)
def test_fetch_exchange_data_url_without_query_params(mock_fetch):
    """Test exchange data fetching appends date to URL without existing params"""
    mock_fetch.return_value = {
        "date": "2025-11-11",
        "info": {"rate": 9.490092},
        "success": True
    }
    
    fetch_exchange_data("http://exchange.example.com/convert")
    
    # Verify URL has date appended with & (current implementation always uses &)
    call_args = mock_fetch.call_args
    url_called = call_args[0][0]
    assert "&date=2025-11-11" in url_called


@patch('src.fetcher._fetch_json')
def test_fetch_exchange_data_extraction_error(mock_fetch):
    """Test exchange data fetching with extraction error"""
    mock_fetch.return_value = {"no_rate": True}
    
    with pytest.raises(ExtractionError):
        fetch_exchange_data("http://exchange.example.com")


@patch('src.fetcher._fetch_json')
def test_fetch_exchange_data_network_error(mock_fetch):
    """Test exchange data fetching with network error"""
    mock_fetch.side_effect = Exception("Timeout")
    
    with pytest.raises(Exception, match="Timeout"):
        fetch_exchange_data("http://exchange.example.com")
#!/usr/bin/env python3
import json
import logging
import urllib.request
import os
import boto3
from decimal import Decimal
from datetime import datetime, timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_secret(secret_name):
    """
    Retrieve a secret from AWS Secrets Manager.
    """
    try:
        client = boto3.client('secretsmanager')
        response = client.get_secret_value(SecretId=secret_name)
        logger.info("get secret response: %s", response)
        return response['SecretString']
    except Exception as e:
        logger.error(f"Error retrieving secret {secret_name}: {e}")
        return None


class ExtractionError(Exception):
    """Raised when a value or date cannot be extracted from an API response."""


def _fetch_json(url, timeout=10, headers=None):
    """
    Internal helper: fetch a URL and parse JSON. Raises on error.
    """
    
    logger.info("fetching URL %s, with header : %s", url, headers is not None)

    try:
        req = urllib.request.Request(url)
        
        # Add User-Agent to avoid being blocked as a bot
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # Add any custom headers
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)
        
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            body = resp.read().decode(charset)
            return json.loads(body)
    except Exception as e:
        logger.error("Error fetching URL %s: %s", url, e)
        raise


def _parse_date_string_to_iso(raw_date):
    """
    Attempt to parse common date formats into ISO date (YYYY-MM-DD).
    Returns ISO date string or None if parsing fails.
    """
    if not isinstance(raw_date, str):
        return None
    fmts = ("%a %b %d %H:%M:%S %Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d %b %Y", "%b %d %Y")
    for fmt in fmts:
        try:
            dt = datetime.strptime(raw_date, fmt)
            return dt.date().isoformat()
        except Exception:
            continue
    try:
        prefix = raw_date.split("T", 1)[0]
        dt = datetime.strptime(prefix, "%Y-%m-%d")
        return dt.date().isoformat()
    except Exception:
        return None


def parse_oil_price(resp):
    """
    Parse the oil API response and return a tuple (date_iso, price_decimal).

    Expected structure:
    {
      "bars": [
        ["Mon Aug 11 00:00:00 2025", 653],
        ["Tue Aug 12 00:00:00 2025", 648.25],
        ["Wed Aug 13 00:00:00 2025", 639.25]
      ],
      "marketId": 5910762
    }

    Raises ExtractionError if date or price cannot be extracted.
    """
    if not isinstance(resp, dict):
        raise ExtractionError("oil response is not a JSON object")

    bars = resp.get("bars")
    if not bars or not isinstance(bars, list):
        raise ExtractionError("oil response missing 'bars' list")

    last = bars[-1]
    if not isinstance(last, (list, tuple)) or len(last) < 2:
        raise ExtractionError("last bar entry malformed")

    raw_date = last[0]
    raw_price = last[1]

    date_iso = _parse_date_string_to_iso(raw_date)
    if date_iso is None:
        raise ExtractionError(f"unable to parse date from oil last bar: {raw_date!r}")

    try:
        price = Decimal(str(raw_price))
    except Exception:
        raise ExtractionError("unable to parse price from oil last bar")

    return date_iso, price


def parse_exchange_rate(resp):
    """
    Parse the exchange rate response and return a tuple (date_iso, rate_decimal).

    Example structure:
    {
      "date": "2025-04-04",
      "historical": true,
      "info": {
        "rate": 9.490092,
        "timestamp": 1743811199
      },
      "query": {...},
      "result": 9.490092,
      "success": true
    }

    Raises ExtractionError if date or rate cannot be extracted.
    """
    if not isinstance(resp, dict):
        raise ExtractionError("exchange response is not a JSON object")

    # Extract rate
    rate = None
    info = resp.get("info")
    if isinstance(info, dict) and "rate" in info:
        try:
            rate = Decimal(str(info["rate"]))
        except Exception:
            rate = None

    if rate is None and "result" in resp:
        try:
            rate = Decimal(str(resp["result"]))
        except Exception:
            rate = None

    if rate is None and "rate" in resp:
        try:
            rate = Decimal(str(resp["rate"]))
        except Exception:
            rate = None

    if rate is None:
        raise ExtractionError("unable to extract exchange rate from response")

    # Extract date
    date_iso = None
    top_date = resp.get("date")
    if isinstance(top_date, str):
        try:
            dt = datetime.strptime(top_date, "%Y-%m-%d")
            date_iso = dt.date().isoformat()
        except Exception:
            date_iso = None

    if date_iso is None and isinstance(info, dict) and "timestamp" in info:
        try:
            ts = int(info["timestamp"])
            dt = datetime.utcfromtimestamp(ts)
            date_iso = dt.date().isoformat()
        except Exception:
            date_iso = None

    if date_iso is None:
        raise ExtractionError("unable to extract date from exchange response")

    return date_iso, rate


# Public API for the app
def fetch_oil_data(url):
    """
    Fetch oil price data from the given URL.
    Returns: (date_iso, price_decimal)
    Raises: ExtractionError or network-related exceptions on failure.
    """
    resp = _fetch_json(url)
    return parse_oil_price(resp)

def get_today_date():
    return datetime.now().strftime("%Y-%m-%d")

def get_yesterday_date():
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

def get_fetch_date():
    return get_yesterday_date()

def fetch_exchange_data(url):
    """
    Fetch exchange rate data from the given URL.
    Appends today's date in format yyyy-MM-dd to the URL.
    Retrieves API key from AWS Secrets Manager.
    Returns: (date_iso, rate_decimal)
    Raises: ExtractionError or network-related exceptions on failure.
    """
    
    # Get today's date in yyyy-MM-dd format
    date = get_fetch_date()
    
    # Append date to URL
    url_with_date = f"{url}&date={date}"
    
    # Get API key from Secrets Manager
    secret_arn = os.environ.get("EXCHANGE_API_KEY_SECRET", "/prod/exchange-api-key")
    api_key = get_secret(secret_arn)
    logger.info("rate api key: %s", api_key)
    
    headers = {}
    if api_key:
        headers["apikey"] = api_key
    
    # Fetch with headers
    resp = _fetch_json(url_with_date, headers=headers)
    return parse_exchange_rate(resp)
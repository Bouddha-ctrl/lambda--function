#!/usr/bin/env python3
import os
import json
from decimal import Decimal

import pytest

import src.app as appmod


def test_lambda_persists_on_date_match(monkeypatch):
    # Arrange: monkeypatch get_store_urls to return the two URLs directly (no SSM call needed)
    def fake_get_store_urls(config_path=None):
        return {"oil_api": "http://oil.example", "exchange_api": "http://fx.example"}

    monkeypatch.setattr(appmod, "get_store_urls", fake_get_store_urls)

    # Mock get_fetch_date to return expected date
    def fake_get_fetch_date():
        return "2025-08-13"
    
    monkeypatch.setattr(appmod, "get_fetch_date", fake_get_fetch_date)

    # Mock the fetch functions to return matching dates
    def fake_fetch_oil_data(url):
        return ("2025-08-13", Decimal("639.25"))
    
    def fake_fetch_exchange_data(url):
        return ("2025-08-13", Decimal("9.49"))

    monkeypatch.setattr(appmod, "fetch_oil_data", fake_fetch_oil_data)
    monkeypatch.setattr(appmod, "fetch_exchange_data", fake_fetch_exchange_data)

    called = {}

    def fake_save_to_dynamodb(table_name, date_str, oil_price, exchange_rate):
        called["args"] = {
            "table_name": table_name,
            "date_str": date_str,
            "oil_price": oil_price,
            "exchange_rate": exchange_rate,
        }

    monkeypatch.setattr(appmod, "save_to_dynamodb", fake_save_to_dynamodb)

    # Act
    result = appmod.lambda_handler({}, None)

    # Assert
    assert result["status"] == "ok"
    assert called.get("args") is not None
    assert called["args"]["date_str"] == "2025-08-13"
    assert called["args"]["oil_price"] == Decimal("639.25")
    assert called["args"]["exchange_rate"] == Decimal("9.49")


def test_lambda_skips_on_date_mismatch(monkeypatch):
    # Arrange: monkeypatch get_store_urls
    def fake_get_store_urls(config_path=None):
        return {"oil_api": "http://oil.example", "exchange_api": "http://fx.example"}

    monkeypatch.setattr(appmod, "get_store_urls", fake_get_store_urls)

    # Mock get_fetch_date to return expected date
    def fake_get_fetch_date():
        return "2025-08-13"
    
    monkeypatch.setattr(appmod, "get_fetch_date", fake_get_fetch_date)

    # Mock oil fetch to return different date (oil price not from expected date)
    def fake_fetch_oil_data(url):
        return ("2025-08-12", Decimal("639.25"))
    
    # Exchange should not be called since oil date doesn't match
    def fake_fetch_exchange_data(url):
        raise AssertionError("fetch_exchange_data should not be called when oil date doesn't match")

    monkeypatch.setattr(appmod, "fetch_oil_data", fake_fetch_oil_data)
    monkeypatch.setattr(appmod, "fetch_exchange_data", fake_fetch_exchange_data)

    persisted = {"called": False}

    def fake_save_to_dynamodb(table_name, date_str, oil_price, exchange_rate):
        persisted["called"] = True

    monkeypatch.setattr(appmod, "save_to_dynamodb", fake_save_to_dynamodb)

    # Act
    result = appmod.lambda_handler({}, None)

    # Assert: should skip exchange fetch and return skipped status
    assert result["status"] == "skipped"
    assert "oil_source_date" in result and "expected_date" in result
    assert result["oil_source_date"] == "2025-08-12"
    assert result["expected_date"] == "2025-08-13"
    assert persisted["called"] is False


def test_lambda_skips_on_exchange_date_mismatch(monkeypatch):
    # Arrange: Test case where oil date matches but exchange date doesn't
    def fake_get_store_urls(config_path=None):
        return {"oil_api": "http://oil.example", "exchange_api": "http://fx.example"}

    monkeypatch.setattr(appmod, "get_store_urls", fake_get_store_urls)

    # Mock get_fetch_date to return expected date
    def fake_get_fetch_date():
        return "2025-08-13"
    
    monkeypatch.setattr(appmod, "get_fetch_date", fake_get_fetch_date)

    # Mock oil fetch to return expected date
    def fake_fetch_oil_data(url):
        return ("2025-08-13", Decimal("639.25"))
    
    # Mock exchange fetch to return different date
    def fake_fetch_exchange_data(url):
        return ("2025-08-12", Decimal("9.49"))

    monkeypatch.setattr(appmod, "fetch_oil_data", fake_fetch_oil_data)
    monkeypatch.setattr(appmod, "fetch_exchange_data", fake_fetch_exchange_data)

    persisted = {"called": False}

    def fake_save_to_dynamodb(table_name, date_str, oil_price, exchange_rate):
        persisted["called"] = True

    monkeypatch.setattr(appmod, "save_to_dynamodb", fake_save_to_dynamodb)

    # Act
    result = appmod.lambda_handler({}, None)

    # Assert: should skip persisting and return skipped status
    assert result["status"] == "skipped"
    assert "exchange_source_date" in result and "expected_date" in result
    assert result["exchange_source_date"] == "2025-08-12"
    assert result["expected_date"] == "2025-08-13"
    assert persisted["called"] is False
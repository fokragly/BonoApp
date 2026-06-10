import pytest
from app.services.portfolio_service import calculate_portfolio, calculate_total


def test_calculate_portfolio_single_holding():
    holdings = [{"ticker": "AL41", "quantity": 100.0}]
    prices = {"AL41": {"price": 43.20, "changePercent": 1.2, "currency": "USD"}}
    result = calculate_portfolio(holdings, prices)
    assert len(result) == 1
    assert result[0]["ticker"] == "AL41"
    assert result[0]["quantity"] == 100.0
    assert result[0]["price"] == 43.20
    assert result[0]["value"] == pytest.approx(4320.0)
    assert result[0]["currency"] == "USD"


def test_calculate_portfolio_missing_price():
    holdings = [{"ticker": "AL41", "quantity": 100.0}]
    prices = {}
    result = calculate_portfolio(holdings, prices)
    assert result[0]["price"] is None
    assert result[0]["value"] is None


def test_calculate_total():
    items = [
        {"value": 4320.0, "currency": "USD"},
        {"value": 6750.0, "currency": "USD"},
        {"value": None, "currency": "USD"},
    ]
    total = calculate_total(items)
    assert total == pytest.approx(11070.0)


def test_calculate_portfolio_percentage():
    holdings = [
        {"ticker": "AL41", "quantity": 100.0},
        {"ticker": "GD30", "quantity": 200.0},
    ]
    prices = {
        "AL41": {"price": 10.0, "changePercent": 0.0, "currency": "USD"},
        "GD30": {"price": 10.0, "changePercent": 0.0, "currency": "USD"},
    }
    result = calculate_portfolio(holdings, prices)
    total = calculate_total(result)
    for item in result:
        item["pct"] = round(item["value"] / total * 100, 1) if total else 0
    assert result[0]["pct"] == pytest.approx(33.3, abs=0.1)
    assert result[1]["pct"] == pytest.approx(66.7, abs=0.1)


def test_calculate_total_all_none():
    items = [{"value": None}, {"value": None}]
    assert calculate_total(items) == 0.0


def test_calculate_portfolio_zero_price():
    """Price of 0.0 is valid and should not be treated as missing."""
    holdings = [{"ticker": "DIST", "quantity": 50.0}]
    prices = {"DIST": {"price": 0.0, "changePercent": 0.0, "currency": "USD"}}
    result = calculate_portfolio(holdings, prices)
    assert result[0]["price"] == 0.0
    assert result[0]["value"] == pytest.approx(0.0)

def calculate_portfolio(holdings: list[dict], prices: dict[str, dict]) -> list[dict]:
    result = []
    for h in holdings:
        ticker = h["ticker"]
        price_data = prices.get(ticker)
        if price_data is not None:
            price = price_data.get("price")
            # price can be 0.0 (valid) — only treat as missing if key absent
            value = round(h["quantity"] * price, 2) if price is not None else None
        else:
            price = None
            value = None
        result.append({
            "ticker": ticker,
            "quantity": h["quantity"],
            "price": price,
            "value": value,
            "changePercent": price_data.get("changePercent") if price_data else None,
            "currency": price_data.get("currency", "USD") if price_data else "USD",
        })
    return result


def calculate_total(items: list[dict]) -> float:
    return sum(item["value"] for item in items if item.get("value") is not None)

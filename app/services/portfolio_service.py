def calculate_portfolio(holdings: list[dict], prices: dict[str, dict]) -> list[dict]:
    result = []
    for h in holdings:
        ticker = h["ticker"]
        price_data = prices.get(ticker)
        if price_data is not None:
            price = price_data.get("price")
            # price can be 0.0 (valid) — only treat as missing if key absent
            value = round(h["quantity"] * price / 100, 2) if price is not None else None
        else:
            price = None
            value = None
        buy_price = h.get("buy_price")
        pnl_pct = None
        pnl_abs = None
        if price is not None and buy_price:
            pnl_pct = round((price - buy_price) / buy_price * 100, 2)
            qty = h["quantity"]
            pnl_abs = round((price - buy_price) / 100 * qty, 2)

        result.append({
            "ticker": ticker,
            "quantity": h["quantity"],
            "price": price,
            "value": value,
            "variation": price_data.get("variation") if price_data else None,
            "currency": price_data.get("currency", "USD") if price_data else "USD",
            "buy_price": buy_price,
            "pnl_pct": pnl_pct,
            "pnl_abs": pnl_abs,
        })
    return result


def calculate_total(items: list[dict]) -> float:
    return sum(item["value"] for item in items if item.get("value") is not None)

from dataclasses import dataclass

@dataclass
class Holding:
    id: int
    ticker: str
    quantity: float
    updated_at: str  # ISO 8601
    buy_price: float | None = None
    buy_date: str | None = None

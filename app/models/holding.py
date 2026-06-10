from dataclasses import dataclass

@dataclass
class Holding:
    id: int
    ticker: str
    quantity: float
    updated_at: str  # ISO 8601

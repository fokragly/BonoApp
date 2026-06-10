from dataclasses import dataclass

@dataclass
class SnapshotEntry:
    id: int
    snapshot_id: str      # UUID that groups all rows from same moment
    timestamp: str        # ISO 8601
    snapshot_type: str    # "open" | "close" | "manual"
    ticker: str
    quantity: float
    price: float
    value: float          # quantity * price
    currency: str         # "USD" | "ARS"

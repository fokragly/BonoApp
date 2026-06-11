from datetime import datetime, timezone
from app.database import get_conn
from app.models.user import User
from app.models.holding import Holding
from app.models.snapshot import SnapshotEntry


# --- Users ---

def create_user(username: str, hashed_password: str, role: str = "viewer") -> None:
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO users (username, hashed_password, role) VALUES (?, ?, ?)",
            (username, hashed_password, role)
        )
        conn.commit()
    finally:
        conn.close()


def get_user_by_username(username: str) -> User | None:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id, username, hashed_password, role FROM users WHERE username = ?",
            (username,)
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return None
    return User(id=row["id"], username=row["username"],
                hashed_password=row["hashed_password"], role=row["role"])


def get_all_users() -> list[User]:
    conn = get_conn()
    try:
        rows = conn.execute("SELECT id, username, hashed_password, role FROM users").fetchall()
    finally:
        conn.close()
    return [User(id=r["id"], username=r["username"],
                 hashed_password=r["hashed_password"], role=r["role"]) for r in rows]


def delete_user(username: str) -> None:
    conn = get_conn()
    try:
        conn.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
    finally:
        conn.close()


def update_user_password(username: str, hashed_password: str) -> None:
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE users SET hashed_password = ? WHERE username = ?",
            (hashed_password, username)
        )
        conn.commit()
    finally:
        conn.close()


# --- Holdings ---

def upsert_holding(ticker: str, quantity: float,
                   buy_price: float | None = None,
                   buy_date: str | None = None) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn = get_conn()
    try:
        conn.execute(
            """INSERT INTO holdings (ticker, quantity, updated_at, buy_price, buy_date)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(ticker) DO UPDATE SET
                 quantity=excluded.quantity,
                 updated_at=excluded.updated_at,
                 buy_price=COALESCE(excluded.buy_price, holdings.buy_price),
                 buy_date=COALESCE(excluded.buy_date, holdings.buy_date)""",
            (ticker, quantity, now, buy_price, buy_date)
        )
        conn.commit()
    finally:
        conn.close()


def get_all_holdings() -> list[Holding]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT id, ticker, quantity, updated_at, buy_price, buy_date FROM holdings"
        ).fetchall()
    finally:
        conn.close()
    return [Holding(id=r["id"], ticker=r["ticker"], quantity=r["quantity"],
                    updated_at=r["updated_at"], buy_price=r["buy_price"],
                    buy_date=r["buy_date"]) for r in rows]


def delete_holding(ticker: str) -> None:
    conn = get_conn()
    try:
        conn.execute("DELETE FROM holdings WHERE ticker = ?", (ticker,))
        conn.commit()
    finally:
        conn.close()


# --- Snapshots ---

def save_snapshot_entries(entries: list[dict]) -> None:
    conn = get_conn()
    try:
        conn.executemany(
            """INSERT INTO snapshots
               (snapshot_id, timestamp, snapshot_type, ticker, quantity, price, value, currency)
               VALUES (:snapshot_id, :timestamp, :snapshot_type, :ticker, :quantity, :price, :value, :currency)""",
            entries
        )
        conn.commit()
    finally:
        conn.close()


def get_snapshot_dates() -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute(
            """SELECT snapshot_id, MIN(timestamp) as timestamp, snapshot_type
               FROM snapshots
               GROUP BY snapshot_id, snapshot_type
               ORDER BY timestamp DESC"""
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_snapshot_totals() -> list[dict]:
    """Returns one row per snapshot with total portfolio value. Single query."""
    conn = get_conn()
    try:
        rows = conn.execute(
            """SELECT snapshot_id, MIN(timestamp) as timestamp, snapshot_type,
                      SUM(value) as total_value
               FROM snapshots
               GROUP BY snapshot_id, snapshot_type
               ORDER BY timestamp ASC"""
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_snapshot_entries(snapshot_id: str) -> list[SnapshotEntry]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM snapshots WHERE snapshot_id = ?", (snapshot_id,)
        ).fetchall()
    finally:
        conn.close()
    return [SnapshotEntry(
        id=r["id"], snapshot_id=r["snapshot_id"], timestamp=r["timestamp"],
        snapshot_type=r["snapshot_type"], ticker=r["ticker"], quantity=r["quantity"],
        price=r["price"], value=r["value"], currency=r["currency"]
    ) for r in rows]


# --- Favorites ---

def get_user_favorites(user_id: int) -> set:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT ticker FROM favorites WHERE user_id = ?", (user_id,)
        ).fetchall()
    finally:
        conn.close()
    return {r["ticker"] for r in rows}


def toggle_favorite(user_id: int, ticker: str) -> bool:
    conn = get_conn()
    try:
        existing = conn.execute(
            "SELECT 1 FROM favorites WHERE user_id = ? AND ticker = ?", (user_id, ticker)
        ).fetchone()
        if existing:
            conn.execute(
                "DELETE FROM favorites WHERE user_id = ? AND ticker = ?", (user_id, ticker)
            )
            conn.commit()
            return False
        else:
            conn.execute(
                "INSERT INTO favorites (user_id, ticker) VALUES (?, ?)", (user_id, ticker)
            )
            conn.commit()
            return True
    finally:
        conn.close()


# --- PPI Config ---

def save_ppi_config(username_ppi: str, password_ppi: str) -> None:
    conn = get_conn()
    try:
        conn.execute(
            """INSERT INTO ppi_config (id, username_ppi, password_ppi) VALUES (1, ?, ?)
               ON CONFLICT(id) DO UPDATE SET username_ppi=excluded.username_ppi, password_ppi=excluded.password_ppi""",
            (username_ppi, password_ppi)
        )
        conn.commit()
    finally:
        conn.close()


def get_ppi_config() -> dict | None:
    conn = get_conn()
    try:
        row = conn.execute("SELECT username_ppi, password_ppi FROM ppi_config WHERE id=1").fetchone()
    finally:
        conn.close()
    return dict(row) if row else None

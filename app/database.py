import sqlite3


def get_conn() -> sqlite3.Connection:
    # Read DB_PATH at runtime so tests can patch app.config.DB_PATH
    from app import config as _config
    conn = sqlite3.connect(_config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    from app import config as _config
    _config.DATA_DIR.mkdir(exist_ok=True)  # ensure data dir exists
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'viewer'
            );

            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT UNIQUE NOT NULL,
                quantity REAL NOT NULL,
                updated_at TEXT NOT NULL,
                buy_price REAL
            );

            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                snapshot_type TEXT NOT NULL,
                ticker TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                value REAL NOT NULL,
                currency TEXT NOT NULL DEFAULT 'USD'
            );

            CREATE TABLE IF NOT EXISTS ppi_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                username_ppi TEXT NOT NULL,
                password_ppi TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                PRIMARY KEY (user_id, ticker),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        # Migrate: add buy_price if missing
        cols = [r[1] for r in conn.execute("PRAGMA table_info(holdings)").fetchall()]
        if "buy_price" not in cols:
            conn.execute("ALTER TABLE holdings ADD COLUMN buy_price REAL")
            conn.commit()
        # Create default admin user if none exists
        from app.auth import hash_password
        existing = conn.execute("SELECT id FROM users WHERE role='admin'").fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO users (username, hashed_password, role) VALUES (?, ?, ?)",
                ("admin", hash_password("admin123"), "admin")
            )
            conn.commit()

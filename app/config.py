import os
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))

DB_PATH = DATA_DIR / "bondsapp.db"
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 horas
PPI_BASE_URL = "https://clientapi.portfoliopersonal.com"
PRICE_CACHE_TTL_SECONDS = 300  # 5 minutos
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"

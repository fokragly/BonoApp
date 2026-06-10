import asyncio
import time
import httpx
from app.config import PPI_BASE_URL, PRICE_CACHE_TTL_SECONDS


class PPIService:
    def __init__(self, username: str, password: str):
        self._username = username
        self._password = password
        self._token: str | None = None
        self._token_expiry: float = 0
        self._cache: dict = {}  # key -> (data, expires_at)
        self._token_lock = asyncio.Lock()

    async def _ensure_token(self):
        if self._token and time.time() < self._token_expiry:
            return
        async with self._token_lock:
            # Double-check after acquiring lock
            if self._token and time.time() < self._token_expiry:
                return
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{PPI_BASE_URL}/v2.0/Account/LoginApi",
                    json={"username": self._username, "password": self._password}
                )
                resp.raise_for_status()
                data = resp.json()
                # PPI may return token under different keys; try all known variants
                self._token = (data.get("accessToken") or data.get("token")
                               or data.get("access_token") or data.get("AccessToken"))
                if not self._token:
                    raise ValueError(
                        f"PPI login succeeded but no token found in response. "
                        f"Known keys: {list(data.keys())}"
                    )
                # Token valid ~24h, refresh every 20h to be safe
                self._token_expiry = time.time() + 20 * 3600

    def _get_cache(self, key: str):
        if key in self._cache:
            data, expires_at = self._cache[key]
            if time.time() < expires_at:
                return data
        return None

    def _set_cache(self, key: str, data):
        self._cache[key] = (data, time.time() + PRICE_CACHE_TTL_SECONDS)

    async def get_bonds(self, instrument_type: str = "BONOS") -> list[dict]:
        cache_key = f"bonds_{instrument_type}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached
        await self._ensure_token()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{PPI_BASE_URL}/v2.0/MarketData/Search",
                params={"type": instrument_type},
                headers={"Authorization": f"Bearer {self._token}"}
            )
            resp.raise_for_status()
            data = resp.json()
        self._set_cache(cache_key, data)
        return data

    async def get_bond_detail(self, ticker: str) -> dict:
        cache_key = f"detail_{ticker}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached
        await self._ensure_token()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{PPI_BASE_URL}/v2.0/MarketData/Current",
                params={"ticker": ticker, "type": "BONOS"},
                headers={"Authorization": f"Bearer {self._token}"}
            )
            resp.raise_for_status()
            data = resp.json()
        self._set_cache(cache_key, data)
        return data

    async def get_price(self, ticker: str) -> float | None:
        detail = await self.get_bond_detail(ticker)
        for key in ("price", "last", "close"):
            val = detail.get(key)
            if val is not None:
                return float(val)
        return None


# Global instance — initialized from DB config at app startup
_instance: PPIService | None = None


def get_ppi_service() -> PPIService | None:
    return _instance


def init_ppi_service(username: str, password: str) -> PPIService:
    global _instance
    _instance = PPIService(username=username, password=password)
    return _instance

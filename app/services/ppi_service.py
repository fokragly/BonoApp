import json
import time
import httpx
from bs4 import BeautifulSoup
from app.config import PRICE_CACHE_TTL_SECONDS

SCRAPE_URL = "https://www.portfoliopersonal.com/Cotizaciones/Bonos"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# currency id -> symbol
_CURRENCY_MAP = {
    10000: "ARS",
    10001: "USD",
    22013: "USD",
}


class PPIService:
    def __init__(self, username: str = "", password: str = ""):
        self._cache: dict = {}

    def _get_cache(self, key: str):
        if key in self._cache:
            data, expires_at = self._cache[key]
            if time.time() < expires_at:
                return data
        return None

    def _set_cache(self, key: str, data):
        self._cache[key] = (data, time.time() + PRICE_CACHE_TTL_SECONDS)

    async def get_bonds(self, instrument_type: str = "BONOS") -> list[dict]:
        cached = self._get_cache("bonds")
        if cached is not None:
            return cached

        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=30) as client:
            resp = await client.get(SCRAPE_URL)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        script_tag = soup.find("script", {"id": "__NEXT_DATA__"})
        if not script_tag:
            return []

        data = json.loads(script_tag.string)
        instruments = data.get("props", {}).get("pageProps", {}).get("instruments", [])

        bonds = []
        for inst in instruments:
            try:
                currency_id = inst.get("currency", {}).get("id", 10000)
                currency = _CURRENCY_MAP.get(currency_id, "ARS")
                maturity = inst.get("expirationDate", "")[:10] if inst.get("expirationDate") else ""

                last_quote_raw = inst.get("lastQuote", "")
                last_quote = last_quote_raw[11:16] if len(last_quote_raw) >= 16 else ""

                bonds.append({
                    "ticker": inst.get("ticker", ""),
                    "name": inst.get("description", ""),
                    "currency": currency,
                    "price": inst.get("lastPrice") or 0,
                    "variation": inst.get("variation") or 0,
                    "tir": inst.get("tir") or 0,
                    "duration": inst.get("modifiedDuration") or 0,
                    "maturity": maturity,
                    "volume": inst.get("volumen") or 0,
                    "opening": inst.get("opening") or 0,
                    "min_day": inst.get("minDay") or 0,
                    "max_day": inst.get("maxDay") or 0,
                    "last_quote": last_quote,
                })
            except Exception:
                continue

        self._set_cache("bonds", bonds)
        return bonds

    async def get_bond_detail(self, ticker: str) -> dict:
        bonds = await self.get_bonds()
        for b in bonds:
            if b["ticker"].upper() == ticker.upper():
                return b
        return {}

    async def get_price(self, ticker: str) -> float | None:
        detail = await self.get_bond_detail(ticker)
        val = detail.get("price")
        if val is not None:
            return float(val)
        return None


def _parse_float(text: str) -> float | None:
    if not text:
        return None
    # Handle Argentine number format: 1.234,56 -> 1234.56
    cleaned = text.strip().replace("\xa0", "").replace(" ", "")
    # If has both dot and comma, it's Argentine format
    if "." in cleaned and "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


# Global instance
_instance: PPIService | None = None


def get_ppi_service() -> PPIService | None:
    return _instance


def init_ppi_service(username: str = "", password: str = "") -> PPIService:
    global _instance
    _instance = PPIService()
    return _instance

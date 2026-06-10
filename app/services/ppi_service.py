import asyncio
import time
import httpx
from bs4 import BeautifulSoup
from app.config import PRICE_CACHE_TTL_SECONDS

SCRAPE_URL = "https://www.portfoliopersonal.com/Cotizaciones/Bonos"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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
        bonds = []

        table = soup.find("table")
        if not table:
            return bonds

        rows = table.find_all("tr")
        for row in rows[1:]:  # skip header
            cols = row.find_all("td")
            if len(cols) < 6:
                continue
            try:
                ticker = cols[0].get_text(strip=True)
                name = cols[1].get_text(strip=True) if len(cols) > 1 else ""
                price_text = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                variation_text = cols[3].get_text(strip=True) if len(cols) > 3 else ""
                tir_text = cols[5].get_text(strip=True) if len(cols) > 5 else ""
                duration_text = cols[9].get_text(strip=True) if len(cols) > 9 else ""

                # Detect currency from price text
                currency = "USD" if "US$" in price_text else "ARS"

                # Clean numeric values
                price = _parse_float(price_text.replace("US$", "").replace("AR$", "").replace("$", ""))
                variation = _parse_float(variation_text.replace("%", ""))
                tir = _parse_float(tir_text.replace("%", ""))
                duration = _parse_float(duration_text)

                if not ticker:
                    continue

                bonds.append({
                    "ticker": ticker,
                    "name": name,
                    "currency": currency,
                    "price": price,
                    "variation": variation,
                    "tir": tir,
                    "duration": duration,
                    "maturity": "",
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

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.ppi_service import PPIService


@pytest.fixture
def ppi():
    return PPIService(username="testuser", password="testpass")


async def test_get_bonds_returns_list(ppi):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"ticker": "AL41", "description": "Bono AL 2041",
         "currency": "USD", "price": 43.20, "changePercent": 1.2,
         "yield": 8.4, "maturityDate": "2041-07-09"}
    ]
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
        with patch.object(ppi, "_ensure_token", new_callable=AsyncMock):
            ppi._token = "faketoken"
            bonds = await ppi.get_bonds()

    assert len(bonds) == 1
    assert bonds[0]["ticker"] == "AL41"


async def test_get_bond_detail(ppi):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ticker": "AL41", "description": "Bono AL 2041",
        "currency": "USD", "price": 43.20, "changePercent": 1.2,
        "yield": 8.4, "maturityDate": "2041-07-09"
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response):
        with patch.object(ppi, "_ensure_token", new_callable=AsyncMock):
            ppi._token = "faketoken"
            detail = await ppi.get_bond_detail("AL41")

    assert detail["ticker"] == "AL41"
    assert detail["price"] == 43.20


async def test_cache_is_used(ppi):
    """Second call should NOT hit the network (cache hit)."""
    mock_response = MagicMock()
    mock_response.json.return_value = [{"ticker": "AL41", "price": 43.20}]
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response) as mock_get:
        with patch.object(ppi, "_ensure_token", new_callable=AsyncMock):
            ppi._token = "faketoken"
            await ppi.get_bonds()
            await ppi.get_bonds()

    assert mock_get.call_count == 1  # only called once, second is from cache

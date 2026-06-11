from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from app.templates_env import templates
from app.dependencies import get_current_user
from app.services import db_service
from app.services.ppi_service import get_ppi_service
from app.services.portfolio_service import calculate_portfolio, calculate_total
from app.models.user import User

router = APIRouter()


async def _build_portfolio_data() -> tuple[list[dict], float, str | None]:
    holdings = db_service.get_all_holdings()
    ppi = get_ppi_service()
    prices = {}
    error = None
    if ppi and holdings:
        for h in holdings:
            try:
                detail = await ppi.get_bond_detail(h.ticker)
                prices[h.ticker] = detail
            except Exception as e:
                error = f"Error cargando {h.ticker}: {e}"
    items = calculate_portfolio(
        [{"ticker": h.ticker, "quantity": h.quantity} for h in holdings],
        prices
    )
    total = calculate_total(items)
    totals_by_currency: dict = {}
    for item in items:
        curr = item.get("currency", "USD")
        if item.get("value") is not None:
            totals_by_currency[curr] = totals_by_currency.get(curr, 0) + item["value"]
        item["pct"] = round(item["value"] / total * 100, 1) if total and item["value"] is not None else 0
    return items, total, totals_by_currency, error


@router.get("/portfolio", response_class=HTMLResponse)
async def portfolio(request: Request, user: User = Depends(get_current_user)):
    items, total, totals_by_currency, error = await _build_portfolio_data()
    return templates.TemplateResponse("portfolio.html", {
        "request": request, "user": user, "items": items,
        "total": total, "totals_by_currency": totals_by_currency,
        "error": error, "active": "portfolio"
    })


@router.get("/portfolio/partial", response_class=HTMLResponse)
async def portfolio_partial(request: Request, user: User = Depends(get_current_user)):
    items, total, totals_by_currency, _ = await _build_portfolio_data()
    return templates.TemplateResponse("partials/portfolio_rows.html",
                                      {"request": request, "items": items, "total": total,
                                       "totals_by_currency": totals_by_currency})

from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, JSONResponse
from app.templates_env import templates
from app.dependencies import get_current_user
from app.services.ppi_service import get_ppi_service
from app.services import db_service
from app.models.user import User

router = APIRouter()


def _sorted_by_favorites(bonds: list, favorites: list) -> list:
    fav_set = set(favorites)
    fav_order = {ticker: i for i, ticker in enumerate(favorites)}
    return sorted(bonds, key=lambda b: (
        (0, fav_order.get(b["ticker"], 999)) if b["ticker"] in fav_set else (1, b["ticker"])
    ))


@router.get("/market", response_class=HTMLResponse)
async def market(request: Request, user: User = Depends(get_current_user),
                 q: str = Query(default="")):
    ppi = get_ppi_service()
    bonds = []
    error = None
    favorites = db_service.get_user_favorites(user.id)
    if ppi:
        try:
            bonds = await ppi.get_bonds()
            if q:
                q_upper = q.upper()
                bonds = [b for b in bonds
                         if q_upper in b.get("ticker", "").upper()
                         or q.lower() in b.get("name", "").lower()]
            bonds = _sorted_by_favorites(bonds, favorites)
        except Exception as e:
            error = f"Error cargando precios: {e}"
    else:
        error = "Servicio no disponible."
    return templates.TemplateResponse("market.html", {
        "request": request, "user": user, "bonds": bonds,
        "error": error, "q": q, "active": "market", "favorites": favorites,
    })


@router.get("/market/partial", response_class=HTMLResponse)
async def market_partial(request: Request, user: User = Depends(get_current_user),
                         q: str = Query(default="")):
    ppi = get_ppi_service()
    bonds = []
    favorites = db_service.get_user_favorites(user.id)
    if ppi:
        try:
            bonds = await ppi.get_bonds()
            if q:
                q_upper = q.upper()
                bonds = [b for b in bonds
                         if q_upper in b.get("ticker", "").upper()
                         or q.lower() in b.get("name", "").lower()]
            bonds = _sorted_by_favorites(bonds, favorites)
        except Exception:
            pass
    return templates.TemplateResponse("partials/bond_rows.html",
                                      {"request": request, "bonds": bonds, "favorites": favorites})


@router.post("/market/favorite/{ticker}", response_class=HTMLResponse)
async def toggle_favorite(request: Request, ticker: str,
                          user: User = Depends(get_current_user)):
    is_fav = db_service.toggle_favorite(user.id, ticker.upper())
    return templates.TemplateResponse("partials/star_btn.html", {
        "request": request, "ticker": ticker.upper(), "is_fav": is_fav,
    })


@router.post("/market/favorites/reorder")
async def reorder_favorites(request: Request, user: User = Depends(get_current_user)):
    data = await request.json()
    tickers = data.get("tickers", [])
    if tickers:
        db_service.reorder_favorites(user.id, tickers)
    return JSONResponse({"ok": True})


@router.get("/market/{ticker}", response_class=HTMLResponse)
async def bond_detail(request: Request, ticker: str,
                      user: User = Depends(get_current_user)):
    ppi = get_ppi_service()
    bond = None
    error = None
    favorites = db_service.get_user_favorites(user.id)
    is_fav = ticker.upper() in favorites
    if ppi:
        try:
            bond = await ppi.get_bond_detail(ticker.upper())
        except Exception as e:
            error = str(e)
    else:
        error = "PPI no configurado."
    return templates.TemplateResponse("market_detail.html", {
        "request": request, "user": user, "bond": bond,
        "ticker": ticker.upper(), "error": error, "active": "market",
        "is_fav": is_fav,
    })

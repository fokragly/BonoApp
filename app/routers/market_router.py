from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import get_current_user
from app.services.ppi_service import get_ppi_service
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/market", response_class=HTMLResponse)
async def market(request: Request, user: User = Depends(get_current_user),
                 q: str = Query(default="")):
    ppi = get_ppi_service()
    bonds = []
    error = None
    if ppi:
        try:
            bonds = await ppi.get_bonds()
            if q:
                q_upper = q.upper()
                bonds = [b for b in bonds
                         if q_upper in b.get("ticker", "").upper()
                         or q.lower() in b.get("name", "").lower()]
        except Exception as e:
            error = f"Error cargando precios: {e}"
    else:
        error = "Servicio no disponible."
    return templates.TemplateResponse("market.html", {
        "request": request, "user": user, "bonds": bonds,
        "error": error, "q": q, "active": "market"
    })


@router.get("/market/partial", response_class=HTMLResponse)
async def market_partial(request: Request, user: User = Depends(get_current_user),
                         q: str = Query(default="")):
    ppi = get_ppi_service()
    bonds = []
    if ppi:
        try:
            bonds = await ppi.get_bonds()
            if q:
                q_upper = q.upper()
                bonds = [b for b in bonds
                         if q_upper in b.get("ticker", "").upper()
                         or q.lower() in b.get("name", "").lower()]
        except Exception:
            pass
    return templates.TemplateResponse("partials/bond_rows.html",
                                      {"request": request, "bonds": bonds})


@router.get("/market/{ticker}", response_class=HTMLResponse)
async def bond_detail(request: Request, ticker: str,
                      user: User = Depends(get_current_user)):
    ppi = get_ppi_service()
    bond = None
    error = None
    if ppi:
        try:
            bond = await ppi.get_bond_detail(ticker.upper())
        except Exception as e:
            error = str(e)
    else:
        error = "PPI no configurado."
    return templates.TemplateResponse("market_detail.html", {
        "request": request, "user": user, "bond": bond,
        "ticker": ticker.upper(), "error": error, "active": "market"
    })

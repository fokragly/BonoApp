from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from app.templates_env import templates
from app.dependencies import require_admin
from app.services import db_service
from app.services.ppi_service import init_ppi_service
from app.models.user import User
from app.auth import hash_password

router = APIRouter(prefix="/admin")


# --- Holdings ---

@router.get("/holdings", response_class=HTMLResponse)
async def admin_holdings(request: Request, user: User = Depends(require_admin)):
    holdings = db_service.get_all_holdings()
    from app.services.ppi_service import get_ppi_service
    prices = {}
    ppi = get_ppi_service()
    if ppi:
        try:
            bonds = await ppi.get_bonds()
            prices = {b["ticker"]: b for b in bonds}
        except Exception:
            pass
    rows = []
    for h in holdings:
        bond = prices.get(h.ticker, {})
        price = bond.get("price") or 0
        currency = bond.get("currency") or "USD"
        value = h.quantity * price
        rows.append({
            "ticker": h.ticker,
            "quantity": h.quantity,
            "updated_at": h.updated_at,
            "price": price,
            "currency": currency,
            "value": value,
        })
    return templates.TemplateResponse("admin_holdings.html", {
        "request": request, "user": user, "holdings": rows, "active": "admin"
    })


@router.post("/holdings/upsert")
def upsert_holding(request: Request, user: User = Depends(require_admin),
                   ticker: str = Form(), quantity: float = Form(),
                   buy_price: float | None = Form(default=None),
                   buy_date: str | None = Form(default=None)):
    if quantity < 0:
        return RedirectResponse(url="/admin/holdings?error=negative-qty", status_code=303)
    db_service.upsert_holding(ticker.upper().strip(), quantity, buy_price, buy_date or None)
    return RedirectResponse(url="/admin/holdings", status_code=303)


@router.post("/holdings/delete")
def delete_holding(request: Request, user: User = Depends(require_admin),
                   ticker: str = Form()):
    db_service.delete_holding(ticker)
    return RedirectResponse(url="/admin/holdings", status_code=303)


# --- Users ---

@router.get("/users", response_class=HTMLResponse)
def admin_users(request: Request, user: User = Depends(require_admin)):
    users = db_service.get_all_users()
    return templates.TemplateResponse("admin_users.html", {
        "request": request, "user": user, "users": users, "active": "admin"
    })


@router.post("/users/create")
def create_user(request: Request, user: User = Depends(require_admin),
                username: str = Form(), password: str = Form(),
                role: str = Form(default="viewer")):
    if role not in ("viewer", "admin"):
        role = "viewer"
    try:
        db_service.create_user(username.strip(), hash_password(password), role)
    except Exception:
        return RedirectResponse(url="/admin/users?error=duplicate", status_code=303)
    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/users/reset-password")
def reset_password(request: Request, user: User = Depends(require_admin),
                   username: str = Form(), new_password: str = Form()):
    if not new_password.strip():
        return RedirectResponse(url="/admin/users?error=empty-password", status_code=303)
    db_service.update_user_password(username, hash_password(new_password))
    return RedirectResponse(url="/admin/users", status_code=303)


@router.post("/users/delete")
def delete_user(request: Request, user: User = Depends(require_admin),
                username: str = Form()):
    if username == user.username:
        return RedirectResponse(url="/admin/users?error=self-delete", status_code=303)
    db_service.delete_user(username)
    return RedirectResponse(url="/admin/users", status_code=303)


# --- PPI Config ---

@router.get("/config", response_class=HTMLResponse)
def admin_config(request: Request, user: User = Depends(require_admin)):
    config = db_service.get_ppi_config()
    return templates.TemplateResponse("admin_config.html", {
        "request": request, "user": user, "config": config, "active": "admin"
    })


@router.post("/config/save")
def save_config(request: Request, user: User = Depends(require_admin),
                username_ppi: str = Form(), password_ppi: str = Form(default="")):
    username_ppi = username_ppi.strip()
    existing = db_service.get_ppi_config()
    # Keep existing password if none provided
    final_password = password_ppi if password_ppi else (existing["password_ppi"] if existing else "")
    if final_password:
        db_service.save_ppi_config(username_ppi, final_password)
        init_ppi_service(username_ppi, final_password)
    return RedirectResponse(url="/admin/config?saved=1", status_code=303)

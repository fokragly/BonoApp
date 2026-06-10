from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.auth import verify_password, create_access_token
from app.services import db_service
from app.config import COOKIE_SECURE

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
def login(request: Request, username: str = Form(), password: str = Form()):
    user = db_service.get_user_by_username(username)
    if user is None or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Usuario o contraseña incorrectos"},
            status_code=401
        )
    token = create_access_token({"sub": user.username, "role": user.role})
    resp = RedirectResponse(url="/market", status_code=303)
    resp.set_cookie("access_token", token, httponly=True, samesite="lax", secure=COOKIE_SECURE)
    return resp


@router.post("/logout")
def logout():
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie("access_token")
    return resp

from fastapi import Request, HTTPException, status
from app.auth import decode_access_token
from app.services import db_service
from app.models.user import User


def get_current_user(request: Request) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER,
                            headers={"Location": "/login"})
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER,
                            headers={"Location": "/login"})
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER,
                            headers={"Location": "/login"})
    user = db_service.get_user_by_username(username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER,
                            headers={"Location": "/login"})
    return user


def require_admin(request: Request) -> User:
    user = get_current_user(request)
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo el admin puede hacer esto")
    return user

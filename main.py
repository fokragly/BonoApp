from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from app.database import init_db
from app.routers import auth_router, market_router, portfolio_router, history_router, admin_router
from app.services.ppi_service import init_ppi_service
from app.services import db_service
from app.scheduler import start_scheduler, stop_scheduler
import app.templates_env  # noqa: F401 — registers Jinja2 filters on shared templates instance


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_ppi_service()
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router.router)
app.include_router(market_router.router)
app.include_router(portfolio_router.router)
app.include_router(history_router.router)
app.include_router(admin_router.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return RedirectResponse(url="/market")

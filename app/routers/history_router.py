from fastapi import APIRouter, Request, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.dependencies import get_current_user
from app.services import db_service
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/history", response_class=HTMLResponse)
def history(request: Request, user: User = Depends(get_current_user),
            snapshot_id: str = Query(default="")):
    dates = db_service.get_snapshot_dates()
    selected_entries = []
    selected_snap = None
    total = 0.0

    if snapshot_id:
        selected_entries = db_service.get_snapshot_entries(snapshot_id)
        total = sum(e.value for e in selected_entries)
        selected_snap = next((d for d in dates if d["snapshot_id"] == snapshot_id), None)
        if selected_snap is None:
            # Invalid snapshot_id — redirect to default (most recent)
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/history", status_code=303)
    elif dates:
        # Show most recent by default
        snapshot_id = dates[0]["snapshot_id"]
        selected_entries = db_service.get_snapshot_entries(snapshot_id)
        total = sum(e.value for e in selected_entries)
        selected_snap = dates[0]

    # Data for evolution chart: one point per snapshot (total value) — single query
    snapshot_totals = db_service.get_snapshot_totals()  # already in chronological order (ASC)
    chart_data = [
        {
            "label": s["timestamp"][:10] + " " + ("Apertura" if s["snapshot_type"] == "open" else "Cierre"),
            "value": round(s["total_value"], 2)
        }
        for s in snapshot_totals
    ]

    return templates.TemplateResponse("history.html", {
        "request": request, "user": user, "dates": dates,
        "selected_entries": selected_entries, "selected_snap": selected_snap,
        "total": total, "snapshot_id": snapshot_id,
        "chart_data": chart_data, "active": "history"
    })

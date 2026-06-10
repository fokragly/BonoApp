import uuid
import logging
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="America/Argentina/Buenos_Aires")


async def take_snapshot(snapshot_type: str):
    """Take a portfolio snapshot of all current holdings at current prices."""
    from app.services import db_service
    from app.services.ppi_service import get_ppi_service

    holdings = db_service.get_all_holdings()
    if not holdings:
        logger.info("Snapshot skipped: no holdings configured")
        return

    ppi = get_ppi_service()
    if not ppi:
        logger.warning("Snapshot skipped: PPI service not initialized")
        return

    snap_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    entries = []

    for h in holdings:
        try:
            detail = await ppi.get_bond_detail(h.ticker)
        except Exception as e:
            logger.warning(f"Skipping {h.ticker} in snapshot: {e}")
            continue

        price = await ppi.get_price(h.ticker)
        if price is None:
            logger.warning(f"Skipping {h.ticker} in snapshot: price is None")
            continue

        currency = detail.get("currency", "USD")
        entries.append({
            "snapshot_id": snap_id,
            "timestamp": now,
            "snapshot_type": snapshot_type,
            "ticker": h.ticker,
            "quantity": h.quantity,
            "price": price,
            "value": round(h.quantity * price, 2),
            "currency": currency,
        })

    if entries:
        db_service.save_snapshot_entries(entries)
        logger.info(f"Snapshot {snapshot_type} saved: {len(entries)} entries, id={snap_id}")


def start_scheduler():
    # Market open: Monday-Friday 11:00 Argentina time
    scheduler.add_job(
        take_snapshot,
        CronTrigger(day_of_week="mon-fri", hour=11, minute=0),
        args=["open"],
        id="snapshot_open",
        replace_existing=True
    )
    # Market close: Monday-Friday 17:00 Argentina time
    scheduler.add_job(
        take_snapshot,
        CronTrigger(day_of_week="mon-fri", hour=17, minute=0),
        args=["close"],
        id="snapshot_close",
        replace_existing=True
    )
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started: snapshots at 11:00 and 17:00 ARS (mon-fri)")
    else:
        logger.info("Scheduler already running, jobs updated")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

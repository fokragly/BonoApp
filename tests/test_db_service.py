import pytest
from app.services import db_service


def test_create_and_get_user(tmp_db):
    db_service.create_user("alice", "hashedpw", "viewer")
    user = db_service.get_user_by_username("alice")
    assert user is not None
    assert user.username == "alice"
    assert user.role == "viewer"


def test_get_user_not_found(tmp_db):
    user = db_service.get_user_by_username("nobody")
    assert user is None


def test_upsert_holding(tmp_db):
    db_service.upsert_holding("AL41", 100.0)
    holdings = db_service.get_all_holdings()
    assert len(holdings) == 1
    assert holdings[0].ticker == "AL41"
    assert holdings[0].quantity == 100.0


def test_upsert_holding_updates_quantity(tmp_db):
    db_service.upsert_holding("AL41", 100.0)
    db_service.upsert_holding("AL41", 200.0)
    holdings = db_service.get_all_holdings()
    assert len(holdings) == 1
    assert holdings[0].quantity == 200.0


def test_delete_holding(tmp_db):
    db_service.upsert_holding("AL41", 100.0)
    db_service.delete_holding("AL41")
    assert db_service.get_all_holdings() == []


def test_save_and_get_snapshots(tmp_db):
    import uuid
    snap_id = str(uuid.uuid4())
    db_service.save_snapshot_entries([
        {"snapshot_id": snap_id, "timestamp": "2026-06-10T11:00:00",
         "snapshot_type": "open", "ticker": "AL41",
         "quantity": 100.0, "price": 43.20, "value": 4320.0, "currency": "USD"},
    ])
    snaps = db_service.get_snapshot_dates()
    assert len(snaps) == 1
    assert snaps[0]["snapshot_id"] == snap_id


def test_get_snapshot_entries(tmp_db):
    import uuid
    snap_id = str(uuid.uuid4())
    db_service.save_snapshot_entries([
        {"snapshot_id": snap_id, "timestamp": "2026-06-10T11:00:00",
         "snapshot_type": "open", "ticker": "AL41",
         "quantity": 100.0, "price": 43.20, "value": 4320.0, "currency": "USD"},
        {"snapshot_id": snap_id, "timestamp": "2026-06-10T11:00:00",
         "snapshot_type": "open", "ticker": "GD30",
         "quantity": 50.0, "price": 67.50, "value": 3375.0, "currency": "USD"},
    ])
    entries = db_service.get_snapshot_entries(snap_id)
    assert len(entries) == 2
    tickers = {e.ticker for e in entries}
    assert tickers == {"AL41", "GD30"}
    al41 = next(e for e in entries if e.ticker == "AL41")
    assert al41.price == 43.20
    assert al41.value == 4320.0
    assert al41.currency == "USD"


def test_get_snapshot_totals(tmp_db):
    import uuid
    snap_id = str(uuid.uuid4())
    db_service.save_snapshot_entries([
        {"snapshot_id": snap_id, "timestamp": "2026-06-10T11:00:00",
         "snapshot_type": "open", "ticker": "AL41",
         "quantity": 100.0, "price": 43.20, "value": 4320.0, "currency": "USD"},
        {"snapshot_id": snap_id, "timestamp": "2026-06-10T11:00:00",
         "snapshot_type": "open", "ticker": "GD30",
         "quantity": 50.0, "price": 67.50, "value": 3375.0, "currency": "USD"},
    ])
    totals = db_service.get_snapshot_totals()
    assert len(totals) == 1
    assert totals[0]["snapshot_id"] == snap_id
    assert totals[0]["total_value"] == pytest.approx(7695.0)


def test_ppi_config(tmp_db):
    assert db_service.get_ppi_config() is None
    db_service.save_ppi_config("user@ppi.com", "secret123")
    config = db_service.get_ppi_config()
    assert config["username_ppi"] == "user@ppi.com"
    assert config["password_ppi"] == "secret123"

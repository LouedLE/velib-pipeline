import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest

from velib_pipeline.ingest import flatten_information, flatten_status, write_snapshot

FIXTURES = Path(__file__).parent / "fixtures"
SNAPSHOT_AT = datetime(2026, 10, 20, 8, 0, tzinfo=UTC)


def load(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text())


def test_flatten_status_splits_bike_types():
    df = flatten_status(load("station_status"), SNAPSHOT_AT)
    first = df.iloc[0]
    assert first["num_mechanical_available"] == 23
    assert first["num_ebike_available"] == 3
    assert first["num_bikes_available"] == 26


def test_flatten_status_handles_empty_bike_types():
    df = flatten_status(load("station_status"), SNAPSHOT_AT)
    empty = df.iloc[1]
    assert empty["num_bikes_available"] == 0
    assert pd.isna(empty["num_mechanical_available"])


def test_station_id_is_string():
    # Les identifiants dépassent 2^31 : on les garde en texte pour éviter toute perte.
    df = flatten_status(load("station_status"), SNAPSHOT_AT)
    assert df["station_id"].tolist() == ["213688169", "19179944124"]


def test_flatten_information_columns():
    df = flatten_information(load("station_information"), SNAPSHOT_AT)
    assert set(df.columns) == {"station_id", "station_code", "name", "lat", "lon", "capacity", "snapshot_at"}
    assert df["capacity"].tolist() == [35, 28]


def test_write_snapshot_partitions_by_date(tmp_path):
    df = flatten_status(load("station_status"), SNAPSHOT_AT)
    path = write_snapshot(df, tmp_path, "station_status", SNAPSHOT_AT)
    assert path == tmp_path / "bronze" / "station_status" / "date=2026-10-20" / "080000.parquet"
    assert len(pd.read_parquet(path)) == 2


def test_fetch_feed_rejects_unexpected_payload(monkeypatch):
    from velib_pipeline import ingest

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"error": "maintenance"}

    class FakeSession:
        def get(self, *args, **kwargs):
            return FakeResponse()

    with pytest.raises(ValueError):
        ingest.fetch_feed("station_status", FakeSession())

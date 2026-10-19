"""Collecte un instantané des flux GBFS Vélib Métropole et l'écrit en Parquet (couche bronze).

Chaque exécution produit deux fichiers :
    data/bronze/station_status/date=YYYY-MM-DD/HHMMSS.parquet
    data/bronze/station_information/date=YYYY-MM-DD/HHMMSS.parquet

La couche bronze garde les champs de la source tels quels, plus l'horodatage de collecte.
Les conversions de types et le nettoyage se font dans dbt (couche silver).
"""

from __future__ import annotations

import argparse
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests

BASE_URL = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole"
FEEDS = ("station_status", "station_information")
TIMEOUT_S = 30

log = logging.getLogger(__name__)


def fetch_feed(feed: str, session: requests.Session | None = None) -> dict[str, Any]:
    """Télécharge un flux GBFS et renvoie le JSON décodé."""
    http = session or requests.Session()
    response = http.get(f"{BASE_URL}/{feed}.json", timeout=TIMEOUT_S)
    response.raise_for_status()
    payload = response.json()
    if "data" not in payload or "stations" not in payload["data"]:
        raise ValueError(f"Flux {feed} inattendu : clé data.stations absente")
    return payload


def _split_bike_types(types: list[dict[str, int]] | None) -> tuple[int | None, int | None]:
    """Le flux encode les types de vélos en liste de dicts : [{"mechanical": 3}, {"ebike": 1}]."""
    if not types:
        return None, None
    merged: dict[str, int] = {}
    for item in types:
        merged.update(item)
    return merged.get("mechanical"), merged.get("ebike")


def flatten_status(payload: dict[str, Any], snapshot_at: datetime) -> pd.DataFrame:
    rows = []
    for station in payload["data"]["stations"]:
        mechanical, ebike = _split_bike_types(station.get("num_bikes_available_types"))
        rows.append(
            {
                "station_id": str(station["station_id"]),
                "station_code": station.get("stationCode"),
                "num_bikes_available": station.get("num_bikes_available"),
                "num_mechanical_available": mechanical,
                "num_ebike_available": ebike,
                "num_docks_available": station.get("num_docks_available"),
                "is_installed": station.get("is_installed"),
                "is_renting": station.get("is_renting"),
                "is_returning": station.get("is_returning"),
                "last_reported": station.get("last_reported"),
                "snapshot_at": snapshot_at,
            }
        )
    return pd.DataFrame(rows)


def flatten_information(payload: dict[str, Any], snapshot_at: datetime) -> pd.DataFrame:
    rows = [
        {
            "station_id": str(station["station_id"]),
            "station_code": station.get("stationCode"),
            "name": station.get("name"),
            "lat": station.get("lat"),
            "lon": station.get("lon"),
            "capacity": station.get("capacity"),
            "snapshot_at": snapshot_at,
        }
        for station in payload["data"]["stations"]
    ]
    return pd.DataFrame(rows)


def write_snapshot(df: pd.DataFrame, data_dir: Path, feed: str, snapshot_at: datetime) -> Path:
    target = data_dir / "bronze" / feed / f"date={snapshot_at:%Y-%m-%d}" / f"{snapshot_at:%H%M%S}.parquet"
    target.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(target, index=False, compression="zstd")
    return target


def run(data_dir: Path) -> None:
    snapshot_at = datetime.now(UTC).replace(microsecond=0)
    with requests.Session() as session:
        status = flatten_status(fetch_feed("station_status", session), snapshot_at)
        info = flatten_information(fetch_feed("station_information", session), snapshot_at)
    for feed, df in (("station_status", status), ("station_information", info)):
        path = write_snapshot(df, data_dir, feed, snapshot_at)
        log.info("%s : %d stations -> %s", feed, len(df), path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run(args.data_dir)


if __name__ == "__main__":
    main()

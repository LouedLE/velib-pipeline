"""Génère des instantanés synthétiques pour faire tourner le pipeline sans attendre la collecte.

Sert en CI et pour tester en local. Les données produites suivent le schéma bronze réel
mais les valeurs sont simulées : ne pas en tirer de conclusions sur le réseau Vélib.
"""

from __future__ import annotations

import argparse
import math
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

from velib_pipeline.ingest import write_snapshot

# Centre de Paris et rayon approximatif du réseau, en degrés
CENTER = (48.8566, 2.3522)
SPREAD = (0.06, 0.09)


def _stations(n: int, rng: random.Random) -> pd.DataFrame:
    rows = []
    for i in range(n):
        capacity = rng.choice([20, 25, 30, 35, 40, 50])
        rows.append(
            {
                "station_id": str(100_000 + i),
                "station_code": f"{rng.randint(1, 20):02d}{i:03d}",
                "name": f"Station démo {i:03d}",
                "lat": CENTER[0] + rng.uniform(-SPREAD[0], SPREAD[0]),
                "lon": CENTER[1] + rng.uniform(-SPREAD[1], SPREAD[1]),
                "capacity": capacity,
            }
        )
    return pd.DataFrame(rows)


def _fill_rate(hour: float, is_residential: bool) -> float:
    """Taux de remplissage simulé : les zones résidentielles se vident le matin."""
    wave = math.sin((hour - 8) / 24 * 2 * math.pi)
    return 0.5 + (0.4 if is_residential else -0.4) * -wave


def generate(data_dir: Path, days: int, stations: int, seed: int) -> None:
    rng = random.Random(seed)
    info = _stations(stations, rng)
    residential = {sid: rng.random() < 0.5 for sid in info["station_id"]}
    start = datetime.now(UTC).replace(minute=0, second=0, microsecond=0) - timedelta(days=days)

    for step in range(days * 24):
        snapshot_at = start + timedelta(hours=step)
        local_hour = (snapshot_at.hour + 1) % 24  # approximation de l'heure de Paris
        rows = []
        for station in info.itertuples():
            rate = _fill_rate(local_hour, residential[station.station_id]) + rng.gauss(0, 0.15)
            bikes = max(0, min(station.capacity, round(rate * station.capacity)))
            ebike = rng.randint(0, bikes)
            stale = rng.random() < 0.02
            last_reported = snapshot_at - timedelta(hours=3 if stale else 0, minutes=rng.randint(0, 9))
            rows.append(
                {
                    "station_id": station.station_id,
                    "station_code": station.station_code,
                    "num_bikes_available": bikes,
                    "num_mechanical_available": bikes - ebike,
                    "num_ebike_available": ebike,
                    "num_docks_available": station.capacity - bikes,
                    "is_installed": 1,
                    "is_renting": 1,
                    "is_returning": 1,
                    "last_reported": int(last_reported.timestamp()),
                    "snapshot_at": snapshot_at,
                }
            )
        write_snapshot(pd.DataFrame(rows), data_dir, "station_status", snapshot_at)

    write_snapshot(info.assign(snapshot_at=start), data_dir, "station_information", start)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--stations", type=int, default=60)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    generate(args.data_dir, args.days, args.stations, args.seed)


if __name__ == "__main__":
    main()

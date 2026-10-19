"""Exporte les tables gold de la base DuckDB vers des fichiers Parquet lus par le dashboard."""

from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

GOLD_TABLES = ("dim_station", "mart_station_reliability", "mart_hourly_profile", "mart_network_timeseries")


def export(db_path: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(db_path), read_only=True) as con:
        for table in GOLD_TABLES:
            target = out_dir / f"{table}.parquet"
            con.execute(f"COPY main_gold.{table} TO '{target}' (FORMAT parquet, COMPRESSION zstd)")
            print(f"{table} -> {target}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("dbt/velib.duckdb"))
    parser.add_argument("--out", type=Path, default=Path("data/gold"))
    args = parser.parse_args()
    export(args.db, args.out)


if __name__ == "__main__":
    main()

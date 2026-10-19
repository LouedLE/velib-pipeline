"""Dashboard Streamlit : fiabilité des stations Vélib à partir des tables gold."""

from __future__ import annotations

import io
import os
from pathlib import Path

import altair as alt
import pandas as pd
import requests
import streamlit as st

# En production, les tables gold sont lues sur la branche `data` du dépôt.
REMOTE_BASE = os.getenv(
    "VELIB_GOLD_URL",
    "https://raw.githubusercontent.com/LouedLE/velib-pipeline/data/gold",
)
LOCAL_DIR = Path(__file__).resolve().parents[1] / "data" / "gold"

st.set_page_config(page_title="Vélib : stations vides ou pleines", layout="wide")


@st.cache_data(ttl=3600)
def load(table: str) -> pd.DataFrame:
    local = LOCAL_DIR / f"{table}.parquet"
    if local.exists():
        return pd.read_parquet(local)
    response = requests.get(f"{REMOTE_BASE}/{table}.parquet", timeout=30)
    response.raise_for_status()
    return pd.read_parquet(io.BytesIO(response.content))


reliability = load("mart_station_reliability")
hourly = load("mart_hourly_profile")
network = load("mart_network_timeseries")

st.title("Vélib Métropole : où trouver un vélo, et quand")
first, last = network["snapshot_at_paris"].min(), network["snapshot_at_paris"].max()
st.caption(
    f"{len(network)} collectes horaires du {first:%d/%m/%Y} au {last:%d/%m/%Y}. "
    "Une station est inutilisable quand elle est vide (pas de vélo) ou pleine (pas de borne libre)."
)

col1, col2, col3 = st.columns(3)
col1.metric("Stations suivies", f"{len(reliability)}")
col2.metric("Temps moyen à vide", f"{reliability['pct_empty'].mean():.1%}")
col3.metric("Temps moyen pleine", f"{reliability['pct_full'].mean():.1%}")

st.subheader("Carte des stations")
threshold = st.slider("Afficher les stations inutilisables plus de X % du temps", 0, 100, 0, step=5)
shown = reliability[reliability["pct_unusable"] >= threshold / 100].copy()
shown["color"] = shown["pct_unusable"].apply(
    lambda p: "#d7301f" if p >= 0.3 else "#fc8d59" if p >= 0.15 else "#1a9850"
)
st.map(shown, latitude="latitude", longitude="longitude", color="color", size=40)
st.caption("Rouge : inutilisable 30 % du temps ou plus. Orange : 15 à 30 %. Vert : moins de 15 %.")

st.subheader("Les 15 stations les moins fiables")
worst = reliability.nlargest(15, "pct_unusable")[
    ["station_name", "capacity", "pct_empty", "pct_full", "pct_unusable", "n_snapshots"]
]
st.dataframe(
    worst.rename(
        columns={
            "station_name": "Station",
            "capacity": "Capacité",
            "pct_empty": "Vide",
            "pct_full": "Pleine",
            "pct_unusable": "Inutilisable",
            "n_snapshots": "Collectes",
        }
    ).style.format({"Vide": "{:.0%}", "Pleine": "{:.0%}", "Inutilisable": "{:.0%}"}),
    hide_index=True,
    width="stretch",
)

st.subheader("Profil horaire d'une station")
names = reliability.set_index("station_id")["station_name"].sort_values()
station_id = st.selectbox("Station", names.index, format_func=names.get)
profile = hourly[hourly["station_id"] == station_id]
chart = (
    alt.Chart(profile)
    .mark_line(point=True)
    .encode(
        x=alt.X("hour_paris:O", title="Heure (Paris)"),
        y=alt.Y("avg_fill_rate:Q", title="Taux de remplissage moyen", axis=alt.Axis(format="%")),
        color=alt.Color("day_type:N", title=None),
        tooltip=["day_type", "hour_paris", "avg_bikes_available", "pct_empty", "pct_full"],
    )
)
st.altair_chart(chart, width="stretch")

st.subheader("Vélos disponibles sur tout le réseau")
series = network.melt(
    id_vars="snapshot_at_paris",
    value_vars=["bikes_available", "ebike_available"],
    var_name="type",
    value_name="vélos",
)
series["type"] = series["type"].map({"bikes_available": "Tous", "ebike_available": "Électriques"})
st.altair_chart(
    alt.Chart(series)
    .mark_line()
    .encode(x=alt.X("snapshot_at_paris:T", title=None), y="vélos:Q", color=alt.Color("type:N", title=None)),
    width="stretch",
)

st.caption("Source : flux GBFS open data Vélib Métropole. Code : github.com/LouedLE/velib-pipeline")

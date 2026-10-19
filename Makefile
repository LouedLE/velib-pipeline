.PHONY: install demo collect build export dashboard test lint all

install:
	uv sync --all-extras

demo:        ## Génère 7 jours de données simulées
	uv run velib-demo --days 7

collect:     ## Collecte un instantané réel du réseau Vélib
	uv run velib-ingest

build:       ## Transformations et tests dbt
	cd dbt && uv run dbt build --profiles-dir .

export:      ## Exporte les tables gold en Parquet
	uv run velib-export

dashboard:
	uv run streamlit run dashboard/app.py

test:
	uv run pytest -q

lint:
	uv run ruff check .

all: demo build export

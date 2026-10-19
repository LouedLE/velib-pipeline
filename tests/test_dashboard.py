from pathlib import Path

import pytest

GOLD = Path(__file__).resolve().parents[1] / "data" / "gold"


@pytest.mark.skipif(not (GOLD / "mart_station_reliability.parquet").exists(), reason="tables gold absentes")
def test_dashboard_renders_without_error():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(GOLD.parents[1] / "dashboard" / "app.py"), default_timeout=60).run()
    assert not app.exception
    assert len(app.metric) == 3

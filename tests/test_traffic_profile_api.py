"""
Stage 6-2: GET /api/traffic/profile. No network, no Solar client involved.

The payload is what the frontend simulator (6-3) will consume:
  meta + available_hours + hours[{hour, volume, arrival_rate_per_sec}]
volume is demand (veh/hour); arrival_rate_per_sec is the spawn rate (veh/sec per lane).
No queue values exist anywhere in this payload.
"""
import csv
import json
from pathlib import Path

import pytest

import app.main as main_module
from app.traffic_data import APPROACHES, DEMAND_NOTE

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_META = ROOT / "data" / "sample_seoul_traffic_history.meta.json"
SEOUL_HEADER = ["지점번호", "년월일", "시간", "유입유출 구분", "차로번호", "교통량"]


@pytest.fixture(autouse=True)
def default_profile_env(monkeypatch):
    """Use the shipped sample unless a test overrides TRAFFIC_PROFILE_META."""
    monkeypatch.delenv("TRAFFIC_PROFILE_META", raising=False)
    main_module.get_traffic_profile.cache_clear()
    yield
    main_module.get_traffic_profile.cache_clear()


def _write_partial_day_profile(tmp_path: Path, hours=(7, 8, 9)) -> Path:
    csv_path = tmp_path / "partial.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(SEOUL_HEADER)
        for site in ("P-N", "P-S", "P-E", "P-W"):
            for h in hours:
                w.writerow([site, "20250514", f"{h:02d}", "유입", 1, 300 + h])
    meta_path = tmp_path / "partial.meta.json"
    meta_path.write_text(json.dumps({
        "csv": "partial.csv",
        "site_id": "P-X",
        "site_name": "partial",
        "site_to_approach": {"P-N": "N", "P-S": "S", "P-E": "E", "P-W": "W"},
    }, ensure_ascii=False), encoding="utf-8")
    return meta_path


def _all_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _all_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _all_keys(v)


# ==========================================================================
# Default sample profile
# ==========================================================================
class TestProfileEndpoint:
    def test_returns_sample_profile(self, client):
        resp = client.get("/api/traffic/profile")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/json")
        body = resp.json()
        assert set(body) == {"meta", "available_hours", "hours"}

    def test_meta_fields_for_the_frontend(self, client):
        meta = client.get("/api/traffic/profile").json()["meta"]
        assert set(meta) == {
            "site_id", "site_name", "date", "weekday", "source", "license", "unit", "lanes",
            "profile_file", "approach_naming", "note",
        }
        assert meta["site_id"] == "DEMO-X"
        assert meta["date"] == "20250514" and meta["weekday"] == "Wed"
        assert meta["unit"] == "veh_per_hour"
        assert meta["lanes"] == {"N": 3, "S": 3, "E": 2, "W": 2}
        assert meta["profile_file"] == SAMPLE_META.name
        assert meta["note"] == DEMAND_NOTE
        assert "북측" in meta["approach_naming"]
        assert "15056899" in meta["source"]

    def test_hours_carry_volume_and_arrival_rate_per_approach(self, client):
        body = client.get("/api/traffic/profile").json()
        assert body["available_hours"] == list(range(24))
        assert [h["hour"] for h in body["hours"]] == list(range(24))
        for entry in body["hours"]:
            assert set(entry) == {"hour", "volume", "arrival_rate_per_sec"}
            assert set(entry["volume"]) == set(APPROACHES)
            assert set(entry["arrival_rate_per_sec"]) == set(APPROACHES)
            for a in APPROACHES:
                assert isinstance(entry["volume"][a], int)
                assert isinstance(entry["arrival_rate_per_sec"][a], float)

    def test_842_example_is_served_with_backend_conversion(self, client):
        hour8 = client.get("/api/traffic/profile").json()["hours"][8]
        assert hour8["hour"] == 8
        assert hour8["volume"] == {"N": 842, "S": 790, "E": 610, "W": 655}
        assert hour8["arrival_rate_per_sec"]["N"] == pytest.approx(842 / 3 / 3600, abs=1e-6)
        assert hour8["arrival_rate_per_sec"]["E"] == pytest.approx(610 / 2 / 3600, abs=1e-6)

    def test_rate_equals_volume_over_lanes_over_3600_for_every_hour(self, client):
        body = client.get("/api/traffic/profile").json()
        lanes = body["meta"]["lanes"]
        for entry in body["hours"]:
            for a in APPROACHES:
                expected = entry["volume"][a] / lanes[a] / 3600
                assert entry["arrival_rate_per_sec"][a] == pytest.approx(expected, abs=1e-6)

    def test_payload_has_no_queue_keys(self, client):
        body = client.get("/api/traffic/profile").json()
        assert not any("queue" in k.lower() for k in _all_keys(body))

    def test_korean_is_not_escaped(self, client):
        assert "북측" in client.get("/api/traffic/profile").text


# ==========================================================================
# ?hour= filter
# ==========================================================================
class TestHourFilter:
    def test_single_hour(self, client):
        body = client.get("/api/traffic/profile", params={"hour": "8"}).json()
        assert [h["hour"] for h in body["hours"]] == [8]
        assert body["hours"][0]["volume"]["N"] == 842
        assert body["available_hours"] == list(range(24))  # full list stays for the hour selector

    @pytest.mark.parametrize("hour", ["24", "-1", "abc", "3.5"])
    def test_invalid_hour_is_400(self, client, hour):
        resp = client.get("/api/traffic/profile", params={"hour": hour})
        assert resp.status_code == 400
        assert "hour" in resp.json()["detail"]

    def test_accepted_hour_forms(self, client):
        for form in ("08", "8시", " 8 "):
            body = client.get("/api/traffic/profile", params={"hour": form}).json()
            assert body["hours"][0]["hour"] == 8

    def test_hour_missing_from_profile_is_404(self, client, tmp_path, monkeypatch):
        monkeypatch.setenv("TRAFFIC_PROFILE_META", str(_write_partial_day_profile(tmp_path)))
        ok = client.get("/api/traffic/profile", params={"hour": "8"})
        assert ok.status_code == 200
        assert ok.json()["available_hours"] == [7, 8, 9]
        missing = client.get("/api/traffic/profile", params={"hour": "10"})
        assert missing.status_code == 404
        assert "10시" in missing.json()["detail"]


# ==========================================================================
# Configuration and failure modes
# ==========================================================================
class TestProfileConfig:
    def test_env_var_selects_another_meta_file(self, client, tmp_path, monkeypatch):
        monkeypatch.setenv("TRAFFIC_PROFILE_META", str(_write_partial_day_profile(tmp_path)))
        body = client.get("/api/traffic/profile").json()
        assert body["meta"]["site_id"] == "P-X"
        assert body["meta"]["lanes"] == {"N": 1, "S": 1, "E": 1, "W": 1}
        assert body["meta"]["profile_file"] == "partial.meta.json"

    def test_missing_meta_file_is_500_with_reason(self, client, tmp_path, monkeypatch):
        monkeypatch.setenv("TRAFFIC_PROFILE_META", str(tmp_path / "nope.meta.json"))
        resp = client.get("/api/traffic/profile")
        assert resp.status_code == 500
        assert "메타 파일" in resp.json()["detail"]

    def test_profile_is_loaded_once_and_cached(self, client, monkeypatch):
        calls = {"n": 0}
        real = main_module.load_profile_from_meta

        def counting(path):
            calls["n"] += 1
            return real(path)

        monkeypatch.setattr(main_module, "load_profile_from_meta", counting)
        main_module.get_traffic_profile.cache_clear()
        client.get("/api/traffic/profile")
        client.get("/api/traffic/profile", params={"hour": "8"})
        assert calls["n"] == 1

    def test_default_meta_path_points_at_shipped_sample(self):
        assert main_module.traffic_profile_meta_path() == SAMPLE_META
        assert SAMPLE_META.exists()


# ==========================================================================
# Existing pipeline untouched
# ==========================================================================
class TestPipelineUnaffected:
    def test_health_and_agent_routes_still_registered(self, client):
        paths = {r.path for r in main_module.app.routes}
        assert {"/", "/api/agent/stream", "/api/traffic/profile"} <= paths

    def test_agent_stream_does_not_call_profile_loader(self, client, fake_solar, frontend_scenario, monkeypatch):
        from tests.conftest import analysis_ok, eval_ok, plan_ok

        called = {"n": 0}
        monkeypatch.setattr(main_module, "load_profile_from_meta", lambda p: called.__setitem__("n", called["n"] + 1))
        main_module.get_traffic_profile.cache_clear()
        fake_solar.queue(analysis_ok(), plan_ok(), eval_ok())
        resp = client.post("/api/agent/stream", json=frontend_scenario)
        assert resp.status_code == 200
        assert "event: done" in resp.text
        assert called["n"] == 0

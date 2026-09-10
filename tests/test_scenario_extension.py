"""
Stage 6-4: the frontend now sends an extended scenario with a `demand` block
(input: volume_per_hour / arrival_rate_per_sec) and `queues.by_approach`
(result: queue / mean_wait_sec / arrivals / saturation per N/S/E/W).

The backend must pass it through unchanged and keep using the top-level
fields for Guardrail and the decision correction. No network access.
"""
import copy

import pytest

from tests.conftest import analysis_ok, eval_ok, parse_sse, plan_ok

APPROACHES = ("N", "S", "E", "W")


@pytest.fixture
def extended_scenario(frontend_scenario):
    """Mirror of what (MAIN) cityflow_final.html builds in profile mode after 6-4."""
    s = copy.deepcopy(frontend_scenario)
    s["demand"] = {
        "mode": "profile",
        "site_id": "DEMO-X",
        "hour": 8,
        "unit": "veh_per_hour",
        "volume_per_hour": {"N": 842, "S": 790, "E": 610, "W": 655},
        "lanes": {"N": 3, "S": 3, "E": 2, "W": 2},
        "arrival_rate_per_sec": {"N": 0.077963, "S": 0.073148, "E": 0.084722, "W": 0.090972},
        "lost_demand_last_60s": {"N": 0, "S": 0, "E": 0, "W": 0},
        "note": "volume_per_hour 는 입력 수요, arrival_rate_per_sec 는 발생률. queue 가 아니다.",
    }
    s["queues"]["by_approach"] = {
        "N": {"queue": 9, "mean_wait_sec": 14.2, "arrivals_last_window": 31, "saturation": 0.83},
        "S": {"queue": 7, "mean_wait_sec": 11.0, "arrivals_last_window": 28, "saturation": 0.75},
        "E": {"queue": 2, "mean_wait_sec": 3.1, "arrivals_last_window": 12, "saturation": 0.31},
        "W": {"queue": 1, "mean_wait_sec": 2.4, "arrivals_last_window": 10, "saturation": 0.27},
    }
    s["context"].update({"demand_mode": "profile", "by_approach_scope": "intersection_approaches", "window_sec": 30})
    return s


def _post(client, scenario):
    resp = client.post("/api/agent/stream", json=scenario)
    assert resp.status_code == 200
    return parse_sse(resp.text)


class TestExtendedScenarioPassThrough:
    def test_pipeline_completes_and_echoes_full_scenario(self, client, fake_solar, extended_scenario):
        fake_solar.queue(analysis_ok(), plan_ok(), eval_ok())
        events = _post(client, extended_scenario)
        assert [e for e, _ in events] == ["message"] * 5 + ["done"]
        done = events[-1][1]
        assert done["input_state"] == extended_scenario
        assert done["input_state"]["demand"]["volume_per_hour"]["N"] == 842
        assert done["input_state"]["queues"]["by_approach"]["N"]["queue"] == 9

    def test_every_agent_receives_demand_and_by_approach(self, client, fake_solar, extended_scenario):
        fake_solar.queue(analysis_ok(), plan_ok(), eval_ok())
        _post(client, extended_scenario)
        assert fake_solar.user_payload(0) == extended_scenario
        for i in (1, 2):
            state = fake_solar.user_payload(i)["state"]
            assert state["demand"]["mode"] == "profile"
            assert set(state["queues"]["by_approach"]) == set(APPROACHES)

    def test_demand_block_never_contains_a_queue_key(self, extended_scenario):
        def keys(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    yield k
                    yield from keys(v)

        assert not any("queue" in k.lower() for k in keys(extended_scenario["demand"]))
        # and the demand volume is not smuggled into the queue fields
        assert extended_scenario["queues"]["stopped_cars"] != extended_scenario["demand"]["volume_per_hour"]["N"]

    def test_guardrail_still_uses_top_level_cycle_and_pedestrians(self, client, fake_solar, extended_scenario):
        fake_solar.queue(analysis_ok(), plan_ok(ns=3, ew=2, ped=5), eval_ok())
        events = _post(client, extended_scenario)
        guard = events[3][1]
        assert guard["durations"] == {"north_south_green_sec": 8, "east_west_green_sec": 8, "pedestrian_green_sec": 0}
        assert guard["before"] == {"north_south_green_sec": 3, "east_west_green_sec": 2, "pedestrian_green_sec": 5}

    def test_decision_correction_still_reads_top_level_stopped_cars(self, client, fake_solar, extended_scenario):
        extended_scenario["queues"]["stopped_cars"] = 25   # by_approach queues sum to 19, top-level says 25
        fake_solar.queue(analysis_ok(), plan_ok(ns=12, ew=8, ped=0), eval_ok("운영자 승인 필요"))
        events = _post(client, extended_scenario)
        assert events[-1][1]["final_decision"] == "자동 적용"

    def test_manual_mode_demand_block_is_also_accepted(self, client, fake_solar, frontend_scenario):
        s = copy.deepcopy(frontend_scenario)
        s["demand"] = {"mode": "manual", "spawn_rate_per_sec_total": 3, "note": "수동 슬라이더 값"}
        s["context"]["demand_mode"] = "manual"
        fake_solar.queue(analysis_ok(), plan_ok(), eval_ok())
        events = _post(client, s)
        assert events[-1][1]["input_state"]["demand"]["mode"] == "manual"

    def test_legacy_scenario_without_extension_still_works(self, client, fake_solar, frontend_scenario):
        fake_solar.queue(analysis_ok(), plan_ok(), eval_ok())
        events = _post(client, frontend_scenario)
        assert events[-1][1]["final_decision"] in {"자동 적용", "운영자 승인 필요", "재계획 필요"}
        assert "demand" not in events[-1][1]["input_state"]

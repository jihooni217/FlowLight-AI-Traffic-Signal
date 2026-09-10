"""
Regression baseline for the FastAPI SSE endpoints with the Solar client mocked.

Pins, without any network access:
- the SSE event order and payload shape the HTML frontend depends on,
- the exact request shape currently sent to Upstage (model, temperature,
  response_format, message layout) so a model swap is visible in the diff,
- how errors from the model call surface on the stream,
- that apply_guardrail and correct_final_decision are wired into the stream.
"""
import json

import pytest

from app.agents import mock_scenario
from tests.conftest import analysis_ok, eval_ok, make_chat_response, parse_sse, plan_ok

ALLOWED_DECISIONS = {"자동 적용", "운영자 승인 필요", "재계획 필요"}


def _post(client, scenario):
    resp = client.post("/api/agent/stream", json=scenario)
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    return parse_sse(resp.text)


# ==========================================================================
# Happy path: POST (frontend path)
# ==========================================================================
class TestPostStreamHappyPath:
    def test_event_sequence_matches_frontend_expectations(self, client, fake_solar, frontend_scenario):
        fake_solar.queue(analysis_ok(), plan_ok(), eval_ok())
        events = _post(client, frontend_scenario)

        names = [e for e, _ in events]
        assert names == ["message", "message", "message", "message", "message", "done"]

        steps = [d.get("step") for _, d in events[:5]]
        assert steps == [1, 2, 3, "guardrail", 4]

        # the frontend labels agents by substring-matching these messages
        texts = [d["message"] for _, d in events[:5]]
        assert "교통 상황 분석" in texts[1]
        assert "신호 계획 생성" in texts[2]
        assert "Guardrail" in texts[3]
        assert "계획 평가" in texts[4]
        # every "message" event must carry a "message" field (frontend calls .includes on it)
        assert all("message" in d for e, d in events if e == "message")

    def test_done_payload_contains_every_field_the_frontend_reads(self, client, fake_solar, frontend_scenario):
        fake_solar.queue(analysis_ok(), plan_ok(), eval_ok())
        events = _post(client, frontend_scenario)
        done = events[-1][1]

        assert set(done) == {"input_state", "traffic_analysis", "signal_plan", "evaluation", "final_decision"}
        assert done["input_state"] == frontend_scenario

        d = done["signal_plan"]["durations"]
        assert set(d) == {"north_south_green_sec", "east_west_green_sec", "pedestrian_green_sec"}
        assert all(isinstance(v, int) for v in d.values())
        assert done["signal_plan"]["priority"] in {"VEHICLE", "PEDESTRIAN", "BALANCED"}
        assert isinstance(done["evaluation"]["total_score"], int)
        assert done["final_decision"] in ALLOWED_DECISIONS
        assert done["final_decision"] == done["evaluation"]["decision_recommendation"]

    def test_guardrail_event_reports_corrected_durations(self, client, fake_solar, frontend_scenario):
        # LLM proposes below-minimum greens and a pedestrian phase although no pedestrians exist
        fake_solar.queue(analysis_ok(), plan_ok(ns=3, ew=2, ped=5), eval_ok())
        events = _post(client, frontend_scenario)

        guard = events[3][1]
        assert guard["step"] == "guardrail"
        assert guard["durations"] == {
            "north_south_green_sec": 8,
            "east_west_green_sec": 8,
            "pedestrian_green_sec": 0,
        }
        # the corrected plan is what reaches the evaluator and the final payload
        assert fake_solar.user_payload(2)["signal_plan"]["durations"] == guard["durations"]
        assert events[-1][1]["signal_plan"]["durations"] == guard["durations"]

    def test_backend_correction_can_override_llm_decision(self, client, fake_solar, frontend_scenario):
        scenario = dict(frontend_scenario)
        scenario["queues"] = {"total_cars": 30, "stopped_cars": 25}  # >= 20 stopped, 0 pedestrians
        fake_solar.queue(analysis_ok(), plan_ok(ns=12, ew=8, ped=0), eval_ok("운영자 승인 필요"))
        events = _post(client, scenario)

        done = events[-1][1]
        assert done["final_decision"] == "자동 적용"
        assert "자동 적용으로 보정" in done["evaluation"]["reason"]

    def test_decision_from_llm_is_kept_when_no_rule_fires(self, client, fake_solar, frontend_scenario):
        fake_solar.queue(analysis_ok(), plan_ok(), eval_ok("재계획 필요"))
        events = _post(client, frontend_scenario)
        assert events[-1][1]["final_decision"] == "재계획 필요"


# ==========================================================================
# Request shape currently sent to Upstage (characterisation of Solar Pro 3 use)
# ==========================================================================
class TestUpstageRequestShape:
    def test_three_sequential_calls_with_current_parameters(self, client, fake_solar, frontend_scenario, monkeypatch):
        monkeypatch.delenv("UPSTAGE_MODEL", raising=False)
        monkeypatch.delenv("UPSTAGE_OUTPUT_MODE", raising=False)
        fake_solar.queue(analysis_ok(), plan_ok(), eval_ok())
        _post(client, frontend_scenario)

        assert len(fake_solar.calls) == 3
        # Stage 1: default model is solar-pro4 (was solar-pro3 in the Stage 0 baseline).
        assert fake_solar.models == ["solar-pro4"] * 3
        # Stage 3: structured outputs, one distinct strict schema per agent.
        assert [c["response_format"]["type"] for c in fake_solar.calls] == ["json_schema"] * 3
        assert [c["response_format"]["json_schema"]["name"] for c in fake_solar.calls] == [
            "traffic_analysis", "signal_plan", "plan_evaluation",
        ]
        for call in fake_solar.calls:
            assert call["temperature"] == 0.2
            assert call["response_format"]["json_schema"]["strict"] is True
            assert "reasoning_effort" not in call
            assert "max_tokens" not in call
            assert [m["role"] for m in call["messages"]] == ["system", "user"]

    def test_json_object_mode_prerequisite_prompt_mentions_json(self, client, fake_solar, frontend_scenario, monkeypatch):
        # Upstage docs: json_object mode requires the word JSON in the conversation.
        # Still enforced so the UPSTAGE_OUTPUT_MODE=json_object fallback keeps working.
        monkeypatch.setenv("UPSTAGE_OUTPUT_MODE", "json_object")
        fake_solar.queue(analysis_ok(), plan_ok(), eval_ok())
        _post(client, frontend_scenario)
        for i in range(3):
            assert fake_solar.calls[i]["response_format"] == {"type": "json_object"}
            assert "JSON" in fake_solar.system_prompt(i)

    def test_agent_inputs_chain_previous_outputs(self, client, fake_solar, frontend_scenario):
        analysis = analysis_ok()
        fake_solar.queue(analysis, plan_ok(), eval_ok())
        _post(client, frontend_scenario)

        assert fake_solar.user_payload(0) == frontend_scenario
        p1 = fake_solar.user_payload(1)
        assert set(p1) == {"state", "traffic_analysis"}
        assert p1["state"] == frontend_scenario
        assert p1["traffic_analysis"] == analysis
        p2 = fake_solar.user_payload(2)
        assert set(p2) == {"state", "traffic_analysis", "signal_plan"}
        assert p2["traffic_analysis"] == analysis

    def test_user_message_is_json_serialised_with_korean_intact(self, client, fake_solar, frontend_scenario):
        fake_solar.queue(analysis_ok(), plan_ok(), eval_ok())
        _post(client, frontend_scenario)
        raw = fake_solar.calls[1]["messages"][1]["content"]
        assert "높음" in raw  # ensure_ascii=False, not \\uXXXX escapes
        json.loads(raw)


# ==========================================================================
# Error paths
# ==========================================================================
class TestPostStreamErrors:
    def test_failure_in_first_agent_stops_stream_with_error_event(self, client, fake_solar, frontend_scenario):
        fake_solar.queue(RuntimeError("boom"))
        events = _post(client, frontend_scenario)

        assert [e for e, _ in events] == ["message", "message", "error"]
        err = events[-1][1]
        assert err["status"] == "error"
        assert err["agent"] == "Traffic Situation Agent"
        assert err["message"] == "Solar API 호출에 실패했습니다."
        assert "boom" in err["detail"]
        assert len(fake_solar.calls) == 1

    def test_failure_in_second_agent_skips_guardrail_and_evaluation(self, client, fake_solar, frontend_scenario):
        fake_solar.queue(analysis_ok(), RuntimeError("boom"))
        events = _post(client, frontend_scenario)

        assert [e for e, _ in events] == ["message", "message", "message", "error"]
        assert events[-1][1]["agent"] == "Signal Planning Agent"
        assert len(fake_solar.calls) == 2

    def test_failure_in_third_agent_reports_evaluation_agent(self, client, fake_solar, frontend_scenario):
        fake_solar.queue(analysis_ok(), plan_ok(), RuntimeError("boom"))
        events = _post(client, frontend_scenario)

        assert [e for e, _ in events] == ["message"] * 5 + ["error"]
        assert events[-1][1]["agent"] == "Plan Evaluation Agent"

    def test_non_json_model_output_becomes_error_event(self, client, fake_solar, frontend_scenario):
        fake_solar.queue("죄송합니다, 분석할 수 없습니다.")
        events = _post(client, frontend_scenario)

        assert events[-1][0] == "error"
        assert events[-1][1]["agent"] == "Traffic Situation Agent"

    def test_truncated_response_is_reported_as_finish_reason_error(self, client, fake_solar, frontend_scenario):
        # Stage 1: finish_reason != "stop" is detected before parsing and surfaces on the stream.
        fake_solar.queue(lambda kw: make_chat_response('{"summary": "차량이 많', finish_reason="length"))
        events = _post(client, frontend_scenario)

        assert [e for e, _ in events] == ["message", "message", "error"]
        err = events[-1][1]
        assert err["agent"] == "Traffic Situation Agent"
        assert err["message"] == "Solar 응답이 정상 종료되지 않았습니다."
        assert err["detail"] == "finish_reason=length"


# ==========================================================================
# GET endpoint (mock_scenario path, used by the original test)
# ==========================================================================
class TestGetStream:
    def test_get_uses_mock_scenario_and_emits_done(self, client, fake_solar):
        fake_solar.queue(analysis_ok(), plan_ok(), eval_ok())
        resp = client.get("/api/agent/stream")
        assert resp.status_code == 200
        events = parse_sse(resp.text)

        assert [e for e, _ in events] == ["message", "message", "message", "message", "done"]
        assert [d.get("step") for _, d in events[:4]] == [1, 2, "guardrail", 3]
        done = events[-1][1]
        assert done["input_state"] == mock_scenario
        assert done["final_decision"] in ALLOWED_DECISIONS
        assert fake_solar.user_payload(0) == mock_scenario

    def test_get_guardrail_uses_mock_defaults_cycle_40_and_no_pedestrians(self, client, fake_solar):
        # mock_scenario has no signals.cycle_sec and no pedestrians.waiting_or_crossing
        fake_solar.queue(analysis_ok(), plan_ok(ns=30, ew=20, ped=9), eval_ok())
        events = parse_sse(client.get("/api/agent/stream").text)
        assert events[2][1]["durations"] == {
            "north_south_green_sec": 24,
            "east_west_green_sec": 16,
            "pedestrian_green_sec": 0,
        }


# ==========================================================================
# Plumbing the browser relies on
# ==========================================================================
class TestPlumbing:
    def test_health_check(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_cors_preflight_allows_file_origin_post(self, client):
        # The HTML is opened from disk, so the browser sends Origin: null before the POST.
        resp = client.options(
            "/api/agent/stream",
            headers={
                "Origin": "null",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert resp.status_code == 200
        assert "access-control-allow-origin" in resp.headers
        assert "POST" in resp.headers.get("access-control-allow-methods", "")

    def test_unknown_route_is_404(self, client):
        assert client.get("/api/wrong-url").status_code == 404

    def test_sse_wire_format(self, client, fake_solar, frontend_scenario):
        fake_solar.queue(analysis_ok(), plan_ok(), eval_ok())
        body = client.post("/api/agent/stream", json=frontend_scenario).text
        blocks = [b for b in body.split("\n\n") if b.strip()]
        for block in blocks:
            lines = block.split("\n")
            assert lines[0].startswith("event: ")
            assert lines[1].startswith("data: ")
            json.loads(lines[1][len("data: "):])

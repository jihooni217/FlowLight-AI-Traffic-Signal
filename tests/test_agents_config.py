"""
Stage 1 checks: Solar Pro 4 model selection and finish_reason handling in
app.agents.call_solar_agent. No network access; the Solar client is faked.
"""
import json

import pytest

from app.agents import (
    DEFAULT_SOLAR_MODEL,
    PLAN_EVALUATION_SCHEMA,
    SIGNAL_PLAN_SCHEMA,
    TRAFFIC_ANALYSIS_SCHEMA,
    get_solar_model,
    is_error,
    plan_evaluation_agent,
    signal_planning_agent,
    traffic_situation_agent,
    traffic_situation_agent_prompt,
    signal_planning_agent_prompt,
    plan_evaluation_agent_prompt,
)
from tests.conftest import analysis_ok, make_chat_response

AGENTS = [
    (traffic_situation_agent, "Traffic Situation Agent", traffic_situation_agent_prompt),
    (signal_planning_agent, "Signal Planning Agent", signal_planning_agent_prompt),
    (plan_evaluation_agent, "Plan Evaluation Agent", plan_evaluation_agent_prompt),
]
AGENT_SCHEMAS = {
    "Traffic Situation Agent": TRAFFIC_ANALYSIS_SCHEMA,
    "Signal Planning Agent": SIGNAL_PLAN_SCHEMA,
    "Plan Evaluation Agent": PLAN_EVALUATION_SCHEMA,
}


@pytest.fixture
def no_model_env(monkeypatch):
    """Guarantee the default path even if a local .env sets UPSTAGE_MODEL / UPSTAGE_OUTPUT_MODE."""
    monkeypatch.delenv("UPSTAGE_MODEL", raising=False)
    monkeypatch.delenv("UPSTAGE_OUTPUT_MODE", raising=False)


# ==========================================================================
# Model selection
# ==========================================================================
class TestModelSelection:
    def test_default_model_is_solar_pro4(self, no_model_env):
        assert DEFAULT_SOLAR_MODEL == "solar-pro4"
        assert get_solar_model() == "solar-pro4"

    def test_env_var_overrides_model(self, monkeypatch):
        monkeypatch.setenv("UPSTAGE_MODEL", "solar-pro3")
        assert get_solar_model() == "solar-pro3"

    def test_snapshot_id_passes_through_unchanged(self, monkeypatch):
        monkeypatch.setenv("UPSTAGE_MODEL", "solar-pro4-260806")
        assert get_solar_model() == "solar-pro4-260806"

    def test_empty_env_var_falls_back_to_default(self, monkeypatch):
        monkeypatch.setenv("UPSTAGE_MODEL", "")
        assert get_solar_model() == "solar-pro4"

    def test_default_model_is_sent_in_request(self, no_model_env, fake_solar):
        fake_solar.queue(analysis_ok())
        traffic_situation_agent({"tick": 0})
        assert fake_solar.models == ["solar-pro4"]

    def test_model_is_read_at_call_time_not_import_time(self, monkeypatch, fake_solar):
        monkeypatch.setenv("UPSTAGE_MODEL", "solar-pro3")
        fake_solar.queue(analysis_ok(), analysis_ok())
        traffic_situation_agent({"tick": 0})
        monkeypatch.setenv("UPSTAGE_MODEL", "solar-pro4")
        traffic_situation_agent({"tick": 1})
        assert fake_solar.models == ["solar-pro3", "solar-pro4"]


# ==========================================================================
# Request parameters (Stage 1: model; Stage 3: response_format is json_schema)
# ==========================================================================
class TestRequestParameters:
    @pytest.mark.parametrize("agent_fn, agent_name, prompt", AGENTS)
    def test_exact_request_kwargs(self, no_model_env, fake_solar, agent_fn, agent_name, prompt):
        fake_solar.queue(analysis_ok())
        agent_fn({"tick": 0})

        call = fake_solar.calls[0]
        # pin the full key set so any newly added parameter shows up in review
        assert set(call) == {"model", "messages", "temperature", "response_format"}
        assert call["model"] == "solar-pro4"
        assert call["temperature"] == 0.2
        assert call["response_format"] == {"type": "json_schema", "json_schema": AGENT_SCHEMAS[agent_name]}
        assert "reasoning_effort" not in call
        assert "max_tokens" not in call
        assert "max_completion_tokens" not in call
        assert "stream" not in call
        assert call["messages"][0] == {"role": "system", "content": prompt}
        assert call["messages"][1]["role"] == "user"
        assert json.loads(call["messages"][1]["content"]) == {"tick": 0}


# ==========================================================================
# finish_reason handling
# ==========================================================================
class TestFinishReason:
    def test_stop_parses_json_as_before(self, fake_solar):
        expected = analysis_ok()
        fake_solar.queue(expected)  # conftest default finish_reason is "stop"
        result = traffic_situation_agent({"tick": 0})
        assert result == expected
        assert not is_error(result)

    @pytest.mark.parametrize("reason", ["length", "content_filter", "tool_calls", None])
    @pytest.mark.parametrize("agent_fn, agent_name, prompt", AGENTS)
    def test_non_stop_returns_error_dict_without_parsing(self, fake_solar, reason, agent_fn, agent_name, prompt):
        # content is deliberately broken JSON: if it were parsed we would see a different error
        fake_solar.queue(lambda kw: make_chat_response('{"summary": "잘림', finish_reason=reason))
        result = agent_fn({"tick": 0})

        assert is_error(result)
        assert set(result) == {"status", "agent", "message", "detail"}
        assert result["agent"] == agent_name
        assert result["message"] == "Solar 응답이 정상 종료되지 않았습니다."
        assert result["detail"] == f"finish_reason={reason}"

    def test_non_stop_is_error_even_if_content_happens_to_be_valid_json(self, fake_solar):
        fake_solar.queue(lambda kw: make_chat_response(json.dumps(analysis_ok()), finish_reason="length"))
        result = traffic_situation_agent({"tick": 0})
        assert is_error(result)
        assert "finish_reason=length" in result["detail"]

    def test_non_stop_with_null_content_does_not_raise(self, fake_solar):
        # Upstage docs: when reasoning eats the budget, content is null and finish_reason is "length"
        fake_solar.queue(lambda kw: make_chat_response(None, finish_reason="length"))
        result = traffic_situation_agent({"tick": 0})
        assert is_error(result)
        assert result["message"] == "Solar 응답이 정상 종료되지 않았습니다."

    def test_api_exception_keeps_original_error_message(self, fake_solar):
        fake_solar.queue(RuntimeError("boom"))
        result = traffic_situation_agent({"tick": 0})
        assert is_error(result)
        assert result["message"] == "Solar API 호출에 실패했습니다."
        assert "boom" in result["detail"]

    def test_invalid_json_with_stop_keeps_original_error_message(self, fake_solar):
        fake_solar.queue("not json at all")
        result = traffic_situation_agent({"tick": 0})
        assert is_error(result)
        assert result["message"] == "Solar API 호출에 실패했습니다."

    def test_both_error_kinds_share_the_same_shape(self, fake_solar):
        fake_solar.queue(
            RuntimeError("boom"),
            lambda kw: make_chat_response("", finish_reason="length"),
        )
        api_err = traffic_situation_agent({"tick": 0})
        finish_err = traffic_situation_agent({"tick": 0})
        assert set(api_err) == set(finish_err)
        assert api_err["status"] == finish_err["status"] == "error"

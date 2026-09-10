"""
Stage 3: JSON Schema (structured outputs) checks. No network access.

Covers:
- each schema obeys the constraints Upstage documents for structured outputs,
- schema field names match the prompts' "출력 형식" blocks exactly,
- the REAL Solar Pro 4 outputs captured in the Stage 2 live run validate
  against the schemas (so the schemas describe what the model already does),
- the schemas reject a missing field, a wrong type, an unknown enum value and
  an extra field,
- the output-mode switch (json_schema default, json_object fallback) and the
  backwards-compatible call_solar_agent signature.
"""
import copy
import json
import re

import pytest

from app.agents import (
    PLAN_EVALUATION_SCHEMA,
    SIGNAL_PLAN_SCHEMA,
    TRAFFIC_ANALYSIS_SCHEMA,
    build_response_format,
    call_solar_agent,
    get_output_mode,
    plan_evaluation_agent,
    plan_evaluation_agent_prompt,
    signal_planning_agent,
    signal_planning_agent_prompt,
    traffic_situation_agent,
    traffic_situation_agent_prompt,
)
from tests.conftest import analysis_ok, eval_ok, plan_ok
from tests.schema_utils import SchemaError, assert_upstage_compatible, is_valid, validate

SCHEMAS = [
    ("traffic_analysis", TRAFFIC_ANALYSIS_SCHEMA),
    ("signal_plan", SIGNAL_PLAN_SCHEMA),
    ("plan_evaluation", PLAN_EVALUATION_SCHEMA),
]

# Verbatim outputs returned by solar-pro4-260806 in the Stage 2 live run
# (json_object mode, temperature 0.2, docs/ai_result.png scenario).
LIVE_STAGE2_OUTPUTS = {
    "traffic_analysis": {
        "summary": "현재 총 차량 28대 중 19대가 정지 상태이며, 혼잡도는 0.894로 매우 높은 수준입니다. 보행자는 대기 중이거나 횡단 중인 인원이 없습니다.",
        "traffic_level": "높음",
        "main_congestion_direction": "전체",
        "pedestrian_issue": False,
        "vulnerable_user_detected": False,
        "risk_level": "보통",
    },
    "signal_plan": {
        "plan_id": "PLAN-001",
        "next_signals": {"north_south": "GREEN", "east_west": "RED", "pedestrian": "RED"},
        "durations": {"north_south_green_sec": 12, "east_west_green_sec": 8, "pedestrian_green_sec": 0},
        "priority": "VEHICLE",
        "explanation": "보행자 대기 인원이 0명이므로 보행자 신호는 0초로 설정하고 우선순위는 VEHICLE로 지정했습니다. 혼잡도가 0.894로 매우 높고 traffic_level이 높음이며 정지 차량이 19대로 많아 차량 녹색 시간을 충분히 확보해야 합니다. cycle_sec 20초 내에서 남북 방향 차량 녹색을 12초, 동서 방향을 8초로 배분하여 전체 차량 신호 합계가 20초가 되도록 했습니다.",
    },
    "plan_evaluation": {
        "total_score": 88,
        "scores": {"vehicle": 22, "pedestrian": 15, "vulnerable_user": 15, "safety": 18, "efficiency": 18},
        "decision_recommendation": "자동 적용",
        "reason": "보행자 대기 인원이 0명이고 혼잡도가 0.894로 매우 높으며 정지 차량이 19대로 많고, 보행자 녹색 시간이 0초이며 신호 시간 합계가 cycle_sec 20초 이내이므로 자동 적용 조건을 모두 만족한다. 차량 흐름이 원활하도록 남북 방향 녹색을 12초로 충분히 배분했고, 보행자 관련 안전 문제도 없다.",
    },
}


def _prompt_output_keys(prompt: str) -> set:
    """Top-level keys of the JSON example inside a prompt's '출력 형식:' block."""
    block = prompt.split("출력 형식:")[1]
    return set(re.findall(r'^\s{2}"([a-z_]+)":', block, flags=re.M))


# ==========================================================================
# 1. Upstage constraint compliance
# ==========================================================================
class TestUpstageConstraints:
    @pytest.mark.parametrize("name, schema", SCHEMAS)
    def test_schema_obeys_documented_subset(self, name, schema):
        assert_upstage_compatible(schema)
        assert schema["name"] == name

    def test_checker_itself_catches_violations(self):
        bad = copy.deepcopy(TRAFFIC_ANALYSIS_SCHEMA)
        bad["schema"]["required"].remove("summary")
        with pytest.raises(SchemaError):
            assert_upstage_compatible(bad)
        bad = copy.deepcopy(SIGNAL_PLAN_SCHEMA)
        bad["schema"]["properties"]["durations"]["additionalProperties"] = True
        with pytest.raises(SchemaError):
            assert_upstage_compatible(bad)
        bad = copy.deepcopy(PLAN_EVALUATION_SCHEMA)
        bad["schema"]["properties"]["total_score"]["minimum"] = 0  # outside documented subset
        with pytest.raises(SchemaError):
            assert_upstage_compatible(bad)


# ==========================================================================
# 2. Schema <-> prompt agreement (field names must not drift)
# ==========================================================================
class TestSchemaMatchesPrompts:
    def test_traffic_analysis_fields_equal_prompt_output_format(self):
        assert set(TRAFFIC_ANALYSIS_SCHEMA["schema"]["properties"]) == _prompt_output_keys(traffic_situation_agent_prompt)

    def test_signal_plan_fields_equal_prompt_output_format(self):
        assert set(SIGNAL_PLAN_SCHEMA["schema"]["properties"]) == _prompt_output_keys(signal_planning_agent_prompt)
        d = SIGNAL_PLAN_SCHEMA["schema"]["properties"]["durations"]["properties"]
        assert set(d) == {"north_south_green_sec", "east_west_green_sec", "pedestrian_green_sec"}
        assert all(v["type"] == "integer" for v in d.values())

    def test_plan_evaluation_fields_equal_prompt_output_format(self):
        assert set(PLAN_EVALUATION_SCHEMA["schema"]["properties"]) == _prompt_output_keys(plan_evaluation_agent_prompt)
        s = PLAN_EVALUATION_SCHEMA["schema"]["properties"]["scores"]["properties"]
        assert set(s) == {"vehicle", "pedestrian", "vulnerable_user", "safety", "efficiency"}

    def test_enums_match_the_strings_the_code_compares_against(self):
        p = TRAFFIC_ANALYSIS_SCHEMA["schema"]["properties"]
        assert p["traffic_level"]["enum"] == ["낮음", "보통", "높음"]
        assert p["risk_level"]["enum"] == ["낮음", "보통", "높음"]
        assert SIGNAL_PLAN_SCHEMA["schema"]["properties"]["priority"]["enum"] == ["VEHICLE", "PEDESTRIAN", "BALANCED"]
        # exact strings used by main.correct_final_decision and the HTML frontend
        assert PLAN_EVALUATION_SCHEMA["schema"]["properties"]["decision_recommendation"]["enum"] == [
            "자동 적용", "운영자 승인 필요", "재계획 필요",
        ]


# ==========================================================================
# 3. Real Solar Pro 4 outputs (Stage 2) and the test fixtures satisfy the schemas
# ==========================================================================
class TestPositiveInstances:
    @pytest.mark.parametrize("name, schema", SCHEMAS)
    def test_live_stage2_output_validates(self, name, schema):
        validate(LIVE_STAGE2_OUTPUTS[name], schema["schema"])

    def test_conftest_fixtures_validate(self):
        validate(analysis_ok(), TRAFFIC_ANALYSIS_SCHEMA["schema"])
        validate(plan_ok(), SIGNAL_PLAN_SCHEMA["schema"])
        validate(eval_ok(), PLAN_EVALUATION_SCHEMA["schema"])
        for d in ("자동 적용", "운영자 승인 필요", "재계획 필요"):
            validate(eval_ok(d), PLAN_EVALUATION_SCHEMA["schema"])


# ==========================================================================
# 4. Negative cases: what the schema forbids
# ==========================================================================
class TestNegativeInstances:
    def test_missing_required_field_is_rejected(self):
        inst = analysis_ok()
        del inst["risk_level"]
        with pytest.raises(SchemaError, match="missing required"):
            validate(inst, TRAFFIC_ANALYSIS_SCHEMA["schema"])

    def test_missing_nested_duration_is_rejected(self):
        inst = plan_ok()
        del inst["durations"]["pedestrian_green_sec"]
        with pytest.raises(SchemaError, match="durations: missing required"):
            validate(inst, SIGNAL_PLAN_SCHEMA["schema"])

    def test_string_duration_is_rejected(self):
        # json_object mode let "12" through and relied on Guardrail's int(); schema forbids it upstream
        assert not is_valid(plan_ok(ns="12"), SIGNAL_PLAN_SCHEMA["schema"])

    def test_float_duration_is_rejected(self):
        assert not is_valid(plan_ok(ns=12.5), SIGNAL_PLAN_SCHEMA["schema"])

    def test_boolean_is_not_accepted_as_integer(self):
        assert not is_valid(eval_ok(score=True), PLAN_EVALUATION_SCHEMA["schema"])

    def test_string_boolean_is_rejected(self):
        assert not is_valid(analysis_ok(pedestrian_issue="false"), TRAFFIC_ANALYSIS_SCHEMA["schema"])

    @pytest.mark.parametrize("bad", ["자동적용", "AUTO_APPLY", "승인 필요", ""])
    def test_unknown_decision_enum_is_rejected(self, bad):
        assert not is_valid(eval_ok(bad), PLAN_EVALUATION_SCHEMA["schema"])

    def test_unknown_traffic_level_is_rejected(self):
        assert not is_valid(analysis_ok(traffic_level="매우 높음"), TRAFFIC_ANALYSIS_SCHEMA["schema"])

    def test_unknown_priority_is_rejected(self):
        assert not is_valid(plan_ok(priority="MIXED"), SIGNAL_PLAN_SCHEMA["schema"])

    def test_extra_field_is_rejected(self):
        inst = eval_ok()
        inst["status"] = "error"  # would collide with is_error() if a model ever emitted it
        with pytest.raises(SchemaError, match="unexpected keys"):
            validate(inst, PLAN_EVALUATION_SCHEMA["schema"])

    def test_missing_reason_is_rejected(self):
        # main.correct_final_decision does evaluation["reason"] += ... ; a missing key was a KeyError risk
        inst = eval_ok()
        del inst["reason"]
        assert not is_valid(inst, PLAN_EVALUATION_SCHEMA["schema"])


# ==========================================================================
# 5. Output-mode switch and request wiring
# ==========================================================================
@pytest.fixture
def no_mode_env(monkeypatch):
    monkeypatch.delenv("UPSTAGE_OUTPUT_MODE", raising=False)


class TestOutputModeSwitch:
    def test_default_mode_is_json_schema(self, no_mode_env):
        assert get_output_mode() == "json_schema"
        assert build_response_format(TRAFFIC_ANALYSIS_SCHEMA) == {
            "type": "json_schema",
            "json_schema": TRAFFIC_ANALYSIS_SCHEMA,
        }

    def test_env_can_fall_back_to_json_object(self, monkeypatch):
        monkeypatch.setenv("UPSTAGE_OUTPUT_MODE", "json_object")
        assert get_output_mode() == "json_object"
        assert build_response_format(TRAFFIC_ANALYSIS_SCHEMA) == {"type": "json_object"}

    @pytest.mark.parametrize("value", ["", "yaml", "JSON_SCHEMA"])
    def test_unknown_or_empty_mode_uses_default(self, monkeypatch, value):
        monkeypatch.setenv("UPSTAGE_OUTPUT_MODE", value)
        assert get_output_mode() == "json_schema"

    def test_no_schema_means_json_object_regardless_of_mode(self, no_mode_env):
        assert build_response_format(None) == {"type": "json_object"}

    @pytest.mark.parametrize(
        "agent_fn, schema",
        [
            (traffic_situation_agent, TRAFFIC_ANALYSIS_SCHEMA),
            (signal_planning_agent, SIGNAL_PLAN_SCHEMA),
            (plan_evaluation_agent, PLAN_EVALUATION_SCHEMA),
        ],
    )
    def test_each_agent_sends_its_own_schema(self, no_mode_env, fake_solar, agent_fn, schema):
        fake_solar.queue(analysis_ok())
        agent_fn({"tick": 0})
        rf = fake_solar.calls[0]["response_format"]
        assert rf["type"] == "json_schema"
        assert rf["json_schema"] is schema
        assert rf["json_schema"]["strict"] is True

    def test_fallback_mode_sends_plain_json_object(self, monkeypatch, fake_solar):
        monkeypatch.setenv("UPSTAGE_OUTPUT_MODE", "json_object")
        fake_solar.queue(analysis_ok())
        traffic_situation_agent({"tick": 0})
        assert fake_solar.calls[0]["response_format"] == {"type": "json_object"}

    def test_call_solar_agent_without_schema_is_backwards_compatible(self, no_mode_env, fake_solar):
        fake_solar.queue(analysis_ok())
        result = call_solar_agent("X", "반드시 JSON만 출력한다.", {"tick": 0})
        assert result == analysis_ok()
        assert fake_solar.calls[0]["response_format"] == {"type": "json_object"}

    def test_schema_is_json_serialisable(self):
        for _, schema in SCHEMAS:
            json.dumps(schema, ensure_ascii=False)

"""
Regression baseline for the two rule-based safety layers.

These are characterisation tests: they pin what the CURRENT code does so that
later changes (Solar Pro 4, structured outputs) can be checked for regressions.
Where current behaviour looks surprising it is documented in the test name and
docstring rather than "fixed" here.
"""
import copy

import pytest

from app.agents import apply_guardrail, mock_scenario
from app.main import correct_final_decision


def _plan(ns, ew, ped):
    return {
        "plan_id": "PLAN-001",
        "durations": {
            "north_south_green_sec": ns,
            "east_west_green_sec": ew,
            "pedestrian_green_sec": ped,
        },
        "priority": "VEHICLE",
    }


def _durations(plan):
    d = plan["durations"]
    return (
        d["north_south_green_sec"],
        d["east_west_green_sec"],
        d["pedestrian_green_sec"],
    )


# ==========================================================================
# apply_guardrail
# ==========================================================================
class TestApplyGuardrail:
    def test_within_cycle_no_pedestrians_forces_ped_zero(self):
        plan = apply_guardrail(_plan(12, 8, 5), cycle_sec=20, pedestrian_count=0)
        assert _durations(plan) == (12, 8, 0)

    def test_vehicle_minimum_is_8_seconds(self):
        plan = apply_guardrail(_plan(3, 2, 0), cycle_sec=40, pedestrian_count=0)
        assert _durations(plan) == (8, 8, 0)

    def test_pedestrian_minimum_is_6_seconds_when_pedestrians_exist(self):
        plan = apply_guardrail(_plan(10, 10, 3), cycle_sec=40, pedestrian_count=2)
        assert _durations(plan) == (10, 10, 6)

    def test_pedestrians_present_but_llm_gave_zero_is_raised_to_6(self):
        plan = apply_guardrail(_plan(12, 8, 0), cycle_sec=40, pedestrian_count=1)
        assert _durations(plan) == (12, 8, 6)

    def test_over_cycle_no_pedestrians_redistributes_proportionally(self):
        # 20+10 > 20 -> ns=int(20*20/30)=13, ew=7 -> ew bumped to 8, ns=12
        plan = apply_guardrail(_plan(20, 10, 0), cycle_sec=20, pedestrian_count=0)
        assert _durations(plan) == (12, 8, 0)
        assert sum(_durations(plan)) == 20

    def test_over_cycle_with_pedestrians_keeps_ped_6_and_splits_rest(self):
        plan = apply_guardrail(_plan(20, 20, 10), cycle_sec=30, pedestrian_count=3)
        assert _durations(plan) == (12, 12, 6)
        assert sum(_durations(plan)) == 30

    def test_over_cycle_tiny_budget_drops_vehicle_minimum_to_4(self):
        # available = 14 - 6 = 8 < 16 -> ns = max(4, 8//2) = 4, ew = max(4, 8-4) = 4
        plan = apply_guardrail(_plan(10, 10, 8), cycle_sec=14, pedestrian_count=1)
        assert _durations(plan) == (4, 4, 6)
        assert sum(_durations(plan)) == 14

    def test_current_behaviour_tiny_cycle_can_still_overshoot(self):
        """Documents current behaviour: with cycle 12 and pedestrians present the
        floors (4+4+6=14) exceed the cycle. correct_final_decision catches this
        downstream by demanding a re-plan. Not a target to change in Stage 0."""
        plan = apply_guardrail(_plan(10, 10, 8), cycle_sec=12, pedestrian_count=1)
        assert _durations(plan) == (4, 4, 6)
        assert sum(_durations(plan)) == 14 > 12

    def test_missing_duration_keys_use_defaults_15_15_0(self):
        plan = apply_guardrail({"durations": {}}, cycle_sec=40, pedestrian_count=0)
        assert _durations(plan) == (15, 15, 0)

    def test_string_numbers_from_llm_are_coerced_to_int(self):
        plan = apply_guardrail(_plan("12", "8", "0"), cycle_sec=20, pedestrian_count=0)
        assert _durations(plan) == (12, 8, 0)
        assert all(isinstance(v, int) for v in _durations(plan))

    def test_mutates_and_returns_the_same_plan_object(self):
        original = _plan(3, 2, 0)
        result = apply_guardrail(original, cycle_sec=40, pedestrian_count=0)
        assert result is original
        assert original["plan_id"] == "PLAN-001"  # untouched keys survive

    def test_default_arguments_are_cycle_40_and_no_pedestrians(self):
        plan = apply_guardrail(_plan(30, 20, 9))
        # 30+20+0 = 50 > 40 -> ns=int(40*30/50)=24, ew=16
        assert _durations(plan) == (24, 16, 0)


# ==========================================================================
# correct_final_decision
# ==========================================================================
def _state(cycle=20, peds=0, stopped=0, congestion=0.5):
    return {
        "signals": {"cycle_sec": cycle},
        "pedestrians": {"waiting_or_crossing": peds},
        "queues": {"total_cars": stopped + 5, "stopped_cars": stopped},
        "metrics": {"congestion": congestion},
    }


def _eval(decision="운영자 승인 필요", reason="원본 사유."):
    return {"total_score": 78, "decision_recommendation": decision, "reason": reason}


class TestCorrectFinalDecision:
    def test_total_over_cycle_forces_replan(self):
        ev = correct_final_decision(_state(cycle=20), _plan(12, 8, 6), _eval("자동 적용"))
        assert ev["decision_recommendation"] == "재계획 필요"
        assert ev["reason"].startswith("원본 사유.")
        assert "주기를 초과" in ev["reason"]

    def test_pedestrians_with_short_ped_green_forces_replan(self):
        ev = correct_final_decision(_state(cycle=40, peds=1), _plan(10, 10, 5), _eval("자동 적용"))
        assert ev["decision_recommendation"] == "재계획 필요"
        assert "6초 미만" in ev["reason"]

    def test_no_pedestrians_heavy_queue_forces_auto_apply(self):
        ev = correct_final_decision(_state(cycle=20, peds=0, stopped=25), _plan(12, 8, 0), _eval("재계획 필요"))
        assert ev["decision_recommendation"] == "자동 적용"
        assert "자동 적용으로 보정" in ev["reason"]

    def test_stopped_cars_below_20_does_not_force_auto_apply(self):
        ev = correct_final_decision(_state(cycle=20, peds=0, stopped=19), _plan(12, 8, 0), _eval("운영자 승인 필요"))
        assert ev["decision_recommendation"] == "운영자 승인 필요"
        assert ev["reason"] == "원본 사유."

    def test_no_rule_matches_leaves_evaluation_untouched(self):
        ev_in = _eval("운영자 승인 필요")
        snapshot = copy.deepcopy(ev_in)
        ev = correct_final_decision(_state(cycle=40, peds=2, stopped=5), _plan(10, 10, 6), ev_in)
        assert ev == snapshot

    def test_cycle_rule_takes_precedence_over_auto_apply_rule(self):
        ev = correct_final_decision(_state(cycle=20, peds=0, stopped=30), _plan(15, 10, 0), _eval("자동 적용"))
        assert ev["decision_recommendation"] == "재계획 필요"

    def test_mutates_and_returns_same_evaluation_object(self):
        ev_in = _eval("자동 적용")
        ev_out = correct_final_decision(_state(cycle=20), _plan(12, 8, 6), ev_in)
        assert ev_out is ev_in

    def test_missing_state_fields_fall_back_to_defaults(self):
        # cycle default 40, pedestrians 0, stopped 0 -> nothing fires
        ev = correct_final_decision({}, _plan(12, 8, 0), _eval("운영자 승인 필요"))
        assert ev["decision_recommendation"] == "운영자 승인 필요"

    def test_current_behaviour_mock_scenario_schema_never_triggers_rules(self):
        """Documents the known schema mismatch: mock_scenario uses
        queues.north/south/... and pedestrians.waiting, so the rule inputs all
        read as 0 and no correction ever fires. To be addressed in the data
        layer phase, not here."""
        ev = correct_final_decision(mock_scenario, _plan(12, 8, 0), _eval("운영자 승인 필요"))
        assert ev["decision_recommendation"] == "운영자 승인 필요"
        assert "stopped_cars" not in mock_scenario["queues"]
        assert "waiting_or_crossing" not in mock_scenario["pedestrians"]

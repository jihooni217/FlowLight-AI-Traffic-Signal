"""
Stage 6-5: prompt contract checks (no network).

Agents 1 and 2 must tell the model that `demand` is input demand and
`queues.by_approach` is simulated state, and use by_approach for direction /
allocation. Agent 3's prompt and every output schema stay as they were.
"""
import re

from app.agents import (
    PLAN_EVALUATION_SCHEMA,
    SIGNAL_PLAN_SCHEMA,
    TRAFFIC_ANALYSIS_SCHEMA,
    plan_evaluation_agent_prompt,
    signal_planning_agent_prompt,
    traffic_situation_agent_prompt,
)


def _output_keys(prompt):
    block = prompt.split("출력 형식:")[1]
    return set(re.findall(r'^\s{2}"([a-z_]+)":', block, flags=re.M))


class TestDemandVsQueueDistinction:
    def test_agent1_distinguishes_demand_from_by_approach(self):
        p = traffic_situation_agent_prompt
        assert "demand" in p and "입력 수요" in p
        assert "queues.by_approach" in p and "현재 상태" in p
        assert "대기 차량 수가 아니" in p
        # direction must come from by_approach when present, legacy fallback otherwise
        assert "main_congestion_direction" in p and "N/S/E/W" in p
        assert "없으면 기존 규칙" in p

    def test_agent2_uses_by_approach_for_axis_allocation(self):
        p = signal_planning_agent_prompt
        assert "state.queues.by_approach" in p
        assert "state.demand" in p and "입력 수요" in p
        assert "직접 근거로 쓰지 말고" in p
        assert "north_south_green_sec vs east_west_green_sec" in p
        assert "by_approach 가 없으면 기존 규칙대로" in p

    def test_agent3_prompt_untouched_by_this_stage(self):
        p = plan_evaluation_agent_prompt
        assert "by_approach" not in p
        assert "demand" not in p


class TestSchemasUnchanged:
    def test_output_format_blocks_still_match_schemas(self):
        assert set(TRAFFIC_ANALYSIS_SCHEMA["schema"]["properties"]) == _output_keys(traffic_situation_agent_prompt)
        assert set(SIGNAL_PLAN_SCHEMA["schema"]["properties"]) == _output_keys(signal_planning_agent_prompt)
        assert set(PLAN_EVALUATION_SCHEMA["schema"]["properties"]) == _output_keys(plan_evaluation_agent_prompt)

    def test_main_congestion_direction_stays_free_text(self):
        # directional values like "N" or "남북" must be allowed, so no enum here
        assert "enum" not in TRAFFIC_ANALYSIS_SCHEMA["schema"]["properties"]["main_congestion_direction"]

    def test_json_word_still_present_for_json_object_fallback(self):
        for p in (traffic_situation_agent_prompt, signal_planning_agent_prompt, plan_evaluation_agent_prompt):
            assert "JSON" in p

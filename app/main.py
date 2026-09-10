import logging
import json
import os
from functools import lru_cache
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body, HTTPException

from app.agents import (
    mock_scenario,
    traffic_situation_agent,
    signal_planning_agent,
    plan_evaluation_agent,
    is_error,
    apply_guardrail,
)
from app.traffic_data import (
    APPROACHES,
    DEMAND_NOTE,
    TrafficDataError,
    load_profile_from_meta,
    validate_hour,
)

app = FastAPI(title="FlowLight Agent Backend MVP")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("flowlight")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def format_sse(event: str, data: dict):
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

def correct_final_decision(state: dict, signal_plan: dict, evaluation: dict):
    durations = signal_plan.get("durations", {})

    ns = int(durations.get("north_south_green_sec", 0))
    ew = int(durations.get("east_west_green_sec", 0))
    ped = int(durations.get("pedestrian_green_sec", 0))

    cycle_sec = int(state.get("signals", {}).get("cycle_sec", 40))
    pedestrian_count = int(state.get("pedestrians", {}).get("waiting_or_crossing", 0))
    vulnerable_count = int(state.get("pedestrians", {}).get("vulnerable_count", 0))
    stopped_cars = int(state.get("queues", {}).get("stopped_cars", 0))
    congestion = float(state.get("metrics", {}).get("congestion", 0))

    total_signal_time = ns + ew + ped

    if total_signal_time > cycle_sec:
        evaluation["decision_recommendation"] = "재계획 필요"
        evaluation["reason"] += " 백엔드 검증 결과, 신호 시간 합계가 현재 주기를 초과하여 재계획 필요로 보정했습니다."
        return evaluation

    if pedestrian_count >= 1 and ped < 6:
        evaluation["decision_recommendation"] = "재계획 필요"
        evaluation["reason"] += " 백엔드 검증 결과, 보행자가 존재하지만 보행자 신호 시간이 6초 미만이므로 재계획 필요로 보정했습니다."
        return evaluation

    # 교통약자(어린이·노약자·휠체어)는 횡단이 느리므로 10초 미만이면 재계획. Guardrail 이 10초로 올리므로 보통은 걸리지 않는다.
    if vulnerable_count >= 1 and ped < 10:
        evaluation["decision_recommendation"] = "재계획 필요"
        evaluation["reason"] += " 백엔드 검증 결과, 교통약자가 있는데 보행자 신호 시간이 10초 미만이므로 재계획 필요로 보정했습니다."
        return evaluation

    # 프롬프트의 자동 적용 선결 조건과 동일하게 맞춘다: 보행자 0명, 정지 20대 이상, 혼잡도 0.7 이상, 보행자 신호 0초.
    # (이전에는 congestion 을 읽기만 하고 조건에 쓰지 않아 프롬프트보다 느슨했다.)
    if pedestrian_count == 0 and stopped_cars >= 20 and congestion >= 0.7 and ped == 0:
        evaluation["decision_recommendation"] = "자동 적용"
        evaluation["reason"] += " 백엔드 검증 결과, 보행자가 없고 차량 혼잡이 높아 자동 적용으로 보정했습니다."
        return evaluation

    return evaluation

@app.get("/")
def health_check():
    return {"status": "ok", "service": "FlowLight Agent Backend"}


# ---------------------------------------------------------------------------
# 교통 수요 프로파일 조회 (6-2)
# data/*.meta.json → app.traffic_data → 정규화 프로파일. 응답에는 시간대별 입력 수요(volume, 대/시)와
# 백엔드가 계산한 차량 발생률(arrival_rate_per_sec, 차로당 대/초)만 담긴다. queue 는 시뮬레이션 결과라 없다.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRAFFIC_PROFILE_META = PROJECT_ROOT / "data" / "sample_seoul_traffic_history.meta.json"
APPROACH_NAMING = "N = 북측에서 진입해 남쪽으로 향하는 차량 (S/E/W 도 같은 규칙)"


def traffic_profile_meta_path() -> Path:
    """환경 변수 TRAFFIC_PROFILE_META 로 다른 메타 파일을 지정할 수 있다. 기본은 6-1 샘플."""
    return Path(os.getenv("TRAFFIC_PROFILE_META") or DEFAULT_TRAFFIC_PROFILE_META)


@lru_cache(maxsize=4)
def get_traffic_profile(meta_path: str):
    """메타 경로별로 한 번만 읽는다. 로드 실패는 캐시되지 않는다."""
    return load_profile_from_meta(meta_path)


def profile_to_payload(profile, hours, meta_file: str) -> dict:
    return {
        "meta": {
            **profile.to_dict()["meta"],
            "profile_file": meta_file,
            "approach_naming": APPROACH_NAMING,
            "note": DEMAND_NOTE,
        },
        "available_hours": profile.available_hours(),
        "hours": [
            {
                **hv.to_dict(),
                "arrival_rate_per_sec": {
                    a: round(r, 6) for a, r in profile.arrival_rates(hv.hour).items()
                },
            }
            for hv in hours
        ],
    }


@app.get("/api/traffic/profile")
def traffic_profile(hour: str | None = None):
    meta_path = traffic_profile_meta_path()
    try:
        profile = get_traffic_profile(str(meta_path))
    except TrafficDataError as e:
        raise HTTPException(status_code=500, detail=f"교통 프로파일을 불러올 수 없습니다: {e}")

    hours = profile.hours
    if hour is not None:
        try:
            wanted = validate_hour(hour)
        except TrafficDataError as e:
            raise HTTPException(status_code=400, detail=str(e))
        try:
            hours = [profile.hour(wanted)]
        except TrafficDataError as e:
            raise HTTPException(status_code=404, detail=str(e))

    return profile_to_payload(profile, hours, meta_path.name)


@app.get("/api/agent/stream")
def stream_agent():
    def event_generator():
        try:
            yield format_sse("message", {"step": 1, "message": "교통 상황 분석 시작"})

            traffic_analysis = traffic_situation_agent(mock_scenario)

            if is_error(traffic_analysis):
                yield format_sse("error", traffic_analysis)
                return

            yield format_sse("message", {"step": 2, "message": "신호 계획 생성 시작"})

            signal_plan = signal_planning_agent({
                "state": mock_scenario,
                "traffic_analysis": traffic_analysis
            })

            if is_error(signal_plan):
                yield format_sse("error", signal_plan)
                return

            cycle_sec = mock_scenario.get("signals", {}).get("cycle_sec", 40)
            pedestrian_count = mock_scenario.get("pedestrians", {}).get("waiting_or_crossing", 0)
            vulnerable_count = mock_scenario.get("pedestrians", {}).get("vulnerable_count", 0)

            before_durations = dict(signal_plan.get("durations", {}))
            signal_plan = apply_guardrail(
                signal_plan,
                cycle_sec=cycle_sec,
                pedestrian_count=pedestrian_count,
                vulnerable_count=vulnerable_count
            )

            yield format_sse("message", {
                "step": "guardrail",
                "message": "최소 신호 시간 Guardrail 적용 완료",
                "durations": signal_plan["durations"],
                "before": before_durations
            })

            yield format_sse("message", {"step": 3, "message": "계획 평가 시작"})

            evaluation = plan_evaluation_agent({
                "state": mock_scenario,
                "traffic_analysis": traffic_analysis,
                "signal_plan": signal_plan
            })

            if is_error(evaluation):
                yield format_sse("error", evaluation)
                return
            
            evaluation = correct_final_decision(mock_scenario, signal_plan, evaluation)

            final_result = {
                "input_state": mock_scenario,
                "traffic_analysis": traffic_analysis,
                "signal_plan": signal_plan,
                "evaluation": evaluation,
                "final_decision": evaluation["decision_recommendation"]
            }

            yield format_sse("done", final_result)

        except Exception as e:
            yield format_sse("error", {
                "message": "SSE 실행 중 오류가 발생했습니다.",
                "detail": str(e)
            })

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/agent/stream")
def stream_agent_with_state(state: dict = Body(...)):
    def event_generator():
        try:
            yield format_sse("message", {"step": 1, "message": "시뮬레이션 데이터 수신 완료"})
            yield format_sse("message", {"step": 2, "message": "교통 상황 분석 시작"})

            traffic_analysis = traffic_situation_agent(state)

            if is_error(traffic_analysis):
                yield format_sse("error", traffic_analysis)
                return

            yield format_sse("message", {"step": 3, "message": "신호 계획 생성 시작"})

            signal_plan = signal_planning_agent({
                "state": state,
                "traffic_analysis": traffic_analysis
            })

            if is_error(signal_plan):
                yield format_sse("error", signal_plan)
                return

            cycle_sec = state.get("signals", {}).get("cycle_sec", 40)
            pedestrian_count = state.get("pedestrians", {}).get("waiting_or_crossing", 0)
            vulnerable_count = state.get("pedestrians", {}).get("vulnerable_count", 0)

            # 프론트가 보정 여부를 표시할 수 있도록 Guardrail 적용 전 값을 함께 보낸다.
            # (apply_guardrail 은 같은 dict 를 제자리 수정하므로 복사해 둔다.)
            before_durations = dict(signal_plan.get("durations", {}))
            signal_plan = apply_guardrail(
                signal_plan,
                cycle_sec=cycle_sec,
                pedestrian_count=pedestrian_count,
                vulnerable_count=vulnerable_count
            )

            yield format_sse("message", {
                "step": "guardrail",
                "message": "최소 신호 시간 Guardrail 적용 완료",
                "durations": signal_plan["durations"],
                "before": before_durations
            })

            yield format_sse("message", {"step": 4, "message": "계획 평가 시작"})

            evaluation = plan_evaluation_agent({
                "state": state,
                "traffic_analysis": traffic_analysis,
                "signal_plan": signal_plan
            })

            if is_error(evaluation):
                yield format_sse("error", evaluation)
                return

            evaluation = correct_final_decision(state, signal_plan, evaluation)

            final_result = {
                "input_state": state,
                "traffic_analysis": traffic_analysis,
                "signal_plan": signal_plan,
                "evaluation": evaluation,
                "final_decision": evaluation["decision_recommendation"]
            }

            yield format_sse("done", final_result)

        except Exception as e:
            yield format_sse("error", {
                "message": "SSE 실행 중 오류가 발생했습니다.",
                "detail": str(e)
            })

    return StreamingResponse(event_generator(), media_type="text/event-stream")
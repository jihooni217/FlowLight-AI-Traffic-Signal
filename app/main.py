import logging
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Body

from app.agents import (
    mock_scenario,
    traffic_situation_agent,
    signal_planning_agent,
    plan_evaluation_agent,
    is_error,
    apply_guardrail,
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

    if pedestrian_count == 0 and stopped_cars >= 20 and ped == 0:
        evaluation["decision_recommendation"] = "자동 적용"
        evaluation["reason"] += " 백엔드 검증 결과, 보행자가 없고 차량 혼잡이 높아 자동 적용으로 보정했습니다."
        return evaluation

    return evaluation

@app.get("/")
def health_check():
    return {"status": "ok", "service": "FlowLight Agent Backend"}


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

            signal_plan = apply_guardrail(
                signal_plan,
                cycle_sec=cycle_sec,
                pedestrian_count=pedestrian_count
            )

            yield format_sse("message", {
                "step": "guardrail",
                "message": "최소 신호 시간 Guardrail 적용 완료",
                "durations": signal_plan["durations"]
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

            signal_plan = apply_guardrail(
                signal_plan,
                cycle_sec=cycle_sec,
                pedestrian_count=pedestrian_count
            )

            yield format_sse("message", {
                "step": "guardrail",
                "message": "최소 신호 시간 Guardrail 적용 완료",
                "durations": signal_plan["durations"]
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
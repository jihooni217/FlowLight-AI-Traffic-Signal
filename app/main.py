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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def format_sse(event: str, data: dict):
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


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

            signal_plan = apply_guardrail(signal_plan)

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

            signal_plan = apply_guardrail(signal_plan)

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
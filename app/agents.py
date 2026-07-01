import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("UPSTAGE_API_KEY"),
    base_url="https://api.upstage.ai/v1"
)

mock_scenario = {
    "intersection_id": "intersection-A",
    "tick": 0,
    "signals": {
        "north_south": "RED",
        "east_west": "GREEN",
        "pedestrian": "RED"
    },
    "queues": {
        "north": 9,
        "south": 9,
        "east": 2,
        "west": 1
    },
    "pedestrians": {
        "waiting": 2,
        "vulnerable": 1
    },
    "context": {
        "time_of_day": "rush_hour",
        "current_phase": "EAST_WEST_GREEN"
    },
    "metrics": {
        "avg_vehicle_wait_sec": 42,
        "avg_pedestrian_wait_sec": 28,
        "idle_vehicle_count": 18
    }
}


def call_solar_agent(agent_name: str, system_prompt: str, user_input: dict):
    try:
        response = client.chat.completions.create(
            model="solar-pro3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_input, ensure_ascii=False)}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        return json.loads(content)

    except Exception as e:
        return {
            "status": "error",
            "agent": agent_name,
            "message": "Solar API 호출에 실패했습니다.",
            "detail": str(e)
        }


traffic_situation_agent_prompt = """
너는 FlowLight 시스템의 교통 상황 판단 에이전트이다.
입력된 교차로 상태 데이터를 분석한다.

출력 규칙:
- 반드시 JSON 형식만 출력한다.
- summary는 한국어로 작성한다.
- traffic_level은 "낮음", "보통", "높음" 중 하나만 사용한다.
- main_congestion_direction은 "남북", "동서", "없음" 중 하나만 사용한다.
- pedestrian_issue와 vulnerable_user_detected는 true 또는 false로 출력한다.
- risk_level은 "낮음", "보통", "높음" 중 하나만 사용한다.

출력 형식:
{
  "summary": "현재 교통 상황 요약",
  "traffic_level": "높음",
  "main_congestion_direction": "남북",
  "pedestrian_issue": true,
  "vulnerable_user_detected": true,
  "risk_level": "높음"
}
"""


signal_planning_agent_prompt = """
너는 FlowLight 시스템의 신호 계획 에이전트이다.

출력 규칙:
- 반드시 JSON 형식만 출력한다.
- plan_id는 "PLAN-001"로 작성한다.
- next_signals 값은 "GREEN" 또는 "RED"만 사용한다.
- 차량 녹색 시간은 최소 30초, 최대 60초로 설정한다.
- 보행자 녹색 시간은 최소 30초, 최대 60초로 설정한다.
- priority는 "VEHICLE", "PEDESTRIAN", "BALANCED" 중 하나만 사용한다.
- explanation은 한국어로 작성한다.

출력 형식:
{
  "plan_id": "PLAN-001",
  "next_signals": {
    "north_south": "GREEN",
    "east_west": "RED",
    "pedestrian": "GREEN"
  },
  "durations": {
    "north_south_green_sec": 45,
    "east_west_green_sec": 30,
    "pedestrian_green_sec": 35
  },
  "priority": "BALANCED",
  "explanation": "신호 계획을 선택한 이유"
}
"""


plan_evaluation_agent_prompt = """
너는 FlowLight 시스템의 계획 평가 에이전트이다.

출력 규칙:
- 반드시 JSON 형식만 출력한다.
- total_score는 0~100 사이의 정수이다.
- decision_recommendation은 "자동 적용", "운영자 승인 필요", "재계획 필요" 중 하나만 사용한다.
- reason은 한국어로 작성한다.

출력 형식:
{
  "total_score": 86,
  "scores": {
    "vehicle": 22,
    "pedestrian": 18,
    "vulnerable_user": 20,
    "safety": 18,
    "efficiency": 8
  },
  "decision_recommendation": "운영자 승인 필요",
  "reason": "평가 이유"
}
"""


def traffic_situation_agent(state: dict):
    return call_solar_agent("Traffic Situation Agent", traffic_situation_agent_prompt, state)


def signal_planning_agent(context: dict):
    return call_solar_agent("Signal Planning Agent", signal_planning_agent_prompt, context)


def plan_evaluation_agent(context: dict):
    return call_solar_agent("Plan Evaluation Agent", plan_evaluation_agent_prompt, context)


def is_error(result: dict):
    return isinstance(result, dict) and result.get("status") == "error"


def apply_guardrail(signal_plan: dict):
    durations = signal_plan["durations"]

    durations["north_south_green_sec"] = max(durations["north_south_green_sec"], 30)
    durations["east_west_green_sec"] = max(durations["east_west_green_sec"], 30)
    durations["pedestrian_green_sec"] = max(durations["pedestrian_green_sec"], 30)

    return signal_plan
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
너는 FlowLight 시스템의 교통 상황 분석 에이전트이다.

입력으로 현재 시뮬레이션 상태(JSON)를 받는다.
반드시 입력값을 기준으로 교통 혼잡도를 판단해야 한다.
예시 문장을 그대로 반복하지 마라.

[판단 기준]

1. total_cars와 stopped_cars를 반드시 확인한다.
- queues.total_cars 또는 state.queues.total_cars
- queues.stopped_cars 또는 state.queues.stopped_cars

2. congestion 값을 반드시 확인한다.
- metrics.congestion 또는 state.metrics.congestion

3. traffic_level 판단:
- congestion >= 0.7 이거나 stopped_cars >= 20 이면 "높음"
- congestion >= 0.3 이거나 stopped_cars >= 8 이면 "보통"
- 그 외는 "낮음"

4. pedestrian_issue 판단:
- waiting_or_crossing >= 5 이면 true
- 그 외는 false

5. risk_level 판단:
- traffic_level이 "높음"이고 pedestrian_issue가 true이면 "높음"
- traffic_level이 "높음"이면 "보통"
- 그 외는 "낮음"

6. main_congestion_direction은 방향 정보가 없으면 "전체" 또는 "없음"으로 작성한다.

반드시 JSON만 출력한다.

출력 형식:
{
  "summary": "현재 차량 수, 정지 차량 수, 혼잡도, 보행자 수를 근거로 한 요약",
  "traffic_level": "낮음/보통/높음",
  "main_congestion_direction": "전체",
  "pedestrian_issue": false,
  "vulnerable_user_detected": false,
  "risk_level": "낮음/보통/높음"
}
"""

signal_planning_agent_prompt = """
너는 FlowLight 시스템의 신호 계획 에이전트이다.

입력으로 state와 traffic_analysis를 받는다.
반드시 현재 교통 상태에 따라 신호 시간을 다르게 결정한다.

[판단 기준]

1. 참고할 입력값
- state.signals.cycle_sec
- state.queues.total_cars
- state.queues.stopped_cars
- state.pedestrians.waiting_or_crossing
- state.metrics.congestion
- state.metrics.throughput_per_min
- traffic_analysis.traffic_level
- traffic_analysis.pedestrian_issue
- traffic_analysis.risk_level

2. 보행자가 0명인 경우
- pedestrian_green_sec는 0으로 설정한다.
- priority는 "VEHICLE"로 설정한다.
- 차량 녹색 시간을 우선 배분한다.

3. 보행자가 1~4명인 경우
- pedestrian_green_sec는 6~8초로 설정한다.
- 차량 흐름과 보행자 안전을 균형 있게 고려한다.

4. 보행자가 5명 이상인 경우
- pedestrian_green_sec는 10~14초로 설정한다.
- priority는 "PEDESTRIAN" 또는 "BALANCED"로 설정한다.

[우선순위 선택 규칙]
- 보행자 대기 인원이 10명 이상이고 congestion이 0.7 이상이면 priority는 반드시 "BALANCED"로 설정한다.
- 보행자 대기 인원이 10명 이상이고 congestion이 0.7 미만이면 priority는 "PEDESTRIAN"으로 설정한다.
- 보행자 대기 인원이 0명이고 congestion이 0.7 이상이면 priority는 "VEHICLE"로 설정한다.
- 그 외의 경우에는 priority를 "BALANCED"로 설정한다.

5. 혼잡도가 높거나 정지 차량이 많으면
- 차량 녹색 시간을 늘린다.
- traffic_level이 "높음"이면 남북/동서 차량 녹색 시간 중 최소 하나는 12초 이상으로 설정한다.

6. 혼잡도가 낮으면
- 전체 신호 시간을 짧게 유지한다.

7. 전체 신호 시간 합계는 state.signals.cycle_sec를 초과하지 않는다.
- north_south_green_sec + east_west_green_sec + pedestrian_green_sec <= state.signals.cycle_sec

8. 반드시 JSON만 출력한다.

[중요]
- 출력 형식의 숫자는 예시가 아니다.
- north_south_green_sec, east_west_green_sec, pedestrian_green_sec는 반드시 입력값을 보고 새로 계산한 정수로 출력한다.
- 보행자 수가 0명이고 혼잡도가 매우 높으면 차량 신호 합계가 cycle_sec와 같아도 된다.
- 단, 매번 12초/8초를 반복하지 마라.

출력 형식:
{
  "plan_id": "PLAN-001",
  "next_signals": {
    "north_south": "GREEN",
    "east_west": "RED",
    "pedestrian": "RED"
  },
  "durations": {
    "north_south_green_sec": "현재 차량/정지차량/혼잡도에 따라 계산한 정수",
    "east_west_green_sec": "현재 차량/정지차량/혼잡도에 따라 계산한 정수",
    "pedestrian_green_sec": "보행자 수에 따라 계산한 정수"
  },
  "priority": "VEHICLE / PEDESTRIAN / BALANCED 중 하나",
  "explanation": "왜 이 신호 시간을 선택했는지 입력값 기반으로 설명"
}
"""

plan_evaluation_agent_prompt = """
너는 FlowLight 시스템의 신호 계획 평가 에이전트이다.

입력으로 다음 정보를 받는다.
- state: 현재 시뮬레이션 상태
- traffic_analysis: 교통 상황 분석 결과
- signal_plan: 신호 계획 결과

반드시 입력값을 기준으로 평가해야 하며, 예시 숫자를 반복해서는 안 된다.

[평가 기준]

1. total_score는 0~100 사이의 정수로 계산한다.

2. 차량 흐름 점수 vehicle은 다음을 고려한다.
- state.queues.total_cars
- state.queues.stopped_cars
- state.metrics.congestion
- state.metrics.throughput_per_min

3. 보행자 점수 pedestrian은 다음을 고려한다.
- state.pedestrians.waiting_or_crossing
- signal_plan.durations.pedestrian_green_sec

4. 안전 점수 safety는 다음을 고려한다.
- state.pedestrians.waiting_or_crossing가 0명이면 pedestrian_green_sec가 0초여도 감점하지 않는다.
- state.pedestrians.waiting_or_crossing가 1명 이상인데 pedestrian_green_sec가 6초 미만이면 감점한다.
- 전체 신호 시간이 state.signals.cycle_sec를 초과하면 크게 감점한다.

5. 효율 점수 efficiency는 다음을 고려한다.
- 혼잡도가 높을 때 차량 녹색 시간이 충분하면 가점한다.
- 혼잡도가 낮은데 너무 긴 신호를 주면 감점한다.

[자동 적용 판단 규칙]

아래 조건은 점수보다 우선한다.

1. 다음 조건을 모두 만족하면 total_score와 관계없이 반드시 "자동 적용"으로 판단한다.
- state.pedestrians.waiting_or_crossing == 0
- traffic_analysis.traffic_level == "높음"
- state.metrics.congestion >= 0.7
- state.queues.stopped_cars >= 20
- signal_plan.durations.pedestrian_green_sec == 0
- 신호 시간 합계가 state.signals.cycle_sec 이내

2. 보행자가 1명 이상인데 pedestrian_green_sec가 6초 미만이면 반드시 "재계획 필요"로 판단한다.

3. 신호 시간 합계가 state.signals.cycle_sec를 초과하면 반드시 "재계획 필요"로 판단한다.

4. 위 조건에 해당하지 않는 경우:
- total_score가 85 이상이면 "자동 적용"
- total_score가 65 이상 84 이하이면 "운영자 승인 필요"
- total_score가 64 이하이면 "재계획 필요"

[중요]
- 매번 같은 점수를 출력하지 마라.
- 입력 상태에 따라 total_score와 세부 점수를 다르게 계산하라.
- 반드시 JSON만 출력한다.

출력 형식:
{
  "total_score": 78,
  "scores": {
    "vehicle": 20,
    "pedestrian": 15,
    "vulnerable_user": 15,
    "safety": 18,
    "efficiency": 10
  },
  "decision_recommendation": "운영자 승인 필요",
  "reason": "현재 상태와 신호 계획을 평가한 이유"
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


def apply_guardrail(signal_plan: dict, cycle_sec: int = 40, pedestrian_count: int = 0):
    durations = signal_plan["durations"]

    ns = int(durations.get("north_south_green_sec", 15))
    ew = int(durations.get("east_west_green_sec", 15))
    ped = int(durations.get("pedestrian_green_sec", 0))

    # 1. 기본 최소값
    ns = max(8, ns)
    ew = max(8, ew)

    if pedestrian_count <= 0:
        ped = 0
    else:
        ped = max(6, ped)

    # 2. 주기 초과 방지
    total = ns + ew + ped

    if total > cycle_sec:
        if pedestrian_count <= 0:
            ped = 0
            available = cycle_sec
        else:
            ped = 6
            available = cycle_sec - ped

        # 차량 신호에 배분 가능한 시간이 부족하면 최소값도 줄여서라도 주기 안에 맞춤
        if available < 16:
            ns = max(4, available // 2)
            ew = max(4, available - ns)
        else:
            # 기존 비율 유지하면서 차량 시간만 재배분
            vehicle_total = ns + ew
            ns = max(8, int(available * ns / vehicle_total))
            ew = available - ns

            if ew < 8:
                ew = 8
                ns = available - ew

            if ns < 8:
                ns = 8
                ew = available - ns

    durations["north_south_green_sec"] = int(ns)
    durations["east_west_green_sec"] = int(ew)
    durations["pedestrian_green_sec"] = int(ped)

    return signal_plan
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("UPSTAGE_API_KEY"),
    base_url="https://api.upstage.ai/v1"
)

# Solar 모델 선택.
# .env 의 UPSTAGE_MODEL 로 덮어쓸 수 있다. 예: "solar-pro3"(롤백), "solar-pro4-260806"(스냅샷 고정).
# 값이 없거나 비어 있으면 기본값을 쓴다. 호출 시점에 읽으므로 서버 재시작 없이 테스트에서 바꿀 수 있다.
DEFAULT_SOLAR_MODEL = "solar-pro4"


def get_solar_model() -> str:
    return os.getenv("UPSTAGE_MODEL") or DEFAULT_SOLAR_MODEL


# 출력 형식 모드.
# "json_schema": Upstage structured outputs. 필드명·타입·enum 을 서버가 강제한다 (기본값).
# "json_object": JSON 문법만 보장하는 기존 방식. 문제 시 .env 에 UPSTAGE_OUTPUT_MODE=json_object 로 즉시 복귀.
DEFAULT_OUTPUT_MODE = "json_schema"
OUTPUT_MODES = ("json_schema", "json_object")


def get_output_mode() -> str:
    mode = os.getenv("UPSTAGE_OUTPUT_MODE") or DEFAULT_OUTPUT_MODE
    return mode if mode in OUTPUT_MODES else DEFAULT_OUTPUT_MODE


def build_response_format(output_schema: dict | None) -> dict:
    """schema 가 없거나 모드가 json_object 이면 기존 json_object, 아니면 strict json_schema."""
    if output_schema is None or get_output_mode() == "json_object":
        return {"type": "json_object"}
    return {"type": "json_schema", "json_schema": output_schema}

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


def call_solar_agent(agent_name: str, system_prompt: str, user_input: dict, output_schema: dict | None = None):
    try:
        response = client.chat.completions.create(
            model=get_solar_model(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_input, ensure_ascii=False)}
            ],
            temperature=0.2,
            response_format=build_response_format(output_schema)
        )

        choice = response.choices[0]

        # Upstage 문서: finish_reason 이 "stop" 이 아니면(예: "length") content 가 잘려 있거나
        # null 이므로 파싱하지 말고 실패로 다뤄야 한다.
        finish_reason = getattr(choice, "finish_reason", None)
        if finish_reason != "stop":
            return {
                "status": "error",
                "agent": agent_name,
                "message": "Solar 응답이 정상 종료되지 않았습니다.",
                "detail": f"finish_reason={finish_reason}"
            }

        content = choice.message.content
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

[입력 구분 — 반드시 지킨다]
- demand 가 있으면 그것은 "입력 수요"다 (volume_per_hour: 대/시, arrival_rate_per_sec: 차로당 대/초).
  현재 대기 차량 수가 아니므로 queue 나 stopped_cars 와 비교하거나 대기 차량 수로 해석하지 마라.
- queues.by_approach 가 있으면 그것은 시뮬레이션이 계산한 "현재 상태"다.
  접근로 N/S/E/W 별 queue(대기 차량 수), mean_wait_sec, arrivals_last_window, saturation 을 담는다.
- queues.by_approach 가 있으면 main_congestion_direction 은 queue 와 saturation 이 가장 큰 접근로 이름(N/S/E/W)으로 적고,
  남북(N,S) 또는 동서(E,W) 두 접근로가 함께 크면 "남북" 또는 "동서"로 적는다. 모든 접근로가 비슷하면 "전체".
- summary 에는 방향별 상태를 근거로 어느 접근로가 왜 혼잡한지 한 문장 포함한다.
- demand 나 queues.by_approach 가 없으면 기존 규칙(total_cars, stopped_cars, congestion)만으로 판단한다.

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
- state.queues.by_approach (있을 때: 접근로 N/S/E/W 별 queue, mean_wait_sec, arrivals_last_window, saturation)
- state.demand (있을 때: 입력 수요. volume_per_hour 는 대/시, arrival_rate_per_sec 는 차로당 대/초)

[입력 구분 — 반드시 지킨다]
- demand 는 입력 수요일 뿐 현재 대기 차량 수가 아니다. 녹색 시간 배분의 직접 근거로 쓰지 말고 참고만 한다.
- queues.by_approach 는 시뮬레이션이 계산한 현재 상태다. 있으면 다음 규칙으로 방향별 배분을 정한다.
  - 남북 축 = N 과 S 의 queue 합과 saturation, 동서 축 = E 와 W 의 queue 합과 saturation 을 비교한다.
  - 대기와 포화도가 큰 축에 차량 녹색 시간을 더 배분한다 (north_south_green_sec vs east_west_green_sec).
  - 두 축이 비슷하면 균등에 가깝게 배분한다.
  - explanation 에 어느 축에 왜 더 배분했는지 by_approach 의 수치를 들어 설명한다.
- queues.by_approach 가 없으면 기존 규칙대로 결정한다.

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


# ---------------------------------------------------------------------------
# Structured outputs 용 JSON Schema.
# 각 프롬프트의 "출력 형식" 블록과 1:1 로 대응한다. 필드명은 프롬프트와 동일하며,
# 프롬프트가 산문으로만 적어 둔 타입(정수)과 허용값(enum)을 서버가 강제하도록 만든다.
# Upstage 제약: root 는 object, 모든 property 를 required 에 포함, 모든 object 에
# additionalProperties: false, strict: true. 지원 타입만 사용 (minimum/maximum 등은 쓰지 않음).
# ---------------------------------------------------------------------------
_LEVEL_ENUM = ["낮음", "보통", "높음"]

TRAFFIC_ANALYSIS_SCHEMA = {
    "name": "traffic_analysis",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "summary": {"type": "string", "description": "현재 차량 수, 정지 차량 수, 혼잡도, 보행자 수를 근거로 한 요약"},
            "traffic_level": {"type": "string", "enum": _LEVEL_ENUM},
            "main_congestion_direction": {"type": "string", "description": "방향 정보가 없으면 '전체' 또는 '없음'"},
            "pedestrian_issue": {"type": "boolean"},
            "vulnerable_user_detected": {"type": "boolean"},
            "risk_level": {"type": "string", "enum": _LEVEL_ENUM},
        },
        "required": [
            "summary", "traffic_level", "main_congestion_direction",
            "pedestrian_issue", "vulnerable_user_detected", "risk_level",
        ],
        "additionalProperties": False,
    },
}

SIGNAL_PLAN_SCHEMA = {
    "name": "signal_plan",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "plan_id": {"type": "string"},
            "next_signals": {
                "type": "object",
                "properties": {
                    "north_south": {"type": "string", "enum": ["RED", "GREEN"]},
                    "east_west": {"type": "string", "enum": ["RED", "GREEN"]},
                    "pedestrian": {"type": "string", "enum": ["RED", "GREEN"]},
                },
                "required": ["north_south", "east_west", "pedestrian"],
                "additionalProperties": False,
            },
            "durations": {
                "type": "object",
                "properties": {
                    "north_south_green_sec": {"type": "integer", "description": "현재 차량/정지차량/혼잡도에 따라 계산한 정수(초)"},
                    "east_west_green_sec": {"type": "integer", "description": "현재 차량/정지차량/혼잡도에 따라 계산한 정수(초)"},
                    "pedestrian_green_sec": {"type": "integer", "description": "보행자 수에 따라 계산한 정수(초)"},
                },
                "required": ["north_south_green_sec", "east_west_green_sec", "pedestrian_green_sec"],
                "additionalProperties": False,
            },
            "priority": {"type": "string", "enum": ["VEHICLE", "PEDESTRIAN", "BALANCED"]},
            "explanation": {"type": "string", "description": "왜 이 신호 시간을 선택했는지 입력값 기반으로 설명"},
        },
        "required": ["plan_id", "next_signals", "durations", "priority", "explanation"],
        "additionalProperties": False,
    },
}

PLAN_EVALUATION_SCHEMA = {
    "name": "plan_evaluation",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "total_score": {"type": "integer", "description": "0~100 사이의 정수"},
            "scores": {
                "type": "object",
                "properties": {
                    "vehicle": {"type": "integer"},
                    "pedestrian": {"type": "integer"},
                    "vulnerable_user": {"type": "integer"},
                    "safety": {"type": "integer"},
                    "efficiency": {"type": "integer"},
                },
                "required": ["vehicle", "pedestrian", "vulnerable_user", "safety", "efficiency"],
                "additionalProperties": False,
            },
            "decision_recommendation": {"type": "string", "enum": ["자동 적용", "운영자 승인 필요", "재계획 필요"]},
            "reason": {"type": "string", "description": "현재 상태와 신호 계획을 평가한 이유"},
        },
        "required": ["total_score", "scores", "decision_recommendation", "reason"],
        "additionalProperties": False,
    },
}


def traffic_situation_agent(state: dict):
    return call_solar_agent("Traffic Situation Agent", traffic_situation_agent_prompt, state, TRAFFIC_ANALYSIS_SCHEMA)


def signal_planning_agent(context: dict):
    return call_solar_agent("Signal Planning Agent", signal_planning_agent_prompt, context, SIGNAL_PLAN_SCHEMA)


def plan_evaluation_agent(context: dict):
    return call_solar_agent("Plan Evaluation Agent", plan_evaluation_agent_prompt, context, PLAN_EVALUATION_SCHEMA)


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
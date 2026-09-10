# 🚦 FlowLight AI Traffic Signal Optimization

> **Upstage Solar Pro 4 기반 Multi-Agent 교통 신호 최적화 데모**
> 실제 교통량 데이터로 차량을 발생시키는 브라우저 시뮬레이터와, 그 상태를 읽고 신호 계획을 세우는 세 개의 LLM Agent를
> FastAPI + SSE(Server-Sent Events)로 연결한 프로젝트입니다. AI의 의사결정 과정을 단계별로 실시간 확인할 수 있습니다.

---

# 📌 프로젝트 소개

FlowLight는 고정 시간 신호 대신 **LLM Agent 세 개**가 교통 상황을 분석하고 신호 시간을 계획한 뒤 스스로 평가하는 구조입니다.
LLM 출력은 **Structured Outputs(JSON Schema)** 로 형식이 강제되고, **Guardrail**(규칙 기반 안전 장치)을 거친 뒤에만 시뮬레이터에 적용됩니다.

이 저장소는 Upstage 공식 Demo/튜토리얼로 발전시키는 중이며, 다음 원칙을 따릅니다.

- 실제 **시간당 교통량(volume)** 을 **차량 발생률(arrival rate)** 로 변환해 시뮬레이터에 차량을 만들고, **대기 차량 수(queue)** 는 시뮬레이터가 계산합니다.
  842대/시라는 교통량을 대기 차량 842대로 취급하지 않습니다.
- LLM의 내부 추론(reasoning)은 사용하지 않으며, 화면에는 Agent가 **명시적으로 반환한** `summary` / `explanation` / `reason` 만 보여 줍니다.

---

# 🏗 시스템 구조

<p align="center">
  <img src="docs/architecture.png" alt="FlowLight System Architecture" width="1000">
</p>

```
공공 교통량 CSV ─(app/traffic_data.py: 정규화·차로 보정·대/시 → 대/초)─▶ 수요 프로파일
   ─(GET /api/traffic/profile)─▶ 브라우저 시뮬레이터 (3x3 교차로, 접근로별 Poisson 도착)
   ─(접근로별 queue·대기시간·도착·포화도 집계)─▶ scenario JSON (demand + queues.by_approach)
   ─(POST /api/agent/stream, SSE)─▶ Agent 1 분석 → Agent 2 계획 → Guardrail → Agent 3 평가 → 최종 판단
   ─▶ 화면 표시 및 신호 적용
```

## 세 가지 값의 구분

| 값 | 의미 | 어디서 나오나 |
|---|---|---|
| `volume_per_hour` | 실제 입력 수요 (대/시) | 공공 데이터 |
| `arrival_rate_per_sec` | 시뮬레이터 차량 발생률 (차로당 대/초) = `volume / lanes / 3600` | 백엔드 `traffic_data.py` |
| `queue` | 현재 대기 차량 수 | **시뮬레이션 결과** (신호·차간 상호작용) |

---

# ✨ 주요 기능

## 🚗 Traffic Situation Agent (Agent 1)
- 차량 수·정지 차량·혼잡도·보행자 수로 교통 수준과 위험도를 판단
- `queues.by_approach` 가 있으면 접근로별 대기·포화도로 **주요 혼잡 방향**(N/S/E/W, 남북/동서)을 판정
- 출력: `summary`, `traffic_level`, `main_congestion_direction`, `pedestrian_issue`, `vulnerable_user_detected`, `risk_level`

## 🤖 Signal Planning Agent (Agent 2)
- 남북/동서 차량 녹색 시간과 보행자 녹색 시간을 정수 초로 계획
- 접근로별 상태가 있으면 대기·포화도가 큰 축에 녹색을 더 배분하고 `explanation` 에 근거 수치를 명시
- 출력: `durations`(3개 정수), `priority`(VEHICLE / PEDESTRIAN / BALANCED), `next_signals`, `explanation`

## ✅ Plan Evaluation Agent (Agent 3)
- 차량·보행자·교통약자·안전·효율 점수와 총점(0~100)
- 판단: `자동 적용` / `운영자 승인 필요` / `재계획 필요` (Schema enum 으로 고정)
- 출력: `total_score`, `scores`, `decision_recommendation`, `reason`

## 🛡 Guardrail (규칙 기반, 코드로 강제)
- 차량 녹색 최소 8초, 보행자가 있으면 보행 녹색 최소 6초(없으면 0초)
- 합계가 주기(`cycle_sec`)를 넘으면 비례 재배분
- 백엔드가 보정 전/후 값을 함께 보내 화면에 "보정됨: 14/6/0 → 12/8/0" 형태로 표시

## 🧭 최종 판단 보정 (백엔드)
LLM 판단을 다음 규칙이 덮어씁니다. 프롬프트의 자동 적용 선결 조건과 동일합니다.
1. 신호 합계가 주기 초과 → `재계획 필요`
2. 보행자가 있는데 보행 녹색 6초 미만 → `재계획 필요`
3. 보행자 0명 · 정지 차량 20대 이상 · 혼잡도 0.7 이상 · 보행 녹색 0초 → `자동 적용`

## 📡 SSE 실시간 스트리밍
`POST /api/agent/stream` 은 다음 이벤트를 순서대로 보냅니다.

| event | data |
|---|---|
| `message` | `{step: 1..4, message}` 단계 진행 |
| `message` | `{step: "guardrail", durations, before}` Guardrail 결과 |
| `done` | `{input_state, traffic_analysis, signal_plan, evaluation, final_decision}` |
| `error` | `{status: "error", agent, message, detail}` (이후 스트림 종료) |

## 🖥 시뮬레이터 (브라우저)
- 한국식 4현시 신호, 좌회전 현시, 황색·전적색, 보행자 4유형과 횡단보도 양보, 4가지 교차로 제어, 녹색파 오프셋
- **교통 수요 입력 모드**
  - 수동: 교통량 슬라이더(네트워크 전체 대/초)로 무작위 진입로에 차량 생성
  - 실데이터 프로파일: 백엔드 프로파일의 접근로별 발생률로 3x3 교차로의 N/S/E/W 진입로에 Poisson 도착 생성, 시간대 선택·자동 진행, 접근로별 수요·발생률·진입·손실·대기 표
- AI 분석 진행 패널(5단계, 단계별 소요 시간), Agent 실제 출력 표시, Guardrail 보정 전후 표시
- Webster 기반 로컬 최적화기와 시드 고정 A/B 검증 하네스(LLM 과 무관)

---

# 🛠 기술 스택

| 영역 | 내용 |
|---|---|
| Backend | Python 3.10+, FastAPI, uvicorn |
| AI | Upstage Solar Pro 4 (`solar-pro4`), OpenAI 호환 SDK, Structured Outputs |
| Frontend | 단일 HTML + Canvas + JavaScript, SSE 수동 파싱 |
| Data | 표준 라이브러리만 사용한 CSV 정규화 계층 |
| Test | pytest, httpx (Solar 호출은 기본적으로 mock) |

---

# 📂 프로젝트 구조

```text
FlowLight-AI-Traffic-Signal
├── app
│   ├── main.py                     # FastAPI: SSE 파이프라인, 최종 판단 보정, 프로파일 엔드포인트
│   ├── agents.py                   # Solar 클라이언트, 프롬프트 3개, JSON Schema 3개, Guardrail
│   ├── traffic_data.py             # 공공 교통량 CSV → 정규화 프로파일 → 발생률
│   ├── (MAIN) cityflow_final.html  # 시뮬레이터 + UI + 백엔드 연동 (현재 사용본)
│   ├── cityflow_5_ai_backup.html   # 이전 버전 (참고용)
│   └── cityflow_6_orignal.html     # AI 연동 전 원본 (참고용)
├── data
│   ├── README.md                   # 데이터 출처, 컬럼 매핑, 합성 예제 공식, 교체 절차
│   ├── sample_seoul_traffic_history.csv
│   └── sample_seoul_traffic_history.meta.json
├── tests                           # 215개 (mock 214 + live 1, live 는 opt-in)
├── docs                            # 아키텍처 그림, 실행 화면
├── .env.example
├── pytest.ini
├── requirements.txt
└── README.md
```

---

# 🚀 실행 방법

### 1. 저장소 Clone

```bash
git clone https://github.com/jihooni217/FlowLight-AI-Traffic-Signal.git
```

### 2. 라이브러리 설치 (Python 3.10 이상)

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env.example` 을 `.env` 로 복사하고 키를 넣습니다. `.env` 는 커밋되지 않습니다.

| 변수 | 기본값 | 설명 |
|---|---|---|
| `UPSTAGE_API_KEY` | (필수) | Upstage 콘솔에서 발급 |
| `UPSTAGE_MODEL` | `solar-pro4` | `solar-pro3` 로 롤백하거나 `solar-pro4-260806` 로 스냅샷 고정 가능 |
| `UPSTAGE_OUTPUT_MODE` | `json_schema` | Structured Outputs. 문제 시 `json_object` 로 폴백 |
| `TRAFFIC_PROFILE_META` | `data/sample_seoul_traffic_history.meta.json` | 다른 교통량 프로파일 메타 파일 경로 |

### 4. 서버 실행

```bash
uvicorn app.main:app --reload
```

서버는 `http://127.0.0.1:8000` 에 뜹니다. `GET /` 로 상태를 확인할 수 있습니다.

### 5. 프론트엔드 열기

`app/(MAIN) cityflow_final.html` 파일을 브라우저에서 직접 엽니다. 프론트는 `http://127.0.0.1:8000` 의 백엔드를 호출하며, CORS 는 열려 있습니다.

### 6. 데모 진행

1. **Play** 로 시뮬레이션을 시작합니다.
2. 사이드바 **교통 수요 입력** 에서 *실데이터 프로파일* 을 선택하면 격자가 3x3 으로 바뀌고, 시간대(0~23시)별 접근로 수요로 차량이 생성됩니다. 기본은 08시 첨두입니다.
3. **AI 분석** 을 누르면 좌측 패널에 5단계 진행 상태가 표시되고, 리포트에 Agent 별 실제 출력·Guardrail 보정·평가 근거가 나타납니다.
4. 최종 판단이 `자동 적용` 이면 신호가 자동 적용되고, 그 외에는 **권장값 적용** 으로 수동 적용할 수 있습니다.

---

# 🔌 API

| 메서드·경로 | 설명 |
|---|---|
| `GET /` | 헬스 체크 |
| `GET /api/traffic/profile` | 정규화된 수요 프로파일. `meta`, `available_hours`, `hours[{hour, volume, arrival_rate_per_sec}]`. `?hour=8` 로 한 시간대만 조회 (범위 밖 400, 없는 시간 404) |
| `POST /api/agent/stream` | 시뮬레이션 상태 JSON → SSE 로 Agent 파이프라인 진행·결과 |
| `GET /api/agent/stream` | 내장 mock 상태로 같은 파이프라인 실행 (테스트용) |

## 입력 상태(scenario) 형식

프론트가 보내는 JSON 입니다. 기존 필드만 있어도 동작하며, `demand` 와 `queues.by_approach` 는 프로파일·격자 조건에 따라 추가됩니다.

```json
{
  "intersection_id": "simulation-current",
  "tick": 412,
  "signals": {"cycle_sec": 20},
  "queues": {
    "total_cars": 28, "stopped_cars": 19,
    "by_approach": {
      "N": {"queue": 9, "mean_wait_sec": 14.2, "arrivals_last_window": 31, "saturation": 0.83},
      "S": {"queue": 7, "mean_wait_sec": 11.0, "arrivals_last_window": 28, "saturation": 0.75},
      "E": {"queue": 2, "mean_wait_sec": 3.1,  "arrivals_last_window": 12, "saturation": 0.31},
      "W": {"queue": 1, "mean_wait_sec": 2.4,  "arrivals_last_window": 10, "saturation": 0.27}
    }
  },
  "pedestrians": {"waiting_or_crossing": 0, "vulnerable_count": 0},
  "context": {"source": "cityflow_final_html", "grid_size": 3, "demand_mode": "profile",
              "by_approach_scope": "intersection_approaches", "window_sec": 30},
  "metrics": {"congestion": 0.894, "throughput_per_min": 125},
  "demand": {
    "mode": "profile", "site_id": "DEMO-X", "hour": 8, "unit": "veh_per_hour",
    "volume_per_hour": {"N": 842, "S": 790, "E": 610, "W": 655},
    "lanes": {"N": 3, "S": 3, "E": 2, "W": 2},
    "arrival_rate_per_sec": {"N": 0.077963, "S": 0.073148, "E": 0.084722, "W": 0.090972},
    "lost_demand_last_60s": {"N": 0, "S": 0, "E": 0, "W": 0}
  }
}
```

- `demand` 는 입력이고 `queues` 는 결과입니다. 프롬프트가 이 구분을 명시하며, `demand` 블록에는 `queue` 키가 존재하지 않습니다.
- 접근로 명명: `N` 은 **북측에서 진입해 남쪽으로 향하는** 차량입니다.

---

# 🧪 테스트

```bash
python -m pytest -q
```

- 기본 실행은 Solar API 를 호출하지 않습니다(클라이언트를 mock). 현재 214개 통과, 1개는 live 로 스킵됩니다.
- 실제 API 를 부르는 테스트는 opt-in 입니다.

```bash
RUN_LIVE_TESTS=1 python -m pytest tests/test_agent_stream.py -v
```

| 테스트 파일 | 내용 |
|---|---|
| `test_guardrail.py` | Guardrail 과 최종 판단 보정 규칙 |
| `test_stream_mocked.py` | SSE 이벤트 순서·페이로드, 요청 형태, 오류 경로, CORS |
| `test_agents_config.py` | 모델 선택, 요청 파라미터, `finish_reason` 처리 |
| `test_output_schemas.py` | Schema 의 Upstage 제약 준수, 프롬프트와 일치, 음성 검증 |
| `test_prompts.py` | 수요/상태 구분 문구와 접근로별 지시 |
| `test_traffic_data.py` | CSV 정규화, 검증, 대/시 → 대/초 변환 |
| `test_traffic_profile_api.py` | 프로파일 엔드포인트 |
| `test_scenario_extension.py` | 확장 입력의 백엔드 통과 |

---

# 📊 실제 API 검증 기록 (solar-pro4-260806, 2026-09-10)

| 조건 | 결과 |
|---|---|
| 기존 입력, `json_object` | 3회 모두 200·`stop`, 12/8/0, 88점, 자동 적용, 전체 15.4초 |
| 기존 입력, `json_schema` | 3회 모두 200·`stop`, Schema 준수, 동일 결과, 전체 15.1초 |
| 접근로별 상태 포함 입력, `json_schema` | 주요 혼잡 방향 "남북", 계획 14/6/0 → Guardrail 이 12/8/0 으로 보정, 88점, 자동 적용, 전체 24.6초 |

reasoning 은 켜지 않았습니다(`reasoning_effort` 미전송, reasoning 토큰 0). 응답 시간은 네트워크 상태에 따라 달라집니다.

---

# 📸 실행 화면

## 메인 화면

![메인 화면](docs/main.png)

## AI 스트리밍(SSE)

![SSE](docs/sse.png)

## 신호 계획 생성 결과

![AI Result](docs/ai_result.png)

## FastAPI 로그

![FastAPI](docs/fastapi.png)

일부 화면은 이전 버전에서 촬영한 것으로, 현재 UI 에는 진행 상태 패널과 수요 입력 패널이 추가되어 있습니다.

---

# ⚠️ 알려진 한계

- 시뮬레이터는 픽셀 단위의 자체 구현으로, 비율(포화유출률 1800대/시/차로)은 현실과 맞추었지만 속도·거리 절대값은 현실과 다릅니다.
- 보행자 녹색 시간은 실제 현시 시간으로 적용되지 않고(0초일 때만 보행 신호를 끔), 적용 후 실제 주기는 차량 녹색 합 + 6초입니다.
- 수동 모드에서 AI 적용 시 120초 동안 교통량을 절반으로 줄이는 완화 로직이 남아 있습니다(프로파일 모드에서는 비활성).
- 샘플 데이터는 실제 데이터셋의 컬럼 구조를 따른 **합성 예제**입니다. 실제 데이터 교체 절차는 `data/README.md` 에 있습니다.
- 첨두 시간대의 실제 수요로도 3x3 교차로 1개에서는 대기가 크지 않습니다. 혼잡을 강조하는 배율(`demo_scale`)과 회전비율(`turn_ratio`) 반영은 아직 적용하지 않았습니다.

---

# 🚀 향후 계획

- 실제 공공 데이터 파일 연동과 회전비율 반영
- 프론트엔드 정적 서빙으로 실행 절차 단순화
- 보행자 현시의 실제 적용과 주기 표시 정합성
- 다중 교차로 협업 제어

---

# 👨‍💻 Developer

**Jihoon Lee**

GitHub

https://github.com/jihooni217

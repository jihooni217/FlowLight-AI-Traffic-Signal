# 🚦 FlowLight

<p align="center">
  <img src="docs/flowlight_banner.png" width="100%">
</p>

<div align="center">

# AI-based Real-Time Traffic Signal Optimization

### Upstage Solar Pro 4 기반 Multi-Agent 실시간 교통 신호 최적화 데모

**FastAPI · SSE · Solar Pro 4 · Structured Outputs · Guardrail · Traffic Simulator**

**한국어** · [English](README.en.md)

</div>

---

## 🎬 Live Demo

사용법 안내 → 실데이터 프로파일 → AI 분석 → 신호 적용까지의 실행 화면입니다.

<p align="center">
  <img src="docs/flowlight_live_demo.gif" width="100%">
</p>

---

# 📌 프로젝트 소개

FlowLight는 고정 시간 신호 대신 **LLM Agent 세 개**가 교통 상황을 분석하고 신호 시간을 계획한 뒤 스스로 평가하는 구조입니다.
출발점은 두 가지였습니다. **횡단보도에 사람이 없으면 보행 신호를 건너뛰어 차량을 흐르게 하고, 어린이·노약자·휠체어 이용자가 건너면 보행 시간을 늘려 주자.**
LLM 출력은 **Structured Outputs(JSON Schema)** 로 형식이 강제되고, **Guardrail**(규칙 기반 안전 장치)을 거친 뒤에만 시뮬레이터에 적용되며,
FastAPI + SSE(Server-Sent Events)로 AI의 의사결정 과정을 단계별로 실시간 확인할 수 있습니다.

이 저장소는 Upstage 공식 Demo/튜토리얼로 발전시키는 중이며, 다음 원칙을 따릅니다.

- 실제 **시간당 교통량(volume)** 을 **차량 발생률(arrival rate)** 로 변환해 시뮬레이터에 차량을 만들고, **대기 차량 수(queue)** 는 시뮬레이터가 계산합니다.
  842대/시라는 교통량을 대기 차량 842대로 취급하지 않습니다.
- LLM의 내부 추론(reasoning)은 사용하지 않으며, 화면에는 Agent가 **명시적으로 반환한** `summary` / `explanation` / `reason`만 보여 줍니다.

---

## 📊 AI 적용 전후 비교

보행자가 한 명도 없는 교차로입니다. 사람이 없어도 매 주기 보행 신호를 8초씩 주는 **고정 시간표**와 **Solar Pro 4가 세운 계획**을, 같은 시드로 만든 같은 상태에서 90초씩 돌린 영상입니다(GIF는 3초 간격). 두 실행의 차이는 신호뿐입니다.

| Before AI (고정 시간표: 남북 11초 / 동서 11초 / 보행 8초) | After AI (남북 10초 / 동서 20초 / 보행 0초) |
|----------|---------|
| <img src="docs/flowlight_before_ai.gif" width="100%"> | <img src="docs/flowlight_after_ai.gif" width="100%"> |

| 지표 (이 영상의 90초) | 고정 시간표 | FlowLight AI |
|:--|--:|--:|
| 🚦 통과 차량 | 138대 | **156대** |
| 🚗 평균 정지 차량 | 25.2대 | **19.1대** |
| ⏱ 평균 대기 시간 | 15.1초 | **12.3초** |

<p align="center">
  <img src="docs/no_pedestrian_effect.png" width="100%">
</p>

위 그래프는 영상 속 90초 동안 초마다 멈춰 있는 차량 수(회색 띠 = 고정 시간표가 빈 횡단보도에 보행 신호를 준 구간)와, 아래 시드 10개 비교의 평균(막대)·각 시드(점)입니다. 회색 띠마다 고정 시간표 쪽 정지 차량이 치솟습니다.

- 왼쪽은 건널 사람이 없는데도 주기마다 8초씩 모든 차가 멈춥니다. 영상 90초 중 16초가 보행 전용 현시였습니다. 오른쪽은 보행 0초라 그 시간에도 차가 흐릅니다.
- 이 영상은 시드 20260702, 워밍업 120초(차량 35대·정지 30대) 상태에서 실제 Solar Pro 4를 한 번 불러 만들었습니다. 결과: 주요 혼잡 방향 "동서", 계획 10/20/0, Guardrail 보정 없음, 88점, `자동 적용`.
- 영상 한 편의 차이(통과 +18대)는 아래 10개 시드 평균(+14.7대)보다 조금 큽니다. 영상용으로 따로 부른 호출이라, 표의 같은 시드 행(계획 12/18/0, +8대)과 계획이 다릅니다. 대표값은 아래 시드 10개 결과를 보세요.

### 보행자가 없는 교차로: 시드 10개 비교

이 프로젝트의 출발점인 "횡단보도에 아무도 없으면 보행 신호를 건너뛴다"를 따로 쟀습니다. 사람이 없어도 매 주기 보행 신호를 주는 고정 시간표와 FlowLight AI를 시드 10개로 비교했습니다. 시드마다 실제 Solar Pro 4를 한 번씩 불러 계획을 받았습니다.

| 비교 대상 (세 가지 모두 계획 합계 30초) | 신호 |
|---|---|
| 고정 A | 남북 11초 / 동서 11초 / 보행 8초, 보행자가 없어도 매 주기 보행 전용 현시 |
| 고정 B | 남북 15초 / 동서 15초 / 보행 0초 |
| FlowLight AI | 시드마다 실제 계획 (10번 모두 보행 0초, 자동 적용), 감응 신호 포함 |

| 지표 (90초, 시드 10개 평균) | 고정 A | 고정 B | FlowLight AI | AI − 고정 A (95% 신뢰구간) |
|:--|--:|--:|--:|:--|
| 🚦 통과 차량 | 134.1대 | 145.9대 | **148.8대** | **+14.7 ± 7.2대 (+11%)**, 10개 시드 모두 AI가 많음 |
| 🚗 평균 정지 차량 | 26.3대 | 22.5대 | **22.0대** | **−4.2 ± 2.2대 (−16%)**, 10개 시드 모두 AI가 적음 |
| ⏱ 평균 대기 시간 | 15.8초 | 13.8초 | 14.0초 | −1.8 ± 2.0초 (−11%), 7개 시드에서 AI가 짧음 |

- 보행자가 없을 때 보행 신호를 건너뛰면 차이가 뚜렷합니다. 통과 차량과 정지 차량 모두 신뢰구간이 0을 포함하지 않았고, 10개 시드 모두 같은 방향이었습니다.
- 이 차이의 대부분은 보행 시간을 차량에 돌려준 몫입니다. 고정 B도 고정 A보다 통과 +11.8 ± 5.7대, 정지 −3.7 ± 1.4대였습니다.
- LLM이 두 축의 시간을 다시 나눈 몫은 작습니다. AI와 고정 B의 차이는 통과 +2.9 ± 5.4대(7개 시드에서 AI가 많음)로, 잡음과 구분되지 않습니다.
- 이 데모에서 AI의 역할은 "지금 보행자가 없다"를 입력 상태에서 읽고 보행 0초를 고른 뒤 그 근거를 적는 것이고, Guardrail은 보행자가 있을 때 이 값을 최소 6초(교통약자 10초)로 되돌립니다. 보행자가 있는지만 보는 단순한 규칙으로도 같은 결정을 내릴 수 있습니다.
- 조건: 실데이터 프로파일 08시, 차로 수는 데이터대로, 혼잡 배율 ×3, 주기 30초, 보행자 생성 0, 시드 20260702~20260711, 워밍업 120초 뒤 같은 상태에서 세 신호로 각각 90초. 고정 A·B는 앱과 같은 적용 경로(직진 70%·좌회전 30%)로 넣고 감응은 끕니다. 신뢰구간은 시드별 짝 차이의 t 분포(자유도 9)입니다. 정체 지수는 이 혼잡도에서 세 경우 모두 0.96 안팎이라 표에서 뺐습니다.
- 적용은 실제 신호 체계대로 했습니다. 방향별 녹색을 직진 70%·좌회전 30% 로 나눠 4현시를 유지하고(2차로 이상이라 좌회전은 전용 차로에서 보호 좌회전), 매 주기 좌회전·보행 대기를 보고 현시를 넣거나 뺐습니다. 방법은 고급 설정의 A/B 검증과 같습니다(같은 시드, 고정 스텝 1/30초, 같은 워밍업 뒤 분기).

### 두 축 수요가 비슷할 때: 고정 신호와 차이 없음

보행 시간이 없는 기본 고정 신호(주기 30초를 두 축에 반씩)와 비교하면 차이가 나지 않았습니다. 같은 조건(시드 20260702, 혼잡 배율 ×3)에서 실제 계획 12/18/0을 60초 돌린 결과입니다.

| 지표 (60초 창) | 기본 고정 신호 | FlowLight AI |
|:--|--:|--:|
| 통과 차량 (최근 1분) | 100대 | 98대 |
| 정지 차량 (60초 평균) | 21.3대 | 21.4대 |
| 정체 지수 (60초 평균) | 0.944 | 0.955 |

- 워밍업 120초 시점의 접근로별 포화도는 동 2.86 · 서 2.29 · 북 1.57 · 남 1.00이었고, AI는 포화도가 큰 동서 축에 녹색을 더 줬습니다.
- 차이는 시드 하나의 잡음 범위 안이라 좋아졌다고도 나빠졌다고도 쓰지 않습니다. 두 축 수요가 크게 다르지 않아 반씩 나눈 고정 신호가 이미 최적에 가깝고, AI 계획은 동서 대기를 줄인 만큼 남북 대기를 늘렸습니다.
- 이전 실험(수동 모드 4x4, 1차로, 5대/초, 2026-09-10)에서는 같은 방법으로 통과 121 → 131대, 정지 33.9 → 31.3대가 나왔습니다. 아래 검증 기록에 남겨 두었습니다.

---

# 🏗 시스템 구조

FlowLight는 **교통 데이터 → 시뮬레이터 → FastAPI → Multi-Agent → Guardrail → 시뮬레이터 적용**으로 이어지는 구조입니다.

<p align="center">
  <img src="docs/system_architecture.png" width="100%">
</p>

> 배너와 위 구조도의 "CityFlow" 는 이 저장소의 자체 시뮬레이터(`app/index.html`)를 뜻하고, "Solar API" 는 현재 Solar Pro 4입니다. 그림은 초기 버전 기준입니다.

교통량 데이터가 Agent까지 흘러가는 경로는 다음과 같습니다. 교통량(대/시)은 발생률로만 바뀌고, 대기 차량 수는 시뮬레이터가 계산합니다.

<p align="center">
  <img src="docs/data_flow.png" width="100%">
</p>

```
공공 교통량 CSV ─(app/traffic_data.py: 정규화·차로 보정·대/시 → 대/초)─▶ 수요 프로파일
   ─(GET /api/traffic/profile)─▶ 브라우저 시뮬레이터 (3x3 교차로, 접근로별 Poisson 도착)
   ─(접근로별 queue·대기시간·도착·포화도 집계)─▶ scenario JSON (demand + queues.by_approach)
   ─(POST /api/agent/stream, SSE)─▶ Agent 1 분석 → Agent 2 계획 → Guardrail → Agent 3 평가 → 최종 판단
   ─▶ 화면 표시 및 신호 적용
```

| Layer | Description |
|-------|-------------|
| 📈 Traffic Data | 공공 교통량 CSV를 접근로별 수요 프로파일로 정규화하고 차량 발생률로 변환 |
| 🖥 Frontend | HTML/JavaScript 시뮬레이터. 수요 프로파일로 차량 생성, 상태 집계, 결과 시각화 |
| ⚙ FastAPI | API 서버, Agent 오케스트레이션, SSE 스트리밍, 수요 프로파일 제공 |
| 🤖 Solar Pro 4 | LLM 기반 교통 분석·신호 계획·평가 (Structured Outputs) |
| 🛡 Guardrail | 최소 녹색 시간·주기 검증, 최종 판단 보정 |
| 🚦 Simulation | 검증된 신호 계획만 적용 |

## 세 가지 값의 구분

| 값 | 의미 | 어디서 나오나 |
|---|---|---|
| `volume_per_hour` | 실제 입력 수요 (대/시) | 공공 데이터 |
| `arrival_rate_per_sec` | 시뮬레이터 차량 발생률 (차로당 대/초) = `volume / lanes / 3600` | 백엔드 `traffic_data.py` |
| `queue` | 현재 대기 차량 수 | **시뮬레이션 결과** (신호·차간 상호작용) |

---

# 🤖 AI 의사결정 과정

FlowLight는 **Multi-Agent 기반 AI Workflow**로 교통 상황을 분석하고 신호 계획을 생성한 뒤 스스로 평가합니다. Guardrail은 계획 직후, 평가 이전에 실행됩니다.

<p align="center">
  <img src="docs/ai_decision_process.png" width="100%">
</p>

| 단계 | 역할 |
|------|------|
| 🔍 Traffic Situation Agent | 교통 수준·위험도·주요 혼잡 방향 판단 |
| 📝 Signal Planning Agent | 남북/동서/보행자 녹색 시간 계획 |
| 🛡 Guardrail | 최소 녹색 시간과 주기 검증, 보정 전/후 전달 |
| 📊 Plan Evaluation Agent | 점수화와 자동 적용 / 운영자 승인 / 재계획 판단 |
| 🚦 Apply | 검증된 계획만 시뮬레이터에 적용 |

## 🚗 Traffic Situation Agent (Agent 1)
- 차량 수·정지 차량·혼잡도·보행자 수로 교통 수준과 위험도를 판단
- `queues.by_approach`가 있으면 포화도가 가장 큰 접근로를 **주요 혼잡 방향**(N/S/E/W, 남북/동서)으로 판정하고, 대기 수는 보조로 봄
- 출력: `summary`, `traffic_level`, `main_congestion_direction`, `pedestrian_issue`, `vulnerable_user_detected`, `risk_level`

## 🤖 Signal Planning Agent (Agent 2)
- 남북/동서 차량 녹색 시간과 보행자 녹색 시간을 정수 초로 계획
- 보행자가 0명이면 보행 녹색 0초. 어린이·노약자·휠체어 이용자(`vulnerable_count`)가 있으면 보행 녹색 10초 이상
- 접근로별 상태가 있으면 남북 축(N+S)과 동서 축(E+W)의 **포화도 합**을 1차 기준으로 비교해 큰 축에 녹색을 더 배분. 대기 수는 보조 기준이고 차로 수(`lanes`)도 참고. 어느 접근로의 평균 대기 시간이 주기의 2배를 넘으면 차량이 적어도 그 축을 방치하지 않음. 근거 수치를 `explanation`에 명시
- 출력: `durations`(3개 정수), `priority`(VEHICLE / PEDESTRIAN / BALANCED), `next_signals`, `explanation`

## ✅ Plan Evaluation Agent (Agent 3)
- 차량·보행자·교통약자·안전·효율 점수와 총점(0~100)
- 판단: `자동 적용` / `운영자 승인 필요` / `재계획 필요` (Schema enum으로 고정)
- 출력: `total_score`, `scores`, `decision_recommendation`, `reason`

## 🛡 Guardrail (규칙 기반, 코드로 강제)
- 차량 녹색 최소 8초
- 보행 녹색: 보행자 없음 0초 / 있음 최소 6초 / 교통약자 있음 최소 10초
- 합계가 주기(`cycle_sec`)를 넘으면 차량 시간만 비례 재배분
- 백엔드가 보정 전/후 값을 함께 보내 화면에 "보정됨: 14/6/0 → 12/8/0" 형태로 표시

## 🧭 최종 판단 보정 (백엔드)
LLM 판단을 다음 규칙이 덮어씁니다. 프롬프트의 자동 적용 선결 조건과 동일합니다.
1. 신호 합계가 주기 초과 → `재계획 필요`
2. 보행자가 있는데 보행 녹색 6초 미만 → `재계획 필요`
3. 교통약자가 있는데 보행 녹색 10초 미만 → `재계획 필요`
4. 보행자 0명 · 정지 차량 20대 이상 · 혼잡도 0.7 이상 · 보행 녹색 0초 → `자동 적용`

## 🚦 계획은 실제 신호 체계대로 적용됩니다
AI 계획(남북 N초 / 동서 M초 / 보행 P초)은 예산이고, 시뮬레이터가 실제 교차로 운영 방식으로 풀어냅니다.
- **한국식 4현시 유지**: 방향별 녹색을 직진 70% / 좌회전 30% 로 나눕니다. 좌회전 등은 4색 신호등의 녹색 화살표입니다.
- **차로와 좌회전**: 방향당 차로 수를 1~3으로 둘 수 있고(기본 2), 실데이터 모드는 데이터의 차로 수를 씁니다. 2차로 이상이면 맨 왼쪽이 좌회전 전용 차로가 되어 보호 좌회전만 허용합니다(직진 녹색 때 좌회전 금지, 도로교통법 시행규칙 별표 2). 1차로 도로는 전용 차로가 없어 보호·비보호 겸용 좌회전(직진 녹색 때 비보호, 화살표 때 보호)을 씁니다. 차는 진입할 때 회전 방향에 맞는 차로를 잡고, 맨 오른쪽 차로가 우회전을 맡습니다.
- **녹색파 연동**: Agent 1이 짚은 주요 혼잡 방향으로 교차로 시작 시점을 어긋나게 둡니다. 시차 = 교차로 간 거리 ÷ 최고 속도. 교차로가 1개면 없습니다.
- **감응 신호 (AI 적용 후에만)**: 주기가 돌 때마다 교차로별로 현장을 보고, 계획이 준 주기 예산 안에서 배분만 바꿉니다.
  - 보행: 어린이·노약자·휠체어 이용자가 있으면 보행 전용 현시를 최소 10초, 보행자가 5명 이상 모이면 최소 6초로 켭니다(계획값이 더 크면 계획값). 그 밖의 보행자는 기본 신호처럼 나란한 직진 녹색과 함께 건너고, 아무도 없으면 보행 현시를 생략해 차량에 다 줍니다. 계획이 0초였어도 교통약자가 오면 켭니다.
  - 좌회전: 좌회전 대기가 두 대 이상 쌓이면 좌회전 현시를 넣고, 선두 차가 좌회전이라 뒤가 막혀 있으면 좌회전을 먼저 켭니다(선행 좌회전). 대기가 없으면 좌회전 현시를 생략합니다.
- **보행 전용 현시**: 모든 차량이 멈추고 모든 횡단보도가 녹색이 되는 현시입니다. 보행 신호 중 우회전은 금지, 적색 우회전은 보행자에게 양보 후 진행합니다.

- **LLM을 부르는 때**: "AI 분석" 버튼을 누를 때, 그리고 "시간대가 바뀌면 AI 재분석"을 켠 경우 실데이터 프로파일의 시간대가 바뀐 뒤 20초가 지났을 때입니다. 실제 교차로가 출근·낮·퇴근 시간대별 계획을 쓰는 것과 같은 방식입니다. 그 사이 매 주기 조정(보행·좌회전 현시)은 위 감응 규칙이 맡고, LLM은 부르지 않습니다.

AI 적용 전의 기본 신호는 고정 시간표(4현시, 주기에서 황색·전적색을 뺀 녹색을 두 축에 반씩, 교차 방향 차량 녹색과 나란히 보행 녹색)입니다.

## 📡 SSE 실시간 스트리밍
`POST /api/agent/stream`은 다음 이벤트를 순서대로 보냅니다.

| event | data |
|---|---|
| `message` | `{step: 1..4, message}` 단계 진행 |
| `message` | `{step: "guardrail", durations, before}` Guardrail 결과 |
| `done` | `{input_state, traffic_analysis, signal_plan, evaluation, final_decision}` |
| `error` | `{status: "error", agent, message, detail}` (이후 스트림 종료) |

## 🖥 시뮬레이터 (브라우저)
- 한국식 4현시 신호, 좌회전 현시, 황색·전적색, 보행자 4유형과 횡단보도 양보, 4가지 교차로 제어, 녹색파 오프셋
- 방향당 차로 수 1~3(기본 2, 슬라이더). 2차로 이상이면 좌회전 전용 차로와 보호 좌회전, 차로별 차간 거리 계산. 기본 주기 30초
- **교통 수요 입력 모드**
  - 수동: 교통량 슬라이더(네트워크 전체 대/초)로 무작위 진입로에 차량 생성
  - 실데이터 프로파일: 백엔드 프로파일의 접근로별 발생률로 3x3 교차로의 N/S/E/W 진입로에 Poisson 도착 생성, 차로 수도 데이터대로(남북 3, 동서 2), 시간대 선택·자동 진행, 접근로별 수요·발생률·진입·손실·대기 표
  - 시간대가 바뀌면 AI 재분석(기본 꺼짐): 시간대가 바뀌고 20초 뒤 AI 분석을 한 번 다시 불러 계획을 바꿉니다. 분석이 진행 중이면 겹쳐 부르지 않고, 자동 호출에서는 리포트 창과 알림을 띄우지 않으며, 서버가 없으면 녹화를 재생하지 않고 건너뜁니다.
  - 혼잡 배율(×1~5, 데모용): 실제 첨두 수요로는 교차로 하나에 차가 많지 않아, 방향별 비율은 그대로 두고 크기만 곱하는 슬라이더. 생성률 = 차로당 발생률 × 차로 수 × 배율. Agent에는 `demand.demo_scale`로 함께 보내 데모용 배율임을 알림
- AI 계획은 4현시 유지·녹색파·감응 신호로 적용(위 절 참고). 적용 후 효과는 시뮬레이션 시간 15초 평균으로 측정하므로 배속을 걸면 그만큼 빨리 나옴
- AI 분석 진행 패널(5단계, 단계별 소요 시간), Agent 실제 출력 표시, Guardrail 보정 전후 표시
- 처음 열면 다섯 단계 사용법 안내가 뜨고, 사이드바의 "사용법 보기"로 다시 열 수 있음
- 녹화 재생: API 키가 없거나 백엔드에 연결되지 않으면 실제 Solar Pro 4 응답 기록을 재생하고 리포트에 표시 (실행 방법 참고)
- 교차로 유형, 데이터 내보내기, Webster 기반 로컬 최적화기와 시드 고정 A/B 검증(LLM과 무관)은 "고급 설정" 접기에 정리

---

# 📊 실험 결과

AI 적용 전후 비교는 위의 [AI 적용 전후 비교](#-ai-적용-전후-비교) 절에 있습니다.

<details>
<summary>이전 버전(Solar Pro 3, 2026-07) 실험 결과</summary>

같은 방식으로 이전 버전에서 측정한 결과입니다. 대기 차량 18대 → 13대(27.8% 감소), 통과 107 → 115대/분(7.5% 증가), 정체 지수 1.00 → 0.76(24.0% 감소).

<p align="center">
  <img src="docs/experiment_results.png" width="100%">
</p>
</details>

## 실제 API 검증 기록 (solar-pro4-260806, 2026-09-10 ~ 09-17)

| 조건 | 결과 |
|---|---|
| 기존 입력, `json_object` | 3회 모두 200·`stop`, 12/8/0, 88점, 자동 적용, 전체 15.4초 |
| 기존 입력, `json_schema` | 3회 모두 200·`stop`, Schema 준수, 동일 결과, 전체 15.1초 |
| 접근로별 상태 포함 입력, `json_schema` | 주요 혼잡 방향 "남북", 계획 14/6/0 → Guardrail이 12/8/0으로 보정, 88점, 자동 적용, 전체 24.6초 |
| 프로파일 모드 화면에서 실행 (차량 9대, 북측 대기 2대·포화도 1.2) | 주요 혼잡 방향 "N", 계획 12/8/0, 82점, 운영자 승인 필요 → 수동 적용 후 정체 지수 0.61 → 0.35 (단순 2현시 적용 시절 측정) |
| 수동 모드 4x4, 1차로, 차량 49대·정지 33대 (이전 전후 비교의 분기 상태) | 주요 혼잡 방향 "남북", 계획 12/8/0, Guardrail 보정 없음, 88점, 자동 적용 → 실제 신호 체계로 적용해 60초 후 통과 121 → 131대 |
| 수동 모드 4x4, 주기 30초, 차량 18대, 횡단보도에 보행자 2명(노약자 1명 포함) | Agent 1 교통약자 감지, 계획 12/8/10 ("교통약자 1명이 있어 횡단 속도를 고려해 10초"), Guardrail 보정 없음, 82점, 운영자 승인 필요 → 적용 후 보행 전용 현시 10초 |
| 프로파일 모드 화면에서 실행, 혼잡 배율 ×1, 시드 20260702, 차량 11대·정지 7대 (현재 리포트·적용 캡처, 09-17) | 주요 혼잡 방향 "동서"(동·서 포화도 1.14, 북측 대기 6대), 계획 10/20/0 (근거: 포화도 합 동서 2.28, 남북 1.29, 북측 대기는 보조 기준), Guardrail 보정 없음, 88점, 자동 적용 → 15초 평균 처리량 37 → 45대/분, 정체 지수 1.00 → 0.99, 정지 7 → 11대(증가) |
| 같은 조건, 시드 20260702, 전후 비교 GIF 용 호출 (09-17) | 주요 혼잡 방향 "동서", 계획 10/20/0, Guardrail 보정 없음, 88점, 자동 적용 → 보행 8초 고정 신호 대비 90초 통과 138 → 156대, 정지 25.2 → 19.1대 |
| 프로파일 모드, 혼잡 배율 ×3, "시간대가 바뀌면 AI 재분석" 켬, 08시 → 03시 → 08시 (09-17) | 시간대가 바뀐 뒤 20초에 자동 분석 2회, 두 번 모두 14/16/0·자동 적용, 리포트 창·알림 없음. 03시로 바꾼 직후 20초 동안은 08시에 들어온 차가 남아 있어 계획이 같게 나왔습니다. 서버를 끊은 상태에서는 녹화 재생 없이 "자동 재분석 건너뜀"으로 표시 |
| 프로파일 모드 08시, 혼잡 배율 ×3, 보행자 0명, 시드 10개 (09-17) | 10회 모두 보행 0초·자동 적용, 계획은 8/22 ~ 18/12로 시드마다 다름 → 보행 8초 고정 신호 대비 90초 통과 +14.7 ± 7.2대, 정지 −4.2 ± 2.2대 (위 "보행자가 없는 교차로" 절) |
| 프로파일 모드 08시, 차로 데이터대로, 혼잡 배율 ×3, 차량 35대·정지 30대 ("두 축 수요가 비슷할 때" 비교의 분기 상태, 09-17) | 주요 혼잡 방향 "동서"(동 포화도 2.86 · 서 2.29), 계획 12/18/0, Guardrail 보정 없음, 88점, 자동 적용 → 60초 후 통과 100 → 98대, 정지 21.3 → 21.4대. 고정 신호와 차이 없음 |

reasoning은 켜지 않았습니다(`reasoning_effort` 미전송, reasoning 토큰 0). 응답 시간은 네트워크 상태에 따라 달라집니다.
Guardrail이 실제 Solar Pro 4 계획을 고친 사례는 다음과 같습니다.

<p align="center">
  <img src="docs/guardrail_cases.png" width="100%">
</p>

---

# 🛠 기술 스택

<p>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white">
  <img src="https://img.shields.io/badge/SSE-2563EB?style=for-the-badge&logo=googletagmanager&logoColor=white">
  <img src="https://img.shields.io/badge/Solar_Pro_4-FF7A00?style=for-the-badge&logo=openai&logoColor=white">
</p>

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
│   ├── index.html                  # 시뮬레이터 + UI + 백엔드 연동 (브라우저로 여는 파일)
│   └── replay_data.js              # 녹화 재생용 실제 Solar Pro 4 응답 기록 (서버 없이 체험)
├── data
│   ├── README.md                   # 데이터 출처, 컬럼 매핑, 합성 예제 공식, 교체 절차
│   ├── sample_seoul_traffic_history.csv
│   └── sample_seoul_traffic_history.meta.json
├── tests                           # 247개 (mock 246 + live 1, live 는 opt-in)
├── docs
│   ├── screens/                    # UI 화면 (사용법, 메인, 프로파일 모드, 진행 패널, 리포트, 적용, 보행 전용 현시, 녹화 재생, 고급 설정)
│   ├── flowlight_banner.png, flowlight_live_demo.gif
│   ├── system_architecture.png, data_flow.png, ai_decision_process.png, guardrail_cases.png
│   ├── flowlight_before_ai.gif, flowlight_after_ai.gif   # AI 적용 전후 비교 (보행자 없는 교차로)
│   ├── experiment_results.png      # 이전 버전 실험
│   └── FlowLight_Final_Presentation.pdf
├── LICENSE                         # MIT
├── .env.example
├── pytest.ini
├── requirements.txt
├── README.md                       # 한국어
└── README.en.md                    # English
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

`.env.example`을 `.env`로 복사하고 키를 넣습니다. `.env`는 커밋되지 않습니다.

| 변수 | 기본값 | 설명 |
|---|---|---|
| `UPSTAGE_API_KEY` | (실제 분석에 필요) | Upstage 콘솔에서 발급. 없어도 서버는 켜지고, AI 분석은 녹화 재생으로 대신합니다 |
| `UPSTAGE_MODEL` | `solar-pro4` | `solar-pro3`로 롤백하거나 `solar-pro4-260806`로 스냅샷 고정 가능 |
| `UPSTAGE_OUTPUT_MODE` | `json_schema` | Structured Outputs. 문제 시 `json_object`로 폴백 |
| `TRAFFIC_PROFILE_META` | `data/sample_seoul_traffic_history.meta.json` | 다른 교통량 프로파일 메타 파일 경로 |

### 4. 서버 실행

```bash
uvicorn app.main:app --reload
```

서버는 `http://127.0.0.1:8000`에 뜹니다. `GET /`로 상태를 확인할 수 있습니다.

### 5. 프론트엔드 열기

`app/index.html` 파일을 브라우저에서 직접 엽니다. 프론트는 `http://127.0.0.1:8000`의 백엔드를 호출하며, CORS는 열려 있습니다.

### 6. 데모 진행

1. 처음 열면 다섯 단계 **사용법 안내** 가 뜹니다. 읽고 "시작하기"를 누릅니다. 사이드바의 "사용법 보기"로 다시 볼 수 있습니다.
2. **Play** 로 시뮬레이션을 시작합니다. 배속은 4x가 보기 편합니다.
3. 사이드바 **교통 수요 입력** 에서 *실데이터 프로파일* 을 선택하면 격자가 3x3으로 바뀌고, 시간대(0~23시)별 접근로 수요로 차량이 생성됩니다. 기본은 08시 첨두입니다. 차로 수는 데이터대로 남북 3차로, 동서 2차로가 됩니다. 실제 수요로는 차가 적어 화면이 한산하니, 붐비는 장면을 보려면 **혼잡 배율** 슬라이더를 ×3 정도로 올립니다. **시간대가 바뀌면 AI 재분석**을 켜고 시간대를 바꾸거나 자동 진행을 켜면, 시간대마다 계획이 자동으로 다시 세워집니다.
4. **AI 분석** 을 누르면 좌측 패널에 5단계 진행 상태가 표시되고, 리포트에 Agent 별 실제 출력·Guardrail 보정·평가 근거가 나타납니다.
5. 최종 판단이 `자동 적용`이면 신호가 자동 적용되고, 그 외에는 **권장값 적용** 으로 수동 적용할 수 있습니다. 시뮬레이션 15초 뒤 적용 전후 효과가 표시됩니다.
6. 보행자 쪽을 보려면 사이드바 **보행자(명/초)** 슬라이더를 1로 올립니다. 횡단보도에 어린이·노약자·휠체어 이용자가 서 있을 때 분석하면 보행 녹색이 10초 이상으로 잡히고, 적용 후 모든 차가 멈추는 보행 전용 현시가 보입니다. 보행자가 없으면 0초로 잡혀 보행 현시가 사라집니다.

### API 키 없이 체험하기 (녹화 재생)

API 키가 없어도 흐름 전체를 볼 수 있습니다. **AI 분석**을 누르면 `app/replay_data.js`에 기록된 **실제 Solar Pro 4 응답**을 원래 시간 간격대로 재생합니다.

| 준비 | 볼 수 있는 것 |
|---|---|
| 키 없이 서버만 켬 (`.env` 없이 `uvicorn app.main:app`) | 실데이터 프로파일 모드 전체. AI 분석은 "API 키가 없어 녹화를 재생한다"는 안내 뒤 재생 |
| 서버 없이 `app/index.html`만 엶 | 수동 모드와 녹화 재생. 실데이터 프로파일은 서버에서 받아오므로 열리지 않습니다 |

서버와 키가 있어도 사이드바의 "서버 없이 녹화 재생" 체크로 재생을 고를 수 있습니다. 시간대 자동 재분석은 녹화를 반복 재생하지 않고 건너뜁니다.

- 기록은 실데이터 프로파일 08시, 혼잡 배율 ×3, 워밍업 120초 상태에서 한 번 호출해 받은 SSE 이벤트 그대로이고 사람이 고치지 않았습니다. 계획 남북 8초 / 동서 22초 / 보행자 0초, 82점, 자동 적용.
- 리포트 제목과 왼쪽 패널에 "녹화 재생" 이 붙고, 입력 상태가 녹화 당시 값이라는 안내가 같이 나옵니다. 계획은 지금 화면에 적용됩니다.
- 진행 패널의 단계별 시간도 녹화된 도착 시각을 따릅니다. 모델을 다시 부르지 않으므로 화면 상태와 상관없이 같은 응답이 나옵니다.
- 다시 기록하려면 서버를 켜고 실제 호출 한 번의 이벤트를 같은 형식으로 저장합니다. `tests/test_replay_data.py`가 형식을 검사합니다.

---

# 🔌 API

| 메서드·경로 | 설명 |
|---|---|
| `GET /` | 헬스 체크 |
| `GET /api/traffic/profile` | 정규화된 수요 프로파일. `meta`, `available_hours`, `hours[{hour, volume, arrival_rate_per_sec}]`. `?hour=8`로 한 시간대만 조회 (범위 밖 400, 없는 시간 404) |
| `POST /api/agent/stream` | 시뮬레이션 상태 JSON → SSE로 Agent 파이프라인 진행·결과 |
| `GET /api/agent/stream` | 내장 mock 상태로 같은 파이프라인 실행 (테스트용) |

## 입력 상태(scenario) 형식

프론트가 보내는 JSON입니다. 기존 필드만 있어도 동작하며, `demand`와 `queues.by_approach`는 프로파일·격자 조건에 따라 추가됩니다.

```json
{
  "intersection_id": "simulation-current",
  "tick": 412,
  "signals": {"cycle_sec": 30},
  "queues": {
    "total_cars": 28, "stopped_cars": 19,
    "by_approach": {
      "N": {"queue": 9, "mean_wait_sec": 14.2, "arrivals_last_window": 31, "saturation": 0.83, "lanes": 3},
      "S": {"queue": 7, "mean_wait_sec": 11.0, "arrivals_last_window": 28, "saturation": 0.75, "lanes": 3},
      "E": {"queue": 2, "mean_wait_sec": 3.1,  "arrivals_last_window": 12, "saturation": 0.31, "lanes": 2},
      "W": {"queue": 1, "mean_wait_sec": 2.4,  "arrivals_last_window": 10, "saturation": 0.27, "lanes": 2}
    }
  },
  "pedestrians": {"waiting_or_crossing": 0, "vulnerable_count": 0},
  "context": {"source": "flowlight_index_html", "grid_size": 3, "demand_mode": "profile",
              "by_approach_scope": "intersection_approaches", "window_sec": 30},
  "metrics": {"congestion": 0.894, "throughput_per_min": 125},
  "demand": {
    "mode": "profile", "site_id": "DEMO-X", "hour": 8, "unit": "veh_per_hour",
    "volume_per_hour": {"N": 842, "S": 790, "E": 610, "W": 655},
    "lanes": {"N": 3, "S": 3, "E": 2, "W": 2},
    "arrival_rate_per_sec": {"N": 0.077963, "S": 0.073148, "E": 0.084722, "W": 0.090972},
    "demo_scale": 1,
    "lost_demand_last_60s": {"N": 0, "S": 0, "E": 0, "W": 0}
  }
}
```

- `demand`는 입력이고 `queues`는 결과입니다. 프롬프트가 이 구분을 명시하며, `demand` 블록에는 `queue` 키가 존재하지 않습니다.
- `demo_scale`은 데모용 혼잡 배율입니다. 실제 생성률은 `arrival_rate_per_sec × lanes × demo_scale`이고, 배율을 걸었을 때는 `note`에 그 사실을 적어 Agent가 수요를 실제값으로 오해하지 않게 합니다.
- 접근로 명명: `N`은 **북측에서 진입해 남쪽으로 향하는** 차량입니다.

---

# 🧪 테스트

```bash
python -m pytest -q
```

- 기본 실행은 Solar API를 호출하지 않습니다(클라이언트를 mock). 현재 246개 통과, 1개는 live로 스킵됩니다.
- 실제 API를 부르는 테스트는 opt-in입니다.

```bash
RUN_LIVE_TESTS=1 python -m pytest tests/test_agent_stream.py -v
```

| 테스트 파일 | 내용 |
|---|---|
| `test_guardrail.py` | Guardrail과 최종 판단 보정 규칙 |
| `test_stream_mocked.py` | SSE 이벤트 순서·페이로드, 요청 형태, 오류 경로, CORS |
| `test_agents_config.py` | 모델 선택, 요청 파라미터, `finish_reason` 처리 |
| `test_output_schemas.py` | Schema의 Upstage 제약 준수, 프롬프트와 일치, 음성 검증 |
| `test_prompts.py` | 수요/상태 구분 문구, 접근로별 지시, 보행자·교통약자·공정성·포화도 우선 규칙 |
| `test_traffic_data.py` | CSV 정규화, 검증, 대/시 → 대/초 변환 |
| `test_traffic_profile_api.py` | 프로파일 엔드포인트 |
| `test_scenario_extension.py` | 확장 입력의 백엔드 통과 |
| `test_replay_data.py` | 녹화 재생 데이터의 SSE 순서·계획·판단 형식과 화면 연결 |
| `test_no_api_key.py` | 키 없이 서버가 켜지는지, Upstage 를 부르지 않고 `no_api_key` 를 보내는지, 화면이 녹화 재생으로 넘어가는지 |
| `test_render_and_ab.py` | 차로 수가 다른 도로의 인도 모서리 그리기, A/B 검증에서 Webster 권장값이 감응 모드에 덮이지 않는지 |
| `test_hourly_reanalysis.py` | 시간대 변경 시 자동 재분석의 예약·중복 방지·조용한 실행 배선 |

---

# 📸 실행 화면

현재 버전(Solar Pro 4, 방향당 2~3차로, 주기 30초)에서 캡처한 화면입니다. 진행 패널·리포트·적용·보행 현시 화면의 Agent 출력은 실제 API 호출 결과이고, 그 밖의 화면은 호출 없이 찍었습니다.

## 처음 열었을 때의 사용법 안내

![사용법 안내](docs/screens/help.png)

## 메인 화면

![메인 화면](docs/screens/main.png)

## 실데이터 프로파일 모드

격자가 3x3 교차로로 바뀌고, 접근로별 수요(입력)와 대기(시뮬레이션 결과)가 한 표에 나란히 표시됩니다.

| 프로파일 모드 | 접근로별 수요·발생률·진입·손실·대기 |
|---|---|
| ![프로파일 모드](docs/screens/profile_mode.png) | ![수요 표](docs/screens/demand_table.png) |

## AI 분석 진행 패널

| 2단계 진행 중 | 다섯 단계 완료 |
|---|---|
| ![진행 중](docs/screens/ai_progress.png) | ![완료](docs/screens/ai_progress_done.png) |

## 분석 리포트

Agent가 실제로 돌려준 `summary` / `explanation` / `reason`과 Guardrail 검증 결과가 그대로 표시됩니다.

![분석 리포트](docs/screens/report.png)

## 신호 적용

![적용 배너와 결과 패널](docs/screens/applied.png)

## 교통약자가 있을 때: 보행 전용 현시

횡단보도에 노약자가 서 있는 상태로 분석한 실제 실행입니다. Agent 1이 교통약자를 감지했고, Agent 2는 "교통약자 1명이 있어 횡단 속도를 고려해 10초" 라는 근거로 12/8/10을 냈습니다. 적용 후 모든 차가 멈추고 모든 횡단보도가 10초 녹색이 되는 현시가 생겼습니다. 이후에는 감응 신호가 주기마다 횡단보도를 봅니다. 교통약자가 있거나 보행자가 많이 모인 교차로에만 이 전용 현시를 켜고, 그 밖의 보행자는 나란한 직진 녹색과 함께 건너며, 아무도 없으면 생략합니다. 아래 화면은 2차로 도로에서 다시 찍은 것입니다.

| 리포트: 교통약자 감지와 계획 근거 | 적용 결과 패널 |
|---|---|
| ![보행자 리포트](docs/screens/ped_report.png) | ![적용 패널](docs/screens/ped_panel.png) |

![보행 전용 현시: 모든 차량 정지, 모든 횡단보도 녹색](docs/screens/ped_phase.png)

## 녹화 재생

백엔드를 끄고 "AI 분석" 을 누른 화면입니다. 연결 실패를 알린 뒤 기록된 실제 응답을 재생하고, 결과 제목에 "녹화 재생" 이 붙습니다.

<p align="center">
  <img src="docs/screens/replay_report.png" width="600">
</p>

## 고급 설정

교차로 유형, 데이터 내보내기, 내장 Webster 최적화는 접기 안에 있습니다.

<p align="center">
  <img src="docs/screens/advanced.png" width="320">
</p>

---

# 📄 발표 자료

프로젝트의 문제 정의, AI Agent 설계, 시스템 아키텍처, 실험 결과, 회고 내용을 발표 자료로 정리했습니다.

[📑 View Final Presentation](docs/FlowLight_Final_Presentation.pdf)

| Section | Description |
|--------|-------------|
| Problem | 고정형 교통 신호 체계의 한계 |
| Method | LLM Agent 기반 분석·계획·평가 구조 |
| Architecture | FastAPI, SSE, Solar API, Guardrail 기반 시스템 구성 |
| Experiment | AI 적용 전후 교통 흐름 비교 |
| Retrospective | 프로젝트를 통해 배운 점과 향후 개선 방향 |

---

# ⚠️ 알려진 한계

- 시뮬레이터는 픽셀 단위의 자체 구현으로, 비율(포화유출률 1800대/시/차로)은 현실과 맞추었지만 속도·거리 절대값은 현실과 다릅니다.
- 시간 축이 압축되어 있습니다. 기본 주기 30초(실제 100~180초), 황색 2초, 교차로 간 녹색파 시차 1.7초. 비율은 실제와 비슷하지만 절대값은 다릅니다. 적용 후 실제 주기는 차량 녹색 합 + 좌회전·보행 현시 + 황색·전적색이라 입력 주기(`cycle_sec`)보다 깁니다.
- 차로는 최대 3개이고 좌회전 전용 차로는 항상 1개입니다. 차는 진입할 때 회전 방향에 맞는 차로를 고르고 중간에 차로를 바꾸지 않으므로, 좌회전 차로가 비어 있어도 직진 차가 옮겨 가지 않습니다. 1차로 도로에서는 직진 때 좌회전을 막는 보호 전용 방식이 격자를 마비시켜 겸용 좌회전을 씁니다.
- 차로를 늘리면 통과량은 늘지만 대기와 정체 지수도 같이 오릅니다. 차로마다 차가 들어오는데 교차로 용량은 신호가 정하기 때문입니다.
- 보행 시간이 없는 고정 신호와 비교하면, 균형 잡힌 수요에서는 AI 계획이 비슷하게 나옵니다("두 축 수요가 비슷할 때" 절). 시드 10개 비교에서 분명한 효과는 보행자가 없을 때 보행 신호를 건너뛰는 데서 나왔고, 두 축의 시간을 다시 나누는 효과는 잡음과 구분되지 않았습니다.
- 자동 재분석은 시간대가 바뀔 때만 동작합니다. 같은 시간대 안에서 수요가 크게 바뀌어도 계획은 그대로이고, 바뀐 직후 20초는 이전 시간대의 차가 남아 있어 계획이 비슷하게 나올 수 있습니다.
- 감응으로 교차로마다 주기가 조금씩 달라지면 녹색파 시차는 흐트러집니다. 교차로별로 다른 계획을 세우는 것은 향후 계획입니다.
- 수동 모드에서 AI 적용 시 120초 동안 교통량을 절반으로 줄이는 완화 로직이 남아 있습니다(프로파일 모드에서는 비활성).
- 샘플 데이터는 실제 데이터셋의 컬럼 구조를 따른 **합성 예제**입니다. 실제 데이터 교체 절차는 `data/README.md`에 있습니다.
- 혼잡 배율(`demo_scale`)은 데모용입니다. 실제 수요가 아니라는 사실을 Agent 입력의 `note`에 적어 보냅니다. 회전비율(`turn_ratio`)은 아직 데이터에서 읽지 않고 시뮬레이터가 무작위로 정합니다.

---

# 🚀 향후 계획

| Improvement Area | Description |
|------------------|-------------|
| **Real Traffic Data** | 실제 공공 데이터 파일 연동, 회전비율(`turn_ratio`) 반영 |
| **Re-planning** | 시간대 변경 외에 포화도 급변·교통약자 출현 같은 상황 변화에도 재분석 |
| **Demo Packaging** | 프론트엔드 정적 서빙으로 실행 절차 단순화 |
| **Signal Fidelity** | 보행자 현시의 실제 적용과 주기 표시 정합성 |
| **Roundabout Scenario** | 회전교차로 차량 흐름과 우선순위 규칙 추가 |
| **Multi-Intersection Control** | 인접 교차로 간 신호 연동 및 녹색파 제어 확장 |
| **Reinforcement Learning** | LLM Agent와 강화학습을 결합한 하이브리드 신호 최적화 |
| **Evaluation Automation** | 평균 속도, 대기 차량 수, 통행량 등 성능 지표 자동 수집 및 분석 |

---

# 👨‍💻 My Contributions

본 프로젝트에서 저는 **LLM Agent 설계, Backend 연동, Guardrail 검증, Frontend 연결, 실험 및 발표 자료 제작**을 중심으로 수행했습니다.

### AI / LLM
- Traffic Analysis Agent, Signal Planning Agent, Plan Evaluation Agent 구조 설계
- Upstage Solar API 기반 LLM 호출 흐름 구현
- 교통 상태 데이터를 LLM 입력에 적합한 Prompt 형식으로 변환
- JSON 기반 신호 계획 출력 형식 설계

### Backend
- FastAPI 기반 AI Agent 서버 구현
- Frontend와 통신하기 위한 API Endpoint 구성
- SSE(Server-Sent Events)를 활용한 실시간 스트리밍 응답 구현
- AI 분석 단계, 신호 계획 생성, 평가 결과를 순차적으로 전달하는 흐름 구성

### Reliability
- Guardrail을 통한 신호 시간 최소/최대 범위 검증
- JSON 응답 형식 검증
- 비정상 값 필터링 및 안전한 신호 계획만 적용하도록 처리
- 오류 발생 시 데모가 중단되지 않도록 예외 처리 보완

### Frontend / Demo
- HTML / JavaScript 기반 시뮬레이션 화면과 Backend 연동
- AI 분석 결과 및 신호 계획을 사용자 화면에 표시
- AI 적용 전 / 후 비교 시나리오 구성
- 전체 시뮬레이션 데모 영상 제작

### Documentation / Presentation
- 프로젝트 발표 자료 제작
- 시스템 아키텍처 및 AI 의사결정 과정 정리
- 실험 결과 분석 및 발표
- 최종 발표 진행

---

# 📝 Lessons Learned

LLM API를 부르는 일보다, 돌아온 답을 평가하고 검증해서 서비스에 안전하게 넣는 일이 더 어려웠습니다.

- 질문 하나에 답 하나를 받는 대신, 분석·계획·평가를 맡은 Agent 세 개로 판단을 나눴습니다.
- 프롬프트와 Structured Outputs로 입력과 출력 형식을 고정했습니다.
- FastAPI와 SSE로 분석 과정을 화면에 단계별로 흘려보냈습니다.
- Guardrail과 JSON 검증을 거친 결과만 신호에 적용했습니다.
- 수치와 영상을 같이 보여 줘야 결과가 전달된다는 것을 알게 됐습니다. 다만 수치는 좋게 나온 한 번이 아니라 여러 번 반복한 결과로 말해야 했습니다.

---

# 📄 라이선스

MIT 라이선스입니다. [LICENSE](LICENSE)를 참고하세요.

---

# 👨‍💻 Developer

**Jihoon Lee**

GitHub

https://github.com/jihooni217

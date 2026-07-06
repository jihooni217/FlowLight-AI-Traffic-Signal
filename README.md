# 🚦 FlowLight AI Traffic Signal Optimization

> **LLM 기반 Multi-Agent 교통 신호 최적화 시스템**  
> FastAPI와 SSE(Server-Sent Events)를 활용하여 AI의 의사결정 과정을 실시간으로 확인할 수 있는 교통 신호 제어 프로젝트입니다.

---

# 📌 프로젝트 소개

FlowLight는 기존의 **고정 시간 기반 신호 제어 방식** 대신 **LLM(Multi-Agent)** 을 활용하여 교통 상황을 분석하고 최적의 신호 시간을 생성하는 AI 기반 교통 신호 최적화 시스템입니다.

AI가 생성한 신호 계획은 평가(Evaluation)와 Guardrail을 거쳐 안정성을 확보한 뒤 적용되며, FastAPI와 SSE를 통해 AI의 의사결정 과정을 실시간으로 확인할 수 있습니다.

---

# 🎯 프로젝트 목표

- 🚗 교통 상황을 AI가 분석
- 🤖 LLM 기반 신호 계획 생성
- ✅ 생성 결과 자동 평가
- 🛡 Guardrail을 통한 안전성 확보
- 📡 SSE 기반 실시간 스트리밍
- 🌐 FastAPI 기반 로컬 서버 운영

---

# 🏗 시스템 아키텍처

```text
                 Traffic Data
                      │
                      ▼
      ┌─────────────────────────┐
      │ Traffic Situation Agent │
      └─────────────────────────┘
                      │
                      ▼
      ┌─────────────────────────┐
      │ Signal Planning Agent   │
      └─────────────────────────┘
                      │
                      ▼
      ┌─────────────────────────┐
      │ Plan Evaluation Agent   │
      └─────────────────────────┘
                      │
                      ▼
      ┌─────────────────────────┐
      │      Guardrail          │
      └─────────────────────────┘
                      │
                      ▼
          FastAPI + SSE Streaming
                      │
                      ▼
             HTML Frontend UI
```

---

# 🤖 AI 의사결정 과정

```text
Traffic Data 입력

↓

Traffic Situation Agent
(교통 상황 분석)

↓

Signal Planning Agent
(신호 시간 생성)

↓

Plan Evaluation Agent
(생성 결과 평가)

↓

Guardrail
(최소·최대 신호 시간 보정)

↓

최종 신호 적용

↓

Frontend 실시간 표시
```

---

# ✨ 주요 기능

## 🚗 Traffic Situation Agent

- 차량 대기열 분석
- 혼잡도 분석
- 교통 상태 판단

---

## 🤖 Signal Planning Agent

- AI 기반 신호 계획 생성
- 동서/남북 방향 신호 시간 계산

---

## ✅ Plan Evaluation Agent

- 생성된 신호 계획 평가
- 평가 점수 기반 적용 여부 판단

---

## 🛡 Guardrail

- 최소 신호 시간 보장
- 최대 신호 시간 제한
- 비정상 결과 자동 보정

---

## 📡 SSE(Server-Sent Events)

AI 처리 과정을 실시간으로 스트리밍

예시

- 교통 분석 시작
- 신호 계획 생성
- 평가 진행
- Guardrail 적용
- 최종 적용 완료

---

## 🌐 FastAPI

- 로컬 서버 운영
- REST API 제공
- Frontend 연동

---

# 🛠 기술 스택

## Backend

- Python
- FastAPI

## AI

- Upstage Solar API
- Multi-Agent

## Frontend

- HTML
- JavaScript
- SSE(Server-Sent Events)

## Tools

- Git
- GitHub
- VS Code
- Google Colab

---

# 📂 프로젝트 구조

```text
FlowLight-AI-Traffic-Signal
│
├── app
│   ├── agents.py
│   ├── main.py
│   ├── (MAIN) cityflow_final.html
│   ├── cityflow_5_ai_backup.html
│   └── cityflow_6_original.html
│
├── tests
│   └── test_agent_stream.py
│
├── README.md
├── requirements.txt
└── .gitignore
```

---

# 🚀 실행 방법

### 1. 저장소 Clone

```bash
git clone https://github.com/jihooni217/FlowLight-AI-Traffic-Signal.git
```

### 2. 라이브러리 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env`

```text
UPSTAGE_API_KEY=YOUR_API_KEY
```

### 4. 서버 실행

```bash
uvicorn app.main:app --reload
```

---

# 📸 실행 화면

## 메인 화면

> *(스크린샷 추가 예정)*

---

## AI 스트리밍(SSE)

> *(스크린샷 추가 예정)*

---

## 신호 계획 생성 결과

> *(스크린샷 추가 예정)*

---

## 최종 신호 적용

> *(스크린샷 추가 예정)*

---

# 📈 프로젝트 특징

✅ LLM 기반 교통 신호 최적화

✅ Multi-Agent 구조 적용

✅ FastAPI 기반 서버 운영

✅ SSE 실시간 스트리밍

✅ Guardrail 기반 신뢰성 확보

✅ 평가(Evaluation)를 통한 안전한 신호 적용

---

# 🚀 향후 개선 사항

- 실제 CityFlow 시뮬레이터와 연동
- 실시간 센서 데이터 기반 제어
- 강화학습(RL) 기반 신호 최적화
- 다중 교차로 협업 제어
- Dashboard 구축

---

# 👨‍💻 Developer

**Jihoon Lee**

GitHub

https://github.com/jihooni217
# 🚦 FlowLight AI Traffic Signal Optimization

LLM(Multi-Agent) 기반 교통 신호 최적화 시스템

FlowLight는 교통 상황을 분석하고 AI가 신호 시간을 생성·평가하여 최적의 신호 계획을 제안하는 프로젝트입니다.  
FastAPI와 SSE(Server-Sent Events)를 활용하여 AI의 의사결정 과정을 실시간으로 확인할 수 있도록 구현했습니다.

---

# 📌 프로젝트 소개

기존의 고정 신호 제어 방식 대신 AI가 교통량을 분석하여 신호 시간을 동적으로 조정하는 시스템입니다.

### 주요 목표

- 🚗 교통 상황 분석
- 🤖 LLM 기반 신호 계획 생성
- ✅ 신호 계획 평가
- 🛡 Guardrail 적용
- 📡 SSE 실시간 스트리밍
- 🌐 FastAPI 기반 로컬 서버 운영

---

# 🏗 시스템 구조

```text
Traffic Data
      │
      ▼
Traffic Situation Agent
      │
      ▼
Signal Planning Agent
      │
      ▼
Plan Evaluation Agent
      │
      ▼
Guardrail
      │
      ▼
FastAPI + SSE
      │
      ▼
Frontend
```

---

# ✨ 주요 기능

## 🚗 Traffic Situation Agent

- 교통량 분석
- 혼잡도 분석
- 현재 교통 상태 판단

## 🤖 Signal Planning Agent

- AI 기반 신호 시간 생성
- 동서 / 남북 방향 신호 계획 수립

## ✅ Plan Evaluation Agent

- 생성된 신호 계획 평가
- 적용 가능 여부 판단

## 🛡 Guardrail

- 최소 신호 시간 보장
- 최대 신호 시간 제한
- 비정상 값 자동 보정

## 📡 SSE(Server-Sent Events)

실시간으로 AI 처리 과정을 확인할 수 있습니다.

예시

- 교통 분석 시작
- 신호 계획 생성
- 평가 진행
- Guardrail 적용
- 최종 적용 완료

---

# 🛠 기술 스택

### Backend

- Python
- FastAPI

### AI

- Upstage Solar API
- Multi-Agent System

### Frontend

- HTML
- JavaScript
- SSE(Server-Sent Events)

### Tools

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

실행 화면은 추후 추가 예정입니다.

- 메인 화면
- SSE 스트리밍 로그
- AI 신호 계획 생성 결과
- 최종 신호 적용 결과

---

# 📈 프로젝트 특징

- LLM 기반 교통 신호 최적화
- Multi-Agent 구조 적용
- FastAPI 기반 로컬 서버 운영
- SSE 실시간 스트리밍
- Guardrail을 통한 안정성 확보

---

# 🔮 향후 개선 사항

- CityFlow와 실시간 연동
- 강화학습(RL) 기반 신호 최적화
- 다중 교차로 협업 제어
- 실시간 대시보드 구축

---

# 👨‍💻 Developer

**Jihoon Lee**

GitHub : https://github.com/jihooni217
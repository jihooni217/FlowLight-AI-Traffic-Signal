# 🚦 FlowLight

<p align="center">
  <img src="docs/flowlight_banner.png" width="100%">
</p>

<div align="center">

# AI-based Real-Time Traffic Signal Optimization

### LLM 기반 Multi-Agent를 활용한 실시간 교통 신호 최적화 시스템

**FastAPI · SSE · Solar API · Guardrail · CityFlow**

</div>

---

## 🎬 Live Demo

> 🚧 Demo GIF를 추가할 예정입니다.

---

## 📊 AI Performance Comparison

| Before AI | After AI |
|------------|----------|
| 🚧 GIF 예정 | 🚧 GIF 예정 |

> 📈 성능 비교 표와 실험 결과를 추가할 예정입니다.

---

## 📖 Project Overview

FlowLight는 **LLM 기반 Multi-Agent**를 활용하여 교차로의 실시간 교통 상황을 분석하고,
최적의 신호 시간을 생성하는 **AI 기반 교통 신호 최적화 시스템**입니다.

기존의 고정 신호 방식과 달리, AI Agent가 교통량과 대기 차량 수를 분석하여
상황에 맞는 신호 계획을 생성합니다.

생성된 신호 계획은 Guardrail을 통해 검증된 후 시뮬레이션에 적용되며,
FastAPI와 SSE(Server-Sent Events)를 이용하여 AI의 의사결정 과정을
실시간으로 확인할 수 있도록 구현했습니다.

---

## ✨ Key Features

- 🚦 **Real-Time Traffic Analysis**
  - 교통 상태를 실시간으로 분석하여 현재 상황을 파악

- 🤖 **LLM Multi-Agent Decision Making**
  - Traffic Analysis, Signal Planning, Plan Evaluation Agent를 통해 최적 신호 생성

- 🛡 **Guardrail Validation**
  - 비정상적인 신호 계획을 검증하고 안전한 결과만 적용

- ⚡ **Real-Time Streaming**
  - FastAPI와 SSE를 활용하여 AI 의사결정 과정을 실시간 표시

- 📊 **Traffic Simulation**
  - CityFlow 시뮬레이션과 연동하여 AI 적용 효과 검증

---

 ## 🤖 AI Decision Process

FlowLight는 **Multi-Agent 기반 AI Workflow**를 통해 교통 상황을 분석하고 최적의 신호 계획을 생성합니다.

<p align="center">
  <img src="docs/ai_decision_process.png" width="100%">
</p>

### AI Workflow

**1️⃣ Traffic Analysis Agent**

- 실시간 교통 데이터를 분석
- 교통량 및 대기 차량 수 파악
- 현재 혼잡도를 분석

**2️⃣ Signal Planning Agent**

- 분석 결과를 기반으로 신호 시간을 생성
- 방향별 Green Time 계산

**3️⃣ Plan Evaluation Agent**

- 생성된 신호 계획 평가
- 기존 신호보다 개선 여부 판단

**4️⃣ Guardrail Validation**

- 최소/최대 신호 시간 검증
- JSON 구조 검증
- 이상 값 제거

**5️⃣ Apply to Simulation**

- 검증된 신호 계획만 CityFlow 시뮬레이션에 적용

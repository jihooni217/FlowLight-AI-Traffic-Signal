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

FlowLight의 전체 시뮬레이션 실행 화면입니다.

<p align="center">
  <img src="docs/flowlight_live_demo.gif" width="100%">
</p>

---

## 📊 AI Performance Comparison

동일한 조건에서 **AI 미적용 고정 신호**와 **FlowLight AI 적용 신호**를 비교했습니다.

| Before AI | After AI |
|----------|---------|
| <img src="docs/flowlight_before_ai.gif" width="100%"> | <img src="docs/flowlight_after_ai.gif" width="100%"> |

> AI가 교통 상황을 분석하여 신호 시간을 조정하고, 검증된 신호 계획만 시뮬레이션에 적용합니다.

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

### Workflow Summary

| Agent | Responsibility |
|--------|----------------|
| 🔍 Traffic Analysis | 교통량 및 혼잡도 분석 |
| 📝 Signal Planning | 최적 신호 시간 생성 |
| 📊 Plan Evaluation | 기존 계획과 비교 평가 |
| 🛡 Guardrail | JSON 및 신호 시간 검증 |
| 🚦 Apply | 검증된 계획만 CityFlow 적용 |

---

## 🏗 System Architecture

FlowLight는 **Frontend → FastAPI → Multi-Agent → Guardrail → CityFlow**로 이어지는 구조를 사용합니다.

<p align="center">
  <img src="docs/system_architecture.png" width="100%">
</p>

### Architecture Summary

| Layer | Description |
|-------|-------------|
| 🖥 Frontend | HTML/JavaScript 기반 시뮬레이션 UI |
| 🚗 CityFlow | 교통 상태 생성 및 시뮬레이션 실행 |
| ⚙ FastAPI | API Server 및 Agent Orchestration |
| 🤖 Solar API | LLM 기반 교통 분석 및 신호 계획 생성 |
| 🛡 Guardrail | JSON 및 신호 시간 검증 |
| 🚦 Simulation | 검증된 신호 계획만 적용 |

---

# 📊 Experiment Results

FlowLight는 **동일한 교통 시나리오와 동일한 초기 조건**에서
기존 **고정 신호 제어(Fixed Signal)** 와
**AI 기반 적응형 신호 제어**의 성능을 비교했습니다.

<p align="center">
  <img src="docs/experiment_results.png" width="100%">
</p>

### Performance Summary

| Metric | Fixed Signal | FlowLight AI | Improvement |
|:--------|-------------:|-------------:|------------:|
| 🚗 Waiting Vehicles | **18** | **13** | **⬇ 27.8%** |
| 🚦 Throughput | **107** | **115** | **⬆ 7.5%** |
| 📈 Congestion Index | **1.00** | **0.76** | **⬇ 24.0%** |

> 동일한 시나리오와 동일한 초기 조건에서 비교를 수행하여 AI 기반 신호 제어의 개선 효과를 확인했습니다.

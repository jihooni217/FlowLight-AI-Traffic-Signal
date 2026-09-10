# 🚦 FlowLight

<p align="center">
  <img src="docs/flowlight_banner.png" width="100%">
</p>

<div align="center">

# AI-based Real-Time Traffic Signal Optimization

### A multi-agent traffic signal demo built on Upstage Solar Pro 4

**FastAPI · SSE · Solar Pro 4 · Structured Outputs · Guardrail · Traffic Simulator**

[한국어](README.md) · **English**

</div>

---

## 🎬 Live Demo

From the first-run guide to the real-data profile, the AI analysis and the applied signal plan.

<p align="center">
  <img src="docs/flowlight_live_demo.gif" width="100%">
</p>

---

# 📌 About the project

FlowLight replaces a fixed-time signal with **three LLM agents** that read the traffic situation, plan the green times and then grade their own plan.
Every LLM answer is forced into a fixed shape with **Structured Outputs (JSON Schema)**, passes through a rule-based **Guardrail**, and only then reaches the simulator.
FastAPI streams each step over SSE (Server-Sent Events), so you can watch the decision being made.

The repository is being turned into an official Upstage demo and tutorial. Two rules hold throughout:

- Real **hourly traffic volume** is converted into a **vehicle arrival rate** that spawns cars in the simulator. The **queue** (waiting vehicles) is always a simulation result.
  A volume of 842 vehicles per hour is never treated as 842 waiting cars.
- The model's internal reasoning is never switched on. The screen shows only the `summary` / `explanation` / `reason` fields the agents **explicitly return**.

---

## 📊 AI Performance Comparison

Fixed-time signals and FlowLight's AI plan under the same conditions.

| Before AI | After AI |
|----------|---------|
| <img src="docs/flowlight_before_ai.gif" width="100%"> | <img src="docs/flowlight_after_ai.gif" width="100%"> |

> The AI analyses the situation, adjusts the green times, and only a verified plan is applied to the simulation.
> These clips were recorded on the previous version (Solar Pro 3, manual traffic mode). The current UI adds a progress panel and a demand input panel.

---

# 🏗 System architecture

The pipeline runs **traffic data → simulator → FastAPI → multi-agent → Guardrail → back to the simulator**.

<p align="center">
  <img src="docs/system_architecture.png" width="100%">
</p>

This is how traffic data travels to the agents. Hourly volume only ever becomes an arrival rate. The number of waiting cars is computed by the simulator.

<p align="center">
  <img src="docs/data_flow.png" width="100%">
</p>

```
public traffic CSV ─(app/traffic_data.py: normalise · lane correction · veh/h → veh/s)─▶ demand profile
   ─(GET /api/traffic/profile)─▶ browser simulator (3x3 intersections, Poisson arrivals per approach)
   ─(per-approach queue · wait · arrivals · saturation)─▶ scenario JSON (demand + queues.by_approach)
   ─(POST /api/agent/stream, SSE)─▶ Agent 1 analysis → Agent 2 plan → Guardrail → Agent 3 evaluation → final decision
   ─▶ shown on screen and applied to the signals
```

| Layer | Description |
|-------|-------------|
| 📈 Traffic Data | Normalises a public traffic CSV into a per-approach demand profile and converts it to arrival rates |
| 🖥 Frontend | HTML/JavaScript simulator. Spawns cars from the profile, aggregates state, shows results |
| ⚙ FastAPI | API server, agent orchestration, SSE streaming, profile endpoint |
| 🤖 Solar Pro 4 | LLM analysis, signal planning and evaluation with Structured Outputs |
| 🛡 Guardrail | Minimum green and cycle checks, final decision correction |
| 🚦 Simulation | Applies verified plans only |

## Three values that must not be confused

| Value | Meaning | Where it comes from |
|---|---|---|
| `volume_per_hour` | Real input demand (veh/h) | public data |
| `arrival_rate_per_sec` | Spawn rate per lane (veh/s) = `volume / lanes / 3600` | backend `traffic_data.py` |
| `queue` | Vehicles currently waiting | **simulation result** (signals and car-following) |

---

# 🤖 How the AI decides

FlowLight is a **multi-agent workflow**: analyse the situation, plan the signal, grade the plan.

<p align="center">
  <img src="docs/ai_decision_process.png" width="100%">
</p>

| Step | Role |
|------|------|
| 🔍 Traffic Situation Agent | Traffic level, risk level, main congested direction |
| 📝 Signal Planning Agent | North-south / east-west / pedestrian green times |
| 🛡 Guardrail | Minimum green and cycle check, sends before/after values |
| 📊 Plan Evaluation Agent | Scores the plan and picks auto-apply / operator approval / re-plan |
| 🚦 Apply | Only verified plans reach the simulator |

## 🚗 Traffic Situation Agent (Agent 1)
- Judges traffic level and risk from vehicle count, stopped vehicles, congestion and pedestrians
- When `queues.by_approach` is present, picks the **main congested direction** (N/S/E/W or the axis) from per-approach queue and saturation
- Output: `summary`, `traffic_level`, `main_congestion_direction`, `pedestrian_issue`, `vulnerable_user_detected`, `risk_level`

## 🤖 Signal Planning Agent (Agent 2)
- Plans north-south and east-west vehicle green plus pedestrian green, in whole seconds
- With per-approach state, gives more green to the axis with the larger queue and saturation and cites the numbers in `explanation`
- Output: `durations` (three integers), `priority` (VEHICLE / PEDESTRIAN / BALANCED), `next_signals`, `explanation`

## ✅ Plan Evaluation Agent (Agent 3)
- Scores vehicles, pedestrians, vulnerable users, safety and efficiency, total 0 to 100
- Decision: `자동 적용` (auto apply) / `운영자 승인 필요` (operator approval) / `재계획 필요` (re-plan), fixed by a schema enum
- Output: `total_score`, `scores`, `decision_recommendation`, `reason`

## 🛡 Guardrail (rule based, enforced in code)
- Vehicle green at least 8 s. Pedestrian green at least 6 s when pedestrians are present, otherwise 0 s
- If the sum exceeds the cycle (`cycle_sec`), the times are redistributed proportionally
- The backend sends both the original and the corrected values, shown as "corrected: 14/6/0 → 12/8/0"

## 🧭 Final decision correction (backend)
These rules override the LLM's decision. They mirror the auto-apply preconditions in the prompt.
1. Green sum exceeds the cycle → `재계획 필요` (re-plan)
2. Pedestrians present but pedestrian green under 6 s → `재계획 필요` (re-plan)
3. No pedestrians · 20 or more stopped cars · congestion 0.7 or higher · pedestrian green 0 s → `자동 적용` (auto apply)

## 📡 SSE streaming
`POST /api/agent/stream` sends these events in order.

| event | data |
|---|---|
| `message` | `{step: 1..4, message}` progress |
| `message` | `{step: "guardrail", durations, before}` Guardrail result |
| `done` | `{input_state, traffic_analysis, signal_plan, evaluation, final_decision}` |
| `error` | `{status: "error", agent, message, detail}` (stream ends) |

## 🖥 Simulator (browser)
- Korean-style four-phase signals, protected left turns, amber and all-red, four pedestrian types with crosswalk yielding, four intersection control types, green-wave offsets
- **Demand input modes**
  - Manual: a network-wide veh/s slider spawns cars at random entry edges
  - Real-data profile: 3x3 grid, Poisson arrivals on the N/S/E/W entry edges from the backend profile, hour picker with auto advance, and a per-approach table of demand, arrival rate, entered, lost and queued vehicles
- Five-step AI progress panel with per-step timing, the agents' real output, Guardrail before/after
- A five-step usage guide appears on first launch and can be reopened from the sidebar
- Intersection type, data export, and the built-in Webster optimiser with a seeded A/B harness (independent of the LLM) live under the collapsed "Advanced settings" section

---

# 📊 Results

## Before and after AI (previous version)

Fixed-time control against AI-adaptive control on **the same scenario and the same initial state**.
This experiment dates from the Solar Pro 3 / manual traffic mode version.

<p align="center">
  <img src="docs/experiment_results.png" width="100%">
</p>

| Metric | Fixed Signal | FlowLight AI | Improvement |
|:--------|-------------:|-------------:|------------:|
| 🚗 Waiting Vehicles | **18** | **13** | **⬇ 27.8%** |
| 🚦 Throughput | **107** | **115** | **⬆ 7.5%** |
| 📈 Congestion Index | **1.00** | **0.76** | **⬇ 24.0%** |

## Live API verification (solar-pro4-260806, 2026-09-10)

| Condition | Result |
|---|---|
| Legacy input, `json_object` | 3/3 runs 200 · `stop`, 12/8/0, score 88, auto apply, 15.4 s total |
| Legacy input, `json_schema` | 3/3 runs 200 · `stop`, schema compliant, same result, 15.1 s total |
| Input with per-approach state, `json_schema` | main direction "north-south", plan 14/6/0 → Guardrail corrected to 12/8/0, score 88, auto apply, 24.6 s total |
| Run from the profile-mode UI (9 cars, 2 queued on N, saturation 1.2) | main direction "N", plan 12/8/0, score 82, operator approval → applied manually, congestion index 0.61 → 0.35 |

Reasoning stayed off (`reasoning_effort` not sent, 0 reasoning tokens). Response times depend on the network.
Cases where the Guardrail actually corrected a real Solar Pro 4 plan:

<p align="center">
  <img src="docs/guardrail_cases.png" width="100%">
</p>

---

# 🛠 Tech stack

<p>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white">
  <img src="https://img.shields.io/badge/SSE-2563EB?style=for-the-badge&logo=googletagmanager&logoColor=white">
  <img src="https://img.shields.io/badge/Solar_Pro_4-FF7A00?style=for-the-badge&logo=openai&logoColor=white">
</p>

| Area | Details |
|---|---|
| Backend | Python 3.10+, FastAPI, uvicorn |
| AI | Upstage Solar Pro 4 (`solar-pro4`), OpenAI-compatible SDK, Structured Outputs |
| Frontend | Single HTML file with Canvas and JavaScript, hand-parsed SSE |
| Data | CSV normalisation layer using the standard library only |
| Test | pytest, httpx (Solar calls are mocked by default) |

---

# 📂 Project layout

```text
FlowLight-AI-Traffic-Signal
├── app
│   ├── main.py                     # FastAPI: SSE pipeline, decision correction, profile endpoint
│   ├── agents.py                   # Solar client, 3 prompts, 3 JSON Schemas, Guardrail
│   ├── traffic_data.py             # public traffic CSV → normalised profile → arrival rates
│   └── index.html                  # simulator + UI + backend client (open this in a browser)
├── data
│   ├── README.md                   # data source, column mapping, synthetic sample formula, replacement steps
│   ├── sample_seoul_traffic_history.csv
│   └── sample_seoul_traffic_history.meta.json
├── tests                           # 215 tests (214 mocked + 1 live, live is opt-in)
├── docs
│   ├── screens/                    # current UI screens (guide, main, profile mode, progress, report, applied, advanced)
│   ├── flowlight_banner.png, flowlight_live_demo.gif
│   ├── system_architecture.png, data_flow.png, ai_decision_process.png, guardrail_cases.png
│   ├── flowlight_before_ai.gif, flowlight_after_ai.gif, experiment_results.png   # previous-version experiment
│   └── FlowLight_Final_Presentation.pdf
├── LICENSE                         # MIT
├── .env.example
├── pytest.ini
├── requirements.txt
├── README.md                       # Korean
└── README.en.md                    # English (this file)
```

---

# 🚀 Getting started

### 1. Clone

```bash
git clone https://github.com/jihooni217/FlowLight-AI-Traffic-Signal.git
```

### 2. Install (Python 3.10 or newer)

```bash
pip install -r requirements.txt
```

### 3. Environment variables

Copy `.env.example` to `.env` and paste your key. `.env` is not committed.

| Variable | Default | Description |
|---|---|---|
| `UPSTAGE_API_KEY` | (required) | Issued in the Upstage console |
| `UPSTAGE_MODEL` | `solar-pro4` | Set `solar-pro3` to roll back, or `solar-pro4-260806` to pin a snapshot |
| `UPSTAGE_OUTPUT_MODE` | `json_schema` | Structured Outputs. Fall back to `json_object` if needed |
| `TRAFFIC_PROFILE_META` | `data/sample_seoul_traffic_history.meta.json` | Path to another profile meta file |

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

The server listens on `http://127.0.0.1:8000`. `GET /` returns a health check.

### 5. Open the frontend

Open `app/index.html` directly in a browser. It calls the backend at `http://127.0.0.1:8000`, and CORS is open.

### 6. Walk through the demo

1. On first launch a five-step **usage guide** appears. Read it and press "Start". The sidebar button reopens it any time.
2. Press **Play** to start the simulation. 4x speed is comfortable to watch.
3. In **Traffic demand input** on the sidebar, choose *real-data profile*. The grid switches to 3x3 and cars are spawned from the per-approach demand of the selected hour (0 to 23). The default is the 08:00 peak.
4. Press **AI analysis**. The left panel shows the five steps as they run, and the report shows each agent's real output, the Guardrail correction and the evaluation reasoning.
5. If the final decision is auto apply, the signals change on their own. Otherwise use **Apply recommended values**. After 15 seconds the before/after effect is shown.

---

# 🔌 API

| Method · path | Description |
|---|---|
| `GET /` | Health check |
| `GET /api/traffic/profile` | Normalised demand profile: `meta`, `available_hours`, `hours[{hour, volume, arrival_rate_per_sec}]`. `?hour=8` returns one hour (400 out of range, 404 missing) |
| `POST /api/agent/stream` | Simulation state JSON → agent pipeline progress and result over SSE |
| `GET /api/agent/stream` | Same pipeline on a built-in mock state (for testing) |

## Input state (scenario) format

This is what the frontend sends. The legacy fields alone are enough. `demand` and `queues.by_approach` are added in profile mode on a 3x3 grid.

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
  "context": {"source": "flowlight_index_html", "grid_size": 3, "demand_mode": "profile",
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

- `demand` is input, `queues` is output. The prompts spell this out, and there is no `queue` key anywhere inside `demand`.
- Approach naming: `N` means vehicles **entering from the north and heading south**.

---

# 🧪 Tests

```bash
python -m pytest -q
```

- The default run never calls the Solar API (the client is mocked). Currently 214 pass and 1 is skipped as live.
- The live API test is opt-in.

```bash
RUN_LIVE_TESTS=1 python -m pytest tests/test_agent_stream.py -v
```

| File | Covers |
|---|---|
| `test_guardrail.py` | Guardrail and final decision correction rules |
| `test_stream_mocked.py` | SSE event order and payloads, request shape, error paths, CORS |
| `test_agents_config.py` | Model selection, request parameters, `finish_reason` handling |
| `test_output_schemas.py` | Upstage schema constraints, prompt consistency, negative cases |
| `test_prompts.py` | Demand vs state wording and per-approach instructions |
| `test_traffic_data.py` | CSV normalisation, validation, veh/h → veh/s conversion |
| `test_traffic_profile_api.py` | Profile endpoint |
| `test_scenario_extension.py` | Extended input passing through the backend |

---

# 📸 Screenshots

All captured on the current version (Solar Pro 4, real-data profile mode) with real API calls. The UI text is Korean.

## Usage guide on first launch

![Usage guide](docs/screens/help.png)

## Main screen

![Main screen](docs/screens/main.png)

## Real-data profile mode

The grid becomes a 3x3 network, and per-approach demand (input) and queue (simulation result) sit side by side in one table.

| Profile mode | Demand · arrival rate · entered · lost · queue per approach |
|---|---|
| ![Profile mode](docs/screens/profile_mode.png) | ![Demand table](docs/screens/demand_table.png) |

## AI progress panel

| Step 2 running | All five steps done |
|---|---|
| ![Running](docs/screens/ai_progress.png) | ![Done](docs/screens/ai_progress_done.png) |

## Analysis report

The `summary` / `explanation` / `reason` returned by the agents and the Guardrail result, shown as is.

![Analysis report](docs/screens/report.png)

## Applied plan

![Applied banner and result panel](docs/screens/applied.png)

## Advanced settings

Intersection type, data export and the built-in Webster optimiser are tucked into a collapsible section.

<p align="center">
  <img src="docs/screens/advanced.png" width="320">
</p>

---

# 📄 Presentation

Problem statement, agent design, architecture, experiment results and retrospective, in slide form (Korean).

[📑 View Final Presentation](docs/FlowLight_Final_Presentation.pdf)

| Section | Description |
|--------|-------------|
| Problem | Limits of fixed-time signal control |
| Method | LLM agents for analysis, planning and evaluation |
| Architecture | FastAPI, SSE, Solar API and Guardrail |
| Experiment | Traffic flow before and after AI |
| Retrospective | What we learned and what comes next |

---

# ⚠️ Known limitations

- The simulator is a pixel-scale custom implementation. Ratios such as the saturation flow (1800 veh/h/lane) match reality, but absolute speeds and distances do not.
- Pedestrian green is not applied as a real phase duration (0 s only turns the pedestrian signal off). After applying a plan the real cycle is the sum of vehicle greens plus 6 s.
- In manual mode, applying an AI plan still halves the spawn rate for 120 s as a relief measure. This is disabled in profile mode.
- The sample data is a **synthetic example** that follows the column layout of the real dataset. Steps for swapping in real data are in `data/README.md`.
- Even real peak-hour demand produces modest queues on a single 3x3 intersection. A congestion multiplier (`demo_scale`) and turn ratios (`turn_ratio`) are not implemented yet.

---

# 🚀 Roadmap

| Area | Description |
|------------------|-------------|
| **Real Traffic Data** | Wire up a real public data file, turn ratios (`turn_ratio`), congestion multiplier (`demo_scale`) |
| **Demo Packaging** | Serve the frontend statically to simplify setup |
| **Signal Fidelity** | Apply pedestrian phases for real and align the displayed cycle |
| **Roundabout Scenario** | Roundabout flow and priority rules |
| **Multi-Intersection Control** | Coordinated signals and green waves across neighbouring intersections |
| **Reinforcement Learning** | Hybrid optimisation combining LLM agents with RL |
| **Evaluation Automation** | Automatic collection of mean speed, queue length, throughput and other metrics |

---

# 👨‍💻 My contributions

I focused on **LLM agent design, backend integration, Guardrail verification, frontend wiring, experiments and the presentation**.

### AI / LLM
- Designed the Traffic Analysis, Signal Planning and Plan Evaluation agents
- Implemented the LLM call flow on the Upstage Solar API
- Converted traffic state into prompt input the model can use
- Designed the JSON output format for signal plans

### Backend
- Built the FastAPI agent server
- Set up the endpoints the frontend talks to
- Implemented real-time streaming with SSE
- Delivered analysis, plan and evaluation to the client in order

### Reliability
- Guardrail checks for minimum and maximum green times
- JSON response validation
- Filtered out invalid values so only safe plans are applied
- Error handling so the demo does not stop on failure

### Frontend / Demo
- Connected the HTML/JavaScript simulator to the backend
- Displayed analysis results and signal plans on screen
- Built the before/after comparison scenario
- Recorded the full demo video

### Documentation / Presentation
- Prepared the slides
- Documented the architecture and the decision process
- Analysed and presented the experiment results
- Gave the final presentation

---

# 📝 Lessons learned

Calling an LLM API turned out to be the easy part. The hard part was **evaluating and verifying the answer before letting it touch the service**.

- Designing an LLM as an **agent-based decision structure** rather than a question-and-answer box.
- Using prompt engineering and Structured Outputs so the model follows **a fixed input and output shape**.
- Streaming the analysis and its result to the screen **in real time** with FastAPI and SSE.
- Applying AI output **only after verification**, through the Guardrail and JSON validation.
- Presenting results with numbers and video together made the project far more convincing.

---

# 📄 License

MIT. See [LICENSE](LICENSE).

---

# 👨‍💻 Developer

**Jihoon Lee**

GitHub

https://github.com/jihooni217

"""
Shared test fixtures for the FlowLight backend.

Design goals (Stage 0 regression baseline):
- No real Upstage API call happens unless a test is marked `live` and
  RUN_LIVE_TESTS=1 is set in the environment.
- The Solar client used by app.agents is replaced with an in-memory fake that
  records every request and returns canned JSON responses, so the tests pin
  the CURRENT behaviour of the agent pipeline without touching app/ code.
"""
import json
import os
import sys
import types
from pathlib import Path

import pytest
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# app.agents builds an OpenAI client at import time and the SDK refuses a
# missing api_key. Mirror the app's own load_dotenv() first (real key wins if
# a .env exists), then fall back to a dummy value so unit tests can run
# anywhere. The value is never printed.
load_dotenv()
os.environ.setdefault("UPSTAGE_API_KEY", "dummy-key-for-unit-tests")


# --------------------------------------------------------------------------
# live-test gating
# --------------------------------------------------------------------------
def pytest_collection_modifyitems(config, items):
    if os.environ.get("RUN_LIVE_TESTS") == "1":
        return
    skip_live = pytest.mark.skip(
        reason="live Upstage API test; set RUN_LIVE_TESTS=1 to run"
    )
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)


# --------------------------------------------------------------------------
# Fake Solar client
# --------------------------------------------------------------------------
def make_chat_response(content, finish_reason="stop", reasoning=None, model="fake-model"):
    """Build an object shaped like openai's ChatCompletion for the fields app.agents reads."""
    message = types.SimpleNamespace(role="assistant", content=content, reasoning=reasoning)
    choice = types.SimpleNamespace(index=0, message=message, finish_reason=finish_reason)
    usage = types.SimpleNamespace(
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
        completion_tokens_details=types.SimpleNamespace(reasoning_tokens=0),
    )
    return types.SimpleNamespace(id="fake-id", model=model, choices=[choice], usage=usage)


class FakeCompletions:
    """Stand-in for client.chat.completions.

    Queue items may be:
      - dict            -> serialised with json.dumps(ensure_ascii=False)
      - str             -> returned verbatim as message.content
      - Exception       -> raised from create()
      - callable(kwargs)-> its return value is used as the response object
    """

    def __init__(self):
        self.calls = []
        self._queue = []

    def queue(self, *items):
        self._queue.extend(items)
        return self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if not self._queue:
            raise AssertionError("FakeCompletions: no queued response for call #%d" % len(self.calls))
        item = self._queue.pop(0)
        if isinstance(item, Exception):
            raise item
        if callable(item):
            return item(kwargs)
        if isinstance(item, dict):
            item = json.dumps(item, ensure_ascii=False)
        return make_chat_response(item)

    # convenience accessors used in assertions
    @property
    def models(self):
        return [c.get("model") for c in self.calls]

    def user_payload(self, idx):
        """Parse the JSON the agent sent as the user message of call `idx`."""
        return json.loads(self.calls[idx]["messages"][1]["content"])

    def system_prompt(self, idx):
        return self.calls[idx]["messages"][0]["content"]


@pytest.fixture
def fake_solar(monkeypatch):
    """Replace app.agents.client with a recording fake. Yields FakeCompletions."""
    import app.agents as agents

    completions = FakeCompletions()
    fake_client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=completions))
    monkeypatch.setattr(agents, "client", fake_client)
    return completions


# --------------------------------------------------------------------------
# Canned agent outputs (shape follows the prompts' "출력 형식" blocks)
# --------------------------------------------------------------------------
def analysis_ok(**overrides):
    out = {
        "summary": "차량 28대 중 19대가 정지해 있고 혼잡도가 0.89로 매우 높습니다.",
        "traffic_level": "높음",
        "main_congestion_direction": "전체",
        "pedestrian_issue": False,
        "vulnerable_user_detected": False,
        "risk_level": "보통",
    }
    out.update(overrides)
    return out


def plan_ok(ns=12, ew=8, ped=0, priority="VEHICLE", **overrides):
    out = {
        "plan_id": "PLAN-001",
        "next_signals": {"north_south": "GREEN", "east_west": "RED", "pedestrian": "RED"},
        "durations": {
            "north_south_green_sec": ns,
            "east_west_green_sec": ew,
            "pedestrian_green_sec": ped,
        },
        "priority": priority,
        "explanation": "정지 차량이 많아 남북 직진에 더 긴 녹색을 배분했습니다.",
    }
    out.update(overrides)
    return out


def eval_ok(decision="운영자 승인 필요", score=78, **overrides):
    out = {
        "total_score": score,
        "scores": {"vehicle": 20, "pedestrian": 15, "vulnerable_user": 15, "safety": 18, "efficiency": 10},
        "decision_recommendation": decision,
        "reason": "차량 흐름은 양호하나 안전 검토가 필요합니다.",
    }
    out.update(overrides)
    return out


# --------------------------------------------------------------------------
# Input scenarios
# --------------------------------------------------------------------------
@pytest.fixture
def frontend_scenario():
    """Exactly the JSON the HTML frontend (app/index.html, the scenario builder in the AI 분석 handler) POSTs."""
    return {
        "intersection_id": "simulation-current",
        "tick": 348,
        "signals": {"cycle_sec": 20},
        "queues": {"total_cars": 28, "stopped_cars": 19},
        "pedestrians": {"waiting_or_crossing": 0, "vulnerable_count": 0},
        "context": {"source": "flowlight_index_html", "grid_size": 4},
        "metrics": {"congestion": 0.894, "throughput_per_min": 125},
    }


# --------------------------------------------------------------------------
# SSE helpers
# --------------------------------------------------------------------------
def parse_sse(body: str):
    """Turn the raw text/event-stream body into a list of (event, data_dict)."""
    events = []
    for block in body.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        event, data = None, None
        for line in block.split("\n"):
            if line.startswith("event:"):
                event = line[len("event:"):].strip()
            elif line.startswith("data:"):
                data = json.loads(line[len("data:"):].strip())
        events.append((event, data))
    return events


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from app.main import app

    return TestClient(app)

"""
녹화 재생 데이터(app/replay_data.js) 계약 검사.

서버 없이 index.html 을 열었을 때 AI 분석 버튼이 재생하는 실제 Solar Pro 4 응답 기록이다.
백엔드가 보내는 SSE 이벤트 순서·형태와 같아야 화면의 파싱 코드가 그대로 동작한다.
"""
import json
import re
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parent.parent / "app"
REPLAY = APP / "replay_data.js"
INDEX = APP / "index.html"


@pytest.fixture(scope="module")
def replay():
    text = REPLAY.read_text(encoding="utf-8")
    m = re.search(r"window\.FLOWLIGHT_REPLAY\s*=\s*(\{.*\});\s*$", text, flags=re.S)
    assert m, "replay_data.js 는 window.FLOWLIGHT_REPLAY = {...}; 형태여야 한다"
    return json.loads(m.group(1))


def test_replay_metadata(replay):
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", replay["recorded_at"])
    assert replay["model"].startswith("solar-pro4")
    assert "실제 응답" in replay["note"]
    assert replay["request"]["demand"]["mode"] == "profile"
    assert "queue" not in replay["request"]["demand"]


def test_replay_events_follow_backend_sse_order(replay):
    events = replay["events"]
    names = [e["event"] for e in events]
    assert names == ["message", "message", "message", "message", "message", "done"]
    times = [e["t"] for e in events]
    assert times == sorted(times) and times[0] >= 0
    msgs = [e["data"] for e in events[:-1]]
    assert [m["step"] for m in msgs] == [1, 2, 3, "guardrail", 4]
    assert "교통 상황 분석" in msgs[1]["message"]
    assert "신호 계획 생성" in msgs[2]["message"]
    assert "Guardrail" in msgs[3]["message"] and "durations" in msgs[3] and "before" in msgs[3]
    assert "계획 평가" in msgs[4]["message"]


def test_replay_done_payload_is_complete_and_guardrail_safe(replay):
    done = replay["events"][-1]["data"]
    assert set(done) == {"input_state", "traffic_analysis", "signal_plan", "evaluation", "final_decision"}
    d = done["signal_plan"]["durations"]
    assert d["north_south_green_sec"] >= 8 and d["east_west_green_sec"] >= 8
    assert d["north_south_green_sec"] + d["east_west_green_sec"] + d["pedestrian_green_sec"] <= done["input_state"]["signals"]["cycle_sec"]
    assert done["final_decision"] in ("자동 적용", "운영자 승인 필요", "재계획 필요")
    assert done["final_decision"] == done["evaluation"]["decision_recommendation"]
    assert done["traffic_analysis"]["summary"] and done["signal_plan"]["explanation"] and done["evaluation"]["reason"]
    # Guardrail 이벤트의 결과가 done 의 계획과 같아야 화면 표시가 어긋나지 않는다
    guard = replay["events"][3]["data"]
    assert guard["durations"] == d


def test_index_wires_replay_mode():
    html = INDEX.read_text(encoding="utf-8")
    assert '<script src="replay_data.js"></script>' in html
    assert 'id="chk-replay"' in html
    assert "makeReplayResponse" in html and "window.FLOWLIGHT_REPLAY" in html
    assert "녹화 재생" in html

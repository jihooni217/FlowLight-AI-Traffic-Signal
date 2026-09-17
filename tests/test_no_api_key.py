"""
API 키 없이 서버를 켠 경우.

교통량 프로파일 API 와 화면의 녹화 재생은 키 없이 쓸 수 있어야 한다.
키가 없으면 Upstage 를 부르지 않고, 스트림은 detail="no_api_key" 오류를 보내며, 화면은 이를 보고 녹화를 재생한다.
"""
import subprocess
import sys
from pathlib import Path

from tests.conftest import parse_sse

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "app" / "index.html").read_text(encoding="utf-8")


def test_backend_imports_without_a_key(tmp_path):
    # .env 가 없는 폴더에서, 키 환경 변수 없이 app 을 import 한다.
    code = (
        "import os, sys; os.environ.pop('UPSTAGE_API_KEY', None); os.environ.pop('OPENAI_API_KEY', None);"
        "sys.path.insert(0, %r); import dotenv; dotenv.load_dotenv = lambda *a, **k: False;"
        "import app.main; from app.agents import has_api_key; print('OK', has_api_key())" % str(ROOT)
    )
    out = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr[-500:]
    assert out.stdout.strip() == "OK False"


def test_agent_call_is_skipped_without_a_key(monkeypatch, fake_solar):
    import app.agents as agents

    monkeypatch.delenv("UPSTAGE_API_KEY", raising=False)
    result = agents.call_solar_agent("Traffic Situation Agent", "prompt", {"a": 1})
    assert result["status"] == "error" and result["detail"] == agents.NO_API_KEY_DETAIL
    assert fake_solar.calls == []


def test_stream_reports_missing_key(monkeypatch, fake_solar, client, frontend_scenario):
    monkeypatch.delenv("UPSTAGE_API_KEY", raising=False)
    resp = client.post("/api/agent/stream", json=frontend_scenario)
    events = parse_sse(resp.text)
    assert events[-1][0] == "error"
    assert events[-1][1]["detail"] == "no_api_key"
    assert fake_solar.calls == []


def test_profile_api_works_without_a_key(monkeypatch, client):
    monkeypatch.delenv("UPSTAGE_API_KEY", raising=False)
    resp = client.get("/api/traffic/profile?hour=8")
    assert resp.status_code == 200


def test_page_falls_back_to_the_recording_on_missing_key():
    assert 'data.detail === "no_api_key" && !replaying' in HTML
    assert "return analyzeOnce(Object.assign({}, opts, {forceReplay: true, keyMissing: true}));" in HTML
    assert "if (!(chkReplay && chkReplay.checked) && !opts.forceReplay && !HOSTED_DEMO) {" in HTML
    assert "자동 재분석 건너뜀 (API 키 없음)" in HTML

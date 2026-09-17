"""
공개 데모(GitHub Pages) 검사.

- app/profile_data.js 는 백엔드 GET /api/traffic/profile 응답과 같아야 한다 (데이터를 바꾸면 scripts/build_profile_data.py 를 다시 돌린다).
- localhost 가 아닌 주소에서는 백엔드를 부르지 않고, 내장 프로파일과 녹화 재생을 쓴다.
- 배포 워크플로는 정적 파일 세 개만 올린다.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "app" / "index.html").read_text(encoding="utf-8")


def _bundled_profile():
    text = (ROOT / "app" / "profile_data.js").read_text(encoding="utf-8")
    m = re.search(r"window\.FLOWLIGHT_PROFILE\s*=\s*(\{.*\});\s*$", text, flags=re.S)
    assert m, "profile_data.js 는 window.FLOWLIGHT_PROFILE = {...}; 형태여야 한다"
    return json.loads(m.group(1))


def test_bundled_profile_matches_backend_response(client, monkeypatch):
    monkeypatch.delenv("TRAFFIC_PROFILE_META", raising=False)
    resp = client.get("/api/traffic/profile")
    assert resp.status_code == 200
    assert _bundled_profile() == resp.json()


def test_page_loads_bundled_files():
    assert '<script src="replay_data.js"></script>' in HTML
    assert '<script src="profile_data.js"></script>' in HTML


def test_hosted_mode_never_calls_the_backend():
    assert "var HOSTED_DEMO = /[?&]hosted=1(&|$)/.test(location.search) ||" in HTML
    assert "if (HOSTED_DEMO) throw new Error('공개 데모');" in HTML
    assert "!opts.forceReplay && !HOSTED_DEMO" in HTML
    assert "자동 재분석 건너뜀 (공개 데모)" in HTML


def test_profile_falls_back_to_bundled_data_when_server_is_down():
    assert "var bundled = window.FLOWLIGHT_PROFILE || null;" in HTML
    assert "서버 없이 내장 데이터 사용" in HTML


def test_pages_workflow_publishes_only_static_files():
    wf = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
    assert "cp app/index.html app/replay_data.js app/profile_data.js _site/" in wf
    assert ".py" not in wf.split("Prepare site")[1]
    assert ".env" not in wf

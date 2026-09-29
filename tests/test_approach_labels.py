"""
접근로 도로 이름 (approach_names): 데이터 계층 → API → 화면 이름표.

- 메타의 approach_names 는 검증을 거쳐 프로파일과 API 응답의 meta 에 그대로 실린다. 없으면 빈 dict.
- 화면은 실데이터 모드에서 이름표·출처 배지를 화면 좌표로 그리고, 이름이 없는 접근로에는 이름표를 붙이지 않는다.
"""
import json
from pathlib import Path

import pytest

from app.traffic_data import TrafficDataError, TrafficProfile, load_profile_from_meta, validate_approach_names

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "app" / "index.html").read_text(encoding="utf-8")
MEASURED_META = ROOT / "data" / "seoul_sungnyemun_20260916.meta.json"


def _profile(**kw):
    base = dict(site_id="X", site_name="x", date="20250514", source="s", license="l",
                lanes={"N": 1, "S": 1, "E": 1, "W": 1}, hours=[{"hour": 8, "volume": {"N": 1, "S": 1, "E": 1, "W": 1}}])
    base.update(kw)
    return TrafficProfile(**base)


def test_names_default_to_empty_and_round_trip():
    p = _profile()
    assert p.approach_names == {} and p.to_dict()["meta"]["approach_names"] == {}
    q = _profile(approach_names={"N": " 세종대로(시청역2) ", "E": "퇴계로"})
    assert q.approach_names == {"N": "세종대로(시청역2)", "E": "퇴계로"}       # 일부 접근로만 있어도 되고 공백은 다듬는다
    assert TrafficProfile.from_dict(q.to_dict()).approach_names == q.approach_names


@pytest.mark.parametrize("bad", [{"X": "a"}, {"N": ""}, {"N": 3}, ["N"]])
def test_bad_names_are_rejected(bad):
    with pytest.raises(TrafficDataError):
        validate_approach_names(bad)


def test_measured_meta_names_every_approach():
    meta = json.loads(MEASURED_META.read_text(encoding="utf-8"))
    assert set(meta["approach_names"]) == {"N", "S", "E", "W"}
    profile = load_profile_from_meta(MEASURED_META)
    assert profile.approach_names["N"] == "세종대로(시청역2)"
    assert profile.approach_names["W"] == "서소문로(시청역)"


def test_api_serves_names_for_the_measured_profile(client, monkeypatch):
    monkeypatch.delenv("TRAFFIC_PROFILE_META", raising=False)
    body = client.get("/api/traffic/profile", params={"profile": "seoul_sungnyemun_20260916"}).json()
    assert body["meta"]["approach_names"]["E"] == "퇴계로(회현역)"
    sample = client.get("/api/traffic/profile").json()
    assert sample["meta"]["approach_names"] == {}


def test_page_draws_labels_outside_the_grid_and_a_source_badge():
    assert "Renderer.prototype._drawDemandOverlay = function(cam)" in HTML
    assert "SimController.prototype.demandOverlay = function()" in HTML
    assert "this.renderer.overlaySource = this;" in HTML
    assert "if (!names[a] || !edges || edges.length === 0) continue;" in HTML     # 이름 없는 접근로는 이름표 없음
    assert "var gap = L.r * cam.scale + 6;" in HTML                               # 인도 원 바깥에 둔다
    assert "var hasLabels = !!(ov && ov.labels && ov.labels.length);" in HTML     # 격자를 맞출 때 이름표 자리를 비운다
    assert "'대/시 ' + L.arrow" in HTML and "차로" not in HTML.split("_drawDemandOverlay = function(cam)")[1].split("// ===== SimController")[0]
    assert "var mx = hasLabels ? 34 : 16;" in HTML                                    # 한 줄 이름표라 여백이 작다
    assert "roadName" in HTML and "row.cells[0].appendChild(small);" in HTML       # 표 둘째 줄
    # 떠 있는 AI 패널의 오른쪽 선(leftBound) 왼쪽에는 격자·이름표·배지를 두지 않는다
    assert "SimController.prototype._panelLeftBound = function()" in HTML
    assert "leftBound: this._panelLeftBound()" in HTML
    assert "var LB = ov.leftBound || 0;" in HTML and "var bx = LB + 10" in HTML


def test_fit_uses_the_drawn_extent_and_centres_on_the_whole_canvas():
    # 맞추는 대상은 그려지는 범위(첫 노드~마지막 노드 + 테두리 여유)이고, 가로는 화면 가운데가 기본, 패널과 겹칠 때만 민다
    assert "var FIT_PAD = 32;" in HTML
    assert "var nw = (self.gridSize - 1) * sp + 2 * FIT_PAD, nh = nw;" in HTML
    assert "var px = (rect.width - nw * s) / 2;" in HTML
    assert "if (px < left + mx) px = left + mx;" in HTML
    assert "return { scale: s, x: px - x0 * s, y: py - y0 * s };" in HTML
    assert "(self.gridSize+1)*100" not in HTML


def test_zoom_out_stops_at_the_fitted_scale():
    # 축소 하한 = 화면 맞춤 배율. 그 아래로는 이름표끼리 겹치므로, 하한에 닿으면 맞춤 위치로 되돌린다.
    assert "var zoomBy = function(factor, mx, my)" in HTML
    assert "if (newScale <= fit.scale) {" in HTML
    assert "self.cam.scale = fit.scale; self.cam.x = fit.x; self.cam.y = fit.y;" in HTML
    assert "Math.max(0.2, Math.min(self.cam.scale" not in HTML                      # 예전 고정 하한 0.2는 없다
    for who in ("zoomBy(Math.exp(wheel * 0.1), mx, my);", "zoomBy(Math.exp(0.2), rect.width / 2, rect.height / 2);",
                "zoomBy(Math.exp(-0.2), rect.width / 2, rect.height / 2);"):
        assert who in HTML

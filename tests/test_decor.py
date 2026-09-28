"""
배경 꾸밈(도로 사이 블록의 건물·녹지 윤곽) 배선 검사.

- 기본은 켜짐이고 고급 설정에서 끌 수 있다.
- 인도·도로보다 먼저 그려서 차량·신호등 위에 올라오지 않는다.
- 배치는 격자 크기와 차로 수로 정해지는 난수라 같은 조건이면 같은 모양이다 (실제 건물이 아니라는 안내 포함).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "app" / "index.html").read_text(encoding="utf-8")


def test_toggle_exists_and_defaults_on():
    assert '<input type="checkbox" id="chk-decor" checked>' in HTML
    assert "self.renderer.decorOn = chkDecor.checked;" in HTML
    assert "실제 건물이 아니고" in HTML


def test_decor_is_drawn_under_roads():
    render = HTML.split("Renderer.prototype.render = function(network, jc, cam)")[1]
    draw_at = render.index("if (this.decorOn !== false) this._drawDecor(network);")
    sidewalk_at = render.index("// 인도:")
    road_at = render.index("// 도로:")
    assert draw_at < sidewalk_at < road_at


def test_boundary_nodes_use_the_ring_road_width_and_lamps_stand_upright():
    # 경계 노드 바닥판은 테두리 도로 폭: 넓은 진입로가 테두리 밖으로 삐져나오지 않는다
    assert "function boundaryHalfOf(nd)" in HTML
    assert "var nh = nd.isBoundary ? boundaryHalfOf(nd) : nodeHalfOf(nd);" in HTML
    # 보행 신호기는 횡단보도 끝 옆 인도 위에, 긴 축을 횡단 방향에 맞춰 두고 녹색 렌즈가 도로 쪽을 본다.
    # 남은 시간은 그 뒤(교차로 반대쪽), 인도와 블록 사이 띠에 붙는다.
    assert "var sx = cw.cx + cw.tx * 7 + cw.px*sd*(cw.half+2.5);" in HTML
    assert "ctx.rotate(Math.atan2(cw.py, cw.px));" in HTML
    assert "ctx.arc(-sd * 1.8, 0, 1.2, 0, Math.PI*2); ctx.fill();" in HTML     # 녹색 렌즈 = 도로 쪽
    assert "var tox = cw.tx * (rh / 2 + 6.5) + cw.px * sd * 1.5;" in HTML
    # 차로 수가 바뀌면 횡단보도 길이를 도로 폭에 맞춘다
    assert "list[c].half = Math.max(CW_HALF, roadWidthOf(list[c].edgeIn) / 2 + 2);" in HTML


def test_layout_is_seeded_and_cached_by_grid_and_lanes():
    assert "function seededRand(seed)" in HTML
    assert "var sig = network.gridSize + '|' + network.edges.length + '|';" in HTML
    assert "if (!this._decor || this._decor.sig !== sig) this._decor = { sig: sig, blocks: this.buildDecor(network) };" in HTML
    assert "var parkAt = count > 1 ? Math.floor(seededRand(N * 7 + 1)() * count) : -1;" in HTML   # 격자당 녹지 하나

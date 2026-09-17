"""
화면 렌더링과 A/B 검증의 회귀 검사 (브라우저 없이 index.html 을 문자열로 확인).

- 차로 수가 다른 도로가 테두리와 만나도 인도의 둥근 끝이 격자 밖으로 튀어나오지 않아야 한다.
- AI 적용 뒤 A/B 검증을 돌려도 B 단계의 Webster 권장값이 감응 모드에 덮어쓰이지 않아야 한다.
"""
import re
from pathlib import Path

HTML = (Path(__file__).resolve().parent.parent / "app" / "index.html").read_text(encoding="utf-8")


def test_sidewalks_use_butt_caps_and_node_circles_sized_by_the_narrowest_road():
    block = HTML[HTML.index("// 인도: 도로 가장자리에 사람만 통행 가능한 영역"):HTML.index("// 도로: 인도 위에 차량이 다니는 슬래브")]
    assert "ctx.lineCap = 'butt';" in block
    assert "lineCap = 'round'" not in block
    assert "Math.min(prev.r, ww / 2)" in block
    assert "ctx.arc(wr.nd.x, wr.nd.y, wr.r, 0, Math.PI * 2)" in block


def test_webster_recommendations_switch_off_actuation():
    start = HTML.index("Analyzer.prototype.applyRecommendations = function()")
    body = HTML[start:HTML.index("// ===== Renderer =====", start)]
    assert re.search(r"light\.actuated = null;\s*light\.leadingLeft = \{\};", body)
    assert body.index("light.actuated = null;") < body.index("light.applyGreens(ng, rec.recommended.cycle);")

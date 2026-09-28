"""
조작 요소 설명: 뜻이 바로 안 보이는 것에만 보이는 한 줄, 나머지는 마우스를 올리면 뜨는 설명(title).
AI 패널의 네 칸(진행·상태·결과·효과)에는 한 줄씩 설명이 있다.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "app" / "index.html").read_text(encoding="utf-8")


def test_visible_hints_only_for_the_unobvious_controls():
    for anchor, text in [
        ('id="sim-cycle"', "AI에 보내는 한 주기 길이입니다"),
        ('id="sim-max-cars"', "화면에 동시에 둘 수 있는 차량 상한입니다"),
        ('id="sim-max-speed"', "차량의 최고 속도입니다"),
        ('id="chk-demand-autohour"', "120초마다 다음 시간대로 넘어갑니다"),
    ]:
        after = HTML.split(anchor, 1)[1][:700]
        assert text in after, anchor


def test_tooltips_on_the_rest():
    for id_, words in [
        ("btn-toggle-play", "시작하거나 멈춥니다"),
        ("btn-reset", "처음 상태로"),
        ("sim-profile-source", "합성 예제는"),
        ("btn-optimize", "10~25초"),
        ("btn-apply-opt", "운영자 승인 필요"),
        ("stat-cars", "차량 수"),
        ("stat-throughput", "최근 1분"),
    ]:
        # title 은 같은 요소나 그 label 에 붙는다: id 앞 400자 안에 있으면 된다
        i = HTML.index('id="%s"' % id_)
        assert words in HTML[max(0, i - 400):i + 200], id_
    assert 'title="화면 속 시간의 빠르기입니다' in HTML          # 배속
    assert 'title="교차로 수입니다. 3x3은 교차로 1개' in HTML    # 격자 크기


def test_ai_panel_sections_each_carry_one_note():
    # 자리가 좁아 결과·효과 두 칸만 보이는 설명, 진행·상태는 제목에 마우스를 올리면 뜨는 설명
    notes = re.findall(r'<span class="panel-note">(.*?)</span>', HTML)
    assert len(notes) == 2
    assert "Guardrail" in notes[0]
    assert "15초" in notes[1]
    assert 'title="AI 분석을 누르면 단계가 차례로 켜지고' in HTML
    assert 'title="Agent가 돌려준 계획입니다' in HTML
    assert "#ai-floating-panel .panel-note" in HTML

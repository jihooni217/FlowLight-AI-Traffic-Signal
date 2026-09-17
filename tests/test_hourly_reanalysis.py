"""
시간대 변경 시 AI 자동 재분석의 화면 배선 검사 (브라우저 없이 index.html 을 문자열로 확인).

실제 교차로가 시간대별 신호 계획을 쓰듯, 실데이터 프로파일의 시간대가 바뀌면 AI 분석을 한 번 다시 부른다.
기본은 꺼져 있고, 켜도 분석이 겹치지 않으며, 자동 호출에서는 리포트 창·알림·녹화 재생을 쓰지 않는다.
"""
from pathlib import Path

HTML = (Path(__file__).resolve().parent.parent / "app" / "index.html").read_text(encoding="utf-8")


def test_checkbox_exists_and_is_off_by_default():
    assert '<input type="checkbox" id="chk-hour-reanalyze">' in HTML
    assert "this.autoReanalyze = false;" in HTML
    assert "시간대가 바뀌면 AI 재분석" in HTML


def test_hour_change_schedules_one_reanalysis_after_settle_time():
    assert "this.reanalyzeSettle = 20;" in HTML
    assert "if (this.autoReanalyze && hour !== this.profileHour) this.reanalyzeAt = this.simTime + this.reanalyzeSettle;" in HTML
    # 예약 시각이 지나고 분석 중이 아닐 때만, A/B 검증(skipUI) 중에는 부르지 않는다
    assert "if (!skipUI && this.autoReanalyze && this.reanalyzeAt !== null && this.simTime >= this.reanalyzeAt" in HTML
    assert "this.runAIAnalysis({auto: true" in HTML


def test_analyses_never_overlap():
    assert "if (self.aiBusy) return;" in HTML
    assert "try { await analyzeOnce(opts); } finally { self.aiBusy = false; }" in HTML


def test_auto_run_is_quiet_and_does_not_replay_recordings():
    assert "if (!opts.auto) document.getElementById('log-overlay').classList.remove('hidden');" in HTML
    assert "if (!self.quietApply) alert(" in HTML
    assert "if (!replayRec || opts.auto) throw netErr;" in HTML
    assert "자동 재분석 건너뜀 (서버 연결 실패)" in HTML


def test_reapplying_stops_the_previous_effect_timer():
    assert "if (self.effectTimer) clearInterval(self.effectTimer);" in HTML

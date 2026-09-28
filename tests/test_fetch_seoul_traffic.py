"""
scripts/fetch_seoul_traffic.py: 열린데이터광장 VolInfo/SpotInfo 응답을 로더 형식 CSV 로 바꾸는 부분.

네트워크는 쓰지 않는다. 응답 XML 은 시험용 키(sample)로 실제 받은 형식을 그대로 흉내 낸다.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fetch_seoul_traffic", ROOT / "scripts" / "fetch_seoul_traffic.py")
fst = importlib.util.module_from_spec(spec)
sys.modules["fetch_seoul_traffic"] = fst
spec.loader.exec_module(fst)

VOL_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><VolInfo><list_total_count>4</list_total_count>'
    "<RESULT><CODE>INFO-000</CODE><MESSAGE>정상 처리되었습니다</MESSAGE></RESULT>"
    "<row><spot_num>A-01</spot_num><ymd>20240101</ymd><hh>08</hh><io_type>1</io_type><lane_num>1</lane_num><vol>247</vol></row>"
    "<row><spot_num>A-01</spot_num><ymd>20240101</ymd><hh>08</hh><io_type>1</io_type><lane_num>2</lane_num><vol>393</vol></row>"
    "<row><spot_num>A-01</spot_num><ymd>20240101</ymd><hh>08</hh><io_type>2</io_type><lane_num>1</lane_num><vol>302</vol></row>"
    "<row><spot_num>A-01</spot_num><ymd>20240101</ymd><hh>08</hh><io_type>2</io_type><lane_num>2</lane_num><vol>290</vol></row>"
    "</VolInfo>"
)
ERR_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><response><RESULT><CODE>ERROR-301</CODE>'
    "<MESSAGE>파일타입 값이 누락 혹은 유효하지 않습니다.</MESSAGE></RESULT></response>"
)
SPOT_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><SpotInfo><list_total_count>2</list_total_count>'
    "<RESULT><CODE>INFO-000</CODE><MESSAGE>정상 처리되었습니다</MESSAGE></RESULT>"
    "<row><spot_num>C-02</spot_num><spot_nm>월드컵대교</spot_nm><grs80tm_x>189882</grs80tm_x><grs80tm_y>450789</grs80tm_y></row>"
    "<row><spot_num>F-01</spot_num><spot_nm>올림픽대로</spot_nm><grs80tm_x>197646</grs80tm_x><grs80tm_y>445188</grs80tm_y></row>"
    "</SpotInfo>"
)


def test_parse_rows_reads_the_real_response_shape():
    total, rows = fst.parse_rows(VOL_XML, "VolInfo")
    assert total == 4 and len(rows) == 4
    assert rows[0] == {"spot_num": "A-01", "ymd": "20240101", "hh": "08", "io_type": "1", "lane_num": "1", "vol": "247"}


def test_parse_rows_raises_on_api_error():
    with pytest.raises(fst.SeoulApiError, match="ERROR-301"):
        fst.parse_rows(ERR_XML, "VolInfo")


def _fake_getter(spot_lanes: dict, date="20240515"):
    """지점별 차로 수에 맞춰 VolInfo 응답을 만든다. 시간대별 교통량 = 100×차로번호 + 시간."""
    def getter(url):
        tail = url.split("/xml/VolInfo/")[1]          # "1/1000/A-01/20240515/08/"
        _, _, spot, ymd, hh, _ = tail.split("/")
        rows = []
        for io in ("1", "2"):
            for lane in range(1, spot_lanes[spot] + 1):
                vol = 100 * lane + int(hh) + (0 if io == "1" else 1000)
                rows.append(f"<row><spot_num>{spot}</spot_num><ymd>{ymd}</ymd><hh>{hh}</hh><io_type>{io}</io_type><lane_num>{lane}</lane_num><vol>{vol}</vol></row>")
        return (f'<?xml version="1.0"?><VolInfo><list_total_count>{len(rows)}</list_total_count>'
                "<RESULT><CODE>INFO-000</CODE><MESSAGE>ok</MESSAGE></RESULT>" + "".join(rows) + "</VolInfo>")
    return getter


def test_fetch_day_maps_io_type_to_the_loader_labels():
    getter = _fake_getter({"A-01": 2})
    rows = fst.fetch_day("k", ["A-01"], "20240515", hours=[8], getter=getter, log=lambda *a: None)
    assert [r[3] for r in rows] == ["유입", "유입", "유출", "유출"]
    assert rows[0] == ["A-01", "20240515", "08", "유입", "1", "108"]


def test_written_csv_loads_through_the_project_loader(tmp_path, monkeypatch):
    monkeypatch.setenv(fst.KEY_ENV, "test-key")
    lanes = {"A-01": 3, "A-02": 3, "B-01": 2, "B-02": 2}
    args = fst.build_parser().parse_args([
        "fetch", "--date", "20240515", "--spot", "N=A-01", "--spot", "S=A-02", "--spot", "E=B-01", "--spot", "W=B-02",
        "--name", "테스트 교차로", "--out", str(tmp_path / "seoul_test.csv"),
    ])
    mapping = fst.parse_spot_args(args.spot)
    rows = fst.fetch_day("k", list(mapping), args.date, hours=range(24), getter=_fake_getter(lanes), log=lambda *a: None)
    meta_path = fst.write_outputs(rows, mapping, args)
    assert meta_path.name == "seoul_test.meta.json"

    profile = fst.verify(meta_path, log=lambda *a: None)
    assert profile.lanes == {"N": 3, "S": 3, "E": 2, "W": 2}       # 차로 수는 차로번호 종류 수로 센다
    assert len(profile.hours) == 24
    hv = profile.hour(8)
    assert hv.volume["N"] == (100 + 8) + (200 + 8) + (300 + 8)      # 유입 행만 더한다
    assert hv.volume["E"] == (100 + 8) + (200 + 8)
    assert profile.site_name == "테스트 교차로" and profile.date == "20240515"


def test_spot_args_require_all_four_approaches():
    with pytest.raises(SystemExit):
        fst.parse_spot_args(["N=A-01", "S=A-02", "E=B-01"])
    assert fst.parse_spot_args(["n=A-01", "S=A-02", "E=B-01", "W=B-02"]) == {"A-01": "N", "A-02": "S", "B-01": "E", "B-02": "W"}


def test_spots_lists_and_sorts_by_distance(capsys, monkeypatch):
    monkeypatch.setenv(fst.KEY_ENV, "test-key")
    args = fst.build_parser().parse_args(["spots", "--near", "197000", "445000", "--k", "1"])
    spots = fst.cmd_spots(args, getter=lambda url: SPOT_XML)
    assert [s["spot_num"] for s in spots] == ["F-01"]
    assert "올림픽대로" in capsys.readouterr().out


def test_key_is_read_from_the_environment_only(monkeypatch):
    monkeypatch.delenv(fst.KEY_ENV, raising=False)
    monkeypatch.setattr(fst, "ROOT", Path("/nonexistent"))
    with pytest.raises(fst.SeoulApiError, match=fst.KEY_ENV):
        fst.api_key()

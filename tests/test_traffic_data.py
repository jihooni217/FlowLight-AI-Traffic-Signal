"""
Stage 6-1: traffic data layer. No network, no simulator, no AI.

Semantics under test:
  volume_per_hour (demand) -> arrival_rate_per_sec (spawn rate) ; queue is never produced here.
"""
import csv
import json
from pathlib import Path

import pytest

from app.traffic_data import (
    APPROACHES,
    DEMAND_NOTE,
    SECONDS_PER_HOUR,
    HourVolume,
    TrafficDataError,
    TrafficProfile,
    load_profile_from_meta,
    load_seoul_traffic_history,
    validate_hour,
    validate_lanes,
    validate_lanes_map,
    validate_turn_ratio,
    validate_volume,
    volume_to_arrival_rate,
    weekday_from_date,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SAMPLE_CSV = DATA / "sample_seoul_traffic_history.csv"
SAMPLE_META = DATA / "sample_seoul_traffic_history.meta.json"
SITE_MAP = {"DEMO-N": "N", "DEMO-S": "S", "DEMO-E": "E", "DEMO-W": "W"}

SEOUL_HEADER = ["지점번호", "년월일", "시간", "유입유출 구분", "차로번호", "교통량"]


def _write_csv(path: Path, rows, header=SEOUL_HEADER):
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return path


def _full_day_rows(date="20250514", flow="유입", lanes=(1,)):
    """4 sites x 24 h x lanes, volume = 100 + hour, per lane."""
    rows = []
    for site in SITE_MAP:
        for h in range(24):
            for lane in lanes:
                rows.append([site, date, f"{h:02d}", flow, lane, 100 + h])
    return rows


# ==========================================================================
# 1. veh/hour -> veh/sec
# ==========================================================================
class TestConversion:
    def test_842_per_hour_is_842_over_3600_per_sec(self):
        assert volume_to_arrival_rate(842) == pytest.approx(842 / 3600)
        assert volume_to_arrival_rate(842) == pytest.approx(0.23389, abs=1e-5)

    def test_lanes_divide_the_rate(self):
        assert volume_to_arrival_rate(842, lanes=3) == pytest.approx(842 / 3 / 3600)
        assert volume_to_arrival_rate(842, lanes=3) == pytest.approx(0.07796, abs=1e-5)

    def test_default_lanes_is_one(self):
        assert volume_to_arrival_rate(3600) == pytest.approx(1.0)

    def test_zero_volume_is_zero_rate(self):
        assert volume_to_arrival_rate(0, lanes=2) == 0.0

    def test_string_inputs_are_accepted(self):
        assert volume_to_arrival_rate("842", "3") == pytest.approx(842 / 3 / 3600)

    def test_constant(self):
        assert SECONDS_PER_HOUR == 3600


# ==========================================================================
# 2. validation
# ==========================================================================
class TestValidation:
    @pytest.mark.parametrize("bad", [-1, 24, "25", "abc", None, 3.5])
    def test_hour_out_of_range_or_invalid(self, bad):
        with pytest.raises(TrafficDataError):
            validate_hour(bad)

    @pytest.mark.parametrize("ok, expected", [(0, 0), (23, 23), ("08", 8), ("8시", 8), (" 7 ", 7)])
    def test_hour_accepted_forms(self, ok, expected):
        assert validate_hour(ok) == expected

    @pytest.mark.parametrize("bad", [-5, "-5", "abc", None, 12.5, float("nan"), float("inf"), True])
    def test_invalid_volume(self, bad):
        with pytest.raises(TrafficDataError):
            validate_volume(bad)

    @pytest.mark.parametrize("ok, expected", [(842, 842), ("842", 842), ("12.0", 12), ("1,250", 1250), (0, 0)])
    def test_valid_volume(self, ok, expected):
        assert validate_volume(ok) == expected

    @pytest.mark.parametrize("bad", [0, -1, "x", None, 2.5, True])
    def test_invalid_lanes(self, bad):
        with pytest.raises(TrafficDataError):
            validate_lanes(bad)

    def test_lanes_map_requires_all_four_approaches(self):
        with pytest.raises(TrafficDataError, match="누락"):
            validate_lanes_map({"N": 3, "S": 3, "E": 2})
        with pytest.raises(TrafficDataError, match="알 수 없는"):
            validate_lanes_map({"N": 3, "S": 3, "E": 2, "W": 2, "NE": 1})
        with pytest.raises(TrafficDataError):
            validate_lanes_map({"N": 3, "S": 0, "E": 2, "W": 2})

    def test_turn_ratio_must_sum_to_one_and_be_non_negative(self):
        ok = {"N": {"straight": 0.7, "left": 0.2, "right": 0.1}}
        assert validate_turn_ratio(ok)["N"]["straight"] == pytest.approx(0.7)
        with pytest.raises(TrafficDataError, match="합계"):
            validate_turn_ratio({"N": {"straight": 0.7, "left": 0.2, "right": 0.2}})
        with pytest.raises(TrafficDataError):
            validate_turn_ratio({"N": {"straight": 1.2, "left": -0.2, "right": 0.0}})
        with pytest.raises(TrafficDataError):
            validate_turn_ratio({"N": {"straight": 1.0}})
        with pytest.raises(TrafficDataError):
            validate_turn_ratio({"X": {"straight": 1.0, "left": 0.0, "right": 0.0}})
        assert validate_turn_ratio(None) is None

    def test_weekday_from_date(self):
        assert weekday_from_date("20250514") == "Wed"
        assert weekday_from_date("2025-05-14") == "Wed"
        with pytest.raises(TrafficDataError):
            weekday_from_date("20250231")


# ==========================================================================
# 3. profile structure
# ==========================================================================
class TestProfileStructure:
    def _profile(self, **overrides):
        kwargs = dict(
            site_id="A-01",
            site_name="예시",
            date="20250514",
            source="test",
            license="test",
            lanes={"N": 3, "S": 3, "E": 2, "W": 2},
            hours=[HourVolume(8, {"N": 842, "S": 790, "E": 610, "W": 655})],
        )
        kwargs.update(overrides)
        return TrafficProfile(**kwargs)

    def test_fields_follow_the_design(self):
        p = self._profile()
        d = p.to_dict()
        assert set(d) == {"meta", "hours"}
        assert set(d["meta"]) == {"site_id", "site_name", "date", "weekday", "source", "license", "unit", "lanes"}
        assert d["meta"]["weekday"] == "Wed"
        assert d["meta"]["unit"] == "veh_per_hour"
        assert set(d["hours"][0]) == {"hour", "volume"}
        assert set(d["hours"][0]["volume"]) == set(APPROACHES)

    def test_hour_volume_requires_all_four_approaches(self):
        with pytest.raises(TrafficDataError, match="누락"):
            HourVolume(8, {"N": 1, "S": 1, "E": 1})

    def test_duplicate_hours_rejected(self):
        with pytest.raises(TrafficDataError, match="중복"):
            self._profile(hours=[
                HourVolume(8, {"N": 1, "S": 1, "E": 1, "W": 1}),
                HourVolume(8, {"N": 2, "S": 2, "E": 2, "W": 2}),
            ])

    def test_empty_hours_rejected(self):
        with pytest.raises(TrafficDataError):
            self._profile(hours=[])

    def test_missing_hour_lookup_is_an_error(self):
        with pytest.raises(TrafficDataError, match="8시|9시"):
            self._profile().hour(9)

    def test_arrival_rates_apply_per_approach_lanes(self):
        rates = self._profile().arrival_rates(8)
        assert rates["N"] == pytest.approx(842 / 3 / 3600)
        assert rates["E"] == pytest.approx(610 / 2 / 3600)

    def test_demand_block_separates_demand_from_queue(self):
        d = self._profile().demand_for_hour(8)
        assert set(d) == {"site_id", "hour", "unit", "volume_per_hour", "lanes", "arrival_rate_per_sec", "note"}
        assert d["volume_per_hour"]["N"] == 842
        assert d["arrival_rate_per_sec"]["N"] == pytest.approx(842 / 3 / 3600, abs=1e-6)

        # No key anywhere in the demand block may be a queue: 842 is demand, never a queue length.
        def keys(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    yield k
                    yield from keys(v)

        assert not any("queue" in k.lower() for k in keys(d))
        assert d["note"] == DEMAND_NOTE
        assert "queue" in d["note"]  # the note exists precisely to say it is NOT a queue

    def test_round_trip_dict(self):
        p = self._profile(hours=[HourVolume(8, {"N": 842, "S": 790, "E": 610, "W": 655},
                                            turn_ratio={"N": {"straight": 0.7, "left": 0.15, "right": 0.15}})])
        again = TrafficProfile.from_dict(json.loads(json.dumps(p.to_dict(), ensure_ascii=False)))
        assert again == p
        assert again.hour(8).turn_ratio["N"]["left"] == pytest.approx(0.15)

    def test_from_dict_missing_meta_keys(self):
        with pytest.raises(TrafficDataError, match="필수"):
            TrafficProfile.from_dict({"meta": {"site_id": "x"}, "hours": []})

    def test_unit_other_than_veh_per_hour_rejected(self):
        with pytest.raises(TrafficDataError, match="unit"):
            self._profile(unit="veh_per_min")


# ==========================================================================
# 4. Seoul traffic-history CSV adapter (with the shipped sample)
# ==========================================================================
class TestSeoulAdapterWithSample:
    def test_sample_files_exist(self):
        assert SAMPLE_CSV.exists()
        assert SAMPLE_META.exists()

    def test_sample_header_matches_public_dataset_columns(self):
        with SAMPLE_CSV.open(encoding="utf-8-sig") as f:
            header = next(csv.reader(f))
        assert header == SEOUL_HEADER

    def test_normalizes_to_nsew_per_hour(self):
        p = load_seoul_traffic_history(SAMPLE_CSV, SITE_MAP, site_id="DEMO-X")
        assert p.available_hours() == list(range(24))
        assert p.date == "20250514" and p.weekday == "Wed"
        assert p.hour(8).volume == {"N": 842, "S": 790, "E": 610, "W": 655}
        for hv in p.hours:
            assert set(hv.volume) == set(APPROACHES)

    def test_lanes_counted_from_lane_numbers(self):
        p = load_seoul_traffic_history(SAMPLE_CSV, SITE_MAP, site_id="DEMO-X")
        assert p.lanes == {"N": 3, "S": 3, "E": 2, "W": 2}

    def test_lanes_override(self):
        p = load_seoul_traffic_history(SAMPLE_CSV, SITE_MAP, site_id="DEMO-X", lanes={"N": 1, "S": 1, "E": 1, "W": 1})
        assert p.arrival_rates(8)["N"] == pytest.approx(842 / 3600)

    def test_only_selected_flow_type_is_summed(self):
        inflow = load_seoul_traffic_history(SAMPLE_CSV, SITE_MAP, site_id="X", flow_type="유입")
        outflow = load_seoul_traffic_history(SAMPLE_CSV, SITE_MAP, site_id="X", flow_type="유출")
        assert inflow.hour(8).volume["N"] == 842
        assert outflow.hour(8).volume["N"] == round(842 * 0.85)
        # cross-check against a manual sum of the CSV
        manual = 0
        with SAMPLE_CSV.open(encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                if r["지점번호"] == "DEMO-N" and r["시간"] == "08" and r["유입유출 구분"] == "유입":
                    manual += int(r["교통량"])
        assert manual == 842

    def test_842_example_end_to_end(self):
        p = load_seoul_traffic_history(SAMPLE_CSV, SITE_MAP, site_id="DEMO-X")
        demand = p.demand_for_hour(8)
        assert demand["volume_per_hour"]["N"] == 842
        assert demand["lanes"]["N"] == 3
        assert demand["arrival_rate_per_sec"]["N"] == pytest.approx(842 / 3 / 3600, abs=1e-6)

    def test_meta_loader(self):
        p = load_profile_from_meta(SAMPLE_META)
        assert p.site_id == "DEMO-X"
        assert p.hour(8).volume["W"] == 655
        assert p.lanes["W"] == 2
        assert "15056899" in p.source

    def test_unmapped_sites_are_ignored_and_site_map_validated(self):
        with pytest.raises(TrafficDataError, match="누락"):
            load_seoul_traffic_history(SAMPLE_CSV, {"DEMO-N": "N"}, site_id="X")
        with pytest.raises(TrafficDataError, match="두 개 이상"):
            load_seoul_traffic_history(SAMPLE_CSV, {**SITE_MAP, "DEMO-Z": "N"}, site_id="X")


# ==========================================================================
# 5. Seoul adapter: error handling on hand-made files
# ==========================================================================
class TestSeoulAdapterErrors:
    def test_missing_column(self, tmp_path):
        header = [c for c in SEOUL_HEADER if c != "차로번호"]
        rows = [[s, "20250514", "08", "유입", 100] for s in SITE_MAP]
        path = _write_csv(tmp_path / "x.csv", rows, header=header)
        with pytest.raises(TrafficDataError, match="필수 컬럼.*차로번호"):
            load_seoul_traffic_history(path, SITE_MAP, site_id="X")

    def test_header_whitespace_is_tolerated(self, tmp_path):
        header = ["지점번호", "년월일", "시간", "유입유출구분", "차로번호", "교통량"]  # no space variant
        rows = [[s, "20250514", "08", "유입", 1, 100] for s in SITE_MAP]
        path = _write_csv(tmp_path / "x.csv", rows, header=header)
        p = load_seoul_traffic_history(path, SITE_MAP, site_id="X")
        assert p.hour(8).volume["N"] == 100

    def test_invalid_volume_reports_line(self, tmp_path):
        rows = _full_day_rows()
        rows[5][5] = "-7"
        path = _write_csv(tmp_path / "x.csv", rows)
        with pytest.raises(TrafficDataError, match=r"7행"):
            load_seoul_traffic_history(path, SITE_MAP, site_id="X")

    def test_invalid_hour_reports_line(self, tmp_path):
        rows = _full_day_rows()
        rows[0][2] = "24"
        path = _write_csv(tmp_path / "x.csv", rows)
        with pytest.raises(TrafficDataError, match=r"2행.*hour"):
            load_seoul_traffic_history(path, SITE_MAP, site_id="X")

    def test_invalid_lanes_override(self, tmp_path):
        path = _write_csv(tmp_path / "x.csv", _full_day_rows())
        with pytest.raises(TrafficDataError, match="차로 수"):
            load_seoul_traffic_history(path, SITE_MAP, site_id="X", lanes={"N": 0, "S": 1, "E": 1, "W": 1})

    def test_missing_approach_for_an_hour(self, tmp_path):
        rows = [r for r in _full_day_rows() if not (r[0] == "DEMO-E" and r[2] == "08")]
        path = _write_csv(tmp_path / "x.csv", rows)
        with pytest.raises(TrafficDataError, match=r"8시.*\['E'\]"):
            load_seoul_traffic_history(path, SITE_MAP, site_id="X")

    def test_duplicate_row_rejected(self, tmp_path):
        rows = _full_day_rows()
        rows.append(rows[0])
        path = _write_csv(tmp_path / "x.csv", rows)
        with pytest.raises(TrafficDataError, match="중복"):
            load_seoul_traffic_history(path, SITE_MAP, site_id="X")

    def test_multiple_dates_need_a_filter(self, tmp_path):
        rows = _full_day_rows("20250514") + _full_day_rows("20250515")
        path = _write_csv(tmp_path / "x.csv", rows)
        with pytest.raises(TrafficDataError, match="여러 날짜"):
            load_seoul_traffic_history(path, SITE_MAP, site_id="X")
        p = load_seoul_traffic_history(path, SITE_MAP, site_id="X", date_filter="2025-05-15")
        assert p.date == "20250515" and p.weekday == "Thu"

    def test_no_matching_flow_type_rows(self, tmp_path):
        path = _write_csv(tmp_path / "x.csv", _full_day_rows(flow="유출"))
        with pytest.raises(TrafficDataError, match="유입"):
            load_seoul_traffic_history(path, SITE_MAP, site_id="X", flow_type="유입")

    def test_empty_file(self, tmp_path):
        path = _write_csv(tmp_path / "x.csv", [])
        with pytest.raises(TrafficDataError, match="데이터 행"):
            load_seoul_traffic_history(path, SITE_MAP, site_id="X")

    def test_missing_file(self, tmp_path):
        with pytest.raises(TrafficDataError, match="없습니다"):
            load_seoul_traffic_history(tmp_path / "nope.csv", SITE_MAP, site_id="X")

    def test_partial_day_is_allowed(self, tmp_path):
        rows = [r for r in _full_day_rows() if r[2] in ("07", "08", "09")]
        path = _write_csv(tmp_path / "x.csv", rows)
        p = load_seoul_traffic_history(path, SITE_MAP, site_id="X")
        assert p.available_hours() == [7, 8, 9]
        with pytest.raises(TrafficDataError):
            p.hour(10)

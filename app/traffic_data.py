"""
교통량 데이터 계층 (6-1): 공공 교통량 CSV → 정규화 프로파일 → 차량 발생률.

세 가지 값을 절대 혼동하지 않는다.
- volume_per_hour      : 실제 입력 수요. 공공 데이터의 시간당 교통량(대/시).
- arrival_rate_per_sec : 시뮬레이터 차량 발생률. volume_per_hour / lanes / 3600 (차로당 대/초).
- queue                : 시뮬레이션의 "결과"인 현재 대기 차량 수. 이 모듈은 queue 를 만들지도 다루지도 않는다.
  842대/시를 queue 에 직접 넣는 방식은 이 계층 어디에도 없다.

표준 라이브러리만 사용한다 (csv, json, dataclasses, datetime).
"""
from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass, field
from datetime import date as _date
from pathlib import Path

APPROACHES = ("N", "S", "E", "W")          # 접근로: N = 북측에서 진입해 남쪽으로 향하는 차량
TURN_TYPES = ("straight", "left", "right")
SECONDS_PER_HOUR = 3600
UNIT_VEH_PER_HOUR = "veh_per_hour"
WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

DEMAND_NOTE = (
    "volume_per_hour 는 입력 수요(대/시), arrival_rate_per_sec 는 시뮬레이터 차량 발생률(차로당 대/초)이다. "
    "둘 다 현재 대기 차량 수(queue)가 아니다. queue 는 시뮬레이션이 계산한다."
)


class TrafficDataError(ValueError):
    """입력 데이터가 규격에 맞지 않을 때."""


# ---------------------------------------------------------------------------
# 검증
# ---------------------------------------------------------------------------
def validate_hour(value) -> int:
    try:
        text = str(value).strip().rstrip("시")
        hour = int(text)
    except (TypeError, ValueError):
        raise TrafficDataError(f"hour 는 0~23 정수여야 합니다: {value!r}")
    if not 0 <= hour <= 23:
        raise TrafficDataError(f"hour 범위(0~23)를 벗어났습니다: {value!r}")
    return hour


def validate_volume(value) -> int:
    """교통량(대/시). 0 이상의 정수. '12.0' 처럼 정수값인 실수 표기는 허용한다."""
    if isinstance(value, bool):
        raise TrafficDataError(f"교통량이 숫자가 아닙니다: {value!r}")
    try:
        number = float(str(value).strip().replace(",", ""))
    except (TypeError, ValueError):
        raise TrafficDataError(f"교통량이 숫자가 아닙니다: {value!r}")
    if not math.isfinite(number) or number < 0:
        raise TrafficDataError(f"교통량은 0 이상의 유한한 값이어야 합니다: {value!r}")
    if number != int(number):
        raise TrafficDataError(f"교통량은 정수(대)여야 합니다: {value!r}")
    return int(number)


def validate_lanes(value) -> int:
    if isinstance(value, bool):
        raise TrafficDataError(f"차로 수가 정수가 아닙니다: {value!r}")
    try:
        lanes = int(str(value).strip())
    except (TypeError, ValueError):
        raise TrafficDataError(f"차로 수가 정수가 아닙니다: {value!r}")
    if lanes < 1:
        raise TrafficDataError(f"차로 수는 1 이상이어야 합니다: {value!r}")
    return lanes


def _validate_approach_map(mapping, what: str, validator) -> dict:
    if not isinstance(mapping, dict):
        raise TrafficDataError(f"{what} 은(는) N/S/E/W 키를 가진 dict 여야 합니다: {mapping!r}")
    missing = [a for a in APPROACHES if a not in mapping]
    extra = [k for k in mapping if k not in APPROACHES]
    if missing:
        raise TrafficDataError(f"{what} 에 접근로가 누락되었습니다: {missing}")
    if extra:
        raise TrafficDataError(f"{what} 에 알 수 없는 접근로가 있습니다: {extra}")
    return {a: validator(mapping[a]) for a in APPROACHES}


def validate_lanes_map(lanes) -> dict:
    return _validate_approach_map(lanes, "lanes", validate_lanes)


def validate_volume_map(volume) -> dict:
    return _validate_approach_map(volume, "volume", validate_volume)


def validate_turn_ratio(turn_ratio):
    """접근로별 {straight, left, right} 비율. 각 값 0 이상, 합계 1 (오차 1e-6)."""
    if turn_ratio is None:
        return None
    if not isinstance(turn_ratio, dict):
        raise TrafficDataError(f"turn_ratio 는 dict 여야 합니다: {turn_ratio!r}")
    out = {}
    for approach, ratios in turn_ratio.items():
        if approach not in APPROACHES:
            raise TrafficDataError(f"turn_ratio 에 알 수 없는 접근로가 있습니다: {approach!r}")
        if not isinstance(ratios, dict) or set(ratios) != set(TURN_TYPES):
            raise TrafficDataError(f"turn_ratio[{approach}] 는 straight/left/right 를 모두 가져야 합니다: {ratios!r}")
        clean = {}
        for turn in TURN_TYPES:
            try:
                r = float(ratios[turn])
            except (TypeError, ValueError):
                raise TrafficDataError(f"turn_ratio[{approach}][{turn}] 이 숫자가 아닙니다: {ratios[turn]!r}")
            if not math.isfinite(r) or r < 0:
                raise TrafficDataError(f"turn_ratio[{approach}][{turn}] 은 0 이상이어야 합니다: {r!r}")
            clean[turn] = r
        if abs(sum(clean.values()) - 1.0) > 1e-6:
            raise TrafficDataError(f"turn_ratio[{approach}] 합계가 1 이 아닙니다: {clean}")
        out[approach] = clean
    return out


def validate_date(value) -> str:
    """'20250514' 또는 '2025-05-14' → 'YYYYMMDD'."""
    text = str(value).strip().replace("-", "").replace(".", "").replace("/", "")
    if len(text) != 8 or not text.isdigit():
        raise TrafficDataError(f"날짜는 YYYYMMDD 형식이어야 합니다: {value!r}")
    try:
        _date(int(text[:4]), int(text[4:6]), int(text[6:8]))
    except ValueError:
        raise TrafficDataError(f"존재하지 않는 날짜입니다: {value!r}")
    return text


def weekday_from_date(yyyymmdd: str) -> str:
    text = validate_date(yyyymmdd)
    return WEEKDAYS[_date(int(text[:4]), int(text[4:6]), int(text[6:8])).weekday()]


# ---------------------------------------------------------------------------
# 변환: 수요(대/시) → 차량 발생률(차로당 대/초)
# ---------------------------------------------------------------------------
def volume_to_arrival_rate(volume_per_hour, lanes=1) -> float:
    """시간당 교통량을 차로당 초당 도착률로 바꾼다.

    시뮬레이터는 방향당 1차로이므로 차로당 값을 넣어야 포화유출률(0.5대/초 = 1800대/시/차로)과
    스케일이 맞는다. 예: 842대/시, 3차로 → 842 / 3 / 3600 ≈ 0.078 대/초.
    """
    volume = validate_volume(volume_per_hour)
    n_lanes = validate_lanes(lanes)
    return volume / n_lanes / SECONDS_PER_HOUR


# ---------------------------------------------------------------------------
# 정규화 프로파일 구조
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class HourVolume:
    hour: int
    volume: dict                 # {"N": 842, "S": 790, "E": 610, "W": 655}  단위: 대/시 (수요)
    turn_ratio: dict | None = None

    def __post_init__(self):
        object.__setattr__(self, "hour", validate_hour(self.hour))
        object.__setattr__(self, "volume", validate_volume_map(self.volume))
        object.__setattr__(self, "turn_ratio", validate_turn_ratio(self.turn_ratio))

    def to_dict(self) -> dict:
        out = {"hour": self.hour, "volume": dict(self.volume)}
        if self.turn_ratio is not None:
            out["turn_ratio"] = {a: dict(r) for a, r in self.turn_ratio.items()}
        return out


@dataclass(frozen=True)
class TrafficProfile:
    site_id: str
    site_name: str
    date: str                    # YYYYMMDD
    source: str
    license: str
    lanes: dict                  # {"N": 3, "S": 3, "E": 2, "W": 2}
    hours: list = field(default_factory=list)   # [HourVolume, ...]
    weekday: str = ""            # 비우면 date 에서 계산
    unit: str = UNIT_VEH_PER_HOUR

    def __post_init__(self):
        if not str(self.site_id).strip():
            raise TrafficDataError("site_id 가 비어 있습니다.")
        object.__setattr__(self, "date", validate_date(self.date))
        object.__setattr__(self, "weekday", self.weekday or weekday_from_date(self.date))
        if self.weekday not in WEEKDAYS:
            raise TrafficDataError(f"weekday 값이 올바르지 않습니다: {self.weekday!r}")
        if self.unit != UNIT_VEH_PER_HOUR:
            raise TrafficDataError(f"unit 은 {UNIT_VEH_PER_HOUR!r} 만 지원합니다: {self.unit!r}")
        object.__setattr__(self, "lanes", validate_lanes_map(self.lanes))
        hours = [h if isinstance(h, HourVolume) else HourVolume(**h) for h in self.hours]
        if not hours:
            raise TrafficDataError("hours 가 비어 있습니다.")
        seen = set()
        for h in hours:
            if h.hour in seen:
                raise TrafficDataError(f"hour 가 중복되었습니다: {h.hour}")
            seen.add(h.hour)
        object.__setattr__(self, "hours", sorted(hours, key=lambda h: h.hour))

    # -- 조회 --
    def available_hours(self) -> list:
        return [h.hour for h in self.hours]

    def hour(self, hour) -> HourVolume:
        h = validate_hour(hour)
        for hv in self.hours:
            if hv.hour == h:
                return hv
        raise TrafficDataError(f"프로파일에 {h}시 데이터가 없습니다. 보유: {self.available_hours()}")

    def arrival_rates(self, hour) -> dict:
        """접근로별 시뮬레이터 차량 발생률(차로당 대/초)."""
        hv = self.hour(hour)
        return {a: volume_to_arrival_rate(hv.volume[a], self.lanes[a]) for a in APPROACHES}

    def demand_for_hour(self, hour) -> dict:
        """AI 입력의 demand 블록. 수요와 발생률만 담고 queue 는 담지 않는다."""
        hv = self.hour(hour)
        return {
            "site_id": self.site_id,
            "hour": hv.hour,
            "unit": self.unit,
            "volume_per_hour": dict(hv.volume),
            "lanes": dict(self.lanes),
            "arrival_rate_per_sec": {a: round(r, 6) for a, r in self.arrival_rates(hv.hour).items()},
            "note": DEMAND_NOTE,
        }

    # -- 직렬화 --
    def to_dict(self) -> dict:
        return {
            "meta": {
                "site_id": self.site_id,
                "site_name": self.site_name,
                "date": self.date,
                "weekday": self.weekday,
                "source": self.source,
                "license": self.license,
                "unit": self.unit,
                "lanes": dict(self.lanes),
            },
            "hours": [h.to_dict() for h in self.hours],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TrafficProfile":
        if not isinstance(data, dict) or "meta" not in data or "hours" not in data:
            raise TrafficDataError("프로파일 dict 는 meta 와 hours 를 가져야 합니다.")
        meta = data["meta"]
        required = ("site_id", "date", "source", "license", "lanes")
        missing = [k for k in required if k not in meta]
        if missing:
            raise TrafficDataError(f"meta 에 필수 항목이 없습니다: {missing}")
        return cls(
            site_id=meta["site_id"],
            site_name=meta.get("site_name", ""),
            date=meta["date"],
            weekday=meta.get("weekday", ""),
            source=meta["source"],
            license=meta["license"],
            unit=meta.get("unit", UNIT_VEH_PER_HOUR),
            lanes=meta["lanes"],
            hours=[HourVolume(**h) for h in data["hours"]],
        )


# ---------------------------------------------------------------------------
# 어댑터: 서울특별시 교통량 이력 정보 (공공데이터포털 15056899) 컬럼 구조
# ---------------------------------------------------------------------------
# 원본 컬럼(공백 제거 후) → 정규화 이름
SEOUL_HISTORY_COLUMNS = {
    "지점번호": "site_id",
    "년월일": "date",
    "시간": "hour",
    "유입유출구분": "flow_type",
    "차로번호": "lane_no",
    "교통량": "volume",
}
SEOUL_HISTORY_SOURCE = "서울특별시_교통량 이력 정보 (공공데이터포털 15056899, 원천: TOPIS)"
SEOUL_HISTORY_LICENSE = "이용허락범위 제한 없음 (공공데이터포털 표기 기준)"


def _normalize_header(name: str) -> str:
    return str(name).replace("﻿", "").replace(" ", "").strip()


def load_seoul_traffic_history(
    csv_path,
    site_to_approach: dict,
    site_id: str,
    site_name: str = "",
    lanes: dict | None = None,
    flow_type: str = "유입",
    date_filter=None,
    encoding: str = "utf-8-sig",
    source: str = SEOUL_HISTORY_SOURCE,
    license: str = SEOUL_HISTORY_LICENSE,
) -> TrafficProfile:
    """서울시 교통량 이력 정보 형식 CSV 를 읽어 한 교차로의 TrafficProfile 로 정규화한다.

    - 이 데이터의 '지점'은 도로 단면이므로, 교차로 접근로 4개 = 지점 4개를 site_to_approach 로 매핑한다.
    - flow_type 과 같은 행만 사용한다 (기본 '유입'). 원본의 유입/유출은 데이터 제공자 기준이므로
      어느 값을 접근 교통으로 볼지는 호출자가 정한다.
    - 차로별 교통량은 접근로 합계로 더하고, 차로 수는 lanes 를 주지 않으면 차로번호의 종류 수로 센다.
    - 여러 날짜가 섞여 있으면 date_filter 로 하루를 골라야 한다.
    """
    approach_of = _validate_site_map(site_to_approach)
    path = Path(csv_path)
    if not path.exists():
        raise TrafficDataError(f"CSV 파일이 없습니다: {path}")

    with path.open("r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise TrafficDataError("CSV 헤더를 읽을 수 없습니다 (빈 파일).")
        header_map = {}
        for raw in reader.fieldnames:
            norm = _normalize_header(raw)
            if norm in SEOUL_HISTORY_COLUMNS:
                header_map[SEOUL_HISTORY_COLUMNS[norm]] = raw
        missing = [k for k in SEOUL_HISTORY_COLUMNS if SEOUL_HISTORY_COLUMNS[k] not in header_map]
        if missing:
            raise TrafficDataError(f"CSV 에 필수 컬럼이 없습니다: {missing} (헤더: {reader.fieldnames})")

        wanted_date = validate_date(date_filter) if date_filter is not None else None
        # (approach, hour) -> 합계 ; approach -> {lane_no}
        totals: dict = {}
        lane_ids: dict = {a: set() for a in APPROACHES}
        seen_rows = set()
        dates_seen = set()
        row_count = 0
        for line_no, row in enumerate(reader, start=2):
            row_count += 1
            site = str(row[header_map["site_id"]]).strip()
            if site not in approach_of:
                continue                                    # 다른 지점은 무시
            if str(row[header_map["flow_type"]]).strip() != flow_type:
                continue
            row_date = validate_date(row[header_map["date"]])
            dates_seen.add(row_date)
            if wanted_date is not None and row_date != wanted_date:
                continue
            approach = approach_of[site]
            try:
                hour = validate_hour(row[header_map["hour"]])
                volume = validate_volume(row[header_map["volume"]])
            except TrafficDataError as e:
                raise TrafficDataError(f"{path.name} {line_no}행: {e}") from e
            lane_no = str(row[header_map["lane_no"]]).strip()
            key = (site, row_date, hour, lane_no)
            if key in seen_rows:
                raise TrafficDataError(f"{path.name} {line_no}행: 중복 행입니다 (지점 {site}, {row_date} {hour}시, 차로 {lane_no})")
            seen_rows.add(key)
            lane_ids[approach].add(lane_no)
            totals[(approach, hour)] = totals.get((approach, hour), 0) + volume

    if row_count == 0:
        raise TrafficDataError("CSV 에 데이터 행이 없습니다.")
    if wanted_date is None:
        if len(dates_seen) > 1:
            raise TrafficDataError(f"여러 날짜가 섞여 있습니다. date_filter 로 하루를 지정하세요: {sorted(dates_seen)}")
        if not dates_seen:
            raise TrafficDataError(f"site_to_approach 에 해당하는 '{flow_type}' 행이 없습니다.")
        wanted_date = next(iter(dates_seen))

    hours_present = sorted({h for (_, h) in totals})
    if not hours_present:
        raise TrafficDataError(f"{wanted_date} 에 해당하는 데이터가 없습니다.")
    hour_volumes = []
    for h in hours_present:
        missing_appr = [a for a in APPROACHES if (a, h) not in totals]
        if missing_appr:
            raise TrafficDataError(f"{h}시에 접근로 데이터가 누락되었습니다: {missing_appr}")
        hour_volumes.append(HourVolume(hour=h, volume={a: totals[(a, h)] for a in APPROACHES}))

    if lanes is None:
        empty = [a for a in APPROACHES if not lane_ids[a]]
        if empty:
            raise TrafficDataError(f"차로 수를 셀 수 없습니다 (행 없음): {empty}")
        lanes = {a: len(lane_ids[a]) for a in APPROACHES}

    return TrafficProfile(
        site_id=site_id,
        site_name=site_name,
        date=wanted_date,
        source=source,
        license=license,
        lanes=lanes,
        hours=hour_volumes,
    )


def _validate_site_map(site_to_approach) -> dict:
    if not isinstance(site_to_approach, dict) or not site_to_approach:
        raise TrafficDataError("site_to_approach 는 {지점번호: 접근로} dict 여야 합니다.")
    inverse = {}
    for site, approach in site_to_approach.items():
        if approach not in APPROACHES:
            raise TrafficDataError(f"site_to_approach 의 접근로가 올바르지 않습니다: {site!r} -> {approach!r}")
        if approach in inverse:
            raise TrafficDataError(f"접근로 {approach} 에 지점이 두 개 이상 매핑되었습니다: {inverse[approach]!r}, {site!r}")
        inverse[approach] = str(site).strip()
    missing = [a for a in APPROACHES if a not in inverse]
    if missing:
        raise TrafficDataError(f"site_to_approach 에 접근로가 누락되었습니다: {missing}")
    return {str(site).strip(): approach for site, approach in site_to_approach.items()}


# ---------------------------------------------------------------------------
# 메타 파일(JSON)로 한 번에 읽기: data/*.meta.json
# ---------------------------------------------------------------------------
def load_profile_from_meta(meta_path) -> TrafficProfile:
    """data/<name>.meta.json 에 적힌 CSV 경로·매핑·출처로 프로파일을 만든다."""
    path = Path(meta_path)
    if not path.exists():
        raise TrafficDataError(f"메타 파일이 없습니다: {path}")
    with path.open("r", encoding="utf-8") as f:
        meta = json.load(f)
    required = ("csv", "site_id", "site_to_approach")
    missing = [k for k in required if k not in meta]
    if missing:
        raise TrafficDataError(f"메타 파일에 필수 항목이 없습니다: {missing}")
    csv_path = (path.parent / meta["csv"]).resolve()
    kwargs = {
        "site_to_approach": meta["site_to_approach"],
        "site_id": meta["site_id"],
        "site_name": meta.get("site_name", ""),
        "lanes": meta.get("lanes"),
        "flow_type": meta.get("flow_type", "유입"),
        "date_filter": meta.get("date"),
        "encoding": meta.get("encoding", "utf-8-sig"),
    }
    if meta.get("source"):
        kwargs["source"] = meta["source"]
    if meta.get("license"):
        kwargs["license"] = meta["license"]
    return load_seoul_traffic_history(csv_path, **kwargs)

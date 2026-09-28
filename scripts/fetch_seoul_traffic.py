"""
서울 열린데이터광장의 교통량 API 로 실측 교통량을 받아 data/ 에 넣을 CSV 와 메타 파일을 만든다.

공공데이터포털 "서울특별시_교통량 이력 정보"(15056899)는 열린데이터광장 API 로 연결되어 있고,
서비스 이름은 VolInfo(교통량 이력)와 SpotInfo(지점 정보)다. 인증키는 data.seoul.go.kr 에서 받는다.

    # 1) 지점 목록 보기 (좌표 기준으로 가까운 지점을 찾을 때 --near 를 준다)
    python scripts/fetch_seoul_traffic.py spots --grep 강남
    python scripts/fetch_seoul_traffic.py spots --near 203000 445000 --k 12

    # 2) 접근로 4개에 지점을 붙여 하루치를 받는다 (지점 4개 × 24시간 = 96번 호출)
    python scripts/fetch_seoul_traffic.py fetch --date 20240515 \
        --spot N=A-01 --spot S=A-02 --spot E=B-01 --spot W=B-02 \
        --name "서울 ○○ 교차로 (실측)" --out data/seoul_xx_20240515.csv

인증키는 환경 변수 SEOUL_OPENAPI_KEY 로만 읽는다 (.env 도 읽는다). 저장소에 키를 넣지 않는다.
받은 CSV 는 app/traffic_data.py 가 읽는 형식(지점번호, 년월일, 시간, 유입유출 구분, 차로번호, 교통량)이라
로더나 API 를 고칠 필요가 없다. 다 받은 뒤 같은 로더로 읽어 08시 표를 출력해 확인한다.
"""
import argparse
import csv
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BASE_URL = "http://openapi.seoul.go.kr:8088"
KEY_ENV = "SEOUL_OPENAPI_KEY"
PAGE = 1000                     # 열린데이터광장의 한 번 호출 최대 건수
IO_TYPE_LABEL = {"1": "유입", "2": "유출"}   # VolInfo 의 io_type 코드 → 로더가 쓰는 글자
HEADER = ["지점번호", "년월일", "시간", "유입유출 구분", "차로번호", "교통량"]
APPROACHES = ("N", "S", "E", "W")


class SeoulApiError(RuntimeError):
    pass


def api_key() -> str:
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    key = os.getenv(KEY_ENV)
    if not key:
        raise SeoulApiError(f"환경 변수 {KEY_ENV} 가 없습니다. data.seoul.go.kr 에서 인증키를 받아 .env 에 {KEY_ENV}=... 로 넣으세요.")
    return key


def parse_rows(xml_text: str, service: str) -> tuple:
    """(전체 건수, [row dict]) 를 돌려준다. 오류 응답이면 SeoulApiError."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise SeoulApiError(f"응답을 XML 로 읽을 수 없습니다: {e}: {xml_text[:200]}") from e
    result = root.find("RESULT")
    code = result.findtext("CODE") if result is not None else None
    if root.tag != service:
        raise SeoulApiError(f"{service} 오류 {code}: {result.findtext('MESSAGE') if result is not None else xml_text[:200]}")
    if code and code != "INFO-000":
        raise SeoulApiError(f"{service} 오류 {code}: {result.findtext('MESSAGE')}")
    total = int(root.findtext("list_total_count") or 0)
    rows = [{child.tag: (child.text or "").strip() for child in row} for row in root.findall("row")]
    return total, rows


def http_get(url: str, retries: int = 3, pause: float = 0.3) -> str:
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                text = resp.read().decode("utf-8")
            # 서버 오류(ERROR-500)는 잠시 뒤 다시 시도한다.
            if "ERROR-500" in text and attempt < retries - 1:
                time.sleep(pause * (attempt + 2))
                continue
            time.sleep(pause)
            return text
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            time.sleep(pause * (attempt + 2))
    raise SeoulApiError(f"요청 실패: {url.split('/xml/')[-1]}: {last}")


def fetch_all(service: str, key: str, extra: str = "", getter=http_get) -> list:
    """list_total_count 만큼 페이지를 넘기며 모두 받는다."""
    start, rows = 1, []
    while True:
        url = f"{BASE_URL}/{key}/xml/{service}/{start}/{start + PAGE - 1}/{extra}"
        total, part = parse_rows(getter(url), service)
        rows.extend(part)
        if not part or len(rows) >= total:
            return rows
        start += PAGE


# ---------------------------------------------------------------------------
# spots: 지점 목록
# ---------------------------------------------------------------------------
def cmd_spots(args, getter=http_get) -> list:
    rows = fetch_all("SpotInfo", api_key(), getter=getter)
    spots = []
    for r in rows:
        try:
            x, y = float(r.get("grs80tm_x") or "nan"), float(r.get("grs80tm_y") or "nan")
        except ValueError:
            x = y = float("nan")
        spots.append({"spot_num": r.get("spot_num", ""), "spot_nm": r.get("spot_nm", ""), "x": x, "y": y})
    if args.grep:
        spots = [s for s in spots if args.grep in s["spot_nm"] or args.grep in s["spot_num"]]
    if args.near:
        cx, cy = args.near
        for s in spots:
            s["dist_m"] = math.hypot(s["x"] - cx, s["y"] - cy) if not math.isnan(s["x"]) else float("inf")
        spots.sort(key=lambda s: s["dist_m"])
        spots = spots[: args.k]
    for s in spots:
        d = f"  {s['dist_m']:8.0f} m" if "dist_m" in s else ""
        print(f"{s['spot_num']:8s} {s['spot_nm']:30s} x={s['x']:.0f} y={s['y']:.0f}{d}")
    print(f"{len(spots)} 지점")
    if args.out:
        with open(args.out, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["spot_num", "spot_nm", "x", "y"], extrasaction="ignore")
            w.writeheader()
            w.writerows(spots)
        print("wrote", args.out)
    return spots


# ---------------------------------------------------------------------------
# fetch: 접근로 4개 × 24시간
# ---------------------------------------------------------------------------
def parse_spot_args(items) -> dict:
    """['N=A-01', 'S=A-02', ...] → {'A-01': 'N', ...}"""
    mapping = {}
    for item in items or []:
        if "=" not in item:
            raise SystemExit(f"--spot 은 접근로=지점번호 꼴이어야 합니다: {item!r}")
        approach, spot = item.split("=", 1)
        approach, spot = approach.strip().upper(), spot.strip()
        if approach not in APPROACHES:
            raise SystemExit(f"접근로는 N/S/E/W 중 하나여야 합니다: {approach!r}")
        mapping[spot] = approach
    missing = [a for a in APPROACHES if a not in mapping.values()]
    if missing:
        raise SystemExit(f"접근로가 빠졌습니다: {missing} (--spot N=... S=... E=... W=...)")
    return mapping


def fetch_day(key: str, spots: list, date: str, hours=range(24), getter=http_get, log=print) -> list:
    """지점별·시간별 VolInfo 를 받아 로더 형식의 행 목록으로 돌려준다."""
    out = []
    for spot in spots:
        got_hours = 0
        for h in hours:
            hh = f"{h:02d}"
            rows = fetch_all("VolInfo", key, extra=f"{spot}/{date}/{hh}/", getter=getter)
            if rows:
                got_hours += 1
            for r in rows:
                label = IO_TYPE_LABEL.get(r.get("io_type", ""), r.get("io_type", ""))
                out.append([r.get("spot_num", spot), r.get("ymd", date), r.get("hh", hh), label, r.get("lane_num", ""), r.get("vol", "")])
        log(f"{spot}: {got_hours}/{len(hours)} 시간대 수신")
    return out


def spot_names(key: str, spots: list, getter=http_get) -> dict:
    """SpotInfo 에서 지점번호 → 지점명. 못 찾은 지점은 번호를 그대로 쓴다."""
    try:
        rows = fetch_all("SpotInfo", key, getter=getter)
    except SeoulApiError:
        rows = []
    names = {r.get("spot_num", ""): r.get("spot_nm", "") for r in rows}
    return {s: (names.get(s) or s) for s in spots}


def write_outputs(rows: list, mapping: dict, args, names: dict | None = None) -> Path:
    out_csv = Path(args.out)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(rows)
    meta_path = out_csv.with_name(out_csv.name[: -len(".csv")] + ".meta.json") if out_csv.name.endswith(".csv") else out_csv.with_suffix(".meta.json")
    site_id = args.site_id or "-".join(sorted(mapping))
    meta = {
        "csv": out_csv.name,
        "encoding": "utf-8-sig",
        "format": "seoul_traffic_history",
        "site_id": site_id,
        "site_name": args.name,
        "date": args.date,
        "flow_type": "유입",
        "site_to_approach": mapping,
        "lanes": None,
        # 화면의 표와 도로 끝 이름표에 쓰는 도로 이름 (지점명). 원하면 손으로 고쳐도 된다.
        "approach_names": {approach: (names or {}).get(spot, spot) for spot, approach in mapping.items()},
        "source": (
            "서울특별시_교통량 이력 정보 (공공데이터포털 15056899 → 서울 열린데이터광장 VolInfo, 원천 TOPIS). "
            f"{args.date} 하루치를 scripts/fetch_seoul_traffic.py 로 받음. io_type 1→유입, 2→유출로 표기"
        ),
        "license": "공공데이터포털 표기상 이용허락범위 제한 없음. 출처: 서울특별시(TOPIS)",
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return meta_path


def verify(meta_path: Path, log=print):
    from app.traffic_data import load_profile_from_meta

    profile = load_profile_from_meta(meta_path)
    log(f"프로파일 확인: {profile.site_name} {profile.date} 시간대 {len(profile.hours)}개 차로 {profile.lanes}")
    hour = 8 if 8 in profile.available_hours() else profile.available_hours()[0]
    hv = profile.hour(hour)
    rates = profile.arrival_rates(hour)
    log(f"{hour:02d}시  접근로  수요(대/시)  차로  발생률(차로당 대/초)")
    for a in APPROACHES:
        log(f"      {a}      {hv.volume[a]:6d}     {profile.lanes[a]}    {rates[a]:.6f}")
    return profile


def cmd_fetch(args, getter=http_get):
    mapping = parse_spot_args(args.spot)
    key = api_key()
    rows = fetch_day(key, list(mapping), args.date, getter=getter)
    if not rows:
        raise SeoulApiError("받은 행이 없습니다. 지점번호와 날짜를 확인하세요.")
    meta_path = write_outputs(rows, mapping, args, names=spot_names(key, list(mapping), getter=getter))
    print(f"wrote {args.out} ({len(rows)} 행), {meta_path.name}")
    verify(meta_path)
    print("다음: python scripts/build_profile_data.py 로 내장 데이터를 다시 만들고, python -m pytest -q 를 돌린다.")


def build_parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("spots", help="지점 목록 (SpotInfo)")
    s.add_argument("--grep", help="지점명/지점번호에 이 글자가 든 것만")
    s.add_argument("--near", nargs=2, type=float, metavar=("X", "Y"), help="GRS80 TM 좌표에서 가까운 순으로")
    s.add_argument("--k", type=int, default=10, help="--near 와 함께: 몇 개까지")
    s.add_argument("--out", help="목록을 CSV 로 저장할 경로")
    f = sub.add_parser("fetch", help="하루치 교통량 (VolInfo)")
    f.add_argument("--date", required=True, help="YYYYMMDD")
    f.add_argument("--spot", action="append", required=True, help="접근로=지점번호 (N/S/E/W 네 번)")
    f.add_argument("--name", required=True, help="메타의 site_name (화면에 표시)")
    f.add_argument("--site-id", help="메타의 site_id (기본: 지점번호를 이어 붙임)")
    f.add_argument("--out", required=True, help="저장할 CSV 경로 (data/ 아래, 메타는 같은 이름 .meta.json)")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "spots":
            cmd_spots(args)
        else:
            cmd_fetch(args)
    except SeoulApiError as e:
        print("오류:", e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

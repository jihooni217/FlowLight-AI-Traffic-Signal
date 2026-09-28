"""
app/profile_data.js 를 만든다: 백엔드 GET /api/traffic/profiles 와 GET /api/traffic/profile?profile=<id> 응답을 파일로 담아 둔다.

서버 없이 여는 공개 데모(GitHub Pages)나 서버가 꺼진 상태에서도 실데이터 프로파일 모드를 쓸 수 있게 하기 위한 것이다.
data/ 의 CSV 나 메타 파일을 바꾸거나 프로파일을 추가하면 이 스크립트를 다시 돌린다.
tests/test_hosted_demo.py 가 백엔드 응답과 같은지 검사한다.

    python scripts/build_profile_data.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.main import (  # noqa: E402
    DEFAULT_TRAFFIC_PROFILE_META,
    get_traffic_profile,
    list_traffic_profiles,
    profile_id_of,
    profile_to_payload,
    resolve_profile_meta,
)

OUT = ROOT / "app" / "profile_data.js"


def build_payload(meta_path=DEFAULT_TRAFFIC_PROFILE_META) -> dict:
    meta = Path(meta_path)
    profile = get_traffic_profile(str(meta))
    return profile_to_payload(profile, profile.hours, meta.name)


def build_all() -> tuple:
    """(기본 프로파일 payload, 목록, {id: payload})"""
    listing = list_traffic_profiles()
    data = {}
    for entry in listing["profiles"]:
        data[entry["id"]] = build_payload(resolve_profile_meta(entry["id"]))
    default_payload = data[profile_id_of(DEFAULT_TRAFFIC_PROFILE_META)]
    return default_payload, listing, data


def main():
    default_payload, listing, data = build_all()
    text = (
        "// FlowLight 내장 교통 수요 프로파일 (scripts/build_profile_data.py 로 생성)\n"
        "// 서버 없이 열었을 때 실데이터 프로파일 모드가 이 데이터를 쓴다.\n"
        "// FLOWLIGHT_PROFILE = 기본 프로파일 (GET /api/traffic/profile 과 같음)\n"
        "// FLOWLIGHT_PROFILE_LIST = GET /api/traffic/profiles, FLOWLIGHT_PROFILE_DATA[id] = GET /api/traffic/profile?profile=id\n"
        "window.FLOWLIGHT_PROFILE = " + json.dumps(default_payload, ensure_ascii=False, indent=1) + ";\n"
        "window.FLOWLIGHT_PROFILE_LIST = " + json.dumps(listing, ensure_ascii=False, indent=1) + ";\n"
        "window.FLOWLIGHT_PROFILE_DATA = " + json.dumps(data, ensure_ascii=False, indent=1) + ";\n"
    )
    OUT.write_text(text, encoding="utf-8")
    print("wrote", OUT, len(text) // 1024, "KB", "profiles", [e["id"] for e in listing["profiles"]])


if __name__ == "__main__":
    main()

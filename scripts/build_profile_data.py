"""
app/profile_data.js 를 만든다: 백엔드 GET /api/traffic/profile 과 같은 응답을 파일로 담아 둔다.

서버 없이 여는 공개 데모(GitHub Pages)나 서버가 꺼진 상태에서도 실데이터 프로파일 모드를 쓸 수 있게 하기 위한 것이다.
샘플 CSV 나 메타 파일을 바꾸면 이 스크립트를 다시 돌린다. tests/test_hosted_demo.py 가 백엔드 응답과 같은지 검사한다.

    python scripts/build_profile_data.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.main import DEFAULT_TRAFFIC_PROFILE_META, get_traffic_profile, profile_to_payload  # noqa: E402

OUT = ROOT / "app" / "profile_data.js"


def build_payload() -> dict:
    meta = DEFAULT_TRAFFIC_PROFILE_META
    profile = get_traffic_profile(str(meta))
    return profile_to_payload(profile, profile.hours, meta.name)


def main():
    payload = build_payload()
    text = (
        "// FlowLight 내장 교통 수요 프로파일: GET /api/traffic/profile 과 같은 내용 (scripts/build_profile_data.py 로 생성)\n"
        "// 서버 없이 열었을 때 실데이터 프로파일 모드가 이 데이터를 쓴다.\n"
        "window.FLOWLIGHT_PROFILE = " + json.dumps(payload, ensure_ascii=False, indent=1) + ";\n"
    )
    OUT.write_text(text, encoding="utf-8")
    print("wrote", OUT, len(text) // 1024, "KB", "hours", len(payload["hours"]))


if __name__ == "__main__":
    main()

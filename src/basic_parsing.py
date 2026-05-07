"""기본 JSON 파싱: 표준 라이브러리 json 모듈 사용"""
import json
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "sample.json"


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def parse_users(data: dict) -> list[dict]:
    return data.get("users", [])


def serialize_to_json(obj: dict | list, indent: int = 2) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=indent)


def main():
    raw = load_json(DATA_FILE)
    print("=== 전체 데이터 ===")
    print(serialize_to_json(raw))

    users = parse_users(raw)
    print(f"\n=== 사용자 수: {len(users)} ===")
    for user in users:
        print(f"  [{user['id']}] {user['name']} / {user['email']} / {user['address']['city']}")

    print("\n=== 직렬화 (JSON 문자열 변환) ===")
    first_user_json = serialize_to_json(users[0])
    print(first_user_json)

    print("\n=== 역직렬화 (문자열 → 객체) ===")
    parsed_back = json.loads(first_user_json)
    print(type(parsed_back), parsed_back["name"])


if __name__ == "__main__":
    main()

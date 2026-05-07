"""orjson 기반 JSON CRUD 앱 — PoC(orjson_saving.py) 코드 구조 유지"""
import json
import sys
from pathlib import Path
import orjson

DB_FILE = Path(__file__).parent.parent / "data" / "db.json"


# ── I/O helpers (PoC 코드 구조 유지) ─────────────────────────────────────

def _load(path: Path = DB_FILE) -> dict:
    if not path.exists() or path.stat().st_size == 0:
        return {"users": [], "meta": {"total": 0}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):  # 구버전 포맷 자동 마이그레이션
        data = {"users": data, "meta": {"total": len(data)}}
    return data


def _save(data: dict, path: Path = DB_FILE):
    """orjson으로 저장 — PoC save_with_orjson 동일 방식"""
    option = orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS
    path.write_bytes(orjson.dumps(data, option=option))


def _next_id(users: list[dict]) -> int:
    return max((u["id"] for u in users), default=0) + 1


# ── CRUD ─────────────────────────────────────────────────────────────────

def create(name: str, email: str, age: int, city: str, zip_code: str, tags: list[str]) -> dict:
    data = _load()
    user = {
        "id": _next_id(data["users"]),
        "name": name,
        "email": email,
        "age": age,
        "address": {"city": city, "zip": zip_code},
        "tags": tags,
    }
    data["users"].append(user)
    data["meta"]["total"] = len(data["users"])
    _save(data)
    return user


def read_all() -> list[dict]:
    return _load()["users"]


def read_by_id(user_id: int) -> dict | None:
    return next((u for u in read_all() if u["id"] == user_id), None)


def search_by_field(key: str, value: str) -> list[dict]:
    result = []
    for u in read_all():
        field_val = u.get(key)
        if field_val is None:
            continue
        if isinstance(field_val, str) and value.lower() in field_val.lower():
            result.append(u)
        elif str(field_val) == value:
            result.append(u)
    return result


def update(user_id: int, fields: dict) -> dict | None:
    """fields 키에 점 표기법 지원 (예: address.city)"""
    data = _load()
    for user in data["users"]:
        if user["id"] != user_id:
            continue
        for key, val in fields.items():
            if "." in key:
                outer, inner = key.split(".", 1)
                if outer in user and isinstance(user[outer], dict):
                    user[outer][inner] = val
            else:
                user[key] = val
        _save(data)
        return user
    return None


def delete(user_id: int) -> bool:
    data = _load()
    before = len(data["users"])
    data["users"] = [u for u in data["users"] if u["id"] != user_id]
    if len(data["users"]) == before:
        return False
    data["meta"]["total"] = len(data["users"])
    _save(data)
    return True


# ── CLI helpers ───────────────────────────────────────────────────────────

def _print_user(user: dict):
    tags = ", ".join(user.get("tags", []))
    addr = user.get("address", {})
    print(f"  [{user['id']}] {user['name']} | {user['email']} | 나이: {user['age']}")
    print(f"       주소: {addr.get('city', '-')} ({addr.get('zip', '-')})  태그: {tags or '-'}")


def _prompt(msg: str) -> str:
    return input(msg).strip()


def _cmd_list():
    users = read_all()
    if not users:
        print("  (데이터 없음)")
        return
    for u in users:
        _print_user(u)


def _cmd_read():
    uid = _prompt("  조회할 ID: ")
    if not uid.isdigit():
        print("  숫자를 입력하세요.")
        return
    user = read_by_id(int(uid))
    if user:
        _print_user(user)
    else:
        print(f"  ID {uid} 를 찾을 수 없습니다.")


def _cmd_search():
    print("  검색 가능 필드: name, email, age, tags")
    key = _prompt("  필드명: ")
    val = _prompt("  검색어: ")
    results = search_by_field(key, val)
    if results:
        for u in results:
            _print_user(u)
    else:
        print("  검색 결과 없음")


def _cmd_create():
    print("  --- 새 사용자 추가 ---")
    name = _prompt("  이름: ")
    email = _prompt("  이메일: ")
    age_str = _prompt("  나이: ")
    if not age_str.isdigit():
        print("  나이는 숫자여야 합니다.")
        return
    city = _prompt("  도시: ")
    zip_code = _prompt("  우편번호: ")
    tags_raw = _prompt("  태그 (쉼표 구분, 없으면 빈칸): ")
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    user = create(name, email, int(age_str), city, zip_code, tags)
    print(f"  추가 완료 → ID: {user['id']}")


def _cmd_update():
    uid = _prompt("  수정할 ID: ")
    if not uid.isdigit():
        print("  숫자를 입력하세요.")
        return
    user = read_by_id(int(uid))
    if not user:
        print(f"  ID {uid} 를 찾을 수 없습니다.")
        return
    _print_user(user)
    print("  수정할 필드를 입력하세요 (예: name / age / address.city / email)")
    print("  완료하려면 빈칸 입력")
    fields: dict = {}
    while True:
        key = _prompt("  필드: ")
        if not key:
            break
        val = _prompt(f"  새 값 ({key}): ")
        if key == "age":
            if not val.isdigit():
                print("  나이는 숫자여야 합니다.")
                continue
            fields[key] = int(val)
        else:
            fields[key] = val
    if not fields:
        print("  변경 사항 없음")
        return
    updated = update(int(uid), fields)
    if updated:
        print("  수정 완료 →")
        _print_user(updated)


def _cmd_delete():
    uid = _prompt("  삭제할 ID: ")
    if not uid.isdigit():
        print("  숫자를 입력하세요.")
        return
    user = read_by_id(int(uid))
    if not user:
        print(f"  ID {uid} 를 찾을 수 없습니다.")
        return
    _print_user(user)
    confirm = _prompt("  정말 삭제하시겠습니까? (y/N): ")
    if confirm.lower() == "y":
        delete(int(uid))
        print(f"  ID {uid} 삭제 완료")
    else:
        print("  삭제 취소")


MENU = {
    "1": ("전체 목록 보기", _cmd_list),
    "2": ("ID로 조회",      _cmd_read),
    "3": ("필드로 검색",    _cmd_search),
    "4": ("새 사용자 추가", _cmd_create),
    "5": ("사용자 수정",    _cmd_update),
    "6": ("사용자 삭제",    _cmd_delete),
}


def main():
    print(f"=== JSON CRUD 앱 (저장소: {DB_FILE}) ===")
    while True:
        print("\n" + "─" * 40)
        for key, (label, _) in MENU.items():
            print(f"  {key}. {label}")
        print("  0. 종료")
        choice = _prompt("선택: ")
        if choice == "0":
            print("종료합니다.")
            sys.exit(0)
        if choice in MENU:
            print()
            MENU[choice][1]()
        else:
            print("  잘못된 입력입니다.")


if __name__ == "__main__":
    main()

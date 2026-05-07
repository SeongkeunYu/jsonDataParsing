"""스키마 검증 파싱: pydantic v2 사용 (pip install pydantic)"""
import json
from pathlib import Path
from pydantic import BaseModel, EmailStr, field_validator

DATA_FILE = Path(__file__).parent.parent / "data" / "sample.json"


class Address(BaseModel):
    city: str
    zip: str


class User(BaseModel):
    id: int
    name: str
    email: str
    age: int
    address: Address
    tags: list[str]

    @field_validator("age")
    @classmethod
    def age_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("age는 양수여야 합니다.")
        return v


class UserList(BaseModel):
    users: list[User]
    meta: dict


def main():
    raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    data = UserList(**raw)

    print("=== pydantic 모델로 파싱된 사용자 ===")
    for user in data.users:
        print(f"  [{user.id}] {user.name} ({user.age}세) — {user.address.city}")
        print(f"       태그: {user.tags}")

    print("\n=== 모델 → dict 변환 ===")
    print(data.users[0].model_dump())

    print("\n=== 모델 → JSON 직렬화 ===")
    print(data.users[0].model_dump_json(indent=2))

    print("\n=== 잘못된 데이터 검증 테스트 ===")
    try:
        bad_user = User(
            id=99, name="테스트", email="bad-email",
            age=-1, address={"city": "대전", "zip": "00000"}, tags=[]
        )
    except Exception as e:
        print(f"  검증 오류 발생: {e}")


if __name__ == "__main__":
    main()

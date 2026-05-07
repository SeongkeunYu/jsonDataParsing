"""파싱 성능 벤치마크: json vs orjson vs pydantic"""
import json
import time
from pathlib import Path
from pydantic import BaseModel
import orjson

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


class UserList(BaseModel):
    users: list[User]
    meta: dict


def benchmark(iterations: int = 10000):
    raw_bytes = DATA_FILE.read_bytes()
    raw_str = raw_bytes.decode("utf-8")

    print(f"=== 파싱 성능 벤치마크 ({iterations}회 반복) ===")

    start = time.perf_counter()
    for _ in range(iterations):
        json.loads(raw_str)
    json_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(iterations):
        orjson.loads(raw_bytes)
    orjson_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(iterations):
        UserList(**json.loads(raw_str))
    pydantic_elapsed = time.perf_counter() - start

    print(f"  json    : {json_elapsed:.4f}s")
    print(f"  orjson  : {orjson_elapsed:.4f}s  ({json_elapsed / orjson_elapsed:.1f}x 빠름)")
    print(f"  pydantic: {pydantic_elapsed:.4f}s  ({json_elapsed / pydantic_elapsed:.1f}x {'빠름' if pydantic_elapsed < json_elapsed else '느림'})")


if __name__ == "__main__":
    benchmark()

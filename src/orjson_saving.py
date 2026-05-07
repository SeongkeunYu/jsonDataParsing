"""고성능 JSON 저장: orjson 사용 (pip install orjson)"""
import json
import time
from pathlib import Path
import orjson

DATA_FILE = Path(__file__).parent.parent / "data" / "sample.json"
OUTPUT_DIR = Path(__file__).parent.parent / "data"


def save_with_json(data: dict, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_with_orjson(data: dict, path: Path, indent: bool = True):
    option = orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS if indent else orjson.OPT_SORT_KEYS
    path.write_bytes(orjson.dumps(data, option=option))


def benchmark(data: dict, iterations: int = 1000):
    print(f"=== 성능 벤치마크 ({iterations}회 반복) ===")

    start = time.perf_counter()
    for _ in range(iterations):
        json.dumps(data, ensure_ascii=False)
    json_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(iterations):
        orjson.dumps(data)
    orjson_elapsed = time.perf_counter() - start

    print(f"  json   : {json_elapsed:.4f}s")
    print(f"  orjson : {orjson_elapsed:.4f}s")
    print(f"  속도 차이: {json_elapsed / orjson_elapsed:.1f}x 빠름")


def main():
    raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))

    # 기본 저장
    out_json = OUTPUT_DIR / "output_json.json"
    out_orjson = OUTPUT_DIR / "output_orjson.json"

    save_with_json(raw, out_json)
    save_with_orjson(raw, out_orjson)

    print("=== 저장 완료 ===")
    print(f"  json   → {out_json}")
    print(f"  orjson → {out_orjson}")

    # 저장 결과 확인
    print("\n=== orjson 저장 결과 (키 정렬 적용) ===")
    print(out_orjson.read_text(encoding="utf-8"))

    # 들여쓰기 없이 compact 저장
    out_compact = OUTPUT_DIR / "output_compact.json"
    out_compact.write_bytes(orjson.dumps(raw, option=orjson.OPT_SORT_KEYS))
    print(f"=== compact 저장 결과 ===")
    print(out_compact.read_text(encoding="utf-8"))

    # 성능 비교
    print()
    benchmark(raw)


if __name__ == "__main__":
    main()

"""
Safety Test — Correctness 정확성 검증
데이터 영속성·격리성·경계 조건·부작용 없음을 검증한다.

검증 항목:
  [영속성]  변경 결과가 파일에 실제로 반영되는가
  [격리성]  한 레코드 조작이 다른 레코드에 영향을 주지 않는가
  [경계]    빈 DB·없는 ID·빈 입력 등 극단값에서 올바르게 동작하는가
  [부작용]  실패 연산이 상태를 변경하지 않는가
  [ID 정책] ID 채번 규칙(max+1, gap 미채움)이 지켜지는가
"""
import json
import pytest
from src.json_crud import (
    create,
    read_all,
    read_by_id,
    search_by_field,
    update,
    delete,
)


# ── Create — 영속성 / 경계 / ID 정책 ─────────────────────────────────────

class TestCreateSafety:
    def test_추가_후_파일_users_수_증가(self, tmp_db):
        """[영속성] create() 후 파일의 users 배열 길이가 늘어야 한다."""
        create("Lee", "lee@example.com", 28, "Incheon", "22001", ["user"])
        data = json.loads(tmp_db.read_text(encoding="utf-8"))
        assert len(data["users"]) == 3

    def test_추가_후_파일_meta_total_동기화(self, tmp_db):
        """[영속성] meta.total 이 실제 users 수와 일치해야 한다."""
        create("Lee", "lee@example.com", 28, "Incheon", "22001", ["user"])
        data = json.loads(tmp_db.read_text(encoding="utf-8"))
        assert data["meta"]["total"] == len(data["users"])

    def test_빈_DB에서_ID_1부터_시작(self, empty_db):
        """[경계] 빈 DB 에 첫 레코드 추가 시 ID 는 1이어야 한다."""
        user = create("Park", "park@example.com", 22, "Daegu", "41944", [])
        assert user["id"] == 1

    def test_삭제_후_추가_시_ID_gap_미채움(self, tmp_db):
        """[ID 정책] 중간 ID 삭제 후 추가해도 빈 자리가 아닌 max+1 이어야 한다."""
        delete(1)                # ID 1 삭제 → 남은 최대 ID = 2
        user = create("New", "new@test.com", 20, "Seoul", "00000", [])
        assert user["id"] == 3  # 1 을 재사용하지 않음

    def test_태그_없이_추가_빈_리스트_저장(self, tmp_db):
        """[경계] tags=[] 로 추가 시 파일에도 빈 배열로 저장돼야 한다."""
        create("Choi", "choi@example.com", 35, "Gwangju", "61001", [])
        data = json.loads(tmp_db.read_text(encoding="utf-8"))
        choi = next(u for u in data["users"] if u["name"] == "Choi")
        assert choi["tags"] == []


# ── Read — 경계 ───────────────────────────────────────────────────────────

class TestReadAllSafety:
    def test_빈_DB_빈_리스트_반환(self, empty_db):
        """[경계] 비어있는 DB 에서 read_all() 은 빈 리스트를 반환해야 한다."""
        assert read_all() == []


class TestReadByIdSafety:
    def test_없는_ID_None_반환(self, tmp_db):
        """[경계] 존재하지 않는 ID 조회는 None 이어야 한다."""
        assert read_by_id(999) is None

    def test_빈_DB_에서_ID_조회_None(self, empty_db):
        """[경계] 빈 DB 에서 임의 ID 조회는 None 이어야 한다."""
        assert read_by_id(1) is None


# ── Search — 경계 / 부작용 ───────────────────────────────────────────────

class TestSearchSafety:
    def test_매칭_없으면_빈_리스트(self, tmp_db):
        """[경계] 검색 결과가 없을 때 빈 리스트여야 한다."""
        assert search_by_field("name", "존재하지않는이름") == []

    def test_존재하지_않는_필드_검색_빈_리스트(self, tmp_db):
        """[경계] 스키마에 없는 필드로 검색해도 예외 없이 빈 리스트여야 한다."""
        assert search_by_field("없는필드", "값") == []

    def test_검색이_원본_데이터_변경하지_않음(self, tmp_db):
        """[부작용] search_by_field() 호출 후 DB 상태가 변하지 않아야 한다."""
        before = len(read_all())
        search_by_field("name", "Hong")
        assert len(read_all()) == before


# ── Update — 영속성 / 격리 / 경계 / 부작용 ──────────────────────────────

class TestUpdateSafety:
    def test_중첩_필드_수정_시_나머지_키_유지(self, tmp_db):
        """[격리] address.city 수정 시 address.zip 은 변경되지 않아야 한다."""
        update(1, {"address.city": "Suwon"})
        user = read_by_id(1)
        assert user["address"]["zip"] == "04524"

    def test_수정_결과_파일에_반영(self, tmp_db):
        """[영속성] update() 후 파일을 직접 읽어도 변경이 반영돼야 한다."""
        update(1, {"email": "new@example.com"})
        data = json.loads(tmp_db.read_text(encoding="utf-8"))
        u1 = next(u for u in data["users"] if u["id"] == 1)
        assert u1["email"] == "new@example.com"

    def test_한_사용자_수정이_다른_사용자에_영향_없음(self, tmp_db):
        """[격리] ID 1 수정이 ID 2 의 데이터를 변경하지 않아야 한다."""
        update(1, {"age": 99})
        assert read_by_id(2)["age"] == 25

    def test_없는_ID_수정_시_파일_변경_없음(self, tmp_db):
        """[부작용] 없는 ID 수정은 파일 상태를 변경하지 않아야 한다."""
        before = tmp_db.read_bytes()
        update(999, {"name": "Ghost"})
        assert tmp_db.read_bytes() == before

    def test_빈_fields_dict_수정_시_데이터_무변경(self, tmp_db):
        """[경계] fields={} 를 전달해도 기존 데이터가 바뀌지 않아야 한다."""
        original_age = read_by_id(1)["age"]
        update(1, {})
        assert read_by_id(1)["age"] == original_age

    def test_존재하지_않는_중첩_outer_키_는_silent_skip(self, tmp_db):
        """[경계] outer 키가 없는 점 표기법은 예외 없이 무시돼야 한다."""
        result = update(1, {"없는키.field": "value"})
        assert result is not None              # 예외 발생 없이 반환
        assert "없는키" not in read_by_id(1)  # 필드 추가되지 않음


# ── Delete — 영속성 / 격리 / 경계 / 부작용 ──────────────────────────────

class TestDeleteSafety:
    def test_삭제_후_해당_ID_조회_불가(self, tmp_db):
        """[영속성] delete() 후 read_by_id() 는 None 을 반환해야 한다."""
        delete(1)
        assert read_by_id(1) is None

    def test_삭제_후_meta_total_감소(self, tmp_db):
        """[영속성] 삭제 후 파일의 meta.total 이 1 감소해야 한다."""
        delete(1)
        data = json.loads(tmp_db.read_text(encoding="utf-8"))
        assert data["meta"]["total"] == 1

    def test_meta_total_과_users_수_일치(self, tmp_db):
        """[영속성] 삭제 후 meta.total 이 실제 users 배열 크기와 같아야 한다."""
        delete(1)
        data = json.loads(tmp_db.read_text(encoding="utf-8"))
        assert data["meta"]["total"] == len(data["users"])

    def test_삭제_후_나머지_레코드_유지(self, tmp_db):
        """[격리] ID 1 삭제 후 ID 2 의 데이터가 온전히 남아야 한다."""
        delete(1)
        remaining = read_all()
        assert len(remaining) == 1
        assert remaining[0]["id"] == 2
        assert remaining[0]["name"] == "Kim"

    def test_없는_ID_삭제_시_파일_변경_없음(self, tmp_db):
        """[부작용] 없는 ID 삭제는 파일 상태를 변경하지 않아야 한다."""
        before = tmp_db.read_bytes()
        delete(999)
        assert tmp_db.read_bytes() == before

    def test_없는_ID_삭제_후_레코드_수_유지(self, tmp_db):
        """[부작용] 없는 ID 삭제 시도 후 전체 레코드 수가 변하지 않아야 한다."""
        delete(999)
        assert len(read_all()) == 2

    def test_전체_삭제_후_빈_목록_및_total_0(self, tmp_db):
        """[경계] 모든 레코드 삭제 후 read_all()=[] 이고 meta.total=0 이어야 한다."""
        delete(1)
        delete(2)
        assert read_all() == []
        data = json.loads(tmp_db.read_text(encoding="utf-8"))
        assert data["meta"]["total"] == 0

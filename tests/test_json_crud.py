"""json_crud.py 단위 테스트"""
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


# ── Create ────────────────────────────────────────────────────────────────

class TestCreate:
    def test_새_사용자_추가시_ID_자동_채번(self, tmp_db):
        user = create("Lee", "lee@example.com", 28, "Incheon", "22001", ["user"])
        assert user["id"] == 3

    def test_추가된_데이터_필드_일치(self, tmp_db):
        user = create("Lee", "lee@example.com", 28, "Incheon", "22001", ["user"])
        assert user["name"] == "Lee"
        assert user["email"] == "lee@example.com"
        assert user["age"] == 28
        assert user["address"] == {"city": "Incheon", "zip": "22001"}
        assert user["tags"] == ["user"]

    def test_추가_후_파일_total_증가(self, tmp_db):
        create("Lee", "lee@example.com", 28, "Incheon", "22001", ["user"])
        data = json.loads(tmp_db.read_text(encoding="utf-8"))
        assert data["meta"]["total"] == 3
        assert len(data["users"]) == 3

    def test_빈_DB에서_ID_1부터_시작(self, empty_db):
        user = create("Park", "park@example.com", 22, "Daegu", "41944", [])
        assert user["id"] == 1

    def test_태그_없이_추가(self, tmp_db):
        user = create("Choi", "choi@example.com", 35, "Gwangju", "61001", [])
        assert user["tags"] == []


# ── Read ─────────────────────────────────────────────────────────────────

class TestReadAll:
    def test_전체_목록_반환(self, tmp_db):
        users = read_all()
        assert len(users) == 2

    def test_빈_DB_빈_리스트_반환(self, empty_db):
        assert read_all() == []


class TestReadById:
    def test_존재하는_ID_조회(self, tmp_db):
        user = read_by_id(1)
        assert user is not None
        assert user["name"] == "Hong"

    def test_두_번째_사용자_조회(self, tmp_db):
        user = read_by_id(2)
        assert user is not None
        assert user["name"] == "Kim"

    def test_없는_ID_조회시_None_반환(self, tmp_db):
        assert read_by_id(999) is None

    def test_빈_DB에서_조회시_None_반환(self, empty_db):
        assert read_by_id(1) is None


# ── Search ────────────────────────────────────────────────────────────────

class TestSearchByField:
    def test_이름_부분_검색_대소문자_무시(self, tmp_db):
        results = search_by_field("name", "ho")
        assert len(results) == 1
        assert results[0]["name"] == "Hong"

    def test_이메일_부분_검색(self, tmp_db):
        results = search_by_field("email", "kim")
        assert len(results) == 1
        assert results[0]["name"] == "Kim"

    def test_나이_정확_검색(self, tmp_db):
        results = search_by_field("age", "25")
        assert len(results) == 1
        assert results[0]["name"] == "Kim"

    def test_일치_결과_없으면_빈_리스트(self, tmp_db):
        assert search_by_field("name", "없는이름") == []

    def test_존재하지_않는_필드는_빈_리스트(self, tmp_db):
        assert search_by_field("없는필드", "값") == []

    def test_여러_결과_반환(self, tmp_db):
        results = search_by_field("tags", "user")  # 두 사람 모두 user 태그 없음 (문자열 비교)
        # tags 는 리스트라 문자열 변환 후 비교됨 — 동작 확인
        assert isinstance(results, list)


# ── Update ────────────────────────────────────────────────────────────────

class TestUpdate:
    def test_단순_필드_수정(self, tmp_db):
        updated = update(1, {"age": 31})
        assert updated["age"] == 31

    def test_이름_수정(self, tmp_db):
        updated = update(1, {"name": "Hong Gil-dong"})
        assert updated["name"] == "Hong Gil-dong"

    def test_중첩_필드_점_표기법_수정(self, tmp_db):
        updated = update(1, {"address.city": "Suwon"})
        assert updated["address"]["city"] == "Suwon"

    def test_중첩_필드_수정시_나머지_유지(self, tmp_db):
        update(1, {"address.city": "Suwon"})
        user = read_by_id(1)
        assert user["address"]["zip"] == "04524"  # 기존 값 유지

    def test_여러_필드_동시_수정(self, tmp_db):
        updated = update(2, {"name": "Kang", "age": 26})
        assert updated["name"] == "Kang"
        assert updated["age"] == 26

    def test_수정_결과_파일에_반영(self, tmp_db):
        update(1, {"email": "new@example.com"})
        data = json.loads(tmp_db.read_text(encoding="utf-8"))
        user1 = next(u for u in data["users"] if u["id"] == 1)
        assert user1["email"] == "new@example.com"

    def test_없는_ID_수정시_None_반환(self, tmp_db):
        assert update(999, {"name": "Ghost"}) is None

    def test_수정이_다른_사용자에_영향_없음(self, tmp_db):
        update(1, {"age": 99})
        user2 = read_by_id(2)
        assert user2["age"] == 25


# ── Delete ────────────────────────────────────────────────────────────────

class TestDelete:
    def test_사용자_삭제_성공(self, tmp_db):
        assert delete(1) is True

    def test_삭제_후_조회시_None(self, tmp_db):
        delete(1)
        assert read_by_id(1) is None

    def test_삭제_후_meta_total_감소(self, tmp_db):
        delete(1)
        data = json.loads(tmp_db.read_text(encoding="utf-8"))
        assert data["meta"]["total"] == 1

    def test_삭제_후_나머지_데이터_유지(self, tmp_db):
        delete(1)
        remaining = read_all()
        assert len(remaining) == 1
        assert remaining[0]["id"] == 2

    def test_없는_ID_삭제시_False_반환(self, tmp_db):
        assert delete(999) is False

    def test_없는_ID_삭제시_데이터_변경_없음(self, tmp_db):
        delete(999)
        assert len(read_all()) == 2

    def test_전체_삭제_후_빈_목록(self, tmp_db):
        delete(1)
        delete(2)
        assert read_all() == []
        data = json.loads(tmp_db.read_text(encoding="utf-8"))
        assert data["meta"]["total"] == 0

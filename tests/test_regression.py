"""
Regression Test — 회귀 검증
핵심 기능의 API 계약(반환값 구조·타입·순서)이 변경 없이 유지되는지 확인한다.
"""
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

class TestCreateRegression:
    def test_단일_사용자_추가_반환_구조(self, tmp_db):
        """create()가 완전한 사용자 dict를 반환해야 한다."""
        user = create("Lee", "lee@example.com", 28, "Incheon", "22001", ["user"])
        assert user["id"] == 3
        assert user["name"] == "Lee"
        assert user["email"] == "lee@example.com"
        assert user["age"] == 28
        assert user["address"] == {"city": "Incheon", "zip": "22001"}
        assert user["tags"] == ["user"]

    def test_연속_추가_시_ID_순차_증가(self, tmp_db):
        """여러 번 create() 호출 시 ID 가 1씩 증가해야 한다."""
        u1 = create("A", "a@test.com", 20, "Seoul", "00001", [])
        u2 = create("B", "b@test.com", 21, "Busan", "00002", [])
        assert u1["id"] == 3
        assert u2["id"] == 4


# ── Read ─────────────────────────────────────────────────────────────────

class TestReadAllRegression:
    def test_전체_목록_개수(self, tmp_db):
        """초기 DB 의 사용자 수가 정확히 반환돼야 한다."""
        assert len(read_all()) == 2

    def test_반환_순서_삽입_순(self, tmp_db):
        """read_all() 은 삽입 순서를 유지해야 한다."""
        users = read_all()
        assert users[0]["name"] == "Hong"
        assert users[1]["name"] == "Kim"


class TestReadByIdRegression:
    def test_첫_번째_사용자_조회(self, tmp_db):
        user = read_by_id(1)
        assert user is not None
        assert user["name"] == "Hong"
        assert user["email"] == "hong@example.com"

    def test_두_번째_사용자_조회(self, tmp_db):
        user = read_by_id(2)
        assert user is not None
        assert user["name"] == "Kim"

    def test_없는_ID_는_None(self, tmp_db):
        assert read_by_id(999) is None


# ── Search ────────────────────────────────────────────────────────────────

class TestSearchRegression:
    def test_이름_부분_검색(self, tmp_db):
        results = search_by_field("name", "Hong")
        assert len(results) == 1
        assert results[0]["id"] == 1

    def test_이름_검색_대소문자_무시(self, tmp_db):
        """대소문자와 무관하게 부분 일치 검색돼야 한다."""
        results = search_by_field("name", "ho")
        assert len(results) == 1
        assert results[0]["name"] == "Hong"

    def test_이메일_부분_검색(self, tmp_db):
        results = search_by_field("email", "kim")
        assert len(results) == 1
        assert results[0]["name"] == "Kim"

    def test_나이_정확_검색(self, tmp_db):
        results = search_by_field("age", "30")
        assert len(results) == 1
        assert results[0]["name"] == "Hong"

    def test_공통_키워드로_복수_결과_반환(self, tmp_db):
        """두 사용자 모두 @example.com 을 가지므로 2건 반환돼야 한다."""
        results = search_by_field("email", "@example.com")
        assert len(results) == 2


# ── Update ────────────────────────────────────────────────────────────────

class TestUpdateRegression:
    def test_단순_필드_수정_반환값(self, tmp_db):
        updated = update(1, {"age": 31})
        assert updated is not None
        assert updated["age"] == 31

    def test_이름_수정(self, tmp_db):
        updated = update(1, {"name": "Hong Gil-dong"})
        assert updated["name"] == "Hong Gil-dong"

    def test_중첩_필드_점_표기법_수정(self, tmp_db):
        updated = update(1, {"address.city": "Suwon"})
        assert updated["address"]["city"] == "Suwon"

    def test_여러_필드_동시_수정(self, tmp_db):
        updated = update(2, {"name": "Kang", "age": 26})
        assert updated["name"] == "Kang"
        assert updated["age"] == 26

    def test_없는_ID_수정_None_반환(self, tmp_db):
        assert update(999, {"name": "Ghost"}) is None


# ── Delete ────────────────────────────────────────────────────────────────

class TestDeleteRegression:
    def test_삭제_성공_시_True_반환(self, tmp_db):
        assert delete(1) is True

    def test_없는_ID_삭제_시_False_반환(self, tmp_db):
        assert delete(999) is False

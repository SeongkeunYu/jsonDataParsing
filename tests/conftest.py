"""pytest 공용 fixture"""
import json
import pytest
import src.json_crud as crud

INITIAL_DATA = {
    "users": [
        {
            "id": 1,
            "name": "Hong",
            "email": "hong@example.com",
            "age": 30,
            "address": {"city": "Seoul", "zip": "04524"},
            "tags": ["admin", "user"],
        },
        {
            "id": 2,
            "name": "Kim",
            "email": "kim@example.com",
            "age": 25,
            "address": {"city": "Busan", "zip": "48058"},
            "tags": ["user"],
        },
    ],
    "meta": {"total": 2},
}


@pytest.fixture
def tmp_db(tmp_path, monkeypatch):
    """각 테스트마다 격리된 임시 DB 파일 제공 — 실제 db.json 을 건드리지 않음"""
    db = tmp_path / "db.json"
    db.write_text(json.dumps(INITIAL_DATA, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(crud, "DB_FILE", db)
    return db


@pytest.fixture
def empty_db(tmp_path, monkeypatch):
    """빈 DB 파일 fixture"""
    db = tmp_path / "empty_db.json"
    db.write_text('{"users": [], "meta": {"total": 0}}', encoding="utf-8")
    monkeypatch.setattr(crud, "DB_FILE", db)
    return db

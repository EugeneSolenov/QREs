from fastapi.testclient import TestClient

from app.main import app


c = TestClient(app)


def test_a():
    r = c.get("/errors/condition", params={"value": -1})

    assert r.status_code == 400
    assert r.json() == {
        "status_code": 400,
        "error_code": "condition_failed",
        "message": "value must be greater than or equal to 0",
        "details": None,
    }


def test_b():
    r = c.get("/errors/resources/999")

    assert r.status_code == 404
    assert r.json()["error_code"] == "resource_not_found"
    assert r.json()["message"] == "resource 999 was not found"


def test_c():
    r = c.post(
        "/validation/users",
        json={
            "username": "student",
            "age": 19,
            "email": "student@example.com",
            "password": "strongpass",
        },
    )

    assert r.status_code == 201
    assert r.json() == {
        "username": "student",
        "age": 19,
        "email": "student@example.com",
        "phone": "Unknown",
    }


def test_d():
    r = c.post(
        "/validation/users",
        json={
            "username": "student",
            "age": 18,
            "email": "not-an-email",
            "password": "short",
        },
    )

    assert r.status_code == 422
    b = r.json()
    assert b["error_code"] == "validation_error"
    assert b["message"] == "Request validation failed"

    arr = {x["field"] for x in b["details"]}
    assert "body.age" in arr
    assert "body.email" in arr
    assert "body.password" in arr

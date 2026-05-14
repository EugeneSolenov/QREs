from fastapi.testclient import TestClient

from app.main import app


c = TestClient(app)


def test_a():
    r = c.post("/users", json={"username": "alice", "age": 30})

    assert r.status_code == 201
    assert r.json() == {"id": 1, "username": "alice", "age": 30}


def test_b():
    a = c.post("/users", json={"username": "bob", "age": 24})
    r = c.get(f"/users/{a.json()['id']}")

    assert r.status_code == 200
    assert r.json() == {"id": 1, "username": "bob", "age": 24}


def test_c():
    r = c.get("/users/404")

    assert r.status_code == 404
    assert r.json()["detail"] == "User not found"


def test_d():
    a = c.post("/users", json={"username": "carol", "age": 27})
    r = c.delete(f"/users/{a.json()['id']}")

    assert r.status_code == 204
    assert r.text == ""


def test_e():
    r = c.delete("/users/404")

    assert r.status_code == 404
    assert r.json()["detail"] == "User not found"

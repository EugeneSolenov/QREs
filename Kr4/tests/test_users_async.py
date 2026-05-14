import pytest
from faker import Faker
from httpx import ASGITransport, AsyncClient

from app.main import app


pytestmark = pytest.mark.asyncio


@pytest.fixture
def faker_ru():
    return Faker("ru_RU")


async def test_a(faker_ru):
    tr = ASGITransport(app=app)
    d = {"username": faker_ru.user_name(), "age": faker_ru.random_int(18, 80)}

    async with AsyncClient(transport=tr, base_url="http://test") as c:
        r = await c.post("/users", json=d)

    b = r.json()
    assert r.status_code == 201
    assert b["id"] == 1
    assert b["username"] == d["username"]
    assert b["age"] == d["age"]


async def test_b(faker_ru):
    tr = ASGITransport(app=app)
    d = {"username": faker_ru.user_name(), "age": faker_ru.random_int(18, 80)}

    async with AsyncClient(transport=tr, base_url="http://test") as c:
        a = await c.post("/users", json=d)
        r = await c.get(f"/users/{a.json()['id']}")

    assert r.status_code == 200
    assert r.json() == {"id": 1, **d}


async def test_c():
    tr = ASGITransport(app=app)

    async with AsyncClient(transport=tr, base_url="http://test") as c:
        r = await c.get("/users/999")

    assert r.status_code == 404
    assert r.json()["detail"] == "User not found"


async def test_d(faker_ru):
    tr = ASGITransport(app=app)
    d = {"username": faker_ru.user_name(), "age": faker_ru.random_int(18, 80)}

    async with AsyncClient(transport=tr, base_url="http://test") as c:
        a = await c.post("/users", json=d)
        uid = a.json()["id"]
        r1 = await c.delete(f"/users/{uid}")
        r2 = await c.delete(f"/users/{uid}")

    assert r1.status_code == 204
    assert r1.text == ""
    assert r2.status_code == 404
    assert r2.json()["detail"] == "User not found"


async def test_e(faker_ru):
    tr = ASGITransport(app=app)
    d = {"username": faker_ru.user_name(), "age": 0}

    async with AsyncClient(transport=tr, base_url="http://test") as c:
        r = await c.post("/users", json=d)

    assert r.status_code == 201
    assert r.json()["age"] == 0

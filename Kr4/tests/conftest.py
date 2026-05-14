import pytest

from app.main import reset_user_storage


@pytest.fixture(autouse=True)
def f0():
    reset_user_storage()
    yield
    reset_user_storage()

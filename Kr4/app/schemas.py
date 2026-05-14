from decimal import Decimal
from typing import Any

from pydantic import BaseModel as B, ConfigDict as Cfg, EmailStr, conint, constr


class ErrorResponse(B):
    status_code: int
    error_code: str
    message: str
    details: list[dict[str, Any]] | None = None


class UserValidationIn(B):
    username: constr(min_length=1)
    age: conint(gt=18)
    email: EmailStr
    password: constr(min_length=8, max_length=16)
    phone: str | None = "Unknown"


class UserValidationOut(B):
    username: str
    age: int
    email: EmailStr
    phone: str | None


class UserIn(B):
    username: constr(min_length=1)
    age: conint(ge=0)


class UserOut(B):
    id: int
    username: str
    age: int


class ProductOut(B):
    model_config = Cfg(from_attributes=True)

    id: int
    title: str
    price: Decimal
    count: int
    description: str

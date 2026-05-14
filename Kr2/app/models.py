import re
from pydantic import BaseModel as B, ConfigDict as Cfg, EmailStr, Field as F, PositiveInt, ValidationError, field_validator
pat = re.compile(
    r"^[A-Za-z]{1,8}(?:-[A-Za-z0-9]{1,8})?"
    r"(?:\s*,\s*[A-Za-z]{1,8}(?:-[A-Za-z0-9]{1,8})?(?:\s*;\s*q=\d(?:\.\d{1,3})?)?)*$"
)
ACCEPT_LANGUAGE_PATTERN = pat
class UserCreate(B):
    name: str = F(min_length=1, max_length=100)
    email: EmailStr
    age: PositiveInt | None = None
    is_subscribed: bool | None = None
    model_config = Cfg(str_strip_whitespace=True)
class Product(B):
    product_id: int
    name: str
    category: str
    price: float
class LoginRequest(B):
    username: str = F(min_length=1, max_length=50)
    password: str = F(min_length=1, max_length=100)
    model_config = Cfg(str_strip_whitespace=True)
class UserProfile(B):
    user_id: str
    username: str
    email: EmailStr
    full_name: str
class CommonHeaders(B):
    user_agent: str = F(alias="User-Agent", min_length=1)
    accept_language: str = F(alias="Accept-Language", min_length=1)
    model_config = Cfg(populate_by_name=True, str_strip_whitespace=True)
    @field_validator("accept_language")
    @classmethod
    def f1(cls, v):
        if not pat.fullmatch(v):
            raise ValueError(
                "Accept-Language must match a valid format like en-US,en;q=0.9,es;q=0.8"
            )
        return v
    def as_response_payload(self):
        return {
            "User-Agent": self.user_agent,
            "Accept-Language": self.accept_language,
        }
    @classmethod
    def from_headers(cls, user_agent, accept_language):
        if not user_agent:
            raise ValueError("Header 'User-Agent' is required")
        if not accept_language:
            raise ValueError("Header 'Accept-Language' is required")
        try:
            return cls.model_validate(
                {
                    "User-Agent": user_agent,
                    "Accept-Language": accept_language,
                }
            )
        except ValidationError as e:
            msg = e.errors()[0]["msg"]
            raise ValueError(msg) from e
def validation_error_message(errors):
    if not errors:
        return "Invalid input"
    return str(errors[0].get("msg", "Invalid input"))

from pydantic import BaseModel, Field

# Simple shape check; not full RFC 5322 validation.
EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(max_length=100, pattern=EMAIL_PATTERN)
    password: str = Field(min_length=8, max_length=128)
    shipping_addr: str = Field(min_length=1, max_length=255)
    billing_addr: str = Field(min_length=1, max_length=255)


class UserUpdate(BaseModel):
    """Every field is optional; only the fields sent are changed."""

    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: str | None = Field(default=None, max_length=100, pattern=EMAIL_PATTERN)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    shipping_addr: str | None = Field(default=None, min_length=1, max_length=255)
    billing_addr: str | None = Field(default=None, min_length=1, max_length=255)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    """What the API returns. Never includes password_hash."""

    user_id: int
    username: str
    email: str
    shipping_addr: str | None
    billing_addr: str | None

from pydantic import BaseModel, Field

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(max_length=100, pattern=EMAIL_PATTERN)
    password: str = Field(min_length=8, max_length=128)
    shipping_addr: str = Field(min_length=1, max_length=255)
    billing_addr: str = Field(min_length=1, max_length=255)

class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: str | None = Field(default=None, max_length=100, pattern=EMAIL_PATTERN)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    shipping_addr: str | None = Field(default=None, min_length=1, max_length=255)
    billing_addr: str | None = Field(default=None, min_length=1, max_length=255)

class UserLogin(BaseModel):
    username: str
    password: str

class UserOut(BaseModel):
    """Ensure the API never includes password_hash when returning."""

    user_id: int
    username: str
    email: str
    shipping_addr: str
    billing_addr: str

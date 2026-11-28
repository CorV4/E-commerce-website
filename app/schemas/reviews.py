from pydantic import BaseModel, Field

class ReviewCreate(BaseModel):
    user_id: int
    stars: int = Field(ge=1, le=5)
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=1000)

class ReviewUpdate(BaseModel):
    stars: int | None = Field(default=None, ge=1, le=5)
    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=1000)

class ReviewOut(BaseModel):
    review_id: int
    item_id: int
    user_id: int
    username: str
    stars: int
    title: str
    description: str

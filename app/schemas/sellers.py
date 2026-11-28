from pydantic import BaseModel, Field

BANK_ACC_PATTERN = r"^[0-9]{4,20}$"  # digits only

class SellerCreate(BaseModel):
    user_id: int
    store_name: str = Field(min_length=1, max_length=100)
    bank_acc_number: str = Field(pattern=BANK_ACC_PATTERN)

class SellerUpdate(BaseModel):
    store_name: str | None = Field(default=None, min_length=1, max_length=100)
    bank_acc_number: str | None = Field(default=None, pattern=BANK_ACC_PATTERN)

class SellerOut(BaseModel):

    seller_id: int
    user_id: int
    store_name: str

from datetime import date

from pydantic import BaseModel, Field

class CardCreate(BaseModel):
    card_number: str = Field(pattern=r"^[0-9]{13,16}$")
    card_cvv: str = Field(pattern=r"^[0-9]{3,4}$")
    card_exp_date: date

class CardUpdate(BaseModel):
    # Can only change cvv and/or expiration date for a card.
    # User will have to delete and add a new card if they want to change the number.
    card_cvv: str | None = Field(default=None, pattern=r"^[0-9]{3,4}$")
    card_exp_date: date | None = None

class CardOut(BaseModel):
    card_number: str
    card_exp_date: date

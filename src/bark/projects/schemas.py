from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class InputQuote(BaseModel):
    seller_id: int = Field(strict=True)
    message: str = Field(min_length=20)
    price_cents: int = Field(strict=True, gt=0)


class QuoteStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class OutputQuote(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field()
    project_id: int = Field()
    seller_id: int = Field()
    message: str = Field()
    price_cents: int = Field()
    status: QuoteStatus = Field()


class SortOrder(str, Enum):
    asc = "asc"
    desc = "desc"

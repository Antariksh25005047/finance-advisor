from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel

class Transaction(BaseModel):
    date:date
    amount: float
    direction: Literal["debit", "credit"]
    narration: str
    merchant: Optional[str] = None
    category: Optional[str] = None
    source : str


class ParseResult(BaseModel):
    trasactions : list[Transaction]
    warnings: list[str] = []
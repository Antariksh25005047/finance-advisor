from datetime import date
from typing import Literal, Optional
from pydantic import BaseModel


class Transaction(BaseModel):
    date: date
    amount: float                      # always positive
    direction: Literal["debit", "credit"]
    narration: str                     # raw description from the statement
    merchant: Optional[str] = None     # cleaned payee name
    category: Optional[str] = None
    category_source: Optional[str] = None   # "rule" | "paytm_tag" | "kind" -> used later for "why this category?"
    kind: str = "merchant"             # "merchant" | "p2p" | "self_transfer"
    tag_hint: Optional[str] = None     # tag given by the source app (e.g. Paytm), only a hint
    source: str


class ParseResult(BaseModel):
    transactions: list[Transaction]
    warnings: list[str] = []

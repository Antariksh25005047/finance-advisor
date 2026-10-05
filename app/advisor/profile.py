from typing import Literal
from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    age: int = Field(ge=18, le=100)
    monthly_income: float = Field(ge=0)
    income_stability: Literal["stable", "variable"]
    emergency_fund_months: float = Field(ge=0)     # kitne mahine ka kharcha bachat mein hai
    has_high_interest_debt: bool                   # credit card / BNPL / personal loan
    investing_horizon_years: float = Field(gt=0)   # paisa kitne saal invest rahega
    market_drop_reaction: Literal["sell", "hold", "buy_more"]   # 20% gire toh?
    experience: Literal["none", "some", "experienced"]
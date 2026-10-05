from pydantic import BaseModel

from .profile import UserProfile
from .risk import RiskResult

GOLD_PCT = 10   # fixed hedge


class Allocation(BaseModel):
    weights: dict[str, int]      # equity / debt / gold / liquid, total 100
    trace: list[str]             # "kyu" wale jawab yahin se banenge
    warnings: list[str]


def build_allocation(p: UserProfile, risk: RiskResult) -> Allocation:
    trace: list[str] = []
    warnings: list[str] = []

    # 1. risk score se base equity
    equity = int(10 + 0.65 * risk.score + 0.5)
    trace.append(f"Base equity from risk score {risk.score}: 10 + 0.65 x {risk.score} = {equity}%")

    # 2. horizon cap: chhote time ka paisa equity mein nahi
    if p.investing_horizon_years < 3:
        cap = 20
    elif p.investing_horizon_years < 5:
        cap = 40
    else:
        cap = 100
    if equity > cap:
        trace.append(f"Horizon {p.investing_horizon_years:g} years is short -> equity capped at {cap}% (was {equity}%)")
        equity = cap

    # 3. liquid: emergency fund jitna kam, utna zyada liquid
    if p.emergency_fund_months >= 6:
        liquid = 10
    elif p.emergency_fund_months >= 3:
        liquid = 20
    else:
        liquid = 30
    trace.append(f"Emergency fund {p.emergency_fund_months:g} months -> liquid {liquid}%")

    # 4. gold
    gold = GOLD_PCT
    trace.append(f"Gold fixed at {gold}% as a hedge")

    # 5. debt funds = baaki sab (kam se kam 5%)
    debt = 100 - equity - gold - liquid
    if debt < 5:
        equity -= 5 - debt
        debt = 5
        trace.append(f"Debt kept at minimum 5%, equity reduced to {equity}%")
    trace.append(f"Debt funds = 100 - equity {equity} - gold {gold} - liquid {liquid} = {debt}%")

    # warnings: allocation se pehle ki basics
    if p.has_high_interest_debt:
        warnings.append("Pay off high-interest debt (credit card / BNPL) first: its interest "
                        "is usually higher than what investments return.")
    if p.emergency_fund_months < 3:
        warnings.append("Build an emergency fund of at least 3-6 months of expenses before "
                        "investing more in equity.")

    weights = {"equity": equity, "debt": debt, "gold": gold, "liquid": liquid}
    return Allocation(weights=weights, trace=trace, warnings=warnings)


def split_amount(weights: dict[str, int], monthly_amount: float) -> dict[str, int]:
    """Rupees mein: monthly_amount ko weights ke hisaab se baanto."""
    return {k: round(monthly_amount * v / 100) for k, v in weights.items()}
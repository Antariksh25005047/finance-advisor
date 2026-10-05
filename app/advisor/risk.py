from pydantic import BaseModel

from .profile import UserProfile


class RiskResult(BaseModel):
    score: int            # 0-100
    label: str            # Conservative / Moderate / Aggressive
    capacity: int
    tolerance: int
    trace: list[str]      # "kyu" wale jawab yahin se banenge


def _horizon_points(years: float) -> int:
    if years < 1:
        return 0
    if years < 3:
        return 10
    if years < 5:
        return 20
    if years < 10:
        return 30
    return 40


def compute_risk(p: UserProfile) -> RiskResult:
    trace: list[str] = []

    # ---- capacity (0-100): risk afford kar sakte ho? ----
    h = _horizon_points(p.investing_horizon_years)
    trace.append(f"Horizon {p.investing_horizon_years:g} years -> +{h} capacity")

    if p.emergency_fund_months >= 6:
        e = 20
    elif p.emergency_fund_months >= 3:
        e = 10
    else:
        e = 0
    trace.append(f"Emergency fund {p.emergency_fund_months:g} months -> +{e} capacity")

    if p.has_high_interest_debt:
        d = 0
        trace.append("High-interest debt present -> +0 capacity")
    else:
        d = 20
        trace.append("No high-interest debt -> +20 capacity")

    s = 20 if p.income_stability == "stable" else 5
    trace.append(f"{p.income_stability.capitalize()} income -> +{s} capacity")

    capacity = h + e + d + s

    # ---- tolerance (0-100): risk lena chahte ho? ----
    r = {"sell": 0, "hold": 50, "buy_more": 80}[p.market_drop_reaction]
    trace.append(f"Reaction to a market drop: {p.market_drop_reaction} -> +{r} tolerance")

    x = {"none": 0, "some": 10, "experienced": 20}[p.experience]
    trace.append(f"Experience: {p.experience} -> +{x} tolerance")

    tolerance = r + x

    # ---- final: kam wala jeetta hai ----
    score = min(capacity, tolerance)
    limiter = "capacity" if capacity < tolerance else "tolerance"
    trace.append(f"Score = min(capacity {capacity}, tolerance {tolerance}) = {score} "
                 f"(limited by {limiter})")

    # ---- foundation first: debt ya emergency fund nahi toh Conservative se upar nahi ----
    if (p.has_high_interest_debt or p.emergency_fund_months < 3) and score > 29:
        score = 29
        trace.append("Foundation first: high-interest debt or emergency fund < 3 months "
                     "-> score capped at 29")

    label = "Conservative" if score < 35 else "Moderate" if score < 70 else "Aggressive"
    return RiskResult(score=score, label=label, capacity=capacity,
                      tolerance=tolerance, trace=trace)
from app.advisor.profile import UserProfile
from app.advisor.risk import compute_risk


def make(**kw):
    base = dict(age=20, monthly_income=15000, income_stability="stable",
                emergency_fund_months=6, has_high_interest_debt=False,
                investing_horizon_years=10, market_drop_reaction="hold",
                experience="some")
    base.update(kw)
    return UserProfile(**base)


def test_balanced_profile_is_moderate():
    r = compute_risk(make())
    assert r.capacity == 100 and r.tolerance == 60
    assert r.score == 60 and r.label == "Moderate"


def test_panic_seller_is_conservative_even_with_great_capacity():
    r = compute_risk(make(market_drop_reaction="sell", experience="none"))
    assert r.score == 0 and r.label == "Conservative"


def test_debt_and_no_emergency_fund_cap_the_score():
    r = compute_risk(make(has_high_interest_debt=True, emergency_fund_months=0,
                          market_drop_reaction="buy_more", experience="experienced"))
    assert r.capacity == 60 and r.tolerance == 100
    assert r.score == 29 and r.label == "Conservative"
    assert any("Foundation first" in line for line in r.trace)


def test_risk_lover_with_strong_foundation_is_aggressive():
    r = compute_risk(make(market_drop_reaction="buy_more", experience="experienced"))
    assert r.score == 100 and r.label == "Aggressive"
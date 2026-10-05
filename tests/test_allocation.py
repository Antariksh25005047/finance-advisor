from app.advisor.allocation import build_allocation, split_amount
from app.advisor.profile import UserProfile
from app.advisor.risk import compute_risk


def make(**kw):
    base = dict(age=20, monthly_income=15000, income_stability="stable",
                emergency_fund_months=6, has_high_interest_debt=False,
                investing_horizon_years=10, market_drop_reaction="hold",
                experience="some")
    base.update(kw)
    return UserProfile(**base)


def alloc(**kw):
    p = make(**kw)
    return build_allocation(p, compute_risk(p))


def test_balanced_profile():
    a = alloc()
    assert a.weights == {"equity": 49, "debt": 31, "gold": 10, "liquid": 10}
    assert not a.warnings


def test_weights_always_sum_to_100():
    for kw in [dict(), dict(market_drop_reaction="buy_more", experience="experienced"),
               dict(market_drop_reaction="sell", experience="none"),
               dict(investing_horizon_years=2), dict(emergency_fund_months=0)]:
        assert sum(alloc(**kw).weights.values()) == 100


def test_short_horizon_caps_equity():
    a = alloc(investing_horizon_years=2, market_drop_reaction="buy_more", experience="experienced")
    assert a.weights["equity"] == 20
    assert any("capped" in line for line in a.trace)


def test_debt_and_no_emergency_fund():
    a = alloc(has_high_interest_debt=True, emergency_fund_months=0,
              market_drop_reaction="buy_more", experience="experienced")
    assert a.weights["liquid"] == 30 and a.weights["equity"] == 29
    assert len(a.warnings) == 2


def test_split_amount():
    assert split_amount({"equity": 50, "debt": 50}, 1000) == {"equity": 500, "debt": 500}
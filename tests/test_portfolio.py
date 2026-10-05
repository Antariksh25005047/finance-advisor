import pytest

from app.advisor.allocation import build_allocation
from app.advisor.portfolio import PortfolioManager, rebalance
from app.advisor.profile import UserProfile
from app.advisor.risk import compute_risk


def manager(**kw):
    base = dict(age=20, monthly_income=15000, income_stability="stable",
                emergency_fund_months=6, has_high_interest_debt=False,
                investing_horizon_years=10, market_drop_reaction="hold", experience="some")
    base.update(kw)
    p = UserProfile(**base)
    r = compute_risk(p)
    return PortfolioManager(p, r, build_allocation(p, r))


def test_rebalance_keeps_total_100():
    w = {"equity": 49, "debt": 31, "gold": 10, "liquid": 10}
    for asset in w:
        for v in (0, 7, 33, 50, 100):
            out = rebalance(w, asset, v)
            assert sum(out.values()) == 100 and out[asset] == v


def test_simulate_does_not_change_portfolio():
    m = manager()
    sim = m.simulate("gold", 20)
    assert sim.after["gold"] == 20 and sum(sim.after.values()) == 100
    assert m.current == sim.before and len(m.versions) == 1


def test_apply_and_undo():
    m = manager()
    sim = m.simulate("gold", 20)
    assert m.apply(sim.simulation_id)["gold"] == 20 and len(m.versions) == 2
    assert m.undo()["gold"] == 10
    with pytest.raises(ValueError):
        m.undo()           # original se peeche nahi ja sakte


def test_guardrails_warn_but_do_not_block():
    sim = manager().simulate("equity", 90)
    assert sim.after["equity"] == 90
    assert len(sim.warnings) >= 2          # risk profile se zyada + concentration


def test_bad_input_and_stale_simulation():
    m = manager()
    with pytest.raises(ValueError):
        m.simulate("crypto", 10)
    with pytest.raises(ValueError):
        m.simulate("gold", 150)
    s1, s2 = m.simulate("gold", 20), m.simulate("equity", 60)
    m.apply(s1.simulation_id)
    with pytest.raises(ValueError):
        m.apply(s2.simulation_id)          # s2 purane portfolio pe bana tha
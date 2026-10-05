from app.advisor.session import AdvisorSession

FULL = dict(age=20, monthly_income=15000, income_stability="stable", emergency_fund_months=6,
            has_high_interest_debt=False, investing_horizon_years=10,
            market_drop_reaction="hold", experience="some")


def test_profile_collected_step_by_step():
    s = AdvisorSession()
    r = s.update_profile(age=20, monthly_income=15000)
    assert "age" not in r["missing_fields"] and "experience" in r["missing_fields"]
    assert s.build_portfolio()["error"] == "MISSING_FIELDS"
    r = s.update_profile(**{k: v for k, v in FULL.items() if k not in ("age", "monthly_income")})
    assert r["missing_fields"] == []


def test_invalid_and_unknown_fields_are_reported_not_raised():
    s = AdvisorSession()
    assert s.update_profile(age=5)["error"] == "INVALID_VALUE"
    assert s.update_profile(favourite_color="blue")["error"] == "UNKNOWN_FIELD"
    assert s.profile_data == {}          # galat value save nahi hui


def test_full_flow_simulate_apply_undo():
    s = AdvisorSession()
    s.update_profile(**FULL)
    b = s.build_portfolio()
    assert b["weights"] == {"equity": 49, "debt": 31, "gold": 10, "liquid": 10}
    sim = s.simulate_change("gold", 20)
    assert s.get_portfolio()["weights"]["gold"] == 10          # simulate ne kuch nahi badla
    assert s.apply_change(sim["simulation_id"])["weights"]["gold"] == 20
    assert s.undo_change()["weights"]["gold"] == 10
    assert s.undo_change()["error"] == "INVALID_REQUEST"
    assert s.simulate_change("crypto", 10)["error"] == "INVALID_REQUEST"


def test_errors_without_portfolio_or_statement():
    s = AdvisorSession()
    assert s.simulate_change("gold", 20)["error"] == "NO_PORTFOLIO"
    assert s.get_spending_insights()["error"] == "NO_STATEMENT"


def test_explain_and_profile_change_note():
    s = AdvisorSession()
    s.update_profile(**FULL)
    s.build_portfolio()
    ex = s.explain_portfolio()
    assert ex["risk_label"] == "Moderate" and ex["allocation_trace"]
    assert "note" in s.update_profile(emergency_fund_months=1)
    assert s.get_portfolio(monthly_amount=1000)["monthly_amount_split"]["equity"] == 490
    
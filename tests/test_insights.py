from datetime import date

from app.analytics.insights import (coverage, investable_amount, monthly_trend,
                                    recurring_payments, savings_opportunities)
from app.parsers.base import Transaction


def tx(d, amt, merchant, cat, direction="debit", kind="merchant", narration=None):
    return Transaction(date=d, amount=amt, direction=direction, kind=kind, merchant=merchant,
                       narration=narration or f"Paid to {merchant}", category=cat, source="test")


def _data():
    t = []
    # statement 2026-07-05 .. 2026-10-02 -> poore mahine: Aug, Sep
    t.append(tx(date(2026, 7, 5), 10, "Seed", "Other"))
    t.append(tx(date(2026, 10, 2), 10, "Seed", "Other"))
    for m in (7, 8, 9):                                   # fixed monthly subscription
        t.append(tx(date(2026, m, 10), 199, "Netflix", "Subscriptions"))
    for d in (1, 5, 9, 14, 20):                           # habit: baar-baar, alag amounts
        t.append(tx(date(2026, 8, d), 100 + d * 7, "Canteen", "Food"))
    for d in (1, 2, 3, 4):                                # chhote same payments = subscription nahi
        t.append(tx(date(2026, 8, d), 40, "Tea Stall", "Food"))
    t.append(tx(date(2026, 8, 15), 300, "Zomato", "Food Delivery"))
    t.append(tx(date(2026, 9, 15), 2000, "Zomato", "Food Delivery"))   # Sep mein spike
    t.append(tx(date(2026, 9, 3), 5000, "Friend", "Transfers (P2P)", kind="p2p"))
    t.append(tx(date(2026, 9, 4), 999, "Own", "Self Transfer", kind="self_transfer"))
    t.append(tx(date(2026, 8, 9), 1, "Spotify", "Subscriptions",
                narration="Automatic payment of Rs139 setup for Spotify"))
    return t


def test_coverage_ignores_partial_months():
    assert coverage(_data())["full_months"] == ["2026-08", "2026-09"]


def test_recurring_detection():
    r = recurring_payments(_data())
    assert [x["merchant"] for x in r["fixed"]] == ["Netflix"]
    habit_names = [x["merchant"] for x in r["habits"]]
    assert "Canteen" in habit_names and "Tea Stall" in habit_names
    assert all(x["merchant"] != "Spotify" for x in r["fixed"] + r["habits"])  # mandate test debit


def test_trend_flags_spike_and_skips_p2p():
    t = monthly_trend(_data())
    cats = {f["category"]: f for f in t["flags"]}
    assert "Food Delivery" in cats and cats["Food Delivery"]["largest_payment"]["amount"] == 2000
    assert "Transfers (P2P)" not in cats


def test_savings_and_investable():
    s = savings_opportunities(_data(), 0.5)
    assert s and all(abs(x["yearly_saving"] - x["monthly_saving"] * 12) < 0.5 for x in s)
    inv = investable_amount(_data(), monthly_income=100000)
    assert inv["investable_per_month"] > 0
    assert investable_amount(_data(), monthly_income=100)["investable_per_month"] == 0
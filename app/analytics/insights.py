"""Rule-based insights on categorized transactions. Pure code, no LLM:
every number the chatbot later quotes comes from these functions."""
from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import date, timedelta

from app.parsers.base import Transaction

ESSENTIAL = {"Health", "Groceries", "Bills & Recharge", "Transport", "Fuel"}
OBLIGATION = {"Credit & EMI", "Rent"}
DISCRETIONARY = {"Food", "Food Delivery", "Shopping", "Subscriptions",
                 "Entertainment", "Vending Machines", "Personal Care"}
TRANSFER = {"Transfers (P2P)"}
MIN_FIXED_AMOUNT = 100   # isse chhote repeat payments (chai, laundry) habit hain, subscription nahi


def group_of(category: str | None) -> str:
    if category in ESSENTIAL:
        return "essential"
    if category in OBLIGATION:
        return "obligation"
    if category in DISCRETIONARY:
        return "discretionary"
    if category in TRANSFER:
        return "transfers"
    return "other"


def _spend(txs: list[Transaction]) -> list[Transaction]:
    """Asli outflow: debits, self transfers nahi."""
    return [t for t in txs if t.direction == "debit" and t.kind != "self_transfer"]


# ---------- coverage ----------

def coverage(txs: list[Transaction]) -> dict:
    """Statement kitne din ka hai, aur kaun se mahine poore hain."""
    first, last = min(t.date for t in txs), max(t.date for t in txs)
    full, d = [], date(first.year, first.month, 1)
    while d <= last:
        nxt = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        if first <= d and last >= nxt - timedelta(days=1):
            full.append(d.strftime("%Y-%m"))
        d = nxt
    return {"first": first.isoformat(), "last": last.isoformat(),
            "days": (last - first).days + 1, "full_months": full}


# ---------- recurring payments ----------

def recurring_payments(txs: list[Transaction], min_months: int = 2) -> dict:
    """fixed  = same payee, lagbhag same amount, ~mahine mein ek baar (subscription/EMI).
    habits = payee ko baar-baar payment, alag amounts (pharmacy, canteen...)."""
    groups: dict[str, list[Transaction]] = defaultdict(list)
    for t in _spend(txs):
        if t.kind == "p2p" or t.narration.startswith("Automatic payment of"):
            continue  # p2p = insaan; "Automatic payment of Rs.. setup" = mandate ke test debits
        groups[(t.merchant or t.narration).strip().lower()].append(t)

    fixed, habits = [], []
    for name, items in groups.items():
        months = {t.date.strftime("%Y-%m") for t in items}
        amounts = [t.amount for t in items]
        mean = statistics.mean(amounts)
        cv = statistics.pstdev(amounts) / mean if mean else 1   # amounts kitne ek jaise hain
        row = {"merchant": items[0].merchant, "category": items[0].category,
               "payments": len(items), "months": len(months),
               "typical_amount": round(statistics.median(amounts), 2),
               "total": round(sum(amounts), 2)}
        monthly_like = len(items) <= len(months) * 1.5   # ~mahine mein ek baar; 2x/mahina = habit
        if (len(months) >= min_months and len(items) >= 2 and cv <= 0.10
                and monthly_like and mean >= MIN_FIXED_AMOUNT):
            fixed.append(row)
        elif len(items) >= 4:
            habits.append(row)
    return {"fixed": sorted(fixed, key=lambda r: -r["typical_amount"]),
            "habits": sorted(habits, key=lambda r: -r["total"])}


# ---------- monthly trend / overspending ----------

def monthly_trend(txs: list[Transaction], min_abs: float = 500, min_pct: float = 25) -> dict:
    """Sabse naye POORE mahine ko pehle ke poore mahinon ke average se compare karta hai.
    Adhoore mahine ignore hote hain, warna wo 'savings' jaise dikhte hain."""
    full = coverage(txs)["full_months"]
    if len(full) < 2:
        return {"months": full, "flags": [], "note": "Need at least 2 full months for a trend."}

    table: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for t in _spend(txs):
        m = t.date.strftime("%Y-%m")
        if m in full and t.kind != "p2p":
            table[t.category or "Uncategorized"][m] += t.amount

    latest, earlier = full[-1], full[:-1]

    # har category ka sabse bada payment (spike ki wajah batane ke liye)
    biggest: dict[str, Transaction] = {}
    for t in _spend(txs):
        if t.kind != "p2p" and t.date.strftime("%Y-%m") == latest:
            c = t.category or "Uncategorized"
            if c not in biggest or t.amount > biggest[c].amount:
                biggest[c] = t

    flags = []
    for cat, by_m in table.items():
        base = statistics.mean(by_m.get(m, 0.0) for m in earlier)
        now = by_m.get(latest, 0.0)
        diff = now - base
        pct = (diff / base * 100) if base else (100.0 if now else 0.0)
        if diff >= min_abs and pct >= min_pct:
            flags.append({"category": cat, "latest_month": latest, "latest": round(now, 2),
                          "earlier_avg": round(base, 2), "increase": round(diff, 2),
                          "increase_pct": round(pct, 1),
                          "largest_payment": {"merchant": biggest[cat].merchant,
                                              "amount": biggest[cat].amount,
                                              "date": biggest[cat].date.isoformat()}})
    return {"months": full, "flags": sorted(flags, key=lambda f: -f["increase"])}


# ---------- averages, savings, investable amount ----------

def monthly_averages(txs: list[Transaction]) -> dict:
    """Poore statement ka average, har 30 din ke hisaab se (adhoore mahine bhi chalte hain)."""
    days = coverage(txs)["days"]
    by_cat: dict[str, float] = defaultdict(float)
    for t in _spend(txs):
        by_cat[t.category or "Uncategorized"] += t.amount
    per_month = {c: round(v / days * 30, 2) for c, v in by_cat.items()}

    groups: dict[str, float] = defaultdict(float)
    for c, v in per_month.items():
        groups[group_of(c)] += v
    return {"days": days,
            "by_category": dict(sorted(per_month.items(), key=lambda kv: -kv[1])),
            "by_group": {g: round(v, 2) for g, v in groups.items()},
            "total": round(sum(per_month.values()), 2)}


def savings_opportunities(txs: list[Transaction], cut_pct: float = 0.30) -> list[dict]:
    """What-if: har discretionary category ko cut_pct se kam karo toh kitna bachega."""
    avg = monthly_averages(txs)["by_category"]
    out = []
    for cat, monthly in avg.items():
        if cat in DISCRETIONARY and monthly > 0:
            out.append({"category": cat, "monthly_now": monthly, "cut_pct": int(cut_pct * 100),
                        "monthly_saving": round(monthly * cut_pct, 2),
                        "yearly_saving": round(monthly * cut_pct * 12, 2)})
    return sorted(out, key=lambda r: -r["yearly_saving"])


def investable_amount(txs: list[Transaction], monthly_income: float, buffer_pct: float = 0.20) -> dict:
    """surplus = income - average monthly outflow; surplus ka buffer_pct side mein rakho."""
    avg = monthly_averages(txs)
    outflow = avg["total"]
    surplus = monthly_income - outflow
    investable = max(0.0, surplus * (1 - buffer_pct))
    return {"monthly_income": monthly_income, "avg_monthly_outflow": outflow,
            "outflow_incl_p2p": True,
            "surplus": round(surplus, 2), "buffer_pct": int(buffer_pct * 100),
            "investable_per_month": round(investable, 2),
            "assumptions": ["Income is user-provided, not read from the statement.",
                            "Outflow includes P2P transfers (their purpose is unknown).",
                            "Emergency fund and loans are not considered yet."]}


def build_insights(txs: list[Transaction], monthly_income: float | None = None) -> dict:
    """Sab insights ek jagah. Chatbot ka tool yahi call karega."""
    res = {"coverage": coverage(txs), "averages": monthly_averages(txs),
           "recurring": recurring_payments(txs), "trend": monthly_trend(txs),
           "savings": savings_opportunities(txs)}
    if monthly_income:
        res["investable"] = investable_amount(txs, monthly_income)
    return res
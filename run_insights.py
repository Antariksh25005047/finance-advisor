"""Usage:  python run_insights.py data\\sample\\paytm.xlsx [--income 15000]"""
import argparse

from app.analytics.insights import build_insights
from app.categorizer.pipeline import categorize
from app.parsers.paytm import parse_paytm


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--income", type=float, default=None, help="monthly income in Rs")
    args = ap.parse_args()

    txs = parse_paytm(args.path).transactions
    categorize(txs)
    r = build_insights(txs, args.income)

    c = r["coverage"]
    print(f"Statement: {c['first']} to {c['last']} ({c['days']} days), full months: {c['full_months']}")

    a = r["averages"]
    print(f"\nAverage per month (30 days): Rs {a['total']:,.0f}")
    for g, v in sorted(a["by_group"].items(), key=lambda kv: -kv[1]):
        print(f"  {g:<14}{v:>10,.0f}")

    print("\nFixed recurring payments (subscriptions / EMIs):")
    for x in r["recurring"]["fixed"]:
        print(f"  {x['merchant']:<45} Rs {x['typical_amount']:>9,.2f}  x{x['payments']} in {x['months']} months")

    print("\nFrequent payees (habits):")
    for x in r["recurring"]["habits"][:6]:
        print(f"  {x['merchant']:<45} Rs {x['total']:>9,.2f}  x{x['payments']}  [{x['category']}]")

    print("\nOverspending vs earlier months:")
    t = r["trend"]
    if not t["flags"]:
        print("  none flagged", t.get("note", ""))
    for f in t["flags"]:
        lp = f["largest_payment"]
        print(f"  {f['category']:<18} {f['earlier_avg']:>8,.0f} -> {f['latest']:>8,.0f}  (+{f['increase_pct']}%)"
              f"  biggest: Rs {lp['amount']:,.0f} to {lp['merchant']} on {lp['date']}")

    print("\nIf you cut discretionary spending by 30%:")
    for s in r["savings"][:5]:
        print(f"  {s['category']:<18} Rs {s['monthly_saving']:>7,.0f}/month = Rs {s['yearly_saving']:>8,.0f}/year")

    if "investable" in r:
        i = r["investable"]
        print(f"\nIncome Rs {i['monthly_income']:,.0f} - outflow Rs {i['avg_monthly_outflow']:,.0f} "
              f"= surplus Rs {i['surplus']:,.0f}; investable (after {i['buffer_pct']}% buffer): "
              f"Rs {i['investable_per_month']:,.0f}/month")
        for note in i["assumptions"]:
            print("  -", note)


if __name__ == "__main__":
    main()
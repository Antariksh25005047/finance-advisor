"""Usage:  python run_paytm.py path\\to\\Paytm_statement.xlsx"""
import sys
from collections import Counter

from app.analytics.summary import spending_summary
from app.categorizer.pipeline import categorize
from app.parsers.paytm import parse_paytm


def main(path: str) -> None:
    result = parse_paytm(path)
    txs = result.transactions
    print(f"Parsed {len(txs)} transactions, {len(result.warnings)} warnings")
    for w in result.warnings[:10]:
        print("  warning:", w)
    if not txs:
        return

    done, pending = categorize(txs)
    print(f"Categorized: {len(done)} | Pending (needs LLM): {len(pending)}")
    print("Decided by:", dict(Counter(t.category_source for t in done)))

    s = spending_summary(txs)
    print(f"\nTotal spent: Rs {s['total_spent']:,.2f} | Received: Rs {s['total_received']:,.2f}\n")
    print(f"{'Category':<20}{'Amount':>12}{'%':>8}")
    for cat, amt in s["by_category"].items():
        print(f"{cat:<20}{amt:>12,.2f}{s['by_category_pct'][cat]:>8}")

    if pending:
        print("\nUncategorized payees (top 10):")
        for name, n in Counter(t.merchant for t in pending).most_common(10):
            print(f"  {name}  x{n}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])

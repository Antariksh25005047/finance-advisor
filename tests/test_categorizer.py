from datetime import date
from app.parsers.base import Transaction
from app.categorizer.pipeline import categorize


def test_rules_categorize_known_merchants():
    txs = [
        Transaction(date=date(2026, 9, 1), amount=350, direction="debit",
                    narration="UPI/ZOMATO/xyz@okhdfc", source="phonepe"),
        Transaction(date=date(2026, 9, 2), amount=120, direction="debit",
                    narration="UPI/random shop/abc@ybl", source="phonepe"),
    ]
    done, pending = categorize(txs)
    assert done[0].category == "Food Delivery"
    assert len(pending) == 1

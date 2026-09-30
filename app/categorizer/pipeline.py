from app.parsers.base import Transaction
from .rules import categorize_by_rules


def categorize(transactions: list[Transaction]) -> tuple[list[Transaction], list[Transaction]]:
    """Returns (categorized, uncategorized). Uncategorized will go to the LLM later."""
    done, pending = [], []
    for tx in transactions:
        cat = categorize_by_rules(f"{tx.merchant or ''} {tx.narration}")
        if cat:
            tx.category = cat
            done.append(tx)
        else:
            pending.append(tx)
    return done, pending

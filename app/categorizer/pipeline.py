from app.parsers.base import Transaction
from .rules import TAG_TO_CATEGORY, categorize_by_rules


def categorize(transactions: list[Transaction]) -> tuple[list[Transaction], list[Transaction]]:
    """Returns (categorized, pending). Pending ones go to the LLM later.

    Priority: kind (self/p2p) -> keyword rules -> source app's tag -> pending.
    category_source records which step decided, for the "why this category?" answers.
    """
    done, pending = [], []
    for tx in transactions:
        if tx.kind == "self_transfer":
            tx.category, tx.category_source = "Self Transfer", "kind"
        elif tx.kind == "p2p":
            tx.category, tx.category_source = "Transfers (P2P)", "kind"
        else:
            cat = categorize_by_rules(f"{tx.merchant or ''} {tx.narration}")
            if cat:
                tx.category, tx.category_source = cat, "rule"
            elif tx.tag_hint and TAG_TO_CATEGORY.get(tx.tag_hint):
                tx.category, tx.category_source = TAG_TO_CATEGORY[tx.tag_hint], "paytm_tag"

        (done if tx.category else pending).append(tx)
    return done, pending

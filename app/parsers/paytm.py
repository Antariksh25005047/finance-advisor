"""Parser for the Paytm UPI statement (.xlsx, sheet "Passbook Payment History")."""
import re
from datetime import datetime

import pandas as pd

from .base import ParseResult, Transaction

SHEET = "Passbook Payment History"
REQUIRED = ["Date", "Transaction Details", "Amount"]

# (prefix in "Transaction Details", kind)
PREFIXES = [
    ("Paid to ", "merchant"),
    ("Money sent to ", "p2p"),
    ("Received from ", "p2p"),
    ("Transferred to Self", "self_transfer"),
    ("Refund for ", "merchant"),
    ("EMI for ", "merchant"),
    ("Automatic payment for ", "merchant"),
]


def _split_details(details: str) -> tuple[str, str]:
    """Returns (payee_name, kind)."""
    d = details.strip()
    m = re.search(r"Automatic payment of .*? setup for (.+)$", d)
    if m:
        return m.group(1).strip(), "merchant"
    for prefix, kind in PREFIXES:
        if d.startswith(prefix):
            return d[len(prefix):].strip(" ,"), kind
    return d, "merchant"


def _parse_amount(raw: str) -> tuple[float, str]:
    s = str(raw).strip().replace(",", "")
    direction = "credit" if s.startswith("+") else "debit"
    return abs(float(s.replace("+", "").replace("-", ""))), direction


def parse_paytm(path: str) -> ParseResult:
    try:
        df = pd.read_excel(path, sheet_name=SHEET, dtype=str)
    except ValueError:
        return ParseResult(transactions=[],
                           warnings=[f'Sheet "{SHEET}" not found. Is this a Paytm UPI statement?'])

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        return ParseResult(transactions=[], warnings=[f"Missing columns: {missing}"])

    txs: list[Transaction] = []
    warnings: list[str] = []
    for i, row in df.iterrows():
        try:
            d = datetime.strptime(str(row["Date"]).strip(), "%d/%m/%Y").date()
            amount, direction = _parse_amount(row["Amount"])
            details = str(row["Transaction Details"])
            payee, kind = _split_details(details)
            if kind == "self_transfer":
                direction = "debit"
            tag = row.get("Tags")
            tag = None if pd.isna(tag) else re.sub(r"^#\S+\s*", "", str(tag)).strip()
            txs.append(Transaction(
                date=d, amount=amount, direction=direction,
                narration=details, merchant=payee, kind=kind,
                tag_hint=tag, source="paytm",
            ))
        except Exception as e:  # keep going, report at the end
            warnings.append(f"Row {i + 2} skipped: {e}")
    return ParseResult(transactions=txs, warnings=warnings)

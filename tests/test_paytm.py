import pandas as pd

from app.categorizer.pipeline import categorize
from app.parsers.paytm import SHEET, parse_paytm

COLS = ["Date", "Time", "Transaction Details", "Your Account", "Amount",
        "Order ID", "Remarks", "Tags", "Comment"]


def _make_file(tmp_path):
    rows = [
        ["02/10/2026", "18:38:22", "Money sent to Test Person", "Bank - 11", "-500.00", None, None, "#💵 Money Transfer", None],
        ["01/10/2026", "10:00:00", "Paid to Swiggy Instamart", "Bank - 11", "-250.50", None, None, "#🛒 Groceries", None],
        ["30/09/2026", "10:00:00", "Paid to Some Random Shop", "Bank - 11", "-1,200.00", None, None, "#🔄 Miscellaneous", None],
        ["29/09/2026", "10:00:00", "Paid to Green Chilli Cafe", "Bank - 11", "-60.00", None, None, "#🛒 Groceries", None],
        ["28/09/2026", "10:00:00", "Received from Another Person", "Bank - 11", "+3,000.00", None, None, "#💵 Money Received", None],
        ["27/09/2026", "10:00:00", "Transferred to Self, Bank - 22", "Bank - 11", "2,100.00", None, None, "#💵 Self Transfer", None],
        ["26/09/2026", "10:00:00", "Paid to Kolkata Sweets Corner", "Bank - 11", "-90.00", None, None, "#🥘 Food", None],
    ]
    path = tmp_path / "paytm.xlsx"
    pd.DataFrame(rows, columns=COLS).to_excel(path, sheet_name=SHEET, index=False)
    return str(path)


def test_parse_basic_fields(tmp_path):
    res = parse_paytm(_make_file(tmp_path))
    assert not res.warnings
    t = res.transactions
    assert len(t) == 7
    assert (t[0].kind, t[0].direction, t[0].amount) == ("p2p", "debit", 500.0)
    assert t[2].amount == 1200.0 and t[2].merchant == "Some Random Shop"
    assert t[4].direction == "credit" and t[4].amount == 3000.0
    assert t[5].kind == "self_transfer"
    assert t[1].tag_hint == "Groceries"


def test_categorization_priority(tmp_path):
    txs = parse_paytm(_make_file(tmp_path)).transactions
    done, pending = categorize(txs)
    by_name = {t.merchant: t for t in done}
    assert by_name["Test Person"].category == "Transfers (P2P)"
    assert by_name["Swiggy Instamart"].category == "Food Delivery" or by_name["Swiggy Instamart"].category == "Groceries"
    # our keyword rule beats the app's wrong "Groceries" tag
    assert by_name["Green Chilli Cafe"].category == "Food"
    assert by_name["Green Chilli Cafe"].category_source == "rule"
    # word-boundary: "ola" must not match inside "Kolkata"; falls back to the app tag
    assert by_name["Kolkata Sweets Corner"].category == "Food"
    # vague tag -> pending for the LLM
    assert [t.merchant for t in pending] == ["Some Random Shop"]

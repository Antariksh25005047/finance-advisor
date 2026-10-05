import pandas as pd
from app.parsers.base import Transaction

def to_df(txs: list[Transaction]) -> pd.DataFrame:
    df = pd.DataFrame([t.model_dump() for t in txs])
    df["data"]= pd.to_datetime(df["date"])
    df["month"]= pd["date"].dt.to_period("M").astype(str)
    return df


def spending_summary(txs: list[Transaction]) -> dict:
    df = to_df(txs)
    debits = df[df["direction"] == "debit"]
    by_cat = debits.groupby("category")["amount"].sum().sort_values(ascending=False)
    monthly = debits.pivot_table(index="category", columns="month",
                                 values="amount", aggfunc="sum", fill_value=0)
    return {
        "total_spent": round(float(debits["amount"].sum()), 2),
        "by_category": by_cat.round(2).to_dict(),
        "monthly_by_category": monthly.round(2).to_dict("index"),
    }
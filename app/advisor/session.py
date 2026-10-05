"""Ek user ki poori conversation ka state + saare 'tools'.
Chatbot (LLM) sirf in methods ko call karega. Har method JSON-friendly dict lautata hai;
galti hone par exception nahi, {"error": CODE, "message": ...} taaki LLM user ko samjha sake."""
from pydantic import ValidationError

from app.analytics.insights import build_insights
from app.parsers.base import Transaction

from .allocation import build_allocation, split_amount
from .portfolio import PortfolioManager
from .profile import UserProfile
from .risk import compute_risk

PROFILE_FIELDS = list(UserProfile.model_fields)


def _err(code: str, message: str) -> dict:
    return {"error": code, "message": message}


class AdvisorSession:
    def __init__(self, transactions: list[Transaction] | None = None):
        self.txs = transactions or []
        self.profile_data: dict = {}
        self.manager: PortfolioManager | None = None

    # ---------- spending ----------
    def get_spending_insights(self) -> dict:
        if not self.txs:
            return _err("NO_STATEMENT", "No bank/UPI statement has been uploaded yet.")
        return build_insights(self.txs, self.profile_data.get("monthly_income"))

    # ---------- profile ----------
    def update_profile(self, **fields) -> dict:
        unknown = [k for k in fields if k not in PROFILE_FIELDS]
        if unknown:
            return _err("UNKNOWN_FIELD", f"Unknown fields {unknown}. Valid fields: {PROFILE_FIELDS}")
        candidate = {**self.profile_data, **fields}
        try:
            UserProfile.model_validate(candidate)
        except ValidationError as e:
            bad = [x for x in e.errors() if x["type"] != "missing"]   # "missing" = abhi poochna baaki hai
            if bad:
                return _err("INVALID_VALUE", "; ".join(f"{x['loc'][0]}: {x['msg']}" for x in bad))
        self.profile_data = candidate
        res = {"profile": dict(self.profile_data),
               "missing_fields": [f for f in PROFILE_FIELDS if f not in self.profile_data]}
        if self.manager is not None:
            res["note"] = ("Profile changed after the portfolio was built. Call build_portfolio "
                           "again to refresh the recommendation (this resets applied changes).")
        return res

    # ---------- portfolio ----------
    def build_portfolio(self) -> dict:
        missing = [f for f in PROFILE_FIELDS if f not in self.profile_data]
        if missing:
            return _err("MISSING_FIELDS", f"Still need: {missing}")
        p = UserProfile(**self.profile_data)
        risk = compute_risk(p)
        alloc = build_allocation(p, risk)
        self.manager = PortfolioManager(p, risk, alloc)
        return {"risk": risk.model_dump(), "weights": alloc.weights,
                "warnings": alloc.warnings, "allocation_trace": alloc.trace}

    def _need_portfolio(self) -> dict | None:
        return None if self.manager else _err("NO_PORTFOLIO", "Build a portfolio first.")

    def get_portfolio(self, monthly_amount: float | None = None) -> dict:
        if (e := self._need_portfolio()):
            return e
        res = {"weights": self.manager.current, "version": len(self.manager.versions)}
        if monthly_amount:
            res["monthly_amount_split"] = split_amount(self.manager.current, monthly_amount)
        return res

    def simulate_change(self, asset: str, value: int) -> dict:
        if (e := self._need_portfolio()):
            return e
        try:
            return self.manager.simulate(asset, value).model_dump()
        except ValueError as ex:
            return _err("INVALID_REQUEST", str(ex))

    def apply_change(self, simulation_id: str) -> dict:
        if (e := self._need_portfolio()):
            return e
        try:
            return {"weights": self.manager.apply(simulation_id), "version": len(self.manager.versions)}
        except ValueError as ex:
            return _err("INVALID_REQUEST", str(ex))

    def undo_change(self) -> dict:
        if (e := self._need_portfolio()):
            return e
        try:
            return {"weights": self.manager.undo(), "version": len(self.manager.versions)}
        except ValueError as ex:
            return _err("INVALID_REQUEST", str(ex))

    def explain_portfolio(self) -> dict:
        """'Ye allocation kyu?' ka asli logic: risk score aur allocation ke rule-trace."""
        if (e := self._need_portfolio()):
            return e
        p, r = self.manager.profile, self.manager.risk
        alloc = build_allocation(p, r)
        return {"risk_label": r.label, "risk_score": r.score,
                "risk_trace": r.trace, "allocation_trace": alloc.trace,
                "original_recommendation": self.manager.versions[0],
                "current": self.manager.current}
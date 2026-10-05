"""LLM ko dikhne wale tool schemas + dispatcher (name -> AdvisorSession method)."""
from app.advisor.session import AdvisorSession

ASSET_ENUM = ["equity", "debt", "gold", "liquid"]


def _fn(name: str, description: str, properties: dict | None = None, required: list[str] | None = None) -> dict:
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": properties or {}, "required": required or []},
    }}


TOOLS = [
    _fn("update_profile",
        "Save facts the user told you about themselves. Call it as soon as the user shares any of "
        "these fields; send only the fields they actually stated. Returns which fields are still missing.",
        {
            "age": {"type": "integer", "description": "Age in years (18+)"},
            "monthly_income": {"type": "number", "description": "Monthly income in INR"},
            "income_stability": {"type": "string", "enum": ["stable", "variable"]},
            "emergency_fund_months": {"type": "number", "description": "How many months of expenses are saved as emergency fund"},
            "has_high_interest_debt": {"type": "boolean", "description": "Credit card / BNPL / personal loan outstanding"},
            "investing_horizon_years": {"type": "number", "description": "For how many years the money can stay invested"},
            "market_drop_reaction": {"type": "string", "enum": ["sell", "hold", "buy_more"],
                                     "description": "What the user would do if their investments fell 20%"},
            "experience": {"type": "string", "enum": ["none", "some", "experienced"], "description": "Investing experience"},
        }),
    _fn("get_spending_insights",
        "Insights from the uploaded bank/UPI statement: monthly averages, recurring payments, "
        "overspending vs earlier months, savings what-ifs, and investable amount (if income is known)."),
    _fn("build_portfolio",
        "Create the recommended asset allocation. Only works once ALL profile fields are collected. "
        "Returns risk score, weights (equity/debt/gold/liquid), warnings and the rule trace."),
    _fn("get_portfolio",
        "Show the current portfolio weights. Optionally split a monthly amount (INR) across assets.",
        {"monthly_amount": {"type": "number", "description": "Monthly investment amount in INR"}}),
    _fn("simulate_change",
        "Calculate what the portfolio would look like if one asset's weight is changed. "
        "Does NOT apply it. Returns before/after, warnings and a simulation_id.",
        {"asset": {"type": "string", "enum": ASSET_ENUM},
         "value": {"type": "integer", "description": "New weight in percent (0-100)"}},
        ["asset", "value"]),
    _fn("apply_change",
        "Apply a previously simulated change. Only call after the user has explicitly confirmed "
        "in a message after seeing the simulation.",
        {"simulation_id": {"type": "string"}}, ["simulation_id"]),
    _fn("undo_change", "Undo the last applied change."),
    _fn("explain_portfolio",
        "Get the exact rules and inputs behind the risk score and the allocation. "
        "Use it for every 'why this?' or 'why not that?' question."),
]


def run_tool(session: AdvisorSession, name: str, args: dict) -> dict:
    try:
        if name == "update_profile":
            return session.update_profile(**args)
        if name == "get_spending_insights":
            return session.get_spending_insights()
        if name == "build_portfolio":
            return session.build_portfolio()
        if name == "get_portfolio":
            return session.get_portfolio(args.get("monthly_amount"))
        if name == "simulate_change":
            return session.simulate_change(str(args["asset"]), int(args["value"]))
        if name == "apply_change":
            return session.apply_change(str(args["simulation_id"]))
        if name == "undo_change":
            return session.undo_change()
        if name == "explain_portfolio":
            return session.explain_portfolio()
        return {"error": "UNKNOWN_TOOL", "message": f"No tool named {name}."}
    except (KeyError, TypeError, ValueError) as e:
        return {"error": "BAD_ARGUMENTS", "message": f"Could not run {name}: {e}"}
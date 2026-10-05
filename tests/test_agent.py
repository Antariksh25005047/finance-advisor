import json
from types import SimpleNamespace as NS

from app.advisor.session import AdvisorSession
from app.chat.agent import Agent
from app.chat.tools import TOOLS, run_tool

FULL = dict(age=20, monthly_income=15000, income_stability="stable", emergency_fund_months=6,
            has_high_interest_debt=False, investing_horizon_years=10,
            market_drop_reaction="hold", experience="some")


def call(id, name, args):
    return NS(id=id, function=NS(name=name, arguments=json.dumps(args)))


def reply(content=None, calls=None):
    return NS(choices=[NS(message=NS(content=content, tool_calls=calls))])


class FakeClient:
    """LLM ki jagah scripted replies: bina internet ke agent loop test hota hai."""
    def __init__(self, script):
        self.script = list(script)
        self.chat = NS(completions=NS(create=self._create))

    def _create(self, **kw):
        return self.script.pop(0)


def ready_session():
    s = AdvisorSession()
    s.update_profile(**FULL)
    s.build_portfolio()
    return s


def test_tool_schemas_match_session_methods():
    names = {t["function"]["name"] for t in TOOLS}
    assert names == {"update_profile", "get_spending_insights", "build_portfolio", "get_portfolio",
                     "simulate_change", "apply_change", "undo_change", "explain_portfolio"}
    assert run_tool(AdvisorSession(), "nope", {})["error"] == "UNKNOWN_TOOL"
    assert run_tool(AdvisorSession(), "simulate_change", {"asset": "gold"})["error"] == "BAD_ARGUMENTS"


def test_agent_runs_tool_then_answers():
    s = AdvisorSession()
    fake = FakeClient([reply(calls=[call("c1", "update_profile", {"age": 21})]),
                       reply(content="Got it, and your monthly income?")])
    out = Agent(s, client=fake).chat("I'm 21")
    assert out == "Got it, and your monthly income?" and s.profile_data["age"] == 21


def test_apply_in_same_turn_as_simulation_is_blocked():
    s = ready_session()
    fake = FakeClient([
        reply(calls=[call("c1", "simulate_change", {"asset": "gold", "value": 20})]),
        reply(calls=[call("c2", "apply_change", {"simulation_id": "sim_1"})]),   # LLM ne jaldbaazi ki
        reply(content="Here is the simulation. Do you want to apply it?")])
    seen = []
    Agent(s, client=fake).chat("make gold 20%", on_tool=lambda n, a, r: seen.append((n, r)))
    assert seen[1][1]["error"] == "CONFIRMATION_REQUIRED"
    assert s.get_portfolio()["weights"]["gold"] == 10        # kuch apply nahi hua


def test_apply_after_user_confirms_in_next_turn():
    s = ready_session()
    fake = FakeClient([
        reply(calls=[call("c1", "simulate_change", {"asset": "gold", "value": 20})]),
        reply(content="Apply this?"),
        reply(calls=[call("c2", "apply_change", {"simulation_id": "sim_1"})]),
        reply(content="Done.")])
    agent = Agent(s, client=fake)
    agent.chat("make gold 20%")
    agent.chat("yes")
    assert s.get_portfolio()["weights"]["gold"] == 20
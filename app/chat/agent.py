import json

from app.advisor.session import AdvisorSession

from .prompt import SYSTEM_PROMPT
from .tools import TOOLS, run_tool

MAX_STEPS = 6   # ek user message ke liye max tool-call rounds


class Agent:
    def __init__(self, session: AdvisorSession, client=None, model: str | None = None):
        if client is None:
            from groq import Groq
            from app.config import GROQ_API_KEY, GROQ_MODEL
            client, model = Groq(api_key=GROQ_API_KEY), model or GROQ_MODEL
        self.session = session
        self.client = client
        self.model = model or "test-model"
        self.messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.turn = 0
        self._sim_turn: dict[str, int] = {}   # simulation_id -> kis turn mein bana

    def _execute(self, name: str, args: dict) -> dict:
        # code-level guardrail: simulate aur apply ek hi turn mein nahi ho sakte,
        # yaani user ko simulation dikhne ke baad naye message mein "haan" bolna padega.
        if name == "apply_change" and self._sim_turn.get(args.get("simulation_id"), self.turn) == self.turn:
            return {"error": "CONFIRMATION_REQUIRED",
                    "message": "Show the simulation to the user and wait for their explicit yes "
                               "in a new message before applying."}
        result = run_tool(self.session, name, args)
        if name == "simulate_change" and "simulation_id" in result:
            self._sim_turn[result["simulation_id"]] = self.turn
        return result

    def chat(self, user_text: str, on_tool=None) -> str:
        self.turn += 1
        self.messages.append({"role": "user", "content": user_text})
        for _ in range(MAX_STEPS):
            resp = self.client.chat.completions.create(
                model=self.model, messages=self.messages, tools=TOOLS,
                tool_choice="auto", temperature=0.2)
            msg = resp.choices[0].message
            if not msg.tool_calls:
                text = msg.content or ""
                self.messages.append({"role": "assistant", "content": text})
                return text

            self.messages.append({
                "role": "assistant", "content": msg.content or "",
                "tool_calls": [{"id": tc.id, "type": "function",
                                "function": {"name": tc.function.name,
                                             "arguments": tc.function.arguments}}
                               for tc in msg.tool_calls]})
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                result = self._execute(tc.function.name, args)
                if on_tool:
                    on_tool(tc.function.name, args, result)
                self.messages.append({"role": "tool", "tool_call_id": tc.id,
                                      "content": json.dumps(result, ensure_ascii=False, default=str)})
        return "Sorry, I got stuck while working on that. Could you rephrase or try again?"
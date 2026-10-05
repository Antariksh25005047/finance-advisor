"""Usage:  python chat_cli.py [data\\sample\\paytm.xlsx]"""
import sys

from app.advisor.session import AdvisorSession
from app.categorizer.pipeline import categorize
from app.chat.agent import Agent
from app.parsers.paytm import parse_paytm


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")   # Windows console par Rs/emoji ke liye
    txs = []
    if len(sys.argv) > 1:
        txs = parse_paytm(sys.argv[1]).transactions
        categorize(txs)
        print(f"Loaded {len(txs)} transactions from the statement.")

    agent = Agent(AdvisorSession(txs))
    print("Finance advisor (educational, not financial advice). Type 'exit' to quit.\n")
    while True:
        try:
            text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if text.lower() in ("exit", "quit"):
            break
        if not text:
            continue
        reply = agent.chat(text, on_tool=lambda n, a, r: print(f"  [tool] {n}({a})"))
        print(f"\nBot: {reply}\n")


if __name__ == "__main__":
    main()
"""Checks: key kaam kar rahi hai? kaunse models available hain? chhota sa test call."""
import sys

from groq import Groq

from app.config import GROQ_API_KEY, GROQ_MODEL

if not GROQ_API_KEY:
    sys.exit("GROQ_API_KEY not found. Check your .env file in the project root.")

client = Groq(api_key=GROQ_API_KEY)

ids = sorted(m.id for m in client.models.list().data)
print("Models available on your account:")
for i in ids:
    print("  ", i)

print(f"\nUsing GROQ_MODEL = {GROQ_MODEL}")
if GROQ_MODEL not in ids:
    print("WARNING: this model is not in the list above. Change GROQ_MODEL in .env.")

resp = client.chat.completions.create(
    model=GROQ_MODEL,
    messages=[{"role": "user", "content": "Say hi in one short Hinglish sentence."}],
    max_tokens=40,
)
print("\nModel replied:", resp.choices[0].message.content)
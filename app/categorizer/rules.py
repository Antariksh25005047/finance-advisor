import re

# Patterns are matched on word boundaries, so "ola" will NOT match "Kolkata".
CATEGORY_PATTERNS: list[tuple[str, list[str]]] = [
    # order matters: first match wins
    ("Credit & EMI", ["pay later", "snapmint", "emi", "simpl", "lazypay", "kreditbee", "slice"]),
    ("Food Delivery", ["zomato", "swiggy", "eatsure"]),
    ("Groceries", ["blinkit", "zepto", "bigbasket", "instamart", "dmart", "departmental",
                   "depatmental", "provisional", "provision", "kirana", "supermarket"]),
    ("Food", ["cafe", "restaurant", "dhaba", "canteen", "bakery", "sweets", "pizza",
              "burger", "juice", "chai", "momos", "biryani", "hotel"]),
    ("Transport", ["uber", "ola", "rapido", "irctc", "redbus", "metro", "dmrc", "ncrtc",
                   "road transport", "roadways", "train", "national capital reg"]),
    ("Subscriptions", ["netflix", "spotify", "hotstar", "prime video", "youtube", "apple",
                       "hiastro", "google play"]),
    ("Vending Machines", ["justvend"]),
    ("Personal Care", ["laundry", "salon", "saloon", "barber"]),
    ("Shopping", ["amazon", "flipkart", "myntra", "ajio", "meesho"]),
    ("Bills & Recharge", ["jio", r"airtel(?! payments bank)", "vodafone", "vi", "electricity",
                          "bescom", "recharge"]),
    ("Investments", ["zerodha", "groww", "upstox", "mutual fund", "sip", "nippon"]),
    ("Rent", ["rent"]),
    ("Health", ["pharmacy", "davaindia", "apollo", "1mg", "pharmeasy", "hospital", "clinic",
                "medical", "medicos", "diagnostic"]),
    ("Entertainment", ["bookmyshow", "pvr", "inox"]),
]

_COMPILED = [
    (cat, re.compile(r"\b(?:" + "|".join(words) + r")\b", re.IGNORECASE))
    for cat, words in CATEGORY_PATTERNS
]

# Fallback: the app's own tag (Paytm) -> our category. None = too vague, send to LLM.
TAG_TO_CATEGORY: dict[str, str | None] = {
    "Food": "Food",
    "Groceries": "Groceries",
    "Travel": "Transport",
    "Taxi": "Transport",
    "Medical": "Health",
    "Shopping": "Shopping",
    "Fuel": "Fuel",
    "Bill Payments": "Bills & Recharge",
    "Entertainment": "Entertainment",
    "Financial Services": "Financial",
    "Financial": "Financial",
    "Services": None,
    "Miscellaneous": None,
    "Refund": "Refund",
}


def categorize_by_rules(text: str) -> str | None:
    for category, pattern in _COMPILED:
        if pattern.search(text):
            return category
    return None

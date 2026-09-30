CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Food Delivery": ["zomato", "swiggy", "eatsure"],
    "Groceries": ["blinkit", "zepto", "bigbasket", "instamart", "dmart"],
    "Transport": ["uber", "ola", "rapido", "irctc", "redbus", "metro"],
    "Subscriptions": ["netflix", "spotify", "hotstar", "prime", "youtube", "apple"],
    "Shopping": ["amazon", "flipkart", "myntra", "ajio", "meesho"],
    "Bills & Recharge": ["jio", "airtel", "vi ", "electricity", "bescom", "recharge"],
    "Investments": ["zerodha", "groww", "upstox", "mutual fund", "sip"],
    "Rent": ["rent"],
    "Health": ["pharmacy", "apollo", "1mg", "pharmeasy", "hospital"],
}


def categorize_by_rules(text: str) -> str | None:
    t = text.lower()
    for category, words in CATEGORY_KEYWORDS.items():
        if any(w in t for w in words):
            return category
    return None
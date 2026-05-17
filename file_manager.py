ACCOUNTS_FILE = "accounts.txt"
CARDS_FILE = "cards.txt"

# ═══ الحسابات ═══

def load_accounts():
    accounts = []
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        email, password = parts
                        accounts.append({
                            "email": email.strip(),
                            "password": password.strip()
                        })
    except FileNotFoundError:
        open(ACCOUNTS_FILE, "w").close()
    return accounts

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        for acc in accounts:
            f.write(f"{acc['email']}:{acc['password']}\n")

def add_account(email, password):
    accounts = load_accounts()
    for acc in accounts:
        if acc["email"] == email:
            return False  # موجود مسبقاً
    accounts.append({"email": email, "password": password})
    save_accounts(accounts)
    return True

def delete_account(email):
    accounts = load_accounts()
    new_accounts = [a for a in accounts if a["email"] != email]
    if len(new_accounts) == len(accounts):
        return False
    save_accounts(new_accounts)
    return True

# ═══ البطاقات ═══

def load_cards():
    cards = []
    try:
        with open(CARDS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "|" in line:
                    parts = line.split("|")
                    if len(parts) == 4:
                        number, month, year, cvv = parts
                        cards.append({
                            "number": number.strip(),
                            "month": month.strip(),
                            "year": year.strip(),
                            "cvv": cvv.strip(),
                            "expiry": f"{month.strip()}/{year.strip()}"
                        })
    except FileNotFoundError:
        open(CARDS_FILE, "w").close()
    return cards

def save_cards(cards):
    with open(CARDS_FILE, "w", encoding="utf-8") as f:
        for card in cards:
            f.write(f"{card['number']}|{card['month']}|{card['year']}|{card['cvv']}\n")

def add_card(number, month, year, cvv):
    cards = load_cards()
    for card in cards:
        if card["number"] == number:
            return False  # موجودة مسبقاً
    cards.append({
        "number": number,
        "month": month,
        "year": year,
        "cvv": cvv,
        "expiry": f"{month}/{year}"
    })
    save_cards(cards)
    return True

def delete_card(number):
    cards = load_cards()
    new_cards = [c for c in cards if c["number"] != number]
    if len(new_cards) == len(cards):
        return False
    save_cards(new_cards)
    return True

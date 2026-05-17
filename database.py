import json
import os

ACCOUNTS_FILE = "accounts.json"
CARDS_FILE = "cards.json"

# ═══ الحسابات ═══

def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        return {}
    with open(ACCOUNTS_FILE, "r") as f:
        return json.load(f)

def save_account(name, email, password):
    accounts = load_accounts()
    accounts[name] = {
        "email": email,
        "password": password
    }
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(accounts, f, ensure_ascii=False, indent=2)

def delete_account(name):
    accounts = load_accounts()
    if name in accounts:
        del accounts[name]
        with open(ACCOUNTS_FILE, "w") as f:
            json.dump(accounts, f, ensure_ascii=False, indent=2)
        return True
    return False

def get_all_accounts():
    return load_accounts()

# ═══ البطاقات ═══

def load_cards():
    if not os.path.exists(CARDS_FILE):
        return {}
    with open(CARDS_FILE, "r") as f:
        return json.load(f)

def save_card(name, number, expiry, cvv):
    cards = load_cards()
    cards[name] = {
        "number": number,
        "expiry": expiry,
        "cvv": cvv
    }
    with open(CARDS_FILE, "w") as f:
        json.dump(cards, f, ensure_ascii=False, indent=2)

def delete_card(name):
    cards = load_cards()
    if name in cards:
        del cards[name]
        with open(CARDS_FILE, "w") as f:
            json.dump(cards, f, ensure_ascii=False, indent=2)
        return True
    return False

def get_all_cards():
    return load_cards()

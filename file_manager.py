import os

ACCOUNTS_FILE = "accounts.txt"
CARDS_FILE = "cards.txt"

# ═══════════════════════════
#        الحسابات
# ═══════════════════════════

def load_accounts():
    accounts = {}
    if not os.path.exists(ACCOUNTS_FILE):
        return accounts
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split("|")
                if len(parts) == 3:
                    name, email, password = parts
                    accounts[name] = {
                        "email": email,
                        "password": password
                    }
    return accounts

def save_account(name, email, password):
    accounts = load_accounts()
    accounts[name] = {"email": email, "password": password}
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        for n, data in accounts.items():
            f.write(f"{n}|{data['email']}|{data['password']}\n")

def delete_account(name):
    accounts = load_accounts()
    if name in accounts:
        del accounts[name]
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            for n, data in accounts.items():
                f.write(f"{n}|{data['email']}|{data['password']}\n")
        return True
    return False

def get_all_accounts():
    return load_accounts()

# ═══════════════════════════
#        البطاقات
# ═══════════════════════════

def load_cards():
    cards = {}
    if not os.path.exists(CARDS_FILE):
        return cards
    with open(CARDS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split("|")
                if len(parts) == 4:
                    name, number, expiry, cvv = parts
                    cards[name] = {
                        "number": number,
                        "expiry": expiry,
                        "cvv": cvv
                    }
    return cards

def save_card(name, number, expiry, cvv):
    cards = load_cards()
    cards[name] = {"number": number, "expiry": expiry, "cvv": cvv}
    with open(CARDS_FILE, "w", encoding="utf-8") as f:
        for n, data in cards.items():
            f.write(f"{n}|{data['number']}|{data['expiry']}|{data['cvv']}\n")

def delete_card(name):
    cards = load_cards()
    if name in cards:
        del cards[name]
        with open(CARDS_FILE, "w", encoding="utf-8") as f:
            for n, data in cards.items():
                f.write(f"{n}|{data['number']}|{data['expiry']}|{data['cvv']}\n")
        return True
    return False

def get_all_cards():
    return load_cards()

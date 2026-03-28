import os

BOT_TOKEN = "8590452175:AAGKpZiKBmneyxUX8Ac9U7w9cRjtWQYT8uU"
ADMIN_IDS = [8493522297]

COIN_NAME = "PAC"
CURRENCY = "PAC"

PAC_PRICE = 80
MIN_WITHDRAW_PAC = 250
PREMIUM_PRICE_PAC = 350
GAME_COMMISSION = 5

PAYMENT_METHODS = {
    "card": "Карта РФ",
    "sbp": "СБП"
}

YOUR_WALLETS = {
    "card": "2200 0000 0000 0000",
    "sbp": "+7 999 888 77 66"
}

MINE_LEVELS = {
    1: {"name": "⛏️ Каменная", "daily_output": 10, "upgrade_cost": 500, "icon": "🪨"},
    2: {"name": "⚒️ Угольная", "daily_output": 20, "upgrade_cost": 1500, "icon": "⚫"},
    3: {"name": "💎 Железная", "daily_output": 35, "upgrade_cost": 4000, "icon": "🔩"},
    4: {"name": "✨ Золотая", "daily_output": 60, "upgrade_cost": 10000, "icon": "⭐"},
    5: {"name": "💎 Алмазная", "daily_output": 100, "upgrade_cost": None, "icon": "💎"},
}
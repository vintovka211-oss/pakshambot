import os

BOT_TOKEN = "8590452175:AAGKpZiKBmneyxUX8Ac9U7w9cRjtWQYT8uU"
ADMIN_IDS = [8493522297]

COIN_NAME = "PAC"
CURRENCY = "₽"

PAC_PRICE = 100
PAC_TO_RUB_RATE = 0.32
MIN_WITHDRAW_PAC = 250
PREMIUM_PRICE_PAC = 350
PREMIUM_PRICE_RUB = 350
GAME_COMMISSION = 5

LOTTERY_TICKET_PRICE = 50
LOTTERY_COMMISSION = 20

TOURNAMENT_ENTRY_FEE = 100
TOURNAMENT_COMMISSION = 20

PAYMENT_METHODS = {
    "card": "Карта РФ",
    "crypto": "USDT (TRC20)"
}

YOUR_WALLETS = {
    "card": "2200 0000 0000 0000",
    "crypto": "TXhjUqkqZxXxXxXxXxXxXxXxXxXxXx"
}

RANKS = {
    0: {"name": "Новичок", "cashback": 1, "icon": "🟤", "min_donate": 0},
    1000: {"name": "Рекрут", "cashback": 2, "icon": "⚪", "min_donate": 0},
    5000: {"name": "Боец", "cashback": 3, "icon": "🔵", "min_donate": 0},
    10000: {"name": "Ветеран", "cashback": 4, "icon": "🟢", "min_donate": 0},
    50000: {"name": "Элит", "cashback": 5, "icon": "🟠", "min_donate": 500},
    100000: {"name": "Легенда", "cashback": 6, "icon": "🔴", "min_donate": 1000},
}

MONTHLY_FREE_LIMITS = {"regular": 100, "premium": 200}

MINE_LEVELS = {
    1: {"name": "⛏️ Каменная", "daily_output": 3.33, "monthly_output": 100, "upgrade_cost": 500, "icon": "🪨"},
    2: {"name": "⚒️ Угольная", "daily_output": 6.66, "monthly_output": 200, "upgrade_cost": 1500, "icon": "⚫"},
    3: {"name": "💎 Железная", "daily_output": 10, "monthly_output": 300, "upgrade_cost": 4000, "icon": "🔩"},
    4: {"name": "✨ Золотая", "daily_output": 16.66, "monthly_output": 500, "upgrade_cost": 10000, "icon": "⭐"},
    5: {"name": "💎 Алмазная", "daily_output": 33.33, "monthly_output": 1000, "upgrade_cost": 25000, "icon": "💎"},
    6: {"name": "👑 Изумрудная", "daily_output": 66.66, "monthly_output": 2000, "upgrade_cost": 50000, "icon": "🟢"},
    7: {"name": "🌌 Космическая", "daily_output": 166.66, "monthly_output": 5000, "upgrade_cost": None, "icon": "🌠"},
}
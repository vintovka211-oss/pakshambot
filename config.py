import os

# ==================== ТОКЕН БОТА ====================
BOT_TOKEN = "8593186262:AAGN6sTyBa1RlJ0eVWwNVzgYUb6aVy_H9LA"

# ID администраторов (ваш ID)
ADMIN_IDS = [8493522297]

# ==================== ВАЛЮТЫ ====================
COIN_NAME = "PAC"
CURRENCY = "₽"

# ==================== ЭКОНОМИКА ====================
PAC_PRICE = 100  # 100 PAC = 100₽
PAC_TO_RUB_RATE = 0.32  # 1 PAC = 0.32₽ при выводе (68% комиссия)
WITHDRAW_COMMISSION = 68

MIN_DONATION = 100
MAX_DONATION = 50000
MIN_WITHDRAW_PAC = 250
MIN_WITHDRAW_RUB = 80

GAME_COMMISSION = 5

# ==================== МЕСЯЧНЫЕ ЛИМИТЫ ХАЛЯВЫ ====================
MONTHLY_FREE_LIMITS = {
    "regular": 100,   # обычные: 100 PAC/месяц
    "premium": 200    # премиум: 200 PAC/месяц
}

DAILY_FREE_LIMITS = {
    "regular": 3.33,
    "premium": 6.66
}

FREE_SOURCES = {
    "daily_bonus": {"regular": 3, "premium": 7, "description": "Ежедневный бонус"},
    "referral": {"regular": 5, "premium": 10, "description": "Рефералы"},
    "mine": {"regular": 0, "premium": 999999, "description": "Шахта"}
}

# ==================== ШАХТА ====================
MINE_LEVELS = {
    1: {
        "name": "⛏️ Каменная шахта",
        "cost": 0,
        "daily_output": 3.33,
        "monthly_output": 100,
        "upgrade_cost": 500,
        "upgrade_time": 86400,
        "icon": "🪨",
        "description": "Начальный уровень. Приносит 100 PAC/месяц"
    },
    2: {
        "name": "⚒️ Угольная шахта",
        "cost": 500,
        "daily_output": 6.66,
        "monthly_output": 200,
        "upgrade_cost": 1500,
        "upgrade_time": 172800,
        "icon": "⚫",
        "description": "Приносит 200 PAC/месяц"
    },
    3: {
        "name": "💎 Железная шахта",
        "cost": 2000,
        "daily_output": 10,
        "monthly_output": 300,
        "upgrade_cost": 4000,
        "upgrade_time": 259200,
        "icon": "🔩",
        "description": "Приносит 300 PAC/месяц"
    },
    4: {
        "name": "✨ Золотая шахта",
        "cost": 6000,
        "daily_output": 16.66,
        "monthly_output": 500,
        "upgrade_cost": 10000,
        "upgrade_time": 345600,
        "icon": "⭐",
        "description": "Приносит 500 PAC/месяц"
    },
    5: {
        "name": "💎 Алмазная шахта",
        "cost": 16000,
        "daily_output": 33.33,
        "monthly_output": 1000,
        "upgrade_cost": 25000,
        "upgrade_time": 432000,
        "icon": "💎",
        "description": "Приносит 1000 PAC/месяц"
    },
    6: {
        "name": "👑 Изумрудная шахта",
        "cost": 41000,
        "daily_output": 66.66,
        "monthly_output": 2000,
        "upgrade_cost": 50000,
        "upgrade_time": 518400,
        "icon": "🟢",
        "description": "Приносит 2000 PAC/месяц"
    },
    7: {
        "name": "🌌 Космическая шахта",
        "cost": 91000,
        "daily_output": 166.66,
        "monthly_output": 5000,
        "upgrade_cost": None,
        "upgrade_time": None,
        "icon": "🌠",
        "description": "Максимальный уровень! Приносит 5000 PAC/месяц"
    }
}

MINE_MAX_LEVEL = 7
MINE_COLLECT_COOLDOWN = 86400

# ==================== БОНУСЫ ЗА ДОНАТЫ ====================
FIRST_DONATION_BONUS = 20

LARGE_DONATION_BONUSES = {
    1000: 10,
    5000: 15,
    10000: 20,
    25000: 25,
    50000: 30
}

VIP_DONATION_THRESHOLD = 2000

VIP_BENEFITS = {
    "cashback": 10,
    "mine_bonus": 20,
    "daily_bonus": 30,
    "withdraw_priority": True,
    "marketplace_discount": 15,
    "lottery_tickets": 5
}

# ==================== ПРЕМИУМ ====================
PREMIUM_PRICE_RUB = 350
PREMIUM_PRICE_PAC = 350

PREMIUM_BENEFITS = {
    "cashback_bonus": 5,
    "daily_bonus": 7,
    "tournament_discount": 20,
    "lottery_tickets": 2,
    "marketplace_discount": 10,
    "cashback_on_purchases": 5,
    "monthly_free_limit": 200,
    "withdraw_priority": True,
    "mine_access": True,
    "no_ads": True
}

# ==================== ЛОТЕРЕЯ ====================
LOTTERY_TICKET_PRICE = 50
LOTTERY_COMMISSION = 20
LOTTERY_MIN_TICKETS = 10
LOTTERY_AUTO_DRAW_DAYS = 7

# ==================== ТУРНИРЫ ====================
TOURNAMENT_ENTRY_FEE = 100
TOURNAMENT_COMMISSION = 20
TOURNAMENT_PRIZE_PLACES = [50, 30, 20]

# ==================== КЛАНЫ ====================
CLAN_CREATE_PRICE = 500
CLAN_MAX_MEMBERS = 50

# ==================== МАРКЕТПЛЕЙС ====================
MARKETPLACE_COMMISSION = 10
PREMIUM_MARKETPLACE_COMMISSION = 5

# ==================== РАНГИ ====================
RANKS = {
    0: {"name": "Новичок", "cashback": 1, "icon": "🟤", "min_donate": 0},
    1000: {"name": "Рекрут", "cashback": 2, "icon": "⚪", "min_donate": 0},
    5000: {"name": "Боец", "cashback": 3, "icon": "🔵", "min_donate": 0},
    10000: {"name": "Ветеран", "cashback": 4, "icon": "🟢", "min_donate": 0},
    50000: {"name": "Элит", "cashback": 5, "icon": "🟠", "min_donate": 500},
    100000: {"name": "Легенда", "cashback": 6, "icon": "🔴", "min_donate": 1000},
    500000: {"name": "Мастер", "cashback": 7, "icon": "🟣", "min_donate": 5000},
    1000000: {"name": "Грандмастер", "cashback": 8, "icon": "💎", "min_donate": 10000},
    5000000: {"name": "Император", "cashback": 10, "icon": "👑", "min_donate": 50000},
}

# ==================== ПЛАТЕЖИ ====================
PAYMENT_METHODS = {
    "card": "Карта РФ",
    "crypto": "USDT (TRC20)",
    "qiwi": "QIWI",
    "yoomoney": "ЮMoney"
}

YOUR_WALLETS = {
    "card": "2200 0000 0000 0000",
    "crypto": "TXhjUqkqZxXxXxXxXxXxXxXxXxXxXx",
    "qiwi": "+79991234567",
    "yoomoney": "4100123456789"
}

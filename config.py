import os

BOT_TOKEN = "8590452175:AAGKpZiKBmneyxUX8Ac9U7w9cRjtWQYT8uU"
ADMIN_IDS = [8493522297]

COIN_NAME = "PAC"
BONUS_PAC = 100
PREMIUM_PRICE_PAC = 350

# Кнопки ставок
BET_BUTTONS = [1, 5, 10, 25, 50, 100, 250, 500]

# Маркетплейс
MARKETPLACE_ITEMS = {
    "gold_card": {"name": "🏆 Золотая карта", "price": 500, "emoji": "🏆", "description": "+5% к выигрышу на 7 дней"},
    "diamond_card": {"name": "💎 Алмазная карта", "price": 1500, "emoji": "💎", "description": "+15% к выигрышу на 30 дней"},
    "lucky_coin": {"name": "🍀 Счастливая монета", "price": 200, "emoji": "🍀", "description": "Увеличивает шанс на 10%"},
    "mystery_box": {"name": "🎁 Тайный сундук", "price": 100, "emoji": "🎁", "description": "Случайный бонус от 50 до 500 PAC"},
    "vip_pass": {"name": "👑 VIP пропуск", "price": 3000, "emoji": "👑", "description": "Доступ к VIP-играм"},
    "four_leaf": {"name": "🍀 Четырёхлистный клевер", "price": 800, "emoji": "🍀", "description": "Шанс на выигрыш +15%"},
    "rabbit_foot": {"name": "🐰 Кроличья лапка", "price": 1200, "emoji": "🐰", "description": "Удача +20% на 14 дней"},
}

MINE_LEVELS = {
    1: {"name": "⛏️ Каменная", "daily_output": 10, "upgrade_cost": 500, "icon": "🪨"},
    2: {"name": "⚒️ Угольная", "daily_output": 20, "upgrade_cost": 1500, "icon": "⚫"},
    3: {"name": "🔩 Железная", "daily_output": 35, "upgrade_cost": 4000, "icon": "🔩"},
    4: {"name": "⭐ Золотая", "daily_output": 60, "upgrade_cost": 10000, "icon": "⭐"},
    5: {"name": "💎 Алмазная", "daily_output": 100, "upgrade_cost": 20000, "icon": "💎"},
    6: {"name": "👑 Изумрудная", "daily_output": 150, "upgrade_cost": 40000, "icon": "🟢"},
    7: {"name": "🌌 Космическая", "daily_output": 250, "upgrade_cost": None, "icon": "🌠"},
}

SBP_PHONE = "+7 999 888 77 66"

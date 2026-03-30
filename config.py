import os

BOT_TOKEN = "8590452175:AAGKpZiKBmneyxUX8Ac9U7w9cRjtWQYT8uU"
ADMIN_IDS = [8493522297]

COIN_NAME = "PAC"
RPG_COIN_NAME = "🪙 RPG"
BONUS_PAC = 100
PREMIUM_PRICE_PAC = 350

RPG_TO_PAC_RATE = 100
BET_BUTTONS = [1, 5, 10, 25, 50, 100, 250, 500]

SBP_PHONE = "+7 999 888 77 66"

# ==================== ИНСТРУМЕНТЫ ДЛЯ ДОБЫЧИ ====================
TOOLS = {
    1: {"name": "🪓 Каменная кирка", "level": 1, "price": 0, "icon": "🪓", "can_mine": ["common"]},
    2: {"name": "⛏️ Железная кирка", "level": 2, "price": 100, "icon": "⛏️", "can_mine": ["common", "rare"]},
    3: {"name": "💎 Алмазная кирка", "level": 3, "price": 500, "icon": "💎", "can_mine": ["common", "rare", "epic"]},
    4: {"name": "✨ Мифриловая кирка", "level": 4, "price": 2000, "icon": "✨", "can_mine": ["common", "rare", "epic", "legendary"]},
    5: {"name": "🌀 Древний бур", "level": 5, "price": 10000, "icon": "🌀", "can_mine": ["common", "rare", "epic", "legendary", "mythic"]},
    6: {"name": "🌌 Космический бур", "level": 6, "price": 50000, "icon": "🌌", "can_mine": ["common", "rare", "epic", "legendary", "mythic", "cosmic"]},
    7: {"name": "⚛️ Первобытный бур", "level": 7, "price": 200000, "icon": "⚛️", "can_mine": ["common", "rare", "epic", "legendary", "mythic", "cosmic", "primordial"]},
    8: {"name": "👁️ Бур вселенной", "level": 8, "price": 1000000, "icon": "👁️", "can_mine": ["common", "rare", "epic", "legendary", "mythic", "cosmic", "primordial", "eternal"]},
}

# ==================== РУДЫ (РАЗНЫЕ РЕСУРСЫ) ====================
ORES = {
    "stone": {"name": "🪨 Камень", "tier": "common", "base_time": 5, "icon": "🪨", "value": 1},
    "wood": {"name": "🪵 Древесина", "tier": "common", "base_time": 5, "icon": "🪵", "value": 1},
    "iron": {"name": "🔩 Железная руда", "tier": "common", "base_time": 8, "icon": "🔩", "value": 2},
    "silver": {"name": "🥈 Серебряная руда", "tier": "rare", "base_time": 15, "icon": "🥈", "value": 5},
    "gold": {"name": "🪙 Золотая руда", "tier": "rare", "base_time": 20, "icon": "🪙", "value": 10},
    "crystal": {"name": "💎 Кристалл", "tier": "epic", "base_time": 30, "icon": "💎", "value": 25},
    "mithril": {"name": "✨ Мифриловая руда", "tier": "epic", "base_time": 40, "icon": "✨", "value": 50},
    "dragon_scale": {"name": "🐉 Чешуя дракона", "tier": "legendary", "base_time": 60, "icon": "🐉", "value": 100},
    "phoenix_feather": {"name": "🕊️ Перо феникса", "tier": "legendary", "base_time": 90, "icon": "🕊️", "value": 150},
    "void_core": {"name": "🌌 Ядро пустоты", "tier": "mythic", "base_time": 120, "icon": "🌌", "value": 300},
    "star_dust": {"name": "✨ Звёздная пыль", "tier": "cosmic", "base_time": 180, "icon": "✨", "value": 500},
    "time_sand": {"name": "🕰️ Песок времени", "tier": "cosmic", "base_time": 240, "icon": "🕰️", "value": 800},
    "reality_fragment": {"name": "🌌 Осколок реальности", "tier": "primordial", "base_time": 360, "icon": "🌌", "value": 1500},
    "light_spark": {"name": "🌠 Искра света", "tier": "eternal", "base_time": 480, "icon": "🌠", "value": 3000},
}

# ==================== ПЕЩЕРЫ (БЕЗ ТРАТЫ HP) ====================
CAVES = {
    1: {"name": "🪨 Каменная пещера", "min_resources": 1, "max_resources": 3, "tiers": ["common"], "time_multiplier": 1, "required_tool": 1},
    2: {"name": "🪵 Лесная чаща", "min_resources": 2, "max_resources": 4, "tiers": ["common", "rare"], "time_multiplier": 1.2, "required_tool": 2},
    3: {"name": "🔥 Вулканическая пещера", "min_resources": 3, "max_resources": 6, "tiers": ["common", "rare", "epic"], "time_multiplier": 1.5, "required_tool": 3},
    4: {"name": "❄️ Ледяной грот", "min_resources": 5, "max_resources": 10, "tiers": ["rare", "epic", "legendary"], "time_multiplier": 2, "required_tool": 4},
    5: {"name": "🌌 Космическая бездна", "min_resources": 10, "max_resources": 20, "tiers": ["epic", "legendary", "mythic"], "time_multiplier": 3, "required_tool": 5},
    6: {"name": "🕰️ Храм времени", "min_resources": 20, "max_resources": 40, "tiers": ["legendary", "mythic", "cosmic"], "time_multiplier": 5, "required_tool": 6},
    7: {"name": "👁️ Сердце вселенной", "min_resources": 50, "max_resources": 100, "tiers": ["mythic", "cosmic", "primordial", "eternal"], "time_multiplier": 10, "required_tool": 7},
}

# ==================== БОССЫ, ОРУЖИЕ, БРОНЯ, АРТЕФАКТЫ, ИВЕНТЫ (остаются как были) ====================
# ... (все остальные настройки остаются без изменений)

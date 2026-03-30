import os

BOT_TOKEN = "8590452175:AAGKpZiKBmneyxUX8Ac9U7w9cRjtWQYT8uU"
ADMIN_IDS = [8493522297]

COIN_NAME = "PAC"
RPG_COIN_NAME = "🪙 RPG"
BONUS_PAC = 100
PREMIUM_PRICE_PAC = 350

RPG_TO_PAC_RATE = 100
MIN_BET = 10
BET_BUTTONS = [10, 25, 50, 100, 250, 500, 1000]

SBP_PHONE = "+7 999 888 77 66"

# CryptoBot настройки
CRYPTOBOT_API_KEY = "ВАШ_API_КЛЮЧ_ОТ_CRYPTOBOT"
CRYPTOBOT_SHOP_ID = "ВАШ_ID_МАГАЗИНА"

# ==================== ИГРЫ (КАК В WINPACO) ====================
SLOTS_SYMBOLS = ["🍒", "🍋", "🍊", "🍉", "⭐", "💎", "7️⃣"]
SLOTS_MULTIPLIERS = {
    ("7️⃣", "7️⃣", "7️⃣"): 10,
    ("💎", "💎", "💎"): 5,
    ("⭐", "⭐", "⭐"): 3,
    ("🍒", "🍒", "🍒"): 2,
    ("🍋", "🍋", "🍋"): 2,
    ("🍊", "🍊", "🍊"): 2,
    ("🍉", "🍉", "🍉"): 2,
}

DICE_MULTIPLIER = 5
COIN_MULTIPLIER = 1.8
ROULETTE_MULTIPLIER = 2
ROULETTE_GREEN_MULTIPLIER = 14

MINES_MULTIPLIERS = [1.15, 1.30, 1.50, 1.80, 2.20, 2.70, 3.30, 4.00, 5.00, 6.50, 8.50, 11.00, 15.00]
TOWER_MULTIPLIERS = [1.30, 1.80, 2.30, 3.00, 4.00, 5.50, 7.50, 10.00]

# ==================== КЛАНЫ ====================
CLAN_CREATE_PRICE = 1000
CLAN_MAX_MEMBERS = 50
CLAN_LEVELS = {
    1: {"name": "🪵 Новички", "exp_needed": 0, "bonus": 0, "icon": "🪵"},
    2: {"name": "🪨 Каменный клан", "exp_needed": 1000, "bonus": 5, "icon": "🪨"},
    3: {"name": "🔩 Железный клан", "exp_needed": 5000, "bonus": 10, "icon": "🔩"},
    4: {"name": "⭐ Золотой клан", "exp_needed": 20000, "bonus": 15, "icon": "⭐"},
    5: {"name": "💎 Алмазный клан", "exp_needed": 50000, "bonus": 20, "icon": "💎"},
    6: {"name": "✨ Мифриловый клан", "exp_needed": 100000, "bonus": 30, "icon": "✨"},
    7: {"name": "👑 Легендарный клан", "exp_needed": 250000, "bonus": 40, "icon": "👑"},
    8: {"name": "🌌 Космический клан", "exp_needed": 500000, "bonus": 50, "icon": "🌌"},
}

CLAN_BOSSES = {
    1: {"name": "🐉 Клановый дракон", "hp": 10000, "attack": 100, "reward": 500, "icon": "🐉", "min_level": 1},
    2: {"name": "👑 Клановый король", "hp": 50000, "attack": 300, "reward": 2000, "icon": "👑", "min_level": 3},
    3: {"name": "💀 Клановый демон", "hp": 200000, "attack": 1000, "reward": 10000, "icon": "💀", "min_level": 5},
    4: {"name": "🌌 Клановый титан", "hp": 1000000, "attack": 5000, "reward": 50000, "icon": "🌌", "min_level": 7},
}

# ==================== ИНСТРУМЕНТЫ ====================
TOOLS = {
    1: {"name": "🪓 Каменная кирка", "level": 1, "price": 0, "icon": "🪓", "can_mine": ["common"]},
    2: {"name": "⛏️ Железная кирка", "level": 2, "price": 100, "icon": "⛏️", "can_mine": ["common", "rare"]},
    3: {"name": "💎 Алмазная кирка", "level": 3, "price": 500, "icon": "💎", "can_mine": ["common", "rare", "epic"]},
    4: {"name": "✨ Мифриловая кирка", "level": 4, "price": 2000, "icon": "✨", "can_mine": ["common", "rare", "epic", "legendary"]},
    5: {"name": "🌀 Древний бур", "level": 5, "price": 10000, "icon": "🌀", "can_mine": ["common", "rare", "epic", "legendary", "mythic"]},
}

# ==================== РУДЫ ====================
ORES = {
    "stone": {"name": "🪨 Камень", "tier": "common", "icon": "🪨", "value": 1},
    "wood": {"name": "🪵 Древесина", "tier": "common", "icon": "🪵", "value": 1},
    "iron": {"name": "🔩 Железная руда", "tier": "common", "icon": "🔩", "value": 2},
    "silver": {"name": "🥈 Серебряная руда", "tier": "rare", "icon": "🥈", "value": 5},
    "gold": {"name": "🪙 Золотая руда", "tier": "rare", "icon": "🪙", "value": 10},
    "crystal": {"name": "💎 Кристалл", "tier": "epic", "icon": "💎", "value": 25},
    "mithril": {"name": "✨ Мифриловая руда", "tier": "epic", "icon": "✨", "value": 50},
    "dragon_scale": {"name": "🐉 Чешуя дракона", "tier": "legendary", "icon": "🐉", "value": 100},
}

# ==================== ПЕЩЕРЫ ====================
CAVES = {
    1: {"name": "🪨 Каменная пещера", "min_resources": 1, "max_resources": 3, "tiers": ["common"], "required_tool": 1},
    2: {"name": "🪵 Лесная чаща", "min_resources": 2, "max_resources": 4, "tiers": ["common", "rare"], "required_tool": 2},
    3: {"name": "🔥 Вулканическая пещера", "min_resources": 3, "max_resources": 6, "tiers": ["common", "rare", "epic"], "required_tool": 3},
    4: {"name": "❄️ Ледяной грот", "min_resources": 5, "max_resources": 10, "tiers": ["rare", "epic", "legendary"], "required_tool": 4},
    5: {"name": "🌌 Космическая бездна", "min_resources": 10, "max_resources": 20, "tiers": ["epic", "legendary", "mythic"], "required_tool": 5},
}

# ==================== БОССЫ ====================
BOSSES = {
    1: {"name": "🐀 Крысиный король", "hp": 50, "attack": 5, "rpg_reward": 5, "exp": 10, "icon": "🐀", "tier": "common", "min_level": 1},
    2: {"name": "🐺 Лесной волк", "hp": 100, "attack": 10, "rpg_reward": 10, "exp": 20, "icon": "🐺", "tier": "common", "min_level": 2},
    3: {"name": "🧟 Гоблин-шаман", "hp": 150, "attack": 15, "rpg_reward": 15, "exp": 30, "icon": "🧟", "tier": "common", "min_level": 3},
    4: {"name": "🐉 Огненный дракон", "hp": 200, "attack": 20, "rpg_reward": 20, "exp": 40, "icon": "🐉", "tier": "rare", "min_level": 5},
    5: {"name": "🧙 Тёмный маг", "hp": 300, "attack": 25, "rpg_reward": 30, "exp": 60, "icon": "🧙", "tier": "rare", "min_level": 7},
    6: {"name": "👑 Тёмный властелин", "hp": 500, "attack": 35, "rpg_reward": 50, "exp": 100, "icon": "👑", "tier": "rare", "min_level": 10},
    7: {"name": "💀 Повелитель смерти", "hp": 1000, "attack": 50, "rpg_reward": 100, "exp": 200, "icon": "💀", "tier": "epic", "min_level": 15},
    8: {"name": "👹 Демон хаоса", "hp": 1500, "attack": 70, "rpg_reward": 150, "exp": 300, "icon": "👹", "tier": "epic", "min_level": 20},
    9: {"name": "🐍 Гидра", "hp": 2000, "attack": 90, "rpg_reward": 200, "exp": 400, "icon": "🐍", "tier": "epic", "min_level": 25},
    10: {"name": "⚡ Бог грома", "hp": 3000, "attack": 120, "rpg_reward": 300, "exp": 600, "icon": "⚡", "tier": "legendary", "min_level": 30},
}

# ==================== ОРУЖИЕ ====================
WEAPONS = {
    1: {"name": "🗡️ Ржавый меч", "attack": 5, "price": 10, "icon": "🗡️", "tier": "common"},
    2: {"name": "⚔️ Стальной меч", "attack": 10, "price": 30, "icon": "⚔️", "tier": "common"},
    3: {"name": "🏹 Длинный лук", "attack": 15, "price": 60, "icon": "🏹", "tier": "common"},
    4: {"name": "🔨 Молот грома", "attack": 25, "price": 150, "icon": "🔨", "tier": "rare"},
    5: {"name": "✨ Меч света", "attack": 40, "price": 300, "icon": "✨", "tier": "rare"},
    6: {"name": "💀 Коса смерти", "attack": 60, "price": 600, "icon": "💀", "tier": "rare"},
    7: {"name": "👑 Экскалибур", "attack": 100, "price": 1500, "icon": "👑", "tier": "epic"},
}

# ==================== БРОНЯ ====================
ARMORS = {
    1: {"name": "🥾 Кожаная броня", "defense": 5, "price": 10, "icon": "🥾", "tier": "common"},
    2: {"name": "🛡️ Кольчуга", "defense": 10, "price": 30, "icon": "🛡️", "tier": "common"},
    3: {"name": "⚔️ Латы", "defense": 20, "price": 80, "icon": "⚔️", "tier": "common"},
    4: {"name": "✨ Магический доспех", "defense": 35, "price": 200, "icon": "✨", "tier": "rare"},
    5: {"name": "👑 Божественная броня", "defense": 60, "price": 500, "icon": "👑", "tier": "rare"},
    6: {"name": "🔥 Огненная броня", "defense": 90, "price": 1000, "icon": "🔥", "tier": "epic"},
}

# ==================== АРТЕФАКТЫ ====================
ARTIFACTS = {
    1: {"name": "🐺 Клык силы", "effect": "attack", "value": 10, "icon": "🐺", "tier": "common"},
    2: {"name": "🐀 Коготь скорости", "effect": "dodge", "value": 5, "icon": "🐀", "tier": "common"},
    3: {"name": "🍀 Амулет удачи", "effect": "crit_chance", "value": 10, "icon": "🍀", "tier": "rare"},
    4: {"name": "🔥 Сердце дракона", "effect": "hp", "value": 50, "icon": "🔥", "tier": "rare"},
    5: {"name": "📜 Посох тьмы", "effect": "attack", "value": 20, "icon": "📜", "tier": "epic"},
    6: {"name": "💍 Кольцо тьмы", "effect": "crit_damage", "value": 15, "icon": "💍", "tier": "epic"},
}

# ==================== ЗЕЛЬЯ ====================
POTIONS = {
    "small": {"name": "🍎 Малое зелье", "heal": 20, "price": 5, "icon": "🍎"},
    "medium": {"name": "🍯 Среднее зелье", "heal": 50, "price": 10, "icon": "🍯"},
    "large": {"name": "🧪 Большое зелье", "heal": 100, "price": 20, "icon": "🧪"},
}

# ==================== ИВЕНТЫ ====================
EVENTS = {
    "double_rpg": {"name": "🎉 Двойные RPG монеты!", "multiplier": 2, "duration": 24, "icon": "🎉"},
    "double_exp": {"name": "⭐ Двойной опыт!", "multiplier": 2, "duration": 24, "icon": "⭐"},
}

# ==================== ШАХТА ====================
MINE_LEVELS = {
    1: {"name": "⛏️ Каменная", "daily_output": 10, "upgrade_cost": 500, "icon": "🪨"},
    2: {"name": "⚒️ Угольная", "daily_output": 20, "upgrade_cost": 1500, "icon": "⚫"},
    3: {"name": "🔩 Железная", "daily_output": 35, "upgrade_cost": 4000, "icon": "🔩"},
    4: {"name": "🥈 Серебряная", "daily_output": 60, "upgrade_cost": 10000, "icon": "🥈"},
    5: {"name": "🪙 Золотая", "daily_output": 100, "upgrade_cost": 20000, "icon": "🪙"},
    6: {"name": "💎 Алмазная", "daily_output": 150, "upgrade_cost": 40000, "icon": "💎"},
    7: {"name": "✨ Мифриловая", "daily_output": 250, "upgrade_cost": 100000, "icon": "✨"},
}

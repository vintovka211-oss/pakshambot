import os

BOT_TOKEN = "8590452175:AAGKpZiKBmneyxUX8Ac9U7w9cRjtWQYT8uU"
ADMIN_IDS = [8493522297]

COIN_NAME = "PAC"
RPG_COIN_NAME = "🪙 RPG"
BONUS_PAC = 100
PREMIUM_PRICE_PAC = 350

RPG_TO_PAC_RATE = 100
BET_BUTTONS = [1, 5, 10, 25, 50, 100, 250, 500]

SBP_PHONE = "+7 927 668 55 12"

# ==================== БОССЫ (35 УРОВНЕЙ) ====================
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
    11: {"name": "❄️ Ледяной великан", "hp": 4000, "attack": 150, "rpg_reward": 400, "exp": 800, "icon": "❄️", "tier": "legendary", "min_level": 35},
    12: {"name": "🌋 Вулканический титан", "hp": 5000, "attack": 180, "rpg_reward": 500, "exp": 1000, "icon": "🌋", "tier": "legendary", "min_level": 40},
    13: {"name": "🌪️ Повелитель бурь", "hp": 6000, "attack": 200, "rpg_reward": 600, "exp": 1200, "icon": "🌪️", "tier": "mythic", "min_level": 45},
    14: {"name": "🕯️ Призрачный король", "hp": 8000, "attack": 250, "rpg_reward": 800, "exp": 1500, "icon": "🕯️", "tier": "mythic", "min_level": 50},
    15: {"name": "🐲 Древний дракон", "hp": 10000, "attack": 300, "rpg_reward": 1000, "exp": 2000, "icon": "🐲", "tier": "mythic", "min_level": 55},
    16: {"name": "👁️ Всевидящее око", "hp": 15000, "attack": 400, "rpg_reward": 1500, "exp": 3000, "icon": "👁️", "tier": "legend", "min_level": 60},
    17: {"name": "⚔️ Воин бездны", "hp": 20000, "attack": 500, "rpg_reward": 2000, "exp": 4000, "icon": "⚔️", "tier": "legend", "min_level": 65},
    18: {"name": "🌌 Космический дракон", "hp": 30000, "attack": 700, "rpg_reward": 3000, "exp": 6000, "icon": "🌌", "tier": "god", "min_level": 70},
    19: {"name": "💀 Аватар смерти", "hp": 50000, "attack": 1000, "rpg_reward": 5000, "exp": 10000, "icon": "💀", "tier": "god", "min_level": 75},
    20: {"name": "👑 Верховный бог", "hp": 100000, "attack": 1500, "rpg_reward": 10000, "exp": 20000, "icon": "👑", "tier": "god", "min_level": 80},
    21: {"name": "🌀 Хаос", "hp": 150000, "attack": 2000, "rpg_reward": 15000, "exp": 30000, "icon": "🌀", "tier": "chaos", "min_level": 85},
    22: {"name": "💎 Кристальный дракон", "hp": 200000, "attack": 2500, "rpg_reward": 20000, "exp": 40000, "icon": "💎", "tier": "chaos", "min_level": 90},
    23: {"name": "🌑 Тёмный бог", "hp": 300000, "attack": 3000, "rpg_reward": 30000, "exp": 60000, "icon": "🌑", "tier": "chaos", "min_level": 95},
    24: {"name": "✨ Создатель", "hp": 500000, "attack": 5000, "rpg_reward": 50000, "exp": 100000, "icon": "✨", "tier": "creator", "min_level": 100},
    25: {"name": "∞ Бесконечность", "hp": 1000000, "attack": 10000, "rpg_reward": 100000, "exp": 200000, "icon": "∞", "tier": "infinite", "min_level": 110},
    26: {"name": "🕰️ Хранитель времени", "hp": 2000000, "attack": 15000, "rpg_reward": 200000, "exp": 400000, "icon": "🕰️", "tier": "cosmic", "min_level": 120},
    27: {"name": "🌌 Архитектор реальности", "hp": 5000000, "attack": 25000, "rpg_reward": 500000, "exp": 1000000, "icon": "🌌", "tier": "cosmic", "min_level": 130},
    28: {"name": "⚛️ Первобытный хаос", "hp": 10000000, "attack": 50000, "rpg_reward": 1000000, "exp": 2000000, "icon": "⚛️", "tier": "primordial", "min_level": 140},
    29: {"name": "🌠 Изначальный свет", "hp": 25000000, "attack": 100000, "rpg_reward": 2500000, "exp": 5000000, "icon": "🌠", "tier": "primordial", "min_level": 150},
    30: {"name": "👁️ Око вселенной", "hp": 50000000, "attack": 200000, "rpg_reward": 5000000, "exp": 10000000, "icon": "👁️", "tier": "eternal", "min_level": 160},
}

# ==================== ОРУЖИЕ (30 УРОВНЕЙ) ====================
WEAPONS = {
    1: {"name": "🗡️ Ржавый меч", "attack": 5, "price": 10, "icon": "🗡️", "tier": "common"},
    2: {"name": "⚔️ Стальной меч", "attack": 10, "price": 30, "icon": "⚔️", "tier": "common"},
    3: {"name": "🏹 Длинный лук", "attack": 15, "price": 60, "icon": "🏹", "tier": "common"},
    4: {"name": "🔨 Молот грома", "attack": 25, "price": 150, "icon": "🔨", "tier": "rare"},
    5: {"name": "✨ Меч света", "attack": 40, "price": 300, "icon": "✨", "tier": "rare"},
    6: {"name": "💀 Коса смерти", "attack": 60, "price": 600, "icon": "💀", "tier": "rare"},
    7: {"name": "👑 Экскалибур", "attack": 100, "price": 1500, "icon": "👑", "tier": "epic"},
    8: {"name": "🔥 Пламенный клинок", "attack": 150, "price": 3000, "icon": "🔥", "tier": "epic"},
    9: {"name": "❄️ Ледяной меч", "attack": 200, "price": 5000, "icon": "❄️", "tier": "epic"},
    10: {"name": "⚡ Громовержец", "attack": 300, "price": 10000, "icon": "⚡", "tier": "legendary"},
    11: {"name": "🌌 Звёздный клинок", "attack": 450, "price": 20000, "icon": "🌌", "tier": "legendary"},
    12: {"name": "💎 Кристальный меч", "attack": 600, "price": 35000, "icon": "💎", "tier": "mythic"},
    13: {"name": "👁️ Око истины", "attack": 800, "price": 50000, "icon": "👁️", "tier": "mythic"},
    14: {"name": "🌌 Космический клинок", "attack": 1200, "price": 100000, "icon": "🌌", "tier": "legend"},
    15: {"name": "👑 Божественный меч", "attack": 2000, "price": 200000, "icon": "👑", "tier": "god"},
    16: {"name": "🌀 Меч хаоса", "attack": 3000, "price": 500000, "icon": "🌀", "tier": "chaos"},
    17: {"name": "💎 Кристальный меч", "attack": 5000, "price": 1000000, "icon": "💎", "tier": "chaos"},
    18: {"name": "🌑 Тьма", "attack": 8000, "price": 2000000, "icon": "🌑", "tier": "creator"},
    19: {"name": "✨ Созидатель", "attack": 12000, "price": 5000000, "icon": "✨", "tier": "creator"},
    20: {"name": "∞ Бесконечность", "attack": 20000, "price": 10000000, "icon": "∞", "tier": "infinite"},
    21: {"name": "🕰️ Клинок времени", "attack": 30000, "price": 20000000, "icon": "🕰️", "tier": "cosmic"},
    22: {"name": "🌌 Реальность", "attack": 50000, "price": 50000000, "icon": "🌌", "tier": "cosmic"},
    23: {"name": "⚛️ Первобытный клинок", "attack": 100000, "price": 100000000, "icon": "⚛️", "tier": "primordial"},
    24: {"name": "🌠 Свет", "attack": 200000, "price": 200000000, "icon": "🌠", "tier": "primordial"},
    25: {"name": "👁️ Око вселенной", "attack": 500000, "price": 500000000, "icon": "👁️", "tier": "eternal"},
}

# ==================== БРОНЯ (25 УРОВНЕЙ) ====================
ARMORS = {
    1: {"name": "🥾 Кожаная броня", "defense": 5, "price": 10, "icon": "🥾", "tier": "common"},
    2: {"name": "🛡️ Кольчуга", "defense": 10, "price": 30, "icon": "🛡️", "tier": "common"},
    3: {"name": "⚔️ Латы", "defense": 20, "price": 80, "icon": "⚔️", "tier": "common"},
    4: {"name": "✨ Магический доспех", "defense": 35, "price": 200, "icon": "✨", "tier": "rare"},
    5: {"name": "👑 Божественная броня", "defense": 60, "price": 500, "icon": "👑", "tier": "rare"},
    6: {"name": "🔥 Огненная броня", "defense": 90, "price": 1000, "icon": "🔥", "tier": "epic"},
    7: {"name": "❄️ Ледяная броня", "defense": 130, "price": 2000, "icon": "❄️", "tier": "epic"},
    8: {"name": "⚡ Броня грома", "defense": 180, "price": 4000, "icon": "⚡", "tier": "epic"},
    9: {"name": "🌌 Звёздная броня", "defense": 250, "price": 8000, "icon": "🌌", "tier": "legendary"},
    10: {"name": "💎 Кристальная броня", "defense": 350, "price": 15000, "icon": "💎", "tier": "legendary"},
    11: {"name": "👁️ Броня истины", "defense": 500, "price": 30000, "icon": "👁️", "tier": "mythic"},
    12: {"name": "🌌 Космическая броня", "defense": 700, "price": 60000, "icon": "🌌", "tier": "legend"},
    13: {"name": "👑 Божественная броня", "defense": 1000, "price": 100000, "icon": "👑", "tier": "god"},
    14: {"name": "🌀 Броня хаоса", "defense": 1500, "price": 250000, "icon": "🌀", "tier": "chaos"},
    15: {"name": "💎 Кристальная броня", "defense": 2500, "price": 500000, "icon": "💎", "tier": "chaos"},
    16: {"name": "🌑 Тьма", "defense": 4000, "price": 1000000, "icon": "🌑", "tier": "creator"},
    17: {"name": "✨ Броня созидателя", "defense": 6000, "price": 2000000, "icon": "✨", "tier": "creator"},
    18: {"name": "∞ Бесконечность", "defense": 10000, "price": 5000000, "icon": "∞", "tier": "infinite"},
    19: {"name": "🕰️ Временная броня", "defense": 15000, "price": 10000000, "icon": "🕰️", "tier": "cosmic"},
    20: {"name": "🌌 Броня реальности", "defense": 25000, "price": 25000000, "icon": "🌌", "tier": "cosmic"},
    21: {"name": "⚛️ Первобытная броня", "defense": 50000, "price": 50000000, "icon": "⚛️", "tier": "primordial"},
    22: {"name": "🌠 Свет", "defense": 100000, "price": 100000000, "icon": "🌠", "tier": "primordial"},
    23: {"name": "👁️ Броня вселенной", "defense": 200000, "price": 200000000, "icon": "👁️", "tier": "eternal"},
}

# ==================== АРТЕФАКТЫ (30 ШТУК) ====================
ARTIFACTS = {
    1: {"name": "🐺 Клык силы", "effect": "attack", "value": 10, "icon": "🐺", "tier": "common"},
    2: {"name": "🐀 Коготь скорости", "effect": "dodge", "value": 5, "icon": "🐀", "tier": "common"},
    3: {"name": "🍀 Амулет удачи", "effect": "crit_chance", "value": 10, "icon": "🍀", "tier": "rare"},
    4: {"name": "🔥 Сердце дракона", "effect": "hp", "value": 50, "icon": "🔥", "tier": "rare"},
    5: {"name": "📜 Посох тьмы", "effect": "attack", "value": 20, "icon": "📜", "tier": "epic"},
    6: {"name": "💍 Кольцо тьмы", "effect": "crit_damage", "value": 15, "icon": "💍", "tier": "epic"},
    7: {"name": "💀 Череп смерти", "effect": "damage", "value": 30, "icon": "💀", "tier": "legendary"},
    8: {"name": "👹 Рог демона", "effect": "hp", "value": 100, "icon": "👹", "tier": "legendary"},
    9: {"name": "🐍 Яд гидры", "effect": "poison", "value": 10, "icon": "🐍", "tier": "mythic"},
    10: {"name": "⚡ Молния Зевса", "effect": "crit_damage", "value": 50, "icon": "⚡", "tier": "mythic"},
    11: {"name": "🌋 Сердце вулкана", "effect": "attack", "value": 80, "icon": "🌋", "tier": "legend"},
    12: {"name": "🌪️ Око бури", "effect": "dodge", "value": 20, "icon": "🌪️", "tier": "legend"},
    13: {"name": "🐲 Драконий глаз", "effect": "crit_chance", "value": 25, "icon": "🐲", "tier": "god"},
    14: {"name": "👑 Корона власти", "effect": "all", "value": 50, "icon": "👑", "tier": "god"},
    15: {"name": "🌀 Сердце хаоса", "effect": "damage", "value": 100, "icon": "🌀", "tier": "chaos"},
    16: {"name": "💎 Кристалл бесконечности", "effect": "all", "value": 100, "icon": "💎", "tier": "chaos"},
    17: {"name": "🌑 Тень", "effect": "dodge", "value": 50, "icon": "🌑", "tier": "creator"},
    18: {"name": "✨ Искра созидания", "effect": "attack", "value": 200, "icon": "✨", "tier": "creator"},
    19: {"name": "∞ Печать бесконечности", "effect": "all", "value": 200, "icon": "∞", "tier": "infinite"},
    20: {"name": "🕰️ Песок времени", "effect": "speed", "value": 50, "icon": "🕰️", "tier": "cosmic"},
    21: {"name": "🌌 Осколок реальности", "effect": "all", "value": 300, "icon": "🌌", "tier": "cosmic"},
    22: {"name": "⚛️ Ядро хаоса", "effect": "damage", "value": 500, "icon": "⚛️", "tier": "primordial"},
    23: {"name": "🌠 Искра света", "effect": "attack", "value": 1000, "icon": "🌠", "tier": "primordial"},
    24: {"name": "👁️ Зрачок вселенной", "effect": "all", "value": 1000, "icon": "👁️", "tier": "eternal"},
}

# ==================== РЕСУРСЫ (15 ВИДОВ) ====================
RESOURCES = {
    "stone": {"name": "🪨 Камень", "tier": "common", "base_time": 5, "icon": "🪨"},
    "wood": {"name": "🪵 Древесина", "tier": "common", "base_time": 5, "icon": "🪵"},
    "iron": {"name": "🔩 Железо", "tier": "common", "base_time": 8, "icon": "🔩"},
    "silver": {"name": "🥈 Серебро", "tier": "rare", "base_time": 15, "icon": "🥈"},
    "gold": {"name": "🪙 Золото", "tier": "rare", "base_time": 20, "icon": "🪙"},
    "crystal": {"name": "💎 Кристалл", "tier": "epic", "base_time": 30, "icon": "💎"},
    "mithril": {"name": "✨ Мифрил", "tier": "epic", "base_time": 40, "icon": "✨"},
    "dragon_scale": {"name": "🐉 Чешуя дракона", "tier": "legendary", "base_time": 60, "icon": "🐉"},
    "phoenix_feather": {"name": "🕊️ Перо феникса", "tier": "legendary", "base_time": 90, "icon": "🕊️"},
    "void_core": {"name": "🌌 Ядро пустоты", "tier": "mythic", "base_time": 120, "icon": "🌌"},
    "star_dust": {"name": "✨ Звёздная пыль", "tier": "legend", "base_time": 180, "icon": "✨"},
    "time_sand": {"name": "🕰️ Песок времени", "tier": "cosmic", "base_time": 300, "icon": "🕰️"},
    "reality_fragment": {"name": "🌌 Осколок реальности", "tier": "primordial", "base_time": 600, "icon": "🌌"},
    "light_spark": {"name": "🌠 Искра света", "tier": "eternal", "base_time": 1200, "icon": "🌠"},
}

# ==================== ПЕЩЕРЫ (7 УРОВНЕЙ) ====================
CAVES = {
    1: {"name": "🪨 Каменная пещера", "hp_cost": 5, "min_resources": 1, "max_resources": 3, "tiers": ["common"], "time_multiplier": 1},
    2: {"name": "🪵 Лесная чаща", "hp_cost": 8, "min_resources": 2, "max_resources": 4, "tiers": ["common", "rare"], "time_multiplier": 1.2},
    3: {"name": "🔥 Вулканическая пещера", "hp_cost": 12, "min_resources": 3, "max_resources": 6, "tiers": ["common", "rare", "epic"], "time_multiplier": 1.5},
    4: {"name": "❄️ Ледяной грот", "hp_cost": 20, "min_resources": 5, "max_resources": 10, "tiers": ["rare", "epic", "legendary"], "time_multiplier": 2},
    5: {"name": "🌌 Космическая бездна", "hp_cost": 50, "min_resources": 10, "max_resources": 20, "tiers": ["epic", "legendary", "mythic"], "time_multiplier": 3},
    6: {"name": "🕰️ Храм времени", "hp_cost": 100, "min_resources": 20, "max_resources": 40, "tiers": ["legendary", "mythic", "legend"], "time_multiplier": 5},
    7: {"name": "👁️ Сердце вселенной", "hp_cost": 200, "min_resources": 50, "max_resources": 100, "tiers": ["mythic", "legend", "cosmic", "primordial"], "time_multiplier": 10},
}

# ==================== ИВЕНТЫ ====================
EVENTS = {
    "double_rpg": {"name": "🎉 Двойные RPG монеты!", "multiplier": 2, "duration": 24, "icon": "🎉"},
    "double_exp": {"name": "⭐ Двойной опыт!", "multiplier": 2, "duration": 24, "icon": "⭐"},
    "half_hp_cost": {"name": "❤️ Половина стоимости HP в пещерах!", "multiplier": 0.5, "duration": 24, "icon": "❤️"},
    "discount_shop": {"name": "🛒 Скидка 30% в магазине!", "multiplier": 0.7, "duration": 24, "icon": "🛒"},
    "legendary_boss": {"name": "👑 Легендарные боссы появляются чаще!", "multiplier": 2, "duration": 24, "icon": "👑"},
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

# ==================== ЗЕЛЬЯ ====================
POTIONS = {
    "small": {"name": "🍎 Малое зелье", "heal": 20, "price": 5, "icon": "🍎"},
    "medium": {"name": "🍯 Среднее зелье", "heal": 50, "price": 10, "icon": "🍯"},
    "large": {"name": "🧪 Большое зелье", "heal": 100, "price": 20, "icon": "🧪"},
    "mega": {"name": "🌟 Эликсир жизни", "heal": "full", "price": 50, "icon": "🌟"},
    "divine": {"name": "✨ Божественный эликсир", "heal": "full", "price": 200, "icon": "✨", "bonus": "temporary_attack", "bonus_value": 50},
}

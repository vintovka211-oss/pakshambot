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
    6: {"name": "🌌 Космический бур", "level": 6, "price": 50000, "icon": "🌌", "can_mine": ["common", "rare", "epic", "legendary", "mythic", "cosmic"]},
    7: {"name": "⚛️ Первобытный бур", "level": 7, "price": 200000, "icon": "⚛️", "can_mine": ["common", "rare", "epic", "legendary", "mythic", "cosmic", "primordial"]},
    8: {"name": "👁️ Бур вселенной", "level": 8, "price": 1000000, "icon": "👁️", "can_mine": ["common", "rare", "epic", "legendary", "mythic", "cosmic", "primordial", "eternal"]},
}

# ==================== РУДЫ ====================
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

# ==================== ПЕЩЕРЫ ====================
CAVES = {
    1: {"name": "🪨 Каменная пещера", "min_resources": 1, "max_resources": 3, "tiers": ["common"], "required_tool": 1},
    2: {"name": "🪵 Лесная чаща", "min_resources": 2, "max_resources": 4, "tiers": ["common", "rare"], "required_tool": 2},
    3: {"name": "🔥 Вулканическая пещера", "min_resources": 3, "max_resources": 6, "tiers": ["common", "rare", "epic"], "required_tool": 3},
    4: {"name": "❄️ Ледяной грот", "min_resources": 5, "max_resources": 10, "tiers": ["rare", "epic", "legendary"], "required_tool": 4},
    5: {"name": "🌌 Космическая бездна", "min_resources": 10, "max_resources": 20, "tiers": ["epic", "legendary", "mythic"], "required_tool": 5},
    6: {"name": "🕰️ Храм времени", "min_resources": 20, "max_resources": 40, "tiers": ["legendary", "mythic", "cosmic"], "required_tool": 6},
    7: {"name": "👁️ Сердце вселенной", "min_resources": 50, "max_resources": 100, "tiers": ["mythic", "cosmic", "primordial", "eternal"], "required_tool": 7},
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
    8: {"name": "🔥 Пламенный клинок", "attack": 150, "price": 3000, "icon": "🔥", "tier": "epic"},
    9: {"name": "❄️ Ледяной меч", "attack": 200, "price": 5000, "icon": "❄️", "tier": "epic"},
    10: {"name": "⚡ Громовержец", "attack": 300, "price": 10000, "icon": "⚡", "tier": "legendary"},
    11: {"name": "🌌 Звёздный клинок", "attack": 450, "price": 20000, "icon": "🌌", "tier": "legendary"},
    12: {"name": "💎 Кристальный меч", "attack": 600, "price": 35000, "icon": "💎", "tier": "mythic"},
    13: {"name": "👁️ Око истины", "attack": 800, "price": 50000, "icon": "👁️", "tier": "mythic"},
    14: {"name": "🌌 Космический клинок", "attack": 1200, "price": 100000, "icon": "🌌", "tier": "legend"},
    15: {"name": "👑 Божественный меч", "attack": 2000, "price": 200000, "icon": "👑", "tier": "god"},
}

# ==================== БРОНЯ ====================
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
}

# ==================== АРТЕФАКТЫ ====================
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
}

# ==================== ЗЕЛЬЯ ====================
POTIONS = {
    "small": {"name": "🍎 Малое зелье", "heal": 20, "price": 5, "icon": "🍎"},
    "medium": {"name": "🍯 Среднее зелье", "heal": 50, "price": 10, "icon": "🍯"},
    "large": {"name": "🧪 Большое зелье", "heal": 100, "price": 20, "icon": "🧪"},
    "mega": {"name": "🌟 Эликсир жизни", "heal": "full", "price": 50, "icon": "🌟"},
}

# ==================== ИВЕНТЫ ====================
EVENTS = {
    "double_rpg": {"name": "🎉 Двойные RPG монеты!", "multiplier": 2, "duration": 24, "icon": "🎉"},
    "double_exp": {"name": "⭐ Двойной опыт!", "multiplier": 2, "duration": 24, "icon": "⭐"},
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

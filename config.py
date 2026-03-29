import os

BOT_TOKEN = "8590452175:AAGKpZiKBmneyxUX8Ac9U7w9cRjtWQYT8uU"
ADMIN_IDS = [8493522297]

COIN_NAME = "PAC"
RPG_COIN_NAME = "🪙 RPG"
BONUS_PAC = 100
PREMIUM_PRICE_PAC = 350

RPG_TO_PAC_RATE = 100
BET_BUTTONS = [1, 5, 10, 25, 50, 100, 250, 500]

PVP_COMMISSION = 5
PVP_MIN_BET = 10
PVP_MAX_BET = 1000

CLAN_CREATE_PRICE = 1000
CLAN_MAX_MEMBERS = 20

FORGE_UPGRADE_COST = {i: 100 * (2 ** (i-1)) for i in range(1, 11)}
FORGE_UPGRADE_STATS = {i: i * 5 for i in range(1, 11)}

ITEM_DURABILITY = 100
REPAIR_COST_MULTIPLIER = 0.5

SBP_PHONE = "+7 999 888 77 66"

BOSSES = {
    1: {"name": "🐀 Крысиный король", "hp": 50, "attack": 5, "rpg_reward": 5, "exp": 10, "artifact_chance": 10, "artifact_id": 1, "icon": "🐀"},
    2: {"name": "🐺 Лесной волк", "hp": 100, "attack": 10, "rpg_reward": 10, "exp": 20, "artifact_chance": 15, "artifact_id": 2, "icon": "🐺"},
    3: {"name": "🧟 Гоблин-шаман", "hp": 150, "attack": 15, "rpg_reward": 15, "exp": 30, "artifact_chance": 20, "artifact_id": 3, "icon": "🧟"},
    4: {"name": "🐉 Огненный дракон", "hp": 200, "attack": 20, "rpg_reward": 20, "exp": 40, "artifact_chance": 25, "artifact_id": 4, "icon": "🐉"},
    5: {"name": "🧙 Тёмный маг", "hp": 300, "attack": 25, "rpg_reward": 30, "exp": 60, "artifact_chance": 30, "artifact_id": 5, "icon": "🧙"},
    6: {"name": "👑 Тёмный властелин", "hp": 500, "attack": 35, "rpg_reward": 50, "exp": 100, "artifact_chance": 35, "artifact_id": 6, "icon": "👑"},
    7: {"name": "💀 Повелитель смерти", "hp": 1000, "attack": 50, "rpg_reward": 100, "exp": 200, "artifact_chance": 40, "artifact_id": 7, "icon": "💀"},
    8: {"name": "👹 Демон хаоса", "hp": 1500, "attack": 70, "rpg_reward": 150, "exp": 300, "artifact_chance": 45, "artifact_id": 8, "icon": "👹"},
    9: {"name": "🐍 Гидра", "hp": 2000, "attack": 90, "rpg_reward": 200, "exp": 400, "artifact_chance": 50, "artifact_id": 9, "icon": "🐍"},
    10: {"name": "⚡ Бог грома", "hp": 3000, "attack": 120, "rpg_reward": 300, "exp": 600, "artifact_chance": 60, "artifact_id": 10, "icon": "⚡"},
}

WEAPONS = {
    1: {"name": "🗡️ Ржавый меч", "attack": 5, "price": 10, "rarity": "common", "icon": "🗡️"},
    2: {"name": "⚔️ Стальной меч", "attack": 10, "price": 30, "rarity": "common", "icon": "⚔️"},
    3: {"name": "🏹 Длинный лук", "attack": 15, "price": 60, "rarity": "rare", "icon": "🏹"},
    4: {"name": "🔨 Молот грома", "attack": 25, "price": 150, "rarity": "rare", "icon": "🔨"},
    5: {"name": "✨ Меч света", "attack": 40, "price": 300, "rarity": "epic", "icon": "✨"},
    6: {"name": "💀 Коса смерти", "attack": 60, "price": 600, "rarity": "epic", "icon": "💀"},
    7: {"name": "👑 Экскалибур", "attack": 100, "price": 1500, "rarity": "legendary", "icon": "👑"},
}

ARMORS = {
    1: {"name": "🥾 Кожаная броня", "defense": 5, "price": 10, "rarity": "common", "icon": "🥾"},
    2: {"name": "🛡️ Кольчуга", "defense": 10, "price": 30, "rarity": "common", "icon": "🛡️"},
    3: {"name": "⚔️ Латы", "defense": 20, "price": 80, "rarity": "rare", "icon": "⚔️"},
    4: {"name": "✨ Магический доспех", "defense": 35, "price": 200, "rarity": "epic", "icon": "✨"},
    5: {"name": "👑 Божественная броня", "defense": 60, "price": 500, "rarity": "legendary", "icon": "👑"},
}

POTIONS = {
    "small": {"name": "🍎 Малое зелье", "heal": 20, "price": 5, "icon": "🍎"},
    "medium": {"name": "🍯 Среднее зелье", "heal": 50, "price": 10, "icon": "🍯"},
    "large": {"name": "🧪 Большое зелье", "heal": 100, "price": 20, "icon": "🧪"},
    "mega": {"name": "🌟 Эликсир жизни", "heal": "full", "price": 50, "icon": "🌟"},
}

ARTIFACTS = {
    1: {"name": "🐺 Клык силы", "effect": "attack", "value": 10, "icon": "🐺"},
    2: {"name": "🐀 Коготь скорости", "effect": "dodge", "value": 5, "icon": "🐀"},
    3: {"name": "🍀 Амулет удачи", "effect": "crit_chance", "value": 10, "icon": "🍀"},
    4: {"name": "🔥 Сердце дракона", "effect": "hp", "value": 50, "icon": "🔥"},
    5: {"name": "📜 Посох тьмы", "effect": "attack", "value": 20, "icon": "📜"},
    6: {"name": "💍 Кольцо тьмы", "effect": "crit_damage", "value": 15, "icon": "💍"},
    7: {"name": "💀 Череп смерти", "effect": "damage", "value": 30, "icon": "💀"},
    8: {"name": "👹 Рог демона", "effect": "hp", "value": 100, "icon": "👹"},
    9: {"name": "🐍 Яд гидры", "effect": "poison", "value": 10, "icon": "🐍"},
    10: {"name": "⚡ Молния Зевса", "effect": "crit_damage", "value": 50, "icon": "⚡"},
}

RESOURCES = {
    "stone": {"name": "🪨 Камень", "rarity": "common", "icon": "🪨"},
    "wood": {"name": "🪵 Древесина", "rarity": "common", "icon": "🪵"},
    "iron": {"name": "🔩 Железо", "rarity": "rare", "icon": "🔩"},
    "crystal": {"name": "💎 Кристалл", "rarity": "epic", "icon": "💎"},
    "mithril": {"name": "✨ Мифрил", "rarity": "legendary", "icon": "✨"},
}

TOOLS = {
    1: {"name": "🪓 Каменная кирка", "efficiency": 2, "price": 0, "icon": "🪓"},
    2: {"name": "⛏️ Железная кирка", "efficiency": 4, "price": 100, "icon": "⛏️"},
    3: {"name": "💎 Алмазная кирка", "efficiency": 6, "price": 500, "icon": "💎"},
    4: {"name": "✨ Мифриловая кирка", "efficiency": 8, "price": 2000, "icon": "✨"},
    5: {"name": "👑 Божественная кирка", "efficiency": 10, "price": 10000, "icon": "👑"},
}

LOTTERY_BOXES = {
    "common": {"name": "🟢 Обычный сундук", "price": 20, "icon": "🟢"},
    "rare": {"name": "🔵 Редкий сундук", "price": 100, "icon": "🔵"},
    "epic": {"name": "🟣 Эпический сундук", "price": 500, "icon": "🟣"},
    "legendary": {"name": "🟠 Легендарный сундук", "price": 2000, "icon": "🟠"},
}

ACHIEVEMENTS = {
    "warrior_10": {"name": "🗡️ Начинающий воин", "condition": 10, "reward": 50},
    "warrior_50": {"name": "⚔️ Опытный воин", "condition": 50, "reward": 200},
    "warrior_200": {"name": "👑 Легендарный воин", "condition": 200, "reward": 1000},
    "collector": {"name": "💎 Коллекционер", "condition": 10, "reward": 200},
    "blacksmith": {"name": "🔨 Кузнец", "condition": 5, "reward": 100},
    "miner": {"name": "⛏️ Шахтёр", "condition": 1000, "reward": 300},
    "rich": {"name": "💰 Богач", "condition": 5000, "reward": 500},
    "clan_leader": {"name": "👑 Мастер клана", "condition": 1, "reward": 500},
}

DAILY_EVENTS = {
    0: {"name": "🪙 День денег", "bonus": "double_rpg"},
    1: {"name": "⛏️ День шахтёра", "bonus": "double_resources"},
    2: {"name": "🛡️ День защиты", "bonus": "double_exp"},
    3: {"name": "🧪 День алхимика", "bonus": "potion_discount"},
    4: {"name": "⚔️ День битв", "bonus": "double_rpg"},
    5: {"name": "🎲 День удачи", "bonus": "crit_bonus"},
    6: {"name": "👑 Королевский день", "bonus": "all_bonus"},
}

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

BOSSES = {
    1: {"name": "🐀 Крысиный король", "hp": 50, "attack": 5, "rpg_reward": 5, "exp": 10, "icon": "🐀"},
    2: {"name": "🐺 Лесной волк", "hp": 100, "attack": 10, "rpg_reward": 10, "exp": 20, "icon": "🐺"},
    3: {"name": "🧟 Гоблин-шаман", "hp": 150, "attack": 15, "rpg_reward": 15, "exp": 30, "icon": "🧟"},
    4: {"name": "🐉 Огненный дракон", "hp": 200, "attack": 20, "rpg_reward": 20, "exp": 40, "icon": "🐉"},
    5: {"name": "🧙 Тёмный маг", "hp": 300, "attack": 25, "rpg_reward": 30, "exp": 60, "icon": "🧙"},
    6: {"name": "👑 Тёмный властелин", "hp": 500, "attack": 35, "rpg_reward": 50, "exp": 100, "icon": "👑"},
    7: {"name": "💀 Повелитель смерти", "hp": 1000, "attack": 50, "rpg_reward": 100, "exp": 200, "icon": "💀"},
    8: {"name": "👹 Демон хаоса", "hp": 1500, "attack": 70, "rpg_reward": 150, "exp": 300, "icon": "👹"},
    9: {"name": "🐍 Гидра", "hp": 2000, "attack": 90, "rpg_reward": 200, "exp": 400, "icon": "🐍"},
    10: {"name": "⚡ Бог грома", "hp": 3000, "attack": 120, "rpg_reward": 300, "exp": 600, "icon": "⚡"},
}

WEAPONS = {
    1: {"name": "🗡️ Ржавый меч", "attack": 5, "price": 10, "icon": "🗡️"},
    2: {"name": "⚔️ Стальной меч", "attack": 10, "price": 30, "icon": "⚔️"},
    3: {"name": "🏹 Длинный лук", "attack": 15, "price": 60, "icon": "🏹"},
    4: {"name": "🔨 Молот грома", "attack": 25, "price": 150, "icon": "🔨"},
    5: {"name": "✨ Меч света", "attack": 40, "price": 300, "icon": "✨"},
    6: {"name": "💀 Коса смерти", "attack": 60, "price": 600, "icon": "💀"},
    7: {"name": "👑 Экскалибур", "attack": 100, "price": 1500, "icon": "👑"},
}

ARMORS = {
    1: {"name": "🥾 Кожаная броня", "defense": 5, "price": 10, "icon": "🥾"},
    2: {"name": "🛡️ Кольчуга", "defense": 10, "price": 30, "icon": "🛡️"},
    3: {"name": "⚔️ Латы", "defense": 20, "price": 80, "icon": "⚔️"},
    4: {"name": "✨ Магический доспех", "defense": 35, "price": 200, "icon": "✨"},
    5: {"name": "👑 Божественная броня", "defense": 60, "price": 500, "icon": "👑"},
}

POTIONS = {
    "small": {"name": "🍎 Малое зелье", "heal": 20, "price": 5, "icon": "🍎"},
    "medium": {"name": "🍯 Среднее зелье", "heal": 50, "price": 10, "icon": "🍯"},
    "large": {"name": "🧪 Большое зелье", "heal": 100, "price": 20, "icon": "🧪"},
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

RESOURCES = {
    "stone": {"name": "🪨 Камень", "icon": "🪨"},
    "wood": {"name": "🪵 Древесина", "icon": "🪵"},
    "iron": {"name": "🔩 Железо", "icon": "🔩"},
}

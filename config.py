import os

BOT_TOKEN = "8590452175:AAGKpZiKBmneyxUX8Ac9U7w9cRjtWQYT8uU"
ADMIN_IDS = [8493522297]

COIN_NAME = "PAC"
RPG_COIN_NAME = "🪙 RPG"
BONUS_PAC = 100
PREMIUM_PRICE_PAC = 350

# Курсы обмена
RPG_TO_PAC_RATE = 100  # 100 RPG = 1 PAC (невыводимый)

# Кнопки ставок для казино
BET_BUTTONS = [1, 5, 10, 25, 50, 100, 250, 500]

# PvP настройки
PVP_COMMISSION = 5  # 5% комиссия
PVP_MIN_BET = 10
PVP_MAX_BET = 1000

# Кланы
CLAN_CREATE_PRICE = 1000  # RPG
CLAN_MAX_MEMBERS = 20

# Кузнец
FORGE_UPGRADE_COST = {
    1: 100, 2: 200, 3: 400, 4: 800, 5: 1600,
    6: 3200, 7: 6400, 8: 12800, 9: 25600, 10: 51200
}
FORGE_UPGRADE_STATS = {i: i * 5 for i in range(1, 11)}  # +5 атаки за уровень

# Прочность предметов
ITEM_DURABILITY = 100  # начальная прочность
REPAIR_COST_MULTIPLIER = 0.5  # 50% от цены предмета

# СБП оплата
SBP_PHONE = "+7 999 888 77 66"

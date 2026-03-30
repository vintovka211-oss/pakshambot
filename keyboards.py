from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Играть", callback_data="games"),
         InlineKeyboardButton(text="💰 Пополнить", callback_data="deposit")],
        [InlineKeyboardButton(text="💸 Вывод", callback_data="withdraw"),
         InlineKeyboardButton(text="👑 Премиум", callback_data="premium")],
        [InlineKeyboardButton(text="⛏️ Шахта", callback_data="mine"),
         InlineKeyboardButton(text="⚔️ RPG режим", callback_data="rpg_menu")],
        [InlineKeyboardButton(text="🏪 Магазин", callback_data="shop"),
         InlineKeyboardButton(text="🏆 ТОП-10", callback_data="top")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help"),
         InlineKeyboardButton(text="👥 Рефералы", callback_data="referral")],
        [InlineKeyboardButton(text="🎁 Ежедневный", callback_data="daily"),
         InlineKeyboardButton(text="🛡️ Админ панель", callback_data="admin_panel")],
    ])

def get_games_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Слоты", callback_data="game_slots"),
         InlineKeyboardButton(text="🎲 Кубик", callback_data="game_dice")],
        [InlineKeyboardButton(text="🎡 Рулетка", callback_data="game_roulette"),
         InlineKeyboardButton(text="🪙 Орёл/Решка", callback_data="game_coin")],
        [InlineKeyboardButton(text="💣 Мины", callback_data="game_mines"),
         InlineKeyboardButton(text="🗼 Башня", callback_data="game_tower")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")],
    ])

def get_bet_keyboard(game):
    buttons = []
    row = []
    for bet in BET_BUTTONS:
        row.append(InlineKeyboardButton(text=f"{bet}", callback_data=f"{game}_bet_{bet}"))
        if len(row) == 4:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="games")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_dice_choice_keyboard(bet):
    buttons = []
    row = []
    for i in range(1, 7):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"dice_choice_{i}_{bet}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="games")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_roulette_choice_keyboard(bet):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔴 Красное", callback_data=f"roulette_choice_🔴_{bet}"),
         InlineKeyboardButton(text="⚫ Чёрное", callback_data=f"roulette_choice_⚫_{bet}")],
        [InlineKeyboardButton(text="🟢 Зелёное", callback_data=f"roulette_choice_🟢_{bet}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="games")]
    ])

def get_coin_choice_keyboard(bet):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪙 Орёл", callback_data=f"coin_choice_орел_{bet}"),
         InlineKeyboardButton(text="🪙 Решка", callback_data=f"coin_choice_решка_{bet}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="games")]
    ])

def get_mines_field_keyboard(game_data):
    buttons = []
    for i in range(5):
        row = []
        for j in range(5):
            cell = i * 5 + j
            if cell in game_data["opened"]:
                text = "✅"
            else:
                text = "⬜"
            row.append(InlineKeyboardButton(text=text, callback_data=f"mines_cell_{cell}"))
        buttons.append(row)
    
    step = game_data["step"]
    multiplier = game_data["multipliers"][step] if step < len(game_data["multipliers"]) else game_data["multipliers"][-1]
    buttons.append([InlineKeyboardButton(text=f"💰 Забрать выигрыш (x{multiplier:.2f})", callback_data=f"mines_cashout_{game_data['bet']}_{step}_{multiplier}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="games")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_mines_result_keyboard(game_data):
    buttons = []
    for i in range(5):
        row = []
        for j in range(5):
            cell = i * 5 + j
            if cell in game_data["mines"]:
                text = "💀"
            elif cell in game_data["opened"]:
                text = "✅"
            else:
                text = "⬜"
            row.append(InlineKeyboardButton(text=text, callback_data="none"))
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="🔁 Играть снова", callback_data="game_mines")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="games")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_tower_keyboard(game_data):
    buttons = []
    row = []
    for i in range(5):
        row.append(InlineKeyboardButton(text=f"🟩 {i+1}", callback_data=f"tower_choice_{i}"))
    buttons.append(row)
    
    current_level = game_data["current_level"]
    multiplier = game_data["multipliers"][current_level]
    buttons.append([InlineKeyboardButton(text=f"💰 Забрать выигрыш (x{multiplier:.2f})", callback_data=f"tower_cashout_{game_data['bet']}_{current_level}_{multiplier}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="games")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_tower_result_keyboard(game_data):
    buttons = []
    for i, level in enumerate(game_data["levels"]):
        if level["revealed"]:
            if level["selected"] in level["mines"]:
                status = "💀 МИНА"
            else:
                status = "💎 АЛМАЗ"
        else:
            status = "❓ НЕ ОТКРЫТ"
        buttons.append([InlineKeyboardButton(text=f"Уровень {i+1}: {status}", callback_data="none")])
    buttons.append([InlineKeyboardButton(text="🔁 Играть снова", callback_data="game_tower")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="games")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])

def get_rpg_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Сразиться с боссом", callback_data="fight_boss")],
        [InlineKeyboardButton(text="⛏️ Пойти в пещеру", callback_data="cave_menu")],
        [InlineKeyboardButton(text="🔧 Улучшить инструмент", callback_data="upgrade_tool")],
        [InlineKeyboardButton(text="💰 Продать руду", callback_data="sell_ores")],
        [InlineKeyboardButton(text="🗡️ Кузнец", callback_data="forge")],
        [InlineKeyboardButton(text="🛡️ Мой инвентарь", callback_data="my_inventory")],
        [InlineKeyboardButton(text="📊 Мои характеристики", callback_data="my_stats_rpg")],
        [InlineKeyboardButton(text="❤️ Использовать зелье", callback_data="use_potion")],
        [InlineKeyboardButton(text="🔄 Обменять RPG на PAC", callback_data="exchange_rpg")],
        [InlineKeyboardButton(text="🏰 Клан", callback_data="clan_menu")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")],
    ])

def get_boss_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for bid, boss in BOSSES.items():
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"{boss['icon']} {boss['name']} (Lv.{boss['min_level']})", callback_data=f"boss_{bid}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="rpg_menu")])
    return kb

def get_shop_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for wid, weapon in WEAPONS.items():
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"{weapon['icon']} {weapon['name']} - {weapon['price']} 🪙", callback_data=f"buy_weapon_{wid}")])
    for aid, armor in ARMORS.items():
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"{armor['icon']} {armor['name']} - {armor['price']} 🪙", callback_data=f"buy_armor_{aid}")])
    for pid, potion in POTIONS.items():
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"{potion['icon']} {potion['name']} - {potion['price']} 🪙", callback_data=f"buy_potion_{pid}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="rpg_menu")])
    return kb

def get_cave_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for level, cave in CAVES.items():
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"{cave['name']} (Ур.{level})", callback_data=f"cave_{level}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="rpg_menu")])
    return kb

def get_cave_duration_keyboard(cave_level):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏱️ 5 минут", callback_data=f"cave_time_{cave_level}_5")],
        [InlineKeyboardButton(text="⏱️ 15 минут", callback_data=f"cave_time_{cave_level}_15")],
        [InlineKeyboardButton(text="⏱️ 30 минут", callback_data=f"cave_time_{cave_level}_30")],
        [InlineKeyboardButton(text="⏱️ 60 минут", callback_data=f"cave_time_{cave_level}_60")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="cave_menu")]
    ])

def get_admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Выдать PAC", callback_data="admin_give_pac")],
        [InlineKeyboardButton(text="🪙 Выдать RPG", callback_data="admin_give_rpg")],
        [InlineKeyboardButton(text="👑 Выдать премиум", callback_data="admin_give_premium")],
        [InlineKeyboardButton(text="🎁 Выдать бонус", callback_data="admin_give_bonus")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")],
    ])

def get_clan_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏰 Информация о клане", callback_data="clan_info")],
        [InlineKeyboardButton(text="👥 Участники", callback_data="clan_members")],
        [InlineKeyboardButton(text="⚔️ Клановый босс", callback_data="clan_boss")],
        [InlineKeyboardButton(text="💪 Улучшить клан", callback_data="clan_upgrade")],
        [InlineKeyboardButton(text="👋 Покинуть клан", callback_data="clan_leave")],
        [InlineKeyboardButton(text="🗑️ Распустить клан", callback_data="clan_disband")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="rpg_menu")],
    ])

def get_no_clan_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать клан", callback_data="clan_create")],
        [InlineKeyboardButton(text="🔍 Найти клан", callback_data="clan_search")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="rpg_menu")],
    ])

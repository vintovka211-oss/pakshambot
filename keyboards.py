from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BET_BUTTONS, WEAPONS, ARMORS, POTIONS, BOSSES, CAVES, ORES, TOOLS

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
         InlineKeyboardButton(text="🃏 Блэкджек", callback_data="game_blackjack")],
        [InlineKeyboardButton(text="💣 Мины", callback_data="game_mines"),
         InlineKeyboardButton(text="🎡 Колесо", callback_data="game_wheel")],
        [InlineKeyboardButton(text="🪙 Орёл/Решка", callback_data="game_coin"),
         InlineKeyboardButton(text="🥢 Палки", callback_data="game_sticks")],
        [InlineKeyboardButton(text="📈 Больше-Меньше", callback_data="game_highlow"),
         InlineKeyboardButton(text="🎲 Кено", callback_data="game_keno")],
        [InlineKeyboardButton(text="🃏 Баккара", callback_data="game_baccarat"),
         InlineKeyboardButton(text="🃏 Покер", callback_data="game_poker")],
        [InlineKeyboardButton(text="🎲 Крэпс", callback_data="game_craps"),
         InlineKeyboardButton(text="🎰 Видео-покер", callback_data="game_video_poker")],
        [InlineKeyboardButton(text="7️⃣ Лакки 7", callback_data="game_lucky7"),
         InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")],
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
        [InlineKeyboardButton(text="◀️ Назад", callback_data="games")]
    ])

def get_coin_choice_keyboard(bet):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🪙 Орёл", callback_data=f"coin_choice_орел_{bet}"),
         InlineKeyboardButton(text="🪙 Решка", callback_data=f"coin_choice_решка_{bet}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="games")]
    ])

def get_mines_choice_keyboard(bet):
    buttons = []
    row = []
    for i in range(1, 10):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"mines_choice_{i}_{bet}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="games")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_sticks_choice_keyboard(bet):
    buttons = []
    row = []
    for i in range(1, 11):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"sticks_choice_{i}_{bet}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="games")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_highlow_choice_keyboard(bet):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 Больше 50", callback_data=f"highlow_choice_high_{bet}"),
         InlineKeyboardButton(text="📉 Меньше 50", callback_data=f"highlow_choice_low_{bet}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="games")]
    ])

def get_keno_choice_keyboard(bet):
    buttons = []
    row = []
    for i in range(1, 21):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"keno_choice_{i}_{bet}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="games")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_baccarat_choice_keyboard(bet):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Игрок", callback_data=f"baccarat_choice_player_{bet}"),
         InlineKeyboardButton(text="🏦 Банкир", callback_data=f"baccarat_choice_banker_{bet}")],
        [InlineKeyboardButton(text="🤝 Ничья", callback_data=f"baccarat_choice_tie_{bet}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="games")]
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

def get_fight_keyboard(user_id):
    """Клавиатура для боя с боссом"""
    from rpg import active_fights
    fight_data = active_fights.get(user_id)
    if not fight_data:
        return get_back_keyboard()
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚔️ Атаковать", callback_data="fight_attack")],
        [InlineKeyboardButton(text="🧪 Использовать зелье", callback_data="fight_heal")],
        [InlineKeyboardButton(text="🏃 Сбежать", callback_data="rpg_menu")],
    ])
    
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
        [InlineKeyboardButton(text="⏱️ 120 минут", callback_data=f"cave_time_{cave_level}_120")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="cave_menu")]
    ])

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

def get_back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
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

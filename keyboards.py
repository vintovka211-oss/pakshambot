from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import BET_BUTTONS

# ==================== МИНЫ ====================
def get_mines_keyboard(game_data):
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

# ==================== БАШНЯ (8 УРОВНЕЙ) ====================
def get_tower_keyboard(game_data):
    buttons = []
    row = []
    for i in range(5):
        row.append(InlineKeyboardButton(text=f"⬜ {i+1}", callback_data=f"tower_choice_{i}"))
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
                status = "✅ БЕЗОПАСНО"
        else:
            status = "❓ НЕ ОТКРЫТ"
        buttons.append([InlineKeyboardButton(text=f"Уровень {i+1}: {status}", callback_data="none")])
    buttons.append([InlineKeyboardButton(text="🔁 Играть снова", callback_data="game_tower")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="games")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

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

def get_back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])

def get_games_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💣 Мины", callback_data="game_mines")],
        [InlineKeyboardButton(text="🗼 Башня", callback_data="game_tower")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")],
    ])

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

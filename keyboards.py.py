from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Играть", callback_data="games"),
         InlineKeyboardButton(text="💰 Пополнить", callback_data="deposit")],
        [InlineKeyboardButton(text="💸 Вывод", callback_data="withdraw"),
         InlineKeyboardButton(text="👑 Премиум", callback_data="premium")],
        [InlineKeyboardButton(text="⛏️ Шахта", callback_data="mine"),
         InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="🏆 ТОП-10", callback_data="top"),
         InlineKeyboardButton(text="❓ Помощь", callback_data="help")],
        [InlineKeyboardButton(text="👥 Рефералы", callback_data="referral"),
         InlineKeyboardButton(text="🎁 Ежедневный", callback_data="daily")],
    ])

def get_games_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎰 Слоты", callback_data="game_slots"),
         InlineKeyboardButton(text="🎲 Кубик", callback_data="game_dice")],
        [InlineKeyboardButton(text="🎡 Рулетка", callback_data="game_roulette"),
         InlineKeyboardButton(text="🃏 21 (Блэкджек)", callback_data="game_blackjack")],
        [InlineKeyboardButton(text="💣 Мины", callback_data="game_mines"),
         InlineKeyboardButton(text="🎡 Колесо Фортуны", callback_data="game_wheel")],
        [InlineKeyboardButton(text="🪙 Орёл/Решка", callback_data="game_coin"),
         InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")],
    ])

def get_back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])

def get_payment_keyboard():
    from config import PAYMENT_METHODS
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for method, name in PAYMENT_METHODS.items():
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"💳 {name}", callback_data=f"donate_method_{method}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")])
    return kb

def get_admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Выдать PAC", callback_data="admin_give_pac"),
         InlineKeyboardButton(text="👑 Выдать премиум", callback_data="admin_give_premium")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")],
    ])
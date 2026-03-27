"""
Клавиатуры для бота W1NPAKSHAM
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎮 Играть", callback_data="games_menu"),
            InlineKeyboardButton(text="💰 Пополнить", callback_data="deposit"),
        ],
        [
            InlineKeyboardButton(text="💸 Вывод", callback_data="withdraw"),
            InlineKeyboardButton(text="👥 Пригласить", callback_data="referral"),
        ],
        [
            InlineKeyboardButton(text="🎫 Лотерея", callback_data="lottery_menu"),
            InlineKeyboardButton(text="🏆 Турниры", callback_data="tournaments_menu"),
        ],
        [
            InlineKeyboardButton(text="⛏️ Шахта", callback_data="mine_info"),
            InlineKeyboardButton(text="👑 Премиум", callback_data="premium_buy"),
        ],
        [
            InlineKeyboardButton(text="🏆 ТОП-10", callback_data="top"),
            InlineKeyboardButton(text="❓ Помощь", callback_data="help"),
        ],
    ])


def get_games_keyboard() -> InlineKeyboardMarkup:
    """Меню игр"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎰 Слоты", callback_data="game_slots"),
            InlineKeyboardButton(text="🎲 Кубик", callback_data="game_dice"),
        ],
        [
            InlineKeyboardButton(text="🎡 Рулетка", callback_data="game_roulette"),
            InlineKeyboardButton(text="🃏 21", callback_data="game_blackjack"),
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"),
        ]
    ])


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Кнопка назад"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")]
    ])


def get_premium_keyboard() -> InlineKeyboardMarkup:
    """Премиум меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⛏️ Шахта", callback_data="mine_info"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="premium_stats"),
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu"),
        ]
    ])


def get_mine_keyboard(is_upgrading: bool = False, max_level: bool = False, upgrade_cost: int = None) -> InlineKeyboardMarkup:
    """Клавиатура шахты"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⛏️ Собрать", callback_data="mine_collect")]
    ])
    
    if not is_upgrading and not max_level and upgrade_cost:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=f"⬆️ Улучшить ({upgrade_cost} PAC)", callback_data="mine_upgrade")
        ])
    
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="◀️ Назад", callback_data="premium_menu")
    ])
    
    return keyboard


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Админ панель"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Выдать PAC", callback_data="admin_give_pac"),
            InlineKeyboardButton(text="👑 Выдать премиум", callback_data="admin_give_premium")
        ],
        [
            InlineKeyboardButton(text="📝 Заявки на вывод", callback_data="admin_withdraw"),
            InlineKeyboardButton(text="💸 Заявки на пополнение", callback_data="admin_deposit")
        ],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
            InlineKeyboardButton(text="💰 Моя прибыль", callback_data="admin_profit")
        ],
        [
            InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")
        ]
    ])


def get_payment_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора способа оплаты"""
    from config import PAYMENT_METHODS
    
    kb = InlineKeyboardMarkup(inline_keyboard=[])
    for method, name in PAYMENT_METHODS.items():
        kb.inline_keyboard.append([InlineKeyboardButton(text=f"💳 {name}", callback_data=f"donate_method_{method}")])
    kb.inline_keyboard.append([InlineKeyboardButton(text="◀️ Назад", callback_data="main_menu")])
    return kb

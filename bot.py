import json
import os
import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

BALANCE_FILE = "balances.json"
DAILY_BONUS_FILE = "daily_bonus.json"
ADMIN_ID = "8493522297"
DAILY_BONUS = 500
RUB_TO_PAK = 10

def load_json(file):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f)

def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 Баланс", callback_data='balance')],
        [InlineKeyboardButton("🎮 Игры", callback_data='games_menu')],
        [InlineKeyboardButton("🎁 Бонус", callback_data='daily')],
        [InlineKeyboardButton("🏆 Топ", callback_data='top')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_games_menu():
    keyboard = [
        [InlineKeyboardButton("🎲 Кубик (x1.8)", callback_data='dice_game')],
        [InlineKeyboardButton("🎰 Множитель (x0.25-x1.5)", callback_data='multiplier_game')],
        [InlineKeyboardButton("🎡 Рулетка (x2-x35)", callback_data='roulette_game')],
        [InlineKeyboardButton("🎰 Слоты (Джекпот)", callback_data='slots_game')],
        [InlineKeyboardButton("✊ Камень-Ножницы-Бумага", callback_data='rps_game')],
        [InlineKeyboardButton("🃏 Блэкджек", callback_data='blackjack_game')],
        [InlineKeyboardButton("🎲 Кости (Сумма)", callback_data='dice_sum_game')],
        [InlineKeyboardButton("🔙 Назад", callback_data='menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== КОМАНДА /start ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    balances = load_json(BALANCE_FILE)
    if str(update.effective_user.id) not in balances:
        balances[str(update.effective_user.id)] = 0
        save_json(BALANCE_FILE, balances)
    
    await update.message.reply_text(
        f"👋 Привет, {user_name}!\n\n"
        f"🎮 **Добро пожаловать в PAK BOT!**\n\n"
        f"💎 1 ₽ = 10 PAK\n\n"
        f"🎲 **Игры:**\n"
        f"• 🎲 Кубик: чет/нечет (x1.8)\n"
        f"• 🎰 Множитель: 1-8 (x0.25-x1.5)\n"
        f"• 🎡 Рулетка: 1-36 (x2-x35)\n"
        f"• 🎰 Слоты: джекпот 5000\n"
        f"• ✊ Камень-Ножницы-Бумага (x2)\n"
        f"• 🃏 Блэкджек (x2)\n"
        f"• 🎲 Кости: сумма 7-12 (x2-x5)\n\n"
        f"🎁 Бонус: {DAILY_BONUS} PAK/день\n\n"
        f"Удачи! 🍀",
        reply_markup=get_main_menu(),
        parse_mode='Markdown'
    )

# ========== ОБРАБОТЧИК КНОПОК ==========
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'menu':
        await query.edit_message_text(
            "Главное меню:",
            reply_markup=get_main_menu()
        )
    elif query.data == 'games_menu':
        await query.edit_message_text(
            "🎮 Выберите игру:",
            reply_markup=get_games_menu()
        )
    elif query.data == 'balance':
        await show_balance(update, context, query)
    elif query.data == 'daily':
        await daily_bonus(update, context, query)
    elif query.data == 'top':
        await show_top(update, context, query)
    elif query.data == 'dice_game':
        await dice_game(update, context, query)
    elif query.data == 'multiplier_game':
        await multiplier_game(update, context, query)
    elif query.data == 'roulette_game':
        await roulette_game(update, context, query)
    elif query.data == 'slots_game':
        await slots_game(update, context, query)
    elif query.data == 'rps_game':
        await rps_game(update, context, query)
    elif query.data == 'blackjack_game':
        await blackjack_game(update, context, query)
    elif query.data == 'dice_sum_game':
        await dice_sum_game(update, context, query)

# ========== ПОКАЗАТЬ БАЛАНС ==========
async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    user_id = str(update.effective_user.id)
    balances = load_json(BALANCE_FILE)
    balance = balances.get(user_id, 0)
    
    text = f"💰 Ваш баланс: **{balance} PAK**\n\n💵 {balance // RUB_TO_PAK} ₽"
    
    if query:
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_main_menu())
    else:
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_main_menu())

# ========== ЕЖЕДНЕВНЫЙ БОНУС ==========
async def daily_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    user_id = str(update.effective_user.id)
    daily_data = load_json(DAILY_BONUS_FILE)
    balances = load_json(BALANCE_FILE)
    
    last_claim = daily_data.get(user_id, 0)
    current_time = time.time()
    
    if current_time - last_claim >= 86400:  # 24 часа
        balances[user_id] = balances.get(user_id, 0) + DAILY_BONUS
        daily_data[user_id] = current_time
        save_json(BALANCE_FILE, balances)
        save_json(DAILY_BONUS_FILE, daily_data)
        
        text = f"🎁 Вы получили {DAILY_BONUS} PAK! 🎉\n\n💰 Баланс: {balances[user_id]} PAK"
    else:
        hours_left = 24 - (current_time - last_claim) / 3600
        text = f"⏰ Бонус уже получен! Следующий через {int(hours_left)} часов."
    
    if query:
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_main_menu())
    else:
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_main_menu())

# ========== ТОП ИГРОКОВ ==========
async def show_top(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    balances = load_json(BALANCE_FILE)
    top_players = sorted(balances.items(), key=lambda x: x[1], reverse=True)[:10]
    
    text = "🏆 **Топ 10 игроков:**\n\n"
    for i, (user_id, balance) in enumerate(top_players, 1):
        text += f"{i}. ID: {user_id} - {balance} PAK\n"
    
    if query:
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_main_menu())
    else:
        await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_main_menu())

# ========== ИГРА В КУБИК ==========
async def dice_game(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    await query.edit_message_text(
        "🎲 Игра 'Кубик'\n\n"
        "Введите сумму ставки (в PAK) и выберите чет/нечет\n"
        "Пример: 100 чет\n"
        "Пример: 50 нечет",
        reply_markup=get_games_menu()
    )
    context.user_data['game'] = 'dice'

# ========== ИГРА В МНОЖИТЕЛЬ ==========
async def multiplier_game(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    await query.edit_message_text(
        "🎰 Игра 'Множитель'\n\n"
        "Введите сумму ставки и число от 1 до 8\n"
        "Пример: 100 5",
        reply_markup=get_games_menu()
    )
    context.user_data['game'] = 'multiplier'

# ========== РУЛЕТКА ==========
async def roulette_game(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    await query.edit_message_text(
        "🎡 Игра 'Рулетка'\n\n"
        "Введите сумму ставки и число от 1 до 36\n"
        "Пример: 100 17",
        reply_markup=get_games_menu()
    )
    context.user_data['game'] = 'roulette'

# ========== СЛОТЫ ==========
async def slots_game(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    await query.edit_message_text(
        "🎰 Игра 'Слоты'\n\n"
        "Введите сумму ставки\n"
        "Пример: 100",
        reply_markup=get_games_menu()
    )
    context.user_data['game'] = 'slots'

# ========== КАМЕНЬ-НОЖНИЦЫ-БУМАГА ==========
async def rps_game(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    await query.edit_message_text(
        "✊ Камень-Ножницы-Бумага\n\n"
        "Введите сумму ставки и ваш выбор:\n"
        "камень, ножницы или бумага\n"
        "Пример: 100 камень",
        reply_markup=get_games_menu()
    )
    context.user_data['game'] = 'rps'

# ========== БЛЭКДЖЕК ==========
async def blackjack_game(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    await query.edit_message_text(
        "🃏 Блэкджек\n\n"
        "Введите сумму ставки\n"
        "Пример: 100",
        reply_markup=get_games_menu()
    )
    context.user_data['game'] = 'blackjack'

# ========== КОСТИ (СУММА) ==========
async def dice_sum_game(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    await query.edit_message_text(
        "🎲 Игра 'Кости'\n\n"
        "Введите сумму ставки и предсказание (7-12)\n"
        "Пример: 100 7",
        reply_markup=get_games_menu()
    )
    context.user_data['game'] = 'dice_sum'

# ========== ОБРАБОТЧИК СООБЩЕНИЙ ДЛЯ СТАВОК ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'game' not in context.user_data:
        return
    
    user_id = str(update.effective_user.id)
    balances = load_json(BALANCE_FILE)
    balance = balances.get(user_id, 0)
    
    try:
        parts = update.message.text.split()
        game = context.user_data['game']
        
        if game == 'dice':
            bet = int(parts[0])
            choice = parts[1].lower()
            
            if bet > balance:
                await update.message.reply_text("❌ Недостаточно средств!")
                return
            
            dice = random.randint(1, 6)
            result = "чет" if dice % 2 == 0 else "нечет"
            win = (choice == result)
            
            if win:
                win_amount = int(bet * 1.8)
                balances[user_id] += win_amount
                text = f"🎲 Выпало: {dice} ({result})\n✅ Вы выиграли! +{win_amount} PAK"
            else:
                balances[user_id] -= bet
                text = f"🎲 Выпало: {dice} ({result})\n❌ Вы проиграли! -{bet} PAK"
            
            save_json(BALANCE_FILE, balances)
            await update.message.reply_text(f"{text}\n💰 Новый баланс: {balances[user_id]} PAK")
        
        elif game == 'slots':
            bet = int(parts[0])
            
            if bet > balance:
                await update.message.reply_text("❌ Недостаточно средств!")
                return
            
            slots = [random.randint(1, 7) for _ in range(3)]
            if slots[0] == slots[1] == slots[2]:
                win_amount = bet * 10
                balances[user_id] += win_amount
                text = f"🎰 [{slots[0]}] [{slots[1]}] [{slots[2]}]\n🎉 ДЖЕКПОТ! Вы выиграли {win_amount} PAK!"
            elif slots[0] == slots[1] or slots[1] == slots[2] or slots[0] == slots[2]:
                win_amount = bet * 2
                balances[user_id] += win_amount
                text = f"🎰 [{slots[0]}] [{slots[1]}] [{slots[2]}]\n✅ Вы выиграли! +{win_amount} PAK"
            else:
                balances[user_id] -= bet
                text = f"🎰 [{slots[0]}] [{slots[1]}] [{slots[2]}]\n❌ Вы проиграли! -{bet} PAK"
            
            save_json(BALANCE_FILE, balances)
            await update.message.reply_text(f"{text}\n💰 Новый баланс: {balances[user_id]} PAK")
        
        # Добавьте остальные игры по аналогии
        
        del context.user_data['game']
        
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Неправильный формат! Пожалуйста, следуйте инструкции.")

# ========== ГЛАВНАЯ ФУНКЦИЯ ==========
def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    
    if not token:
        print("Ошибка: TELEGRAM_BOT_TOKEN не установлен")
        return
    
    app = Application.builder().token(token).build()
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()

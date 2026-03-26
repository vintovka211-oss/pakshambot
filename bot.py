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

# ========== БАЛАНС ==========
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    balances = load_json(BALANCE_FILE)
    balance = balances.get(user_id, 0)
    rub = balance / RUB_TO_PAK
    await update.message.reply_text(
        f"💰 Баланс: {balance:.0f} PAK ({rub:.2f} ₽)",
        reply_markup=get_main_menu()
    )

# ========== ИГРА 1: КУБИК ==========
async def play_dice_game(update, bet, choice_name):
    user_id = str(update.effective_user.id)
    balances = load_json(BALANCE_FILE)
    current_balance = balances.get(user_id, 0)
    
    if bet > current_balance:
        await update.message.reply_text(f"❌ Недостаточно средств! Баланс: {current_balance:.0f} PAK")
        return
    
    dice = random.randint(1, 6)
    is_even = dice % 2 == 0
    
    if choice_name == "even":
        player_wins = is_even
        player_choice = "ЧЕТНОЕ"
    else:
        player_wins = not is_even
        player_choice = "НЕЧЕТНОЕ"
    
    dice_emoji = ["🎲", "⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
    
    if player_wins:
        win_amount = int(bet * 1.8)
        new_balance = current_balance - bet + win_amount
        balances[user_id] = new_balance
        save_json(BALANCE_FILE, balances)
        
        await update.message.reply_text(
            f"🎲 **КУБИК**\n\n"
            f"Выпало: {dice_emoji[dice]} {dice}\n"
            f"Твой выбор: {player_choice}\n\n"
            f"✅ ВЫИГРЫШ! (x1.8)\n"
            f"💰 Ставка: {bet} PAK\n"
            f"🎉 Выигрыш: {win_amount} PAK\n"
            f"📊 Новый баланс: {new_balance:.0f} PAK",
            parse_mode='Markdown'
        )
    else:
        new_balance = current_balance - bet
        balances[user_id] = new_balance
        save_json(BALANCE_FILE, balances)
        
        await update.message.reply_text(
            f"🎲 **КУБИК**\n\n"
            f"Выпало: {dice_emoji[dice]} {dice}\n"
            f"Твой выбор: {player_choice}\n\n"
            f"❌ ПРОИГРЫШ!\n"
            f"💰 Потеряно: {bet} PAK\n"
            f"📊 Новый баланс: {new_balance:.0f} PAK",
            parse_mode='Markdown'
        )

# ========== ИГРА 2: МНОЖИТЕЛЬ ==========
async def play_multiplier_game(update, bet, chosen_number):
    user_id = str(update.effective_user.id)
    multipliers = [0.25, 0.5, 0.75, 1.0, 1.1, 1.2, 1.3, 1.5]
    random.shuffle(multipliers)
    multiplier = multipliers[chosen_number - 1]
    
    balances = load_json(BALANCE_FILE)
    current_balance = balances.get(user_id, 0)
    
    if bet > current_balance:
        await update.message.reply_text(f"❌ Недостаточно средств! Баланс: {current_balance:.0f} PAK")
        return
    
    win_amount = int(bet * multiplier)
    new_balance = current_balance - bet + win_amount
    balances[user_id] = new_balance
    save_json(BALANCE_FILE, balances)
    
    if multiplier < 1:
        result = "❌ ПРОИГРЫШ!"
    elif multiplier == 1:
        result = "🔄 НИЧЬЯ (вернули ставку)"
    else:
        result = "✅ ВЫИГРЫШ!"
    
    await update.message.reply_text(
        f"🎰 **МНОЖИТЕЛЬ**\n\n"
        f"Твой выбор: цифра {chosen_number}\n"
        f"🎲 Выпал множитель: x{multiplier}\n"
        f"{result}\n"
        f"💰 Ставка: {bet} PAK\n"
        f"🎉 Результат: {win_amount} PAK\n"
        f"📊 Новый баланс: {new_balance:.0f} PAK",
        parse_mode='Markdown'
    )

# ========== ИГРА 3: РУЛЕТКА ==========
async def play_roulette_game(update, bet, choice):
    user_id = str(update.effective_user.id)
    balances = load_json(BALANCE_FILE)
    current_balance = balances.get(user_id, 0)
    
    if bet > current_balance:
        await update.message.reply_text(f"❌ Недостаточно средств! Баланс: {current_balance:.0f} PAK")
        return
    
    result = random.randint(0, 36)
    win_amount = 0
    
    if isinstance(choice, int) and choice == result:
        win_amount = bet * 35
        result_text = f"✅ ВЫИГРЫШ! x35"
    elif choice == "red" and result in [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]:
        win_amount = bet * 2
        result_text = f"✅ ВЫИГРЫШ! x2"
    elif choice == "black" and result in [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]:
        win_amount = bet * 2
        result_text = f"✅ ВЫИГРЫШ! x2"
    elif choice == "even" and result % 2 == 0 and result != 0:
        win_amount = bet * 2
        result_text = f"✅ ВЫИГРЫШ! x2"
    elif choice == "odd" and result % 2 != 0:
        win_amount = bet * 2
        result_text = f"✅ ВЫИГРЫШ! x2"
    else:
        result_text = "❌ ПРОИГРЫШ!"
    
    if win_amount > 0:
        new_balance = current_balance - bet + win_amount
        balances[user_id] = new_balance
        save_json(BALANCE_FILE, balances)
    else:
        new_balance = current_balance - bet
        balances[user_id] = new_balance
        save_json(BALANCE_FILE, balances)
    
    await update.message.reply_text(
        f"🎡 **РУЛЕТКА**\n\n"
        f"Выпало число: {result}\n"
        f"{result_text}\n"
        f"💰 Ставка: {bet} PAK\n"
        f"🎉 Результат: {win_amount} PAK\n"
        f"📊 Новый баланс: {new_balance:.0f} PAK",
        parse_mode='Markdown'
    )

# ========== ИГРА 4: СЛОТЫ ==========
async def play_slots_game(update, bet):
    user_id = str(update.effective_user.id)
    balances = load_json(BALANCE_FILE)
    current_balance = balances.get(user_id, 0)
    
    if bet > current_balance:
        await update.message.reply_text(f"❌ Недостаточно средств! Баланс: {current_balance:.0f} PAK")
        return
    
    symbols = ["🍒", "🍋", "🍊", "🍉", "⭐", "7️⃣", "💎"]
    reel1 = random.choice(symbols)
    reel2 = random.choice(symbols)
    reel3 = random.choice(symbols)
    
    win_amount = 0
    
    if reel1 == reel2 == reel3:
        if reel1 == "7️⃣":
            win_amount = bet * 50
        elif reel1 == "💎":
            win_amount = bet * 25
        elif reel1 == "⭐":
            win_amount = bet * 10
        else:
            win_amount = bet * 5
    elif reel1 == reel2 or reel2 == reel3 or reel1 == reel3:
        win_amount = bet * 2
    
    if win_amount > 0:
        new_balance = current_balance - bet + win_amount
        balances[user_id] = new_balance
        save_json(BALANCE_FILE, balances)
        result_text = f"✅ ВЫИГРЫШ! x{win_amount//bet}"
    else:
        new_balance = current_balance - bet
        balances[user_id] = new_balance
        save_json(BALANCE_FILE, balances)
        result_text = "❌ ПРОИГРЫШ!"
    
    await update.message.reply_text(
        f"🎰 **СЛОТЫ**\n\n"
        f"┌─────┬─────┬─────┐\n"
        f"│  {reel1}  │  {reel2}  │  {reel3}  │\n"
        f"└─────┴─────┴─────┘\n\n"
        f"{result_text}\n"
        f"💰 Ставка: {bet} PAK\n"
        f"🎉 Выигрыш: {win_amount} PAK\n"
        f"📊 Новый баланс: {new_balance:.0f} PAK",
        parse_mode='Markdown'
    )

# ========== ИГРА 5: КАМЕНЬ-НОЖНИЦЫ-БУМАГА ==========
async def play_rps_game(update, bet, choice):
    user_id = str(update.effective_user.id)
    choices = {"камень": "✊", "ножницы": "✌️", "бумага": "✋"}
    bot_choice = random.choice(list(choices.keys()))
    
    balances = load_json(BALANCE_FILE)
    current_balance = balances.get(user_id, 0)
    
    if bet > current_balance:
        await update.message.reply_text(f"❌ Недостаточно средств! Баланс: {current_balance:.0f} PAK")
        return
    
    if choice == bot_choice:
        win_amount = bet
        result = "🔄 НИЧЬЯ"
    elif (choice == "камень" and bot_choice == "ножницы") or \
         (choice == "ножницы" and bot_choice == "бумага") or \
         (choice == "бумага" and bot_choice == "камень"):
        win_amount = bet * 2
        result = "✅ ВЫИГРЫШ!"
    else:
        win_amount = 0
        result = "❌ ПРОИГРЫШ!"
    
    if win_amount > 0:
        new_balance = current_balance - bet + win_amount
        balances[user_id] = new_balance
        save_json(BALANCE_FILE, balances)
    else:
        new_balance = current_balance - bet
        balances[user_id] = new_balance
        save_json(BALANCE_FILE, balances)
    
    await update.message.reply_text(
        f"✊ **КАМЕНЬ-НОЖНИЦЫ-БУМАГА**\n\n"
        f"Твой выбор: {choices[choice]}\n"
        f"Выбор бота: {choices[bot_choice]}\n\n"
        f"{result}\n"
        f"💰 Ставка: {bet} PAK\n"
        f"🎉 Результат: {win_amount} PAK\n"
        f"📊 Новый баланс: {new_balance:.0f} PAK",
        parse_mode='Markdown'
    )

# ========== ИГРА 6: БЛЭКДЖЕК ==========
async def play_blackjack_game(update, bet):
    user_id = str(update.effective_user.id)
    balances = load_json(BALANCE_FILE)
    current_balance = balances.get(user_id, 0)
    
    if bet > current_balance:
        await update.message.reply_text(f"❌ Недостаточно средств! Баланс: {current_balance:.0f} PAK")
        return
    
    def get_card():
        return random.randint(1, 11)
    
    player_cards = [get_card(), get_card()]
    dealer_cards = [get_card(), get_card()]
    player_sum = sum(player_cards)
    dealer_sum = sum(dealer_cards)
    
    while player_sum < 17:
        player_cards.append(get_card())
        player_sum = sum(player_cards)
    
    if player_sum > 21:
        new_balance = current_balance - bet
        balances[user_id] = new_balance
        save_json(BALANCE_FILE, balances)
        await update.message.reply_text(
            f"🃏 **БЛЭКДЖЕК**\n\n"
            f"Твои карты: {player_cards} (сумма {player_sum})\n\n"
            f"❌ ПЕРЕБОР!\n"
            f"💰 Потеряно: {bet} PAK\n"
            f"📊 Новый баланс: {new_balance:.0f} PAK",
            parse_mode='Markdown'
        )
        return
    
    while dealer_sum < 17:
        dealer_cards.append(get_card())
        dealer_sum = sum(dealer_cards)
    
    if dealer_sum > 21 or player_sum > dealer_sum:
        win_amount = bet * 2
        new_balance = current_balance - bet + win_amount
        balances[user_id] = new_balance
        save_json(BALANCE_FILE, balances)
        await update.message.reply_text(
            f"🃏 **БЛЭКДЖЕК**\n\n"
            f"Твои карты: {player_cards} (сумма {player_sum})\n"
            f"Карты дилера: {dealer_cards} (сумма {dealer_sum})\n\n"
            f"✅ ВЫИГРЫШ!\n"
            f"💰 Ставка: {bet} PAK\n"
            f"🎉 Выигрыш: {win_amount} PAK\n"
            f"📊 Новый баланс: {new_balance:.0f} PAK",
            parse_mode='Markdown'
        )
    else:
        new_balance = current_balance - bet
        balances[user_id] = new_balance
        save_json(BALANCE_FILE, balances)
        await update.message.reply_text(
            f"🃏 **БЛЭКДЖЕК**\n\n"
            f"Твои карты: {player_cards} (сумма {player_sum})\n"
            f"Карты дилера: {dealer_cards} (сумма {dealer_sum})\n\n"
            f"❌ ПРОИГРЫШ!\n"
            f"💰 Потеряно: {bet} PAK\n"
            f"📊 Новый баланс: {new_balance:.0f} PAK",
            parse_mode='Markdown'
        )

# ========== ИГРА 7: КОСТИ (СУММА) ==========
async def play_dice_sum_game(update, bet, target_sum):
    user_id = str(update.effective_user.id)
    balances = load_json(BALANCE_FILE)
    current_balance = balances.get(user_id, 0)
    
    if bet > current_balance:
        await update.message.reply_text(f"❌ Недостаточно средств! Баланс: {current_balance:.0f} PAK")
        return
    
    dice1 = random.randint(1, 6)
    dice2 = random.randint(1, 6)
    total = dice1 + dice2
    
    multipliers = {7: 5, 8: 3, 9: 2.5, 10: 2, 11: 3, 12: 5}
    multiplier = multipliers.get(target_sum, 0)
    
    if total == target_sum and multiplier > 0:
        win_amount = int(bet * multiplier)
        new_balance = current_balance - bet + win_amount
        balances[user_id] = new_balance
        save_json(BALANCE_FILE, balances)
        
        await update.message.reply_text(
            f"🎲 **КОСТИ**\n\n"
            f"Выпало: {dice1} + {dice2} = {total}\n"
            f"Твоя ставка: сумма {target_sum}\n\n"
            f"✅ ВЫИГРЫШ! x{multiplier}\n"
            f"💰 Ставка: {bet} PAK\n"
            f"🎉 Выигрыш: {win_amount} PAK\n"
            f"📊 Новый баланс: {new_balance:.0f} PAK",
            parse_mode='Markdown'
        )
    else:
        new_balance = current_balance - bet
        balances[user_id] = new_balance
        save_json(BALANCE_FILE, balances)
        
        await update.message.reply_text(
            f"🎲 **КОСТИ**\n\n"
            f"Выпало: {dice1} + {dice2} = {total}\n"
            f"Твоя ставка: сумма {target_sum}\n\n"
            f"❌ ПРОИГРЫШ!\n"
            f"💰 Потеряно: {bet} PAK\n"
            f"📊 Новый баланс: {new_balance:.0f} PAK",
            parse_mode='Markdown'
        )

# ========== ЕЖЕДНЕВНЫЙ БОНУС ==========
async def daily_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    daily_data = load_json(DAILY_BONUS_FILE)
    
    last_bonus = daily_data.get(user_id, 0)
    current_time = time.time()
    
    if current_time - last_bonus < 86400:
        time_left = 86400 - (current_time - last_bonus)
        hours = int(time_left // 3600)
        minutes = int((time_left % 3600) // 60)
        await update.message.reply_text(f"❌ Бонус уже получен! Следующий через: {hours}ч {minutes}м")
        return
    
    balances = load_json(BALANCE_FILE)
    balances[user_id] = balances.get(user_id, 0) + DAILY_BONUS
    save_json(BALANCE_FILE, balances)
    
    daily_data[user_id] = current_time
    save_json(DAILY_BONUS_FILE, daily_data)
    
    await update.message.reply_text(
        f"🎁 Бонус! +{DAILY_BONUS} PAK\n💰 Новый баланс: {balances[user_id]:.0f} PAK",
        reply_markup=get_main_menu()
    )

# ========== ТОП ИГРОКОВ ==========
async def top_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    balances = load_json(BALANCE_FILE)
    sorted_players = sorted(balances.items(), key=lambda x: x[1], reverse=True)[:10]
    
    if not sorted_players:
        await update.message.reply_text("📊 Топ игроков пока пуст!")
        return
    
    top_text = "🏆 **ТОП 10 ИГРОКОВ** 🏆\n\n"
    for i, (user_id, balance) in enumerate(sorted_players, 1):
        try:
            user = await context.bot.get_chat(int(user_id))
            name = user.first_name[:15] if user.first_name else f"User_{user_id[:5]}"
        except:
            name = f"User_{user_id[:5]}"
        
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
        rub = balance / RUB_TO_PAK
        top_text += f"{medal} {i}. {name} — {balance:.0f} PAK ({rub:.2f} ₽)\n"
    
    await update.message.reply_text(top_text, parse_mode='Markdown')

# ========== СЕКРЕТНАЯ КОМАНДА ДЛЯ АДМИНА ==========
async def secret_give_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        return
    
    if not context.args:
        await update.message.reply_text("❌ /give [сумма] - выдать PAK")
        return
    
    try:
        amount = int(context.args[0])
        balances = load_json(BALANCE_FILE)
        balances[user_id] = balances.get(user_id, 0) + amount
        save_json(BALANCE_FILE, balances)
        rub = amount / RUB_TO_PAK
        await update.message.reply_text(f"✅ Выдано {amount} PAK ({rub:.2f} ₽)\n💰 Новый баланс: {balances[user_id]:.0f} PAK")
    except ValueError:
        await update.message.reply_text("❌ Сумма должна быть числом!")

# ========== ОБРАБОТЧИК КНОПОК ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    balances = load_json(BALANCE_FILE)
    balance = balances.get(user_id, 0)
    
    if query.data == 'balance':
        rub = balance / RUB_TO_PAK
        await query.edit_message_text(f"💰 Баланс: {balance:.0f} PAK ({rub:.2f} ₽)", reply_markup=get_main_menu())
    
    elif query.data == 'games_menu':
        await query.edit_message_text("🎮 **Выбери игру:**", reply_markup=get_games_menu(), parse_mode='Markdown')
    
    elif query.data == 'dice_game':
        await query.edit_message_text(
            f"🎲 **Кубик**\n\n💰 Баланс: {balance:.0f} PAK\n\nНапиши:\n• чет 100\n• нечет 50\n\nВыигрыш x1.8!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='games_menu')]])
        )
    
    elif query.data == 'multiplier_game':
        await query.edit_message_text(
            f"🎰 **Множитель**\n\n💰 Баланс: {balance:.0f} PAK\n\nНапиши: множитель 100 5\n(цифра 1-8)",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='games_menu')]])
        )
    
    elif query.data == 'roulette_game':
        await query.edit_message_text(
            f"🎡 **Рулетка**\n\n💰 Баланс: {balance:.0f} PAK\n\nНапиши:\n• рулетка 100 7\n• рулетка 100 red\n• рулетка 100 even",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='games_menu')]])
        )
    
    elif query.data == 'slots_game':
        await query.edit_message_text(
            f"🎰 **Слоты**\n\n💰 Баланс: {balance:.0f} PAK\n\nНапиши: слоты 100\n\nДжекпот 5000 PAK!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='games_menu')]])
        )
    
    elif query.data == 'rps_game':
        await query.edit_message_text(
            f"✊ **Камень**Камень-Ножницы-Бумага**\n\n💰 Баланс: {balance:.0f} PAK\n\nНапиши: кнб 100 камень",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='games_menu')]])
        )
    
    elif query.data == 'blackjack_game':
        await query.edit_message_text(
            f"🃏 **Блэкджек**\n\n💰 Баланс: {balance:.0f} PAK\n\nНапиши: блэкджек 100",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='games_menu')]])
        )
    
    elif query.data == 'dice_sum_game':
        await query.edit_message_text(
            f"🎲 **Кости (Сумма)**\n\n💰 Баланс: {balance:.0f} PAK\n\nНапиши: кости 100 7\n(сумма 7-12)\n\nВыигрыши:\n7 или 12 → x5\n8 или 11 → x3\n9 или 10 → x2",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='games_menu')]])
        )
    
    elif query.data == 'daily':
        daily_data = load_json(DAILY_BONUS_FILE)
        last_bonus = daily_data.get(user_id, 0)
        current_time = time.time()
        
        if current_time - last_bonus < 86400:
            time_left = 86400 - (current_time - last_bonus)
            hours = int(time_left // 3600)
            minutes = int((time_left % 3600) // 60)
            await query.edit_message_text(
                f"❌ Бонус уже получен!\n⏱️ Следующий через: {hours}ч {minutes}м",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='menu')]])
            )
        else:
            balances[user_id] = balance + DAILY_BONUS
            save_json(BALANCE_FILE, balances)
            daily_data[user_id] = current_time
            save_json(DAILY_BONUS_FILE, daily_data)
            await query.edit_message_text(
                f"🎁 Бонус! +{DAILY_BONUS} PAK\n💰 Новый баланс: {balances[user_id]:.0f} PAK",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='menu')]])
            )
    
    elif query.data == 'top':
        await top_players(update, context)
    
    elif query.data == 'menu':
        await query.edit_message_text("Главное меню:", reply_markup=get_main_menu())

# ========== ОБРАБОТЧИК СООБЩЕНИЙ ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    
    if text.startswith('/'):
        return
    
    # КУБИК
    if text.startswith("чет") or text.startswith("чёт"):
        parts = text.split()
        if len(parts) > 1:
            try:
                bet = int(parts[1])
                await play_dice_game(update, bet, "even")
            except:
                pass
        return
    
    elif text.startswith("нечет") or text.startswith("нечёт"):
        parts = text.split()
        if len(parts) > 1:
            try:
                bet = int(parts[1])
                await play_dice_game(update, bet, "odd")
            except:
                pass
        return
    
    # МНОЖИТЕЛЬ
    elif text.startswith("множитель"):
        parts = text.split()
        if len(parts) > 2:
            try:
                bet = int(parts[1])
                number = int(parts[2])
                if 1 <= number <= 8:
                    await play_multiplier_game(update, bet, number)
            except:
                pass
        return
    
    # РУЛЕТКА
    elif text.startswith("рулетка"):
        parts = text.split()
        if len(parts) > 2:
            try:
                bet = int(parts[1])
                choice = parts[2]
                if choice.isdigit() and 0 <= int(choice) <= 36:
                    await play_roulette_game(update, bet, int(choice))
                elif choice in ["red", "black", "even", "odd"]:
                    await play_roulette_game(update, bet, choice)
            except:
                pass
        return
    
    # СЛОТЫ
    elif text.startswith("слоты"):
        parts = text.split()
        if len(parts) > 1:
            try:
                bet = int(parts[1])
                await play_slots_game(update, bet)
            except:
                pass
        return
    
    # КНБ
    elif text.startswith("кнб"):
        parts = text.split()
        if len(parts) > 2:
            try:
                bet = int(parts[1])
                choice = parts[2]
                if choice in ["камень", "ножницы", "бумага"]:
                    await play_rps_game(update, bet, choice)
            except:
                pass
        return
    
    # БЛЭКДЖЕК
    elif text.startswith("блэкджек"):
        parts = text.split()
        if len(parts) > 1:
            try:
                bet = int(parts[1])
                await play_blackjack_game(update, bet)
            except:
                pass
        return
    
    # КОСТИ
    elif text.startswith("кости"):
        parts = text.split()
        if len(parts) > 2:
            try:
                bet = int(parts[1])
                target = int(parts[2])
                if 7 <= target <= 12:
                    await play_dice_sum_game(update, bet, target)
            except:
                pass
        return

# ========== ЗАПУСК ==========
def main():
    TOKEN = "8593186262:AAGN6sTyBa1RlJ0eVWwNVzgYUb6aVy_H9LA"
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("bonus", daily_bonus))
    application.add_handler(CommandHandler("give", secret_give_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 PAK BOT запущен!")
    print("✅ 7 игр доступно!")
    print("✅ 1 ₽ = 10 PAK")
    application.run_polling()

if __name__ == '__main__':
    main()
```

---

Как играть:

Игра Команда
Кубик чет 100 или нечет 100
Множитель множитель 100 5
Рулетка рулетка 100 7 или рулетка 100 red
Слоты слоты 100
КНБ кнб 100 камень
Блэкджек блэкджек 100
Кости кости 100 7

---

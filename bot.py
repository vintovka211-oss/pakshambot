import json
import os
import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# ========== ФАЙЛЫ ДЛЯ ХРАНЕНИЯ ДАННЫХ ==========
BALANCE_FILE = "balances.json"
REFERRAL_FILE = "referrals.json"
DAILY_BONUS_FILE = "daily_bonus.json"

def load_json(file):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f)

# ========== КОНСТАНТЫ ==========
ADMIN_ID = "8493522297"
REFERRAL_PERCENT = 10
DAILY_BONUS = 50

# ========== ГЛАВНОЕ МЕНЮ ==========
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("💰 Баланс", callback_data='balance')],
        [InlineKeyboardButton("⭐ Пополнить", callback_data='recharge')],
        [InlineKeyboardButton("🎲 Кубик", callback_data='dice_menu')],
        [InlineKeyboardButton("👥 Рефералы", callback_data='referral')],
        [InlineKeyboardButton("🎁 Бонус", callback_data='daily')],
        [InlineKeyboardButton("🏆 Топ", callback_data='top')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== КОМАНДЫ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    balances = load_json(BALANCE_FILE)
    if str(update.effective_user.id) not in balances:
        balances[str(update.effective_user.id)] = 0
        save_json(BALANCE_FILE, balances)
    
    await update.message.reply_text(
        f"👋 Привет, {user_name}!\n\n"
        f"🎮 **Добро пожаловать!**\n\n"
        f"💎 1 Star = 20 ₽\n\n"
        f"🎲 Игры:\n"
        f"• Кубик: чет/нечет (выигрыш x1.8)\n\n"
        f"👥 Приглашай друзей и получай 10% от их пополнений!\n"
        f"🎁 Ежедневный бонус: {DAILY_BONUS} ₽\n\n"
        f"Удачи! 🍀",
        reply_markup=get_main_menu(),
        parse_mode='Markdown'
    )

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    balances = load_json(BALANCE_FILE)
    balance = balances.get(user_id, 0)
    await update.message.reply_text(
        f"💰 Баланс: {balance:.2f} ₽",
        reply_markup=get_main_menu()
    )

async def recharge_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    balances = load_json(BALANCE_FILE)
    balance = balances.get(user_id, 0)
    keyboard = [
        [InlineKeyboardButton("⭐ 5 Stars → +100 ₽", callback_data='pay_5')],
        [InlineKeyboardButton("⭐ 10 Stars → +200 ₽", callback_data='pay_10')],
        [InlineKeyboardButton("⭐ 25 Stars → +500 ₽", callback_data='pay_25')],
        [InlineKeyboardButton("⭐ 50 Stars → +1000 ₽", callback_data='pay_50')],
        [InlineKeyboardButton("⭐ 100 Stars → +2000 ₽", callback_data='pay_100')],
        [InlineKeyboardButton("🔙 Назад", callback_data='menu')]
    ]
    await update.message.reply_text(
        f"💰 Баланс: {balance:.2f} ₽\n\n⭐ Выбери сумму:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========== ИГРА В КУБИК ==========
async def play_dice_game(update, bet, choice_name):
    user_id = str(update.effective_user.id)
    balances = load_json(BALANCE_FILE)
    current_balance = balances.get(user_id, 0)
    
    if bet > current_balance:
        await update.message.reply_text(f"❌ Недостаточно средств!\n💰 Баланс: {current_balance:.2f} ₽")
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
            f"🎲 Бросаем кубик...\n\n"
            f"Выпало: {dice_emoji[dice]} {dice}\n"
            f"Твой выбор: {player_choice}\n\n"
            f"✅ ВЫИГРЫШ! (x1.8)\n"
            f"💰 Ставка: {bet} ₽ → +{win_amount} ₽\n"
            f"📊 Новый баланс: {new_balance:.2f} ₽"
        )
    else:
        new_balance = current_balance - bet
        balances[user_id] = new_balance
        save_json(BALANCE_FILE, balances)
        
        await update.message.reply_text(
            f"🎲 Бросаем кубик...\n\n"
            f"Выпало: {dice_emoji[dice]} {dice}\n"
            f"Твой выбор: {player_choice}\n\n"
            f"❌ ПРОИГРЫШ!\n"
            f"💰 Потеряно: {bet} ₽\n"
            f"📊 Новый баланс: {new_balance:.2f} ₽"
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
        f"🎁 **Ежедневный бонус!**\n\n💰 +{DAILY_BONUS} ₽\n📊 Новый баланс: {balances[user_id]:.2f} ₽",
        parse_mode='Markdown'
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
        top_text += f"{medal} {i}. {name} — {balance:.2f} ₽\n"
    
    await update.message.reply_text(top_text, parse_mode='Markdown')

# ========== СЕКРЕТНАЯ КОМАНДА ДЛЯ АДМИНА ==========
async def secret_give_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id != ADMIN_ID:
        return
    
    if not context.args:
        await update.message.reply_text("❌ /give [сумма]")
        return
    
    try:
        amount = int(context.args[0])
        target_user = user_id
        
        balances = load_json(BALANCE_FILE)
        current_balance = balances.get(target_user, 0)
        new_balance = current_balance + amount
        balances[target_user] = new_balance
        save_json(BALANCE_FILE, balances)
        
        await update.message.reply_text(f"✅ Выдано {amount} ₽\n💰 Новый баланс: {new_balance:.2f} ₽")
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
        await query.edit_message_text(f"💰 Баланс: {balance:.2f} ₽", reply_markup=get_main_menu())
    
    elif query.data == 'recharge':
        keyboard = [
            [InlineKeyboardButton("⭐ 5 Stars → +100 ₽", callback_data='pay_5')],
            [InlineKeyboardButton("⭐ 10 Stars → +200 ₽", callback_data='pay_10')],
            [InlineKeyboardButton("⭐ 25 Stars → +500 ₽", callback_data='pay_25')],
            [InlineKeyboardButton("⭐ 50 Stars → +1000 ₽", callback_data='pay_50')],
            [InlineKeyboardButton("⭐ 100 Stars → +2000 ₽", callback_data='pay_100')],
            [InlineKeyboardButton("🔙 Назад", callback_data='menu')]
        ]
        await query.edit_message_text(f"💰 Баланс: {balance:.2f} ₽\n\n⭐ Выбери сумму:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif query.data == 'dice_menu':
        await query.edit_message_text(
            f"🎲 ИГРА «КУБИК»\n\n💰 Баланс: {balance:.2f} ₽\n\nНапиши:\n• чет 100\n• нечет 50\n\nВыигрыш x1.8!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='menu')]])
        )
    
    elif query.data == 'referral':
        await query.edit_message_text(
            f"👥 **Реферальная система**\n\n"
            f"🔗 Твоя ссылка:\n"
            f"`https://t.me/{context.bot.username}?start=ref`\n\n"
            f"🎁 За каждого друга +10% от его пополнений!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='menu')]]),
            parse_mode='Markdown'
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
                f"🎁 **Ежедневный бонус!**\n\n💰 +{DAILY_BONUS} ₽\n📊 Новый баланс: {balances[user_id]:.2f} ₽",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='menu')]]),
                parse_mode='Markdown'
            )
    
    elif query.data == 'top':
        await top_players(update, context)
    
    elif query.data in ['pay_5', 'pay_10', 'pay_25', 'pay_50', 'pay_100']:
        # Демо-пополнение (без реальных денег)
        amounts = {'pay_5': 100, 'pay_10': 200, 'pay_25': 500, 'pay_50': 1000, 'pay_100': 2000}
        amount = amounts[query.data]
        balances[user_id] = balance + amount
        save_json(BALANCE_FILE, balances)
        await query.edit_message_text(
            f"✅ Пополнено на {amount} ₽ (демо-режим)\n💰 Новый баланс: {balances[user_id]:.2f} ₽",
            reply_markup=get_main_menu()
        )
    
    elif query.data == 'menu':
        await query.edit_message_text("Главное меню:", reply_markup=get_main_menu())

# ========== ОБРАБОТЧИК СООБЩЕНИЙ ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    
    if text.startswith('/'):
        return
    
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

# ========== ЗАПУСК ==========
def main():
    TOKEN = "8593186262:AAGN6sTyBa1RlJ0eVWwNVzgYUb6aVy_H9LA"
    
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("recharge", recharge_command))
    application.add_handler(CommandHandler("bonus", daily_bonus))
    application.add_handler(CommandHandler("give", secret_give_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Бот запущен на Render!")
    print("✅ Режим: демо-пополнение (без реальных денег)")
    application.run_polling()

if __name__ == '__main__':
    main()

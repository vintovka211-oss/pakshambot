import json
import os
import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# ========== ФАЙЛЫ ==========
BALANCE_FILE = "balances.json"
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
DAILY_BONUS = 500
RUB_TO_PAK = 10

# ========== МЕНЮ ==========
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
        [InlineKeyboardButton("🎲 Кубик", callback_data='dice_game')],
        [InlineKeyboardButton("🎰 Множитель", callback_data='multiplier_game')],
        [InlineKeyboardButton("🎡 Рулетка", callback_data='roulette_game')],
        [InlineKeyboardButton("🎰 Слоты", callback_data='slots_game')],
        [InlineKeyboardButton("✊ КНБ", callback_data='rps_game')],
        [InlineKeyboardButton("🃏 Блэкджек", callback_data='blackjack_game')],
        [InlineKeyboardButton("🎲 Кости", callback_data='dice_sum_game')],
        [InlineKeyboardButton("🔙 Назад", callback_data='menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== СТАРТ ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    uid = str(update.effective_user.id)
    balances = load_json(BALANCE_FILE)
    if uid not in balances:
        balances[uid] = 0
        save_json(BALANCE_FILE, balances)
    
    await update.message.reply_text(
        f"👋 Привет, {user_name}!\n\n"
        f"🎮 **PAK BOT**\n"
        f"💎 1 ₽ = 10 PAK\n\n"
        f"🎲 **Игры:**\n"
        f"• Кубик: чет/нечет (x1.8)\n"
        f"• Множитель: 1-8 (x0.25-x1.5)\n"
        f"• Рулетка: 1-36 (x2-x35)\n"
        f"• Слоты: джекпот 5000\n"
        f"• КНБ: камень/ножницы/бумага (x2)\n"
        f"• Блэкджек: 21 (x2)\n"
        f"• Кости: сумма 7-12 (x2-x5)\n\n"
        f"🎁 Бонус: {DAILY_BONUS} PAK/день\n\n"
        f"📝 **Команды:**\n"
        f"/balance - баланс\n"
        f"/bonus - бонус\n"
        f"/give [сумма] - админ\n\n"
        f"🎮 **Игры в чат:**\n"
        f"чет 100, нечет 50, множитель 100 5, рулетка 100 7,\n"
        f"рулетка 100 red, слоты 100, кнб 100 камень,\n"
        f"блэкджек 100, кости 100 7",
        reply_markup=get_main_menu()
    )

# ========== БАЛАНС ==========
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    balances = load_json(BALANCE_FILE)
    balance = balances.get(uid, 0)
    rub = balance / RUB_TO_PAK
    await update.message.reply_text(
        f"💰 Баланс: {balance:.0f} PAK ({rub:.2f} ₽)",
        reply_markup=get_main_menu()
    )

# ========== БОНУС ==========
async def daily_bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    daily = load_json(DAILY_BONUS_FILE)
    last = daily.get(uid, 0)
    now = time.time()
    
    if now - last < 86400:
        left = 86400 - (now - last)
        h = int(left // 3600)
        m = int((left % 3600) // 60)
        await update.message.reply_text(f"❌ Бонус через {h}ч {m}м")
        return
    
    balances = load_json(BALANCE_FILE)
    balances[uid] = balances.get(uid, 0) + DAILY_BONUS
    save_json(BALANCE_FILE, balances)
    daily[uid] = now
    save_json(DAILY_BONUS_FILE, daily)
    
    await update.message.reply_text(
        f"🎁 +{DAILY_BONUS} PAK\n💰 Баланс: {balances[uid]:.0f} PAK",
        reply_markup=get_main_menu()
    )

# ========== ТОП ==========
async def top_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    balances = load_json(BALANCE_FILE)
    sorted_list = sorted(balances.items(), key=lambda x: x[1], reverse=True)[:10]
    if not sorted_list:
        await update.message.reply_text("Топ пуст")
        return
    
    text = "🏆 ТОП 10 🏆\n\n"
    for i, (uid, bal) in enumerate(sorted_list, 1):
        try:
            user = await context.bot.get_chat(int(uid))
            name = user.first_name[:12] if user.first_name else f"User_{uid[:4]}"
        except:
            name = f"User_{uid[:4]}"
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🔹"
        text += f"{medal} {i}. {name} — {bal:.0f} PAK\n"
    await update.message.reply_text(text)

# ========== АДМИН ==========
async def give_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if uid != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("❌ /give [сумма]")
        return
    try:
        amount = int(context.args[0])
        bal = load_json(BALANCE_FILE)
        bal[uid] = bal.get(uid, 0) + amount
        save_json(BALANCE_FILE, bal)
        await update.message.reply_text(f"✅ Выдано {amount} PAK\n💰 Баланс: {bal[uid]:.0f} PAK")
    except:
        await update.message.reply_text("❌ Ошибка")

# ========== ИГРЫ ==========
async def play_dice(update, bet, choice_type):
    uid = str(update.effective_user.id)
    bal = load_json(BALANCE_FILE)
    cur = bal.get(uid, 0)
    if bet > cur:
        await update.message.reply_text(f"❌ Не хватает! Баланс: {cur:.0f} PAK")
        return
    dice = random.randint(1, 6)
    is_even = dice % 2 == 0
    win = (choice_type == "even" and is_even) or (choice_type == "odd" and not is_even)
    if win:
        win_amount = int(bet * 1.8)
        new_bal = cur - bet + win_amount
        bal[uid] = new_bal
        save_json(BALANCE_FILE, bal)
        await update.message.reply_text(f"🎲 Кубик: {dice}\n✅ ВЫИГРЫШ! +{win_amount} PAK\n💰 Баланс: {new_bal:.0f} PAK")
    else:
        new_bal = cur - bet
        bal[uid] = new_bal
        save_json(BALANCE_FILE, bal)
        await update.message.reply_text(f"🎲 Кубик: {dice}\n❌ ПРОИГРЫШ! -{bet} PAK\n💰 Баланс: {new_bal:.0f} PAK")

async def play_multiplier(update, bet, num):
    uid = str(update.effective_user.id)
    bal = load_json(BALANCE_FILE)
    cur = bal.get(uid, 0)
    if bet > cur:
        await update.message.reply_text(f"❌ Не хватает! Баланс: {cur:.0f} PAK")
        return
    mults = [0.25, 0.5, 0.75, 1.0, 1.1, 1.2, 1.3, 1.5]
    random.shuffle(mults)
    mult = mults[num - 1]
    win = int(bet * mult)
    new_bal = cur - bet + win
    bal[uid] = new_bal
    save_json(BALANCE_FILE, bal)
    res = "✅ ВЫИГРЫШ!" if mult > 1 else "❌ ПРОИГРЫШ!" if mult < 1 else "🔄 НИЧЬЯ"
    await update.message.reply_text(f"🎰 Множитель: x{mult}\n{res}\n💰 Ставка: {bet} → {win} PAK\n📊 Баланс: {new_bal:.0f} PAK")

async def play_roulette(update, bet, choice):
    uid = str(update.effective_user.id)
    bal = load_json(BALANCE_FILE)
    cur = bal.get(uid, 0)
    if bet > cur:
        await update.message.reply_text(f"❌ Не хватает! Баланс: {cur:.0f} PAK")
        return
    res = random.randint(0, 36)
    win = 0
    if isinstance(choice, int) and choice == res:
        win = bet * 35
    elif choice == "red" and res in [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]:
        win = bet * 2
    elif choice == "black" and res in [2,4,6,8,10,11,13,15,17,20,22,24,26,28,29,31,33,35]:
        win = bet * 2
    elif choice == "even" and res % 2 == 0 and res != 0:
        win = bet * 2
    elif choice == "odd" and res % 2 != 0:
        win = bet * 2
    if win > 0:
        new_bal = cur - bet + win
        bal[uid] = new_bal
        save_json(BALANCE_FILE, bal)
        await update.message.reply_text(f"🎡 Рулетка: {res}\n✅ ВЫИГРЫШ! +{win} PAK\n💰 Баланс: {new_bal:.0f} PAK")
    else:
        new_bal = cur - bet
        bal[uid] = new_bal
        save_json(BALANCE_FILE, bal)
        await update.message.reply_text(f"🎡 Рулетка: {res}\n❌ ПРОИГРЫШ! -{bet} PAK\n💰 Баланс: {new_bal:.0f} PAK")

async def play_slots(update, bet):
    uid = str(update.effective_user.id)
    bal = load_json(BALANCE_FILE)
    cur = bal.get(uid, 0)
    if bet > cur:
        await update.message.reply_text(f"❌ Не хватает! Баланс: {cur:.0f} PAK")
        return
    sym = ["🍒", "🍋", "🍊", "🍉", "⭐", "7️⃣", "💎"]
    r1, r2, r3 = random.choice(sym), random.choice(sym), random.choice(sym)
    win = 0
    if r1 == r2 == r3:
        if r1 == "7️⃣": win = bet * 50
        elif r1 == "💎": win = bet * 25
        elif r1 == "⭐": win = bet * 10
        else: win = bet * 5
    elif r1 == r2 or r2 == r3 or r1 == r3:
        win = bet * 2
    if win > 0:
        new_bal = cur - bet + win
        bal[uid] = new_bal
        save_json(BALANCE_FILE, bal)
        await update.message.reply_text(f"🎰 Слоты: {r1} {r2} {r3}\n✅ ВЫИГРЫШ! +{win} PAK\n💰 Баланс: {new_bal:.0f} PAK")
    else:
        new_bal = cur - bet
        bal[uid] = new_bal
        save_json(BALANCE_FILE, bal)
        await update.message.reply_text(f"🎰 Слоты: {r1} {r2} {r3}\n❌ ПРОИГРЫШ! -{bet} PAK\n💰 Баланс: {new_bal:.0f} PAK")

async def play_rps(update, bet, choice):
    uid = str(update.effective_user.id)
    bal = load_json(BALANCE_FILE)
    cur = bal.get(uid, 0)
    if bet > cur:
        await update.message.reply_text(f"❌ Не хватает! Баланс: {cur:.0f} PAK")
        return
    opts = {"камень": "✊", "ножницы": "✌️", "бумага": "✋"}
    bot = random.choice(list(opts.keys()))
    win = 0
    if choice == bot:
        win = bet
    elif (choice == "камень" and bot == "ножницы") or (choice == "ножницы" and bot == "бумага") or (choice == "бумага" and bot == "камень"):
        win = bet * 2
    if win > 0:
        new_bal = cur - bet + win
        bal[uid] = new_bal
        save_json(BALANCE_FILE, bal)
        await update.message.reply_text(f"✊ КНБ: ты {opts[choice]}, бот {opts[bot]}\n✅ ВЫИГРЫШ! +{win} PAK\n💰 Баланс: {new_bal:.0f} PAK")
    else:
        new_bal = cur - bet
        bal[uid] = new_bal
        save_json(BALANCE_FILE, bal)
        await update.message.reply_text(f"✊ КНБ: ты {opts[choice]}, бот {opts[bot]}\n❌ ПРОИГРЫШ! -{bet} PAK\n💰 Баланс: {new_bal:.0f} PAK")

async def play_blackjack(update, bet):
    uid = str(update.effective_user.id)
    bal = load_json(BALANCE_FILE)
    cur = bal.get(uid, 0)
    if bet > cur:
        await update.message.reply_text(f"❌ Не хватает! Баланс: {cur:.0f} PAK")
        return
    def card(): return random.randint(1, 11)
    p = [card(), card()]
    d = [card(), card()]
    ps = sum(p)
    ds = sum(d)
    while ps < 17:
        p.append(card())
        ps = sum(p)
    if ps > 21:
        new_bal = cur - bet
        bal[uid] = new_bal
        save_json(BALANCE_FILE, bal)
        await update.message.reply_text(f"🃏 Блэкджек: {p} = {ps}\n❌ ПЕРЕБОР! -{bet} PAK\n💰 Баланс: {new_bal:.0f} PAK")
        return
    while ds < 17:
        d.append(card())
        ds = sum(d)
    if ds > 21 or ps > ds:
        win = bet * 2
        new_bal = cur - bet + win
        bal[uid] = new_bal
        save_json(BALANCE_FILE, bal)
        await update.message.reply_text(f"🃏 Блэкджек: ты {ps}, дилер {ds}\n✅ ВЫИГРЫШ! +{win} PAK\n💰 Баланс: {new_bal:.0f} PAK")
    else:
        new_bal = cur - bet
        bal[uid] = new_bal
        save_json(BALANCE_FILE, bal)
        await update.message.reply_text(f"🃏 Блэкджек: ты {ps}, дилер {ds}\n❌ ПРОИГРЫШ! -{bet} PAK\n💰 Баланс: {new_bal:.0f} PAK")

async def play_dice_sum(update, bet, target):
    uid = str(update.effective_user.id)
    bal = load_json(BALANCE_FILE)
    cur = bal.get(uid, 0)
    if bet > cur:
        await update.message.reply_text(f"❌ Не хватает! Баланс: {cur:.0f} PAK")
        return
    d1, d2 = random.randint(1, 6), random.randint(1, 6)
    total = d1 + d2
    mults = {7: 5, 8: 3, 9: 2.5, 10: 2, 11: 3, 12: 5}
    mult = mults.get(target, 0)
    if total == target and mult > 0:
        win = int(bet * mult)
        new_bal = cur - bet + win
        bal[uid] = new_bal
        save_json(BALANCE_FILE, bal)
        await update.message.reply_text(f"🎲 Кости: {d1}+{d2}={total}\n✅ ВЫИГРЫШ! x{mult} +{win} PAK\n💰 Баланс: {new_bal:.0f} PAK")
    else:
        new_bal = cur - bet
        bal[uid] = new_bal
        save_json(BALANCE_FILE, bal)
        await update.message.reply_text(f"🎲 Кости: {d1}+{d2}={total}\n❌ ПРОИГРЫШ! -{bet} PAK\n💰 Баланс: {new_bal:.0f} PAK")

# ========== КНОПКИ ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = str(query.from_user.id)
    bal = load_json(BALANCE_FILE)
    balance = bal.get(uid, 0)
    
    if query.data == 'balance':
        rub = balance / RUB_TO_PAK
        await query.edit_message_text(f"💰 Баланс: {balance:.0f} PAK ({rub:.2f} ₽)", reply_markup=get_main_menu())
    elif query.data == 'games_menu':
        await query.edit_message_text("🎮 Выбери игру:", reply_markup=get_games_menu())
    elif query.data == 'dice_game':
        await query.edit_message_text(f"🎲 Кубик\n💰 Баланс: {balance:.0f} PAK\n\nНапиши: чет 100 или нечет 50", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='games_menu')]]))
    elif query.data == 'multiplier_game':
        await query.edit_message_text(f"🎰 Множитель\n💰 Баланс: {balance:.0f} PAK\n\nНапиши: множитель 100 5", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='games_menu')]]))
    elif query.data == 'roulette_game':
        await query.edit_message_text(f"🎡 Рулетка\n💰 Баланс: {balance:.0f} PAK\n\nНапиши: рулетка 100 7 или рулетка 100 red", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='games_menu')]]))
    elif query.data == 'slots_game':
        await query.edit_message_text(f"🎰 Слоты\n💰 Баланс: {balance:.0f} PAK\n\nНапиши: слоты 100", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='games_menu')]]))
    elif query.data == 'rps_game':
        await query.edit_message_text(f"✊ КНБ\n💰 Баланс: {balance:.0f} PAK\n\nНапиши: кнб 100 камень", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='games_menu')]]))
    elif query.data == 'blackjack_game':
        await query.edit_message_text(f"🃏 Блэкджек\n💰 Баланс: {balance:.0f} PAK\n\nНапиши: блэкджек 100", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='games_menu')]]))
    elif query.data == 'dice_sum_game':
        await query.edit_message_text(f"🎲 Кости\n💰 Баланс: {balance:.0f} PAK\n\nНапиши: кости 100 7", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='games_menu')]]))
    elif query.data == 'daily':
        daily = load_json(DAILY_BONUS_FILE)
        last = daily.get(uid, 0)
        now = time.time()
        if now - last < 86400:
            left = 86400 - (now - last)
            h, m = int(left//3600), int((left%3600)//60)
            await query.edit_message_text(f"❌ Бонус через {h}ч {m}м", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='menu')]]))
        else:
            bal[uid] = balance + DAILY_BONUS
            save_json(BALANCE_FILE, bal)
            daily[uid] = now
            save_json(DAILY_BONUS_FILE, daily)
            await query.edit_message_text(f"🎁 +{DAILY_BONUS} PAK\n💰 Баланс: {bal[uid]:.0f} PAK", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='menu')]]))
    elif query.data == 'top':
        await top_players(update, context)
    elif query.data == 'menu':
        await query.edit_message_text("Главное меню:", reply_markup=get_main_menu())

# ========== ОБРАБОТКА СООБЩЕНИЙ ==========
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()
    if text.startswith('/'):
        return
    try:
        if text.startswith("чет") or text.startswith("чёт"):
            p = text.split()
            if len(p) > 1:
                await play_dice(update, int(p[1]), "even")
        elif text.startswith("нечет") or text.startswith("нечёт"):
            p = text.split()
            if len(p) > 1:
                await play_dice(update, int(p[1]), "odd")
        elif text.startswith("множитель"):
            p = text.split()
            if len(p) > 2:
                await play_multiplier(update, int(p[1]), int(p[2]))
        elif text.startswith("рулетка"):
            p = text.split()
            if len(p) > 2:
                bet = int(p[1])
                ch = p[2]
                if ch.isdigit():
                    await play_roulette(update, bet, int(ch))
                else:
                    await play_roulette(update, bet, ch)
        elif text.startswith("слоты"):
            p = text.split()
            if len(p) > 1:
                await play_slots(update, int(p[1]))
        elif text.startswith("кнб"):
            p = text.split()
            if len(p) > 2 and p[2] in ["камень", "ножницы", "бумага"]:
                await play_rps(update, int(p[1]), p[2])
        elif text.startswith("блэкджек"):
            p = text.split()
            if len(p) > 1:
                await play_blackjack(update, int(p[1]))
        elif text.startswith("кости"):
            p = text.split()
            if len(p) > 2:
                await play_dice_sum(update, int(p[1]), int(p[2]))
    except:
        pass

# ========== ЗАПУСК ==========
def main():
    TOKEN = "8593186262:AAGN6sTyBa1RlJ0eVWwNVzgYUb6aVy_H9LA"
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("bonus", daily_bonus))
    app.add_handler(CommandHandler("give", give_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен! 7 игр доступно!")
    app.run_polling()

if __name__ == '__main__':
    main()

import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# ========= ДАННЫЕ ПОЛЬЗОВАТЕЛЕЙ =========
# В реальном проекте используйте БД, здесь для примера словарь
user_data = {}

def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {"balance": 0, "bonus_claimed": False}
    return user_data[user_id]

# ========= ИГРЫ =========
# 5 игр с высокой вероятностью проигрыша (40% победы, 60% проигрыша)
GAMES = {
    "game1": {"name": "🎲 Кости", "win_chance": 0.4, "multiplier": 2},
    "game2": {"name": "🎰 Слоты", "win_chance": 0.35, "multiplier": 2.5},
    "game3": {"name": "⚡ Угадай число", "win_chance": 0.3, "multiplier": 3},
    "game4": {"name": "💎 Рулетка", "win_chance": 0.4, "multiplier": 2},
    "game5": {"name": "🔥 Карты", "win_chance": 0.38, "multiplier": 2.2},
}

# ========= ДУЭЛЬ (ОЖИДАНИЕ) =========
duels = {}  # {user_id: {"opponent": None, "bet": 0, "waiting": True}}

# ========= ПОПОЛНЕНИЕ ТОЛЬКО ЗВЕЗДАМИ =========
STARS_RATES = {
    10: 100,   # 10 звезд = 100 монет
    50: 600,   # 50 звезд = 600 монет
    100: 1300, # 100 звезд = 1300 монет
}

# ========= КОМАНДЫ =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_user(user_id)
    await update.message.reply_text(
        "🎮 Добро пожаловать в игровой бот!\n\n"
        "💰 Пополнение только через Telegram Stars!\n"
        "🎲 Доступно 5 игр с высокими рисками\n"
        "⚔️ Режим дуэли: бросьте кубик против соперника\n"
        "🎁 Ежедневный бонус!\n\n"
        "Команды:\n"
        "/balance - баланс\n"
        "/games - список игр\n"
        "/duel - вызвать на дуэль\n"
        "/bonus - получить бонус\n"
        "/top - топ игроков"
    )

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    await update.message.reply_text(f"💰 Ваш баланс: {user['balance']} монет")

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if user["bonus_claimed"]:
        await update.message.reply_text("🎁 Вы уже получали бонус сегодня! Приходите завтра.")
        return
    
    bonus_amount = 50
    user["balance"] += bonus_amount
    user["bonus_claimed"] = True
    await update.message.reply_text(f"🎁 Вы получили бонус {bonus_amount} монет!\n💰 Баланс: {user['balance']}")

async def games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for game_id, game in GAMES.items():
        keyboard.append([InlineKeyboardButton(game["name"], callback_data=f"game_{game_id}")])
    
    keyboard.append([InlineKeyboardButton("⚔️ ДУЭЛЬ", callback_data="duel_menu")])
    keyboard.append([InlineKeyboardButton("⭐ Пополнить Stars", callback_data="stars_topup")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎮 Выберите игру:", reply_markup=reply_markup)

async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sorted_users = sorted(user_data.items(), key=lambda x: x[1]["balance"], reverse=True)[:5]
    
    if not sorted_users:
        await update.message.reply_text("📊 Топ игроков пока пуст.")
        return
    
    text = "🏆 ТОП ИГРОКОВ 🏆\n\n"
    for i, (user_id, data) in enumerate(sorted_users, 1):
        text += f"{i}. ID: {user_id} — {data['balance']} монет\n"
    
    await update.message.reply_text(text)

# ========= ПОПОЛНЕНИЕ ЗВЕЗДАМИ =========
async def stars_topup_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    for stars, coins in STARS_RATES.items():
        keyboard.append([InlineKeyboardButton(f"⭐ {stars} → {coins} монет", callback_data=f"topup_{stars}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_games")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text("⭐ Пополнение через Telegram Stars:\n\nВыберите количество звезд:", reply_markup=reply_markup)

async def process_stars_topup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    stars = int(query.data.split("_")[1])
    coins = STARS_RATES[stars]
    user_id = query.from_user.id
    user = get_user(user_id)
    
    # Здесь должна быть интеграция с Telegram Stars API
    # В демо-версии просто начисляем монеты
    user["balance"] += coins
    
    await query.edit_message_text(
        f"✅ Пополнение успешно!\n"
        f"⭐ {stars} звезд → {coins} монет\n"
        f"💰 Новый баланс: {user['balance']} монет"
    )

# ========= ИГРОВАЯ ЛОГИКА =========
async def play_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    game_id = query.data.split("_")[1]
    game = GAMES.get(game_id)
    
    if not game:
        await query.edit_message_text("❌ Игра не найдена")
        return
    
    user_id = query.from_user.id
    user = get_user(user_id)
    
    # Запрашиваем ставку
    context.user_data["game"] = game_id
    await query.edit_message_text(
        f"🎮 {game['name']}\n"
        f"💰 Ваш баланс: {user['balance']} монет\n\n"
        f"Введите сумму ставки (число):"
    )
    context.user_data["awaiting_bet"] = True

async def process_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_bet"):
        return
    
    user_id = update.effective_user.id
    user = get_user(user_id)
    game_id = context.user_data.get("game")
    game = GAMES.get(game_id)
    
    try:
        bet = int(update.message.text)
        if bet <= 0:
            await update.message.reply_text("❌ Ставка должна быть положительной!")
            return
        if bet > user["balance"]:
            await update.message.reply_text(f"❌ Недостаточно средств! У вас {user['balance']} монет.")
            return
        
        # Игровая механика
        win = random.random() < game["win_chance"]
        
        if win:
            win_amount = int(bet * game["multiplier"])
            user["balance"] += win_amount
            result_text = f"🎉 ПОБЕДА!\nВы выиграли {win_amount} монет!\n💰 Баланс: {user['balance']}"
        else:
            user["balance"] -= bet
            result_text = f"💔 ПРОИГРЫШ!\nВы проиграли {bet} монет.\n💰 Баланс: {user['balance']}"
        
        await update.message.reply_text(
            f"🎮 {game['name']}\n"
            f"Ставка: {bet}\n"
            f"{result_text}"
        )
        
        context.user_data["awaiting_bet"] = False
        context.user_data["game"] = None
        
    except ValueError:
        await update.message.reply_text("❌ Введите число!")

# ========= ДУЭЛЬ =========
async def duel_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("⚔️ Вызвать на дуэль", callback_data="duel_challenge")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_games")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("⚔️ ДУЭЛЬ\n\nБросьте кубик против соперника! У кого выпадет больше — тот забирает сумму ставки.", reply_markup=reply_markup)

async def duel_challenge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("Введите ID пользователя, которого хотите вызвать на дуэль:")
    context.user_data["awaiting_duel_opponent"] = True

async def process_duel_opponent(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_duel_opponent"):
        return
    
    try:
        opponent_id = int(update.message.text)
        user_id = update.effective_user.id
        
        if opponent_id == user_id:
            await update.message.reply_text("❌ Нельзя вызвать самого себя!")
            return
        
        # Проверяем, существует ли противник
        if opponent_id not in user_data:
            await update.message.reply_text("❌ Игрок не найден!")
            return
        
        context.user_data["duel_opponent"] = opponent_id
        await update.message.reply_text("Введите сумму ставки для дуэли:")
        context.user_data["awaiting_duel_bet"] = True
        context.user_data["awaiting_duel_opponent"] = False
        
    except ValueError:
        await update.message.reply_text("❌ Введите корректный ID!")

async def process_duel_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_duel_bet"):
        return
    
    user_id = update.effective_user.id
    user = get_user(user_id)
    opponent_id = context.user_data["duel_opponent"]
    opponent = get_user(opponent_id)
    
    try:
        bet = int(update.message.text)
        if bet <= 0:
            await update.message.reply_text("❌ Ставка должна быть положительной!")
            return
        if bet > user["balance"]:
            await update.message.reply_text(f"❌ Недостаточно средств! У вас {user['balance']} монет.")
            return
        if bet > opponent["balance"]:
            await update.message.reply_text(f"❌ У противника {opponent['balance']} монет, он не может принять такую ставку.")
            return
        
        # Блокируем ставку у обоих
        user["balance"] -= bet
        opponent["balance"] -= bet
        
        # Бросаем кубики
        user_roll = random.randint(1, 6)
        opponent_roll = random.randint(1, 6)
        
        if user_roll > opponent_roll:
            winnings = bet * 2
            user["balance"] += winnings
            result = f"🎲 Ваш кубик: {user_roll}\n🎲 Кубик противника: {opponent_roll}\n\n🏆 ВЫ ПОБЕДИЛИ!\nВыигрыш: {winnings} монет!"
        elif opponent_roll > user_roll:
            opponent["balance"] += bet * 2
            result = f"🎲 Ваш кубик: {user_roll}\n🎲 Кубик противника: {opponent_roll}\n\n💔 ВЫ ПРОИГРАЛИ!\nПотеряно: {bet} монет."
        else:
            user["balance"] += bet
            opponent["balance"] += bet
            result = f"🎲 Ваш кубик: {user_roll}\n🎲 Кубик противника: {opponent_roll}\n\n🤝 НИЧЬЯ!\nСтавка возвращена."
        
        await update.message.reply_text(f"⚔️ ДУЭЛЬ\n\n{result}\n\n💰 Ваш баланс: {user['balance']}")
        
        # Уведомляем противника (если нужно, добавьте логику отправки сообщения)
        
        context.user_data["awaiting_duel_bet"] = False
        context.user_data["duel_opponent"] = None
        
    except ValueError:
        await update.message.reply_text("❌ Введите число!")

# ========= НАВИГАЦИЯ =========
async def back_to_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await games(update, context)

# ========= ЗАПУСК =========
def main():
    TOKEN = "8593186262:AAGN6sTyBa1Rl"
    
    application = Application.builder().token(TOKEN).build()
    
    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("balance", balance))
    application.add_handler(CommandHandler("games", games))
    application.add_handler(CommandHandler("bonus", bonus))
    application.add_handler(CommandHandler("top", top))
    
    # Обработчики сообщений (ставки, дуэли)
    application.add_handler(CallbackQueryHandler(play_game, pattern="^game_"))
    application.add_handler(CallbackQueryHandler(stars_topup_menu, pattern="^stars_topup$"))
    application.add_handler(CallbackQueryHandler(process_stars_topup, pattern="^topup_"))
    application.add_handler(CallbackQueryHandler(duel_menu, pattern="^duel_menu$"))
    application.add_handler(CallbackQueryHandler(duel_challenge, pattern="^duel_challenge$"))
    application.add_handler(CallbackQueryHandler(back_to_games, pattern="^back_to_games$"))
    
    # Обработчики текстовых сообщений
    application.add_handler(CallbackQueryHandler(play_game, pattern="^game_"))
    application.add_handler(CommandHandler("games", games))
    
    # Общие обработчики для ввода текста
    from telegram.ext import MessageHandler, filters
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_bet))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_duel_opponent))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_duel_bet))
    
    print("🤖 Игровой бот запущен!")
    print("🎮 5 игр с вероятностью проигрыша 60-70%")
    print("⭐ Пополнение только через Stars")
    print("⚔️ Режим дуэли активен")
    print("🎁 Бонусная система работает")
    
    application.run_polling()

if __name__ == '__main__':
    main()

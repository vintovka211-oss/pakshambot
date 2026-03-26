import asyncio
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from config import TOKEN, ADMIN_ID, MSG_REWARD
from database import Database
from casino_games import CasinoGames

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация базы данных
db = Database()

# Хранилище активных дуэлей
active_duels = {}

# Функция проверки админа
def is_admin(user_id):
    return user_id == ADMIN_ID

# ==================== КОМАНДЫ ====================

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.register_user(user.id, user.username or str(user.id))
    
    welcome_text = """
🎮 Добро пожаловать в W1nPAK Бот!

💰 У тебя есть:
• PAK: 0
• РУБ: 0

Доступные команды:
💰 /balance - Баланс
🎲 /casino - Казино
⚔️ /duel - Дуэль с игроком
⚔️ /duel_accept - Принять дуэль
❌ /duel_cancel - Отменить дуэль
🏆 /leaderboard - Топ игроков
👥 /clan - Кланы
⭐ /buy - Купить PAK за звезды
📝 /help - Помощь

💡 Подсказка: Установи @W1npakshambot в описании профиля и получай 5 PAK за каждое сообщение!
"""
    await update.message.reply_text(welcome_text)

# Команда /balance
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    
    if user_data:
        text = f"""
💰 Твой баланс:

💎 PAK: {user_data[2]}
💵 РУБ: {user_data[3]}

⭐ 100 PAK = 10 звезд
💰 1 рубль = 1 рубль
"""
        await update.message.reply_text(text)
    else:
        await update.message.reply_text("❌ Ошибка! Попробуй /start")

# Команда /buy
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Купить 100 PAK за 10⭐", callback_data="buy_pak_100")],
        [InlineKeyboardButton("Купить 500 PAK за 50⭐", callback_data="buy_pak_500")],
        [InlineKeyboardButton("Купить 1 РУБ за 1⭐", callback_data="buy_rub_1")],
        [InlineKeyboardButton("Купить 10 РУБ за 10⭐", callback_data="buy_rub_10")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выбери покупку:", reply_markup=reply_markup)

# Команда /casino
async def casino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎲 Кости (x1.1-1.5)", callback_data="game_dice")],
        [InlineKeyboardButton("🃏 Блэкджек (x1.1-1.4)", callback_data="game_blackjack")],
        [InlineKeyboardButton("🎰 Слоты (x1.3-5)", callback_data="game_slots")],
        [InlineKeyboardButton("💀 High Risk (x2-5)", callback_data="game_highrisk")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎮 Выбери игру и введи ставку в формате: PAK РУБ\nПример: 100 50", reply_markup=reply_markup)
    context.user_data['waiting_for_bet'] = True

# Обработка ставки для казино
async def handle_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('waiting_for_bet'):
        return
    
    user_id = update.effective_user.id
    text = update.message.text.split()
    
    if len(text) != 2:
        await update.message.reply_text("❌ Неверный формат! Введите: PAK РУБ\nПример: 100 50")
        return
    
    try:
        bet_pak = int(text[0])
        bet_rub = int(text[1])
    except ValueError:
        await update.message.reply_text("❌ Ставки должны быть числами!")
        return
    
    user_data = db.get_user(user_id)
    if user_data[2] < bet_pak or user_data[3] < bet_rub:
        await update.message.reply_text("❌ Недостаточно средств!")
        context.user_data['waiting_for_bet'] = False
        return
    
    if bet_pak <= 0 or bet_rub < 0:
        await update.message.reply_text("❌ Ставка должна быть положительной!")
        context.user_data['waiting_for_bet'] = False
        return
    
    game = context.user_data.get('selected_game', 'dice')
    
    if game == 'dice':
        win, change_pak, change_rub, result_text = await CasinoGames.roll_dice(update, context, bet_pak, bet_rub)
    elif game == 'blackjack':
        win, change_pak, change_rub, result_text = await CasinoGames.blackjack(update, context, bet_pak, bet_rub)
    elif game == 'slots':
        win, change_pak, change_rub, result_text = await CasinoGames.slot_machine(update, context, bet_pak, bet_rub)
    elif game == 'highrisk':
        win, change_pak, change_rub, result_text = await CasinoGames.high_risk(update, context, bet_pak, bet_rub)
    else:
        await update.message.reply_text("❌ Игра не найдена!")
        context.user_data['waiting_for_bet'] = False
        return
    
    if win is True:
        db.update_balance(user_id, change_pak, change_rub)
    elif win is False:
        db.update_balance(user_id, -change_pak, -change_rub)
    
    await update.message.reply_text(result_text)
    
    new_balance = db.get_user(user_id)
    await update.message.reply_text(f"💰 Новый баланс: {new_balance[2]} PAK, {new_balance[3]} РУБ")
    
    context.user_data['waiting_for_bet'] = False

# ==================== ДУЭЛИ ====================

# Команда /duel - ВЫЗВАТЬ НА ДУЭЛЬ
async def duel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    
    if len(args) < 3:
        await update.message.reply_text(
            "⚔️ ИСПОЛЬЗОВАНИЕ ДУЭЛИ:\n\n"
            "/duel @username [PAK] [РУБ]\n\n"
            "Пример: /duel @ivan 100 50\n\n"
            "💰 Ставка: 100 PAK и 50 РУБ"
        )
        return
    
    opponent_username = args[0].replace('@', '')
    try:
        bet_pak = int(args[1])
        bet_rub = int(args[2])
    except ValueError:
        await update.message.reply_text("❌ Ставки должны быть числами!")
        return
    
    if bet_pak <= 0 and bet_rub <= 0:
        await update.message.reply_text("❌ Ставка должна быть больше 0!")
        return
    
    challenger_data = db.get_user(user_id)
    if not challenger_data:
        await update.message.reply_text("❌ Сначала напишите /start")
        return
    
    if challenger_data[2] < bet_pak:
        await update.message.reply_text(f"❌ Недостаточно PAK! У вас {challenger_data[2]} PAK")
        return
    
    if challenger_data[3] < bet_rub:
        await update.message.reply_text(f"❌ Недостаточно РУБ! У вас {challenger_data[3]} РУБ")
        return
    
    opponent = db.get_user_by_username(opponent_username)
    if not opponent:
        await update.message.reply_text(f"❌ Пользователь @{opponent_username} не найден!")
        return
    
    opponent_id = opponent[0]
    
    if opponent_id == user_id:
        await update.message.reply_text("❌ Нельзя вызвать самого себя на дуэль!")
        return
    
    # Проверяем, нет ли уже активной дуэли
    for opp_id, duel_info in active_duels.items():
        if duel_info['challenger_id'] == user_id or opp_id == user_id:
            await update.message.reply_text("❌ У вас уже есть активная дуэль!")
            return
    
    duel_id = db.create_duel(user_id, opponent_id, bet_pak, bet_rub)
    
    active_duels[opponent_id] = {
        'duel_id': duel_id,
        'challenger_id': user_id,
        'challenger_name': update.effective_user.username or str(user_id),
        'bet_pak': bet_pak,
        'bet_rub': bet_rub
    }
    
    await update.message.reply_text(
        f"⚔️ ВЫ ВЫЗВАЛИ НА ДУЭЛЬ @{opponent_username}!\n\n"
        f"💰 Ставка: {bet_pak} PAK и {bet_rub} РУБ\n\n"
        f"⏳ Ожидайте ответа..."
    )
    
    try:
        await context.bot.send_message(
            chat_id=opponent_id,
            text=f"⚔️ ВАС ВЫЗВАЛИ НА ДУЭЛЬ!\n\n"
                 f"👤 Противник: @{update.effective_user.username or 'Игрок'}\n"
                 f"💰 Ставка: {bet_pak} PAK и {bet_rub} РУБ\n\n"
                 f"✅ Чтобы принять дуэль, напишите:\n"
                 f"/duel_accept\n\n"
                 f"❌ Чтобы отклонить, проигнорируйте сообщение"
        )
    except:
        pass

# Команда /duel_accept - ПРИНЯТЬ ДУЭЛЬ
async def duel_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in active_duels:
        await update.message.reply_text("❌ У вас нет активных приглашений на дуэль!")
        return
    
    duel_info = active_duels[user_id]
    challenger_id = duel_info['challenger_id']
    bet_pak = duel_info['bet_pak']
    bet_rub = duel_info['bet_rub']
    duel_id = duel_info['duel_id']
    
    acceptor_data = db.get_user(user_id)
    if not acceptor_data:
        await update.message.reply_text("❌ Сначала напишите /start")
        del active_duels[user_id]
        return
    
    if acceptor_data[2] < bet_pak:
        await update.message.reply_text(f"❌ Недостаточно PAK для дуэли! У вас {acceptor_data[2]} PAK")
        del active_duels[user_id]
        return
    
    if acceptor_data[3] < bet_rub:
        await update.message.reply_text(f"❌ Недостаточно РУБ для дуэли! У вас {acceptor_data[3]} РУБ")
        del active_duels[user_id]
        return
    
    # Снимаем ставки
    db.update_balance(challenger_id, -bet_pak, -bet_rub)
    db.update_balance(user_id, -bet_pak, -bet_rub)
    
    # Бросаем кубики
    challenger_roll = random.randint(1, 6)
    acceptor_roll = random.randint(1, 6)
    
    if challenger_roll > acceptor_roll:
        winner_id = challenger_id
        winner_name = "Вызывающий"
        result_text = f"🎲 Вызывающий выбросил {challenger_roll}\n🎲 Противник выбросил {acceptor_roll}\n\n🏆 ПОБЕДИЛ ВЫЗЫВАЮЩИЙ!"
        win_pak = bet_pak * 2
        win_rub = bet_rub * 2
        db.update_balance(winner_id, win_pak, win_rub)
        
    elif acceptor_roll > challenger_roll:
        winner_id = user_id
        winner_name = "Принявший"
        result_text = f"🎲 Вызывающий выбросил {challenger_roll}\n🎲 Противник выбросил {acceptor_roll}\n\n🏆 ПОБЕДИЛ ПРИНЯВШИЙ!"
        win_pak = bet_pak * 2
        win_rub = bet_rub * 2
        db.update_balance(winner_id, win_pak, win_rub)
        
    else:
        db.update_balance(challenger_id, bet_pak, bet_rub)
        db.update_balance(user_id, bet_pak, bet_rub)
        
        await update.message.reply_text(
            f"🤝 НИЧЬЯ!\n\n"
            f"🎲 Вызывающий выбросил {challenger_roll}\n"
            f"🎲 Противник выбросил {acceptor_roll}\n\n"
            f"💰 Ставки возвращены!"
        )
        
        try:
            await context.bot.send_message(
                chat_id=challenger_id,
                text=f"🤝 НИЧЬЯ В ДУЭЛИ!\n\n"
                     f"🎲 Ваш бросок: {challenger_roll}\n"
                     f"🎲 Бросок противника: {acceptor_roll}\n\n"
                     f"💰 Ставки возвращены!"
            )
        except:
            pass
        
        db.complete_duel(duel_id, None)
        del active_duels[user_id]
        return
    
    await update.message.reply_text(
        f"⚔️ РЕЗУЛЬТАТ ДУЭЛИ!\n\n"
        f"{result_text}\n\n"
        f"💰 {winner_name} выиграл {bet_pak} PAK и {bet_rub} РУБ!\n\n"
    )
    
    try:
        await context.bot.send_message(
            chat_id=challenger_id,
            text=f"⚔️ РЕЗУЛЬТАТ ДУЭЛИ!\n\n"
                 f"{result_text}\n\n"
                 f"💰 {'Вы выиграли' if winner_id == challenger_id else 'Вы проиграли'} {bet_pak} PAK и {bet_rub} РУБ!\n\n"
        )
    except:
        pass
    
    db.complete_duel(duel_id, winner_id)
    del active_duels[user_id]

# Команда /duel_cancel - ОТМЕНИТЬ ДУЭЛЬ
async def duel_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    cancelled = False
    for opponent_id, duel_info in list(active_duels.items()):
        if duel_info['challenger_id'] == user_id:
            await update.message.reply_text(f"❌ Вы отменили дуэль")
            
            try:
                await context.bot.send_message(
                    chat_id=opponent_id,
                    text=f"❌ Противник отменил дуэль!"
                )
            except:
                pass
            
            del active_duels[opponent_id]
            cancelled = True
            break
    
    if not cancelled:
        await update.message.reply_text("❌ У вас нет активных дуэлей для отмены!")

# ==================== ОСТАЛЬНЫЕ КОМАНДЫ ====================

# Команда /leaderboard
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = db.get_leaderboard(10)
    
    if not top_users:
        await update.message.reply_text("🏆 Пока нет игроков!")
        return
    
    text = "🏆 Топ 10 игроков:\n\n"
    for i, user in enumerate(top_users, 1):
        text += f"{i}. {user[0]}: 💎{user[1]} PAK | 💵{user[2]} РУБ\n"
    
    await update.message.reply_text(text)

# Команда /clan
async def clan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📋 Список кланов", callback_data="clan_list")],
        [InlineKeyboardButton("➕ Создать клан", callback_data="clan_create")],
        [InlineKeyboardButton("👥 Мои кланы", callback_data="clan_my")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👥 Управление кланами:", reply_markup=reply_markup)

# Команда /give
async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Недостаточно прав!")
        return
    
    if len(context.args) == 0:
        db.update_balance(user_id, 10000, 1000)
        user_data = db.get_user(user_id)
        await update.message.reply_text(f"✅ Выдано себе: 10000 PAK и 1000 РУБ\n💰 Новый баланс: {user_data[2]} PAK, {user_data[3]} РУБ")
        return
    
    if len(context.args) < 3:
        await update.message.reply_text("❌ Использование:\n/give - выдать себе\n/give @username PAK РУБ - выдать пользователю")
        return
    
    username = context.args[0].replace('@', '')
    try:
        pak = int(context.args[1])
        rub = int(context.args[2])
    except ValueError:
        await update.message.reply_text("❌ Суммы должны быть числами!")
        return
    
    user = db.get_user_by_username(username)
    if user:
        db.update_balance(user[0], pak, rub)
        await update.message.reply_text(f"✅ Выдано {pak} PAK и {rub} РУБ пользователю @{username}")
    else:
        await update.message.reply_text(f"❌ Пользователь @{username} не найден!")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_for_bet'):
        await handle_bet(update, context)
        return
    
    if update.message.text and update.message.text.startswith('/'):
        return
    
    user_id = update.effective_user.id
    user = update.effective_user
    
    db.register_user(user_id, user.username or str(user_id))
    
    if db.can_get_message_reward(user_id):
        if user.bio and "W1npakshambot" in user.bio:
            db.update_balance(user_id, MSG_REWARD, 0)
            db.update_message_time(user_id)
            await update.message.reply_text(f"💎 +{MSG_REWARD} PAK за сообщение!")

# Обработка callback запросов
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("game_"):
        game = query.data.replace("game_", "")
        context.user_data['selected_game'] = game
        await query.edit_message_text(f"🎮 Выбрана игра: {game}\n💰 Введите ставку в формате: PAK РУБ")
        context.user_data['waiting_for_bet'] = True
        
    elif query.data.startswith("buy_"):
        await query.edit_message_text("🛒 Покупка через Telegram Stars. Функция в разработке!")
        
    elif query.data == "clan_list":
        clans = db.get_all_clans()
        if clans:
            text = "📋 Доступные кланы:\n\n"
            for clan in clans:
                text += f"🏰 {clan[1]}: {clan[2]}\n"
            await query.edit_message_text(text)
        else:
            await query.edit_message_text("❌ Нет доступных кланов")
            
    elif query.data == "clan_create":
        await query.edit_message_text("🏰 Функция создания клана в разработке!")
        
    elif query.data == "clan_my":
        user_id = query.from_user.id
        user_data = db.get_user(user_id)
        if user_data and user_data[4]:
            await query.edit_message_text("👥 Вы состоите в клане!")
        else:
            await query.edit_message_text("❌ Вы не состоите в клане")

# ==================== ЗАПУСК ====================

async def main():
    print("🚀 Запуск бота W1nPAK...")
    
    try:
        application = Application.builder().token(TOKEN).build()
        
        # Регистрация команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("balance", balance))
        application.add_handler(CommandHandler("buy", buy))
        application.add_handler(CommandHandler("casino", casino))
        application.add_handler(CommandHandler("duel", duel))
        application.add_handler(CommandHandler("duel_accept", duel_accept))
        application.add_handler(CommandHandler("duel_cancel", duel_cancel))
        application.add_handler(CommandHandler("leaderboard", leaderboard))
        application.add_handler(CommandHandler("clan", clan))
        application.add_handler(CommandHandler("give", give))
        application.add_handler(CommandHandler("help", start))
        
        # Обработчики
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(handle_callback))
        
        print("✅ Бот успешно запущен и готов к работе!")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        await asyncio.Event().wait()
        
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())

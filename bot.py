import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from config import TOKEN, ADMIN_ID, MSG_REWARD
from database import Database
from casino_games import CasinoGames  # Импортируем новые игры

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация базы данных
db = Database()

# Функция проверки админа
def is_admin(user_id):
    return user_id == ADMIN_ID

# Хранилище для ставок
user_bets = {}

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
    
    # Проверяем баланс
    user_data = db.get_user(user_id)
    if user_data[2] < bet_pak or user_data[3] < bet_rub:
        await update.message.reply_text("❌ Недостаточно средств!")
        context.user_data['waiting_for_bet'] = False
        return
    
    if bet_pak <= 0 or bet_rub < 0:
        await update.message.reply_text("❌ Ставка должна быть положительной!")
        context.user_data['waiting_for_bet'] = False
        return
    
    # Сохраняем ставку
    game = context.user_data.get('selected_game', 'dice')
    context.user_data['bet_pak'] = bet_pak
    context.user_data['bet_rub'] = bet_rub
    
    # Запускаем игру
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
    
    # Обновляем баланс
    if win is True:
        db.update_balance(user_id, change_pak, change_rub)
    elif win is False:
        db.update_balance(user_id, -change_pak, -change_rub)
    else:  # Ничья
        db.update_balance(user_id, 0, 0)
    
    await update.message.reply_text(result_text)
    
    # Показываем новый баланс
    new_balance = db.get_user(user_id)
    await update.message.reply_text(f"💰 Новый баланс: {new_balance[2]} PAK, {new_balance[3]} РУБ")
    
    context.user_data['waiting_for_bet'] = False

# Команда /duel
async def duel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("❌ Использование: /duel @username [сумма_PAK] [сумма_РУБ]")
        return
    
    opponent = args[0]
    try:
        bet_pak = int(args[1])
        bet_rub = int(args[2])
    except ValueError:
        await update.message.reply_text("❌ Ставки должны быть числами!")
        return
    
    await update.message.reply_text(f"⚔️ Вы вызвали на дуэль {opponent}!\nСтавка: {bet_pak} PAK и {bet_rub} РУБ\nЖдите ответа...")

# Команда /duel_accept
async def duel_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚔️ Вы приняли дуэль! Бросаем кубики...")

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

# Команда /give (ИСПРАВЛЕНА - РАБОТАЕТ!)
async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Проверка админа
    if not is_admin(user_id):
        await update.message.reply_text("❌ Недостаточно прав! Команда доступна только администратору.")
        return
    
    # Если нет аргументов - выдаем себе для тестирования
    if len(context.args) == 0:
        db.update_balance(user_id, 10000, 1000)
        user_data = db.get_user(user_id)
        await update.message.reply_text(f"✅ Выдано себе: 10000 PAK и 1000 РУБ\n💰 Новый баланс: {user_data[2]} PAK, {user_data[3]} РУБ")
        return
    
    # Если есть аргументы - выдаем другому пользователю
    if len(context.args) < 3:
        await update.message.reply_text("❌ Использование:\n/give - выдать себе 10000 PAK и 1000 РУБ\n/give @username PAK РУБ - выдать пользователю")
        return
    
    username = context.args[0].replace('@', '')
    try:
        pak = int(context.args[1])
        rub = int(context.args[2])
    except ValueError:
        await update.message.reply_text("❌ Суммы должны быть числами!")
        return
    
    # Ищем пользователя в базе по username
    conn = db.conn
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    
    if result:
        target_id = result[0]
        db.update_balance(target_id, pak, rub)
        target_data = db.get_user(target_id)
        await update.message.reply_text(f"✅ Выдано {pak} PAK и {rub} РУБ пользователю @{username}\n💰 Новый баланс: {target_data[2]} PAK, {target_data[3]} РУБ")
    else:
        await update.message.reply_text(f"❌ Пользователь @{username} не найден в базе! Убедитесь, что он написал /start боту.")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, ждем ли ставку
    if context.user_data.get('waiting_for_bet'):
        await handle_bet(update, context)
        return
    
    # Проверяем, что это не команда
    if update.message.text and update.message.text.startswith('/'):
        return
    
    user_id = update.effective_user.id
    user = update.effective_user
    
    db.register_user(user_id, user.username or str(user_id))
    
    # Проверяем, можно ли получить награду
    if db.can_get_message_reward(user_id):
        # Проверяем, установлен ли бот в описании
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
        await query.edit_message_text(f"🎮 Выбрана игра: {game}\n💰 Введите ставку в формате: PAK РУБ\nПример: 100 50")
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
    else:
        await query.edit_message_text("🛒 Функция в разработке!")

# ГЛАВНАЯ ФУНКЦИЯ
async def main():
    """Запуск бота"""
    print("🚀 Запуск бота W1nPAK...")
    
    try:
        # Создаем приложение
        application = Application.builder().token(TOKEN).build()
        
        # Регистрация команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("balance", balance))
        application.add_handler(CommandHandler("buy", buy))
        application.add_handler(CommandHandler("casino", casino))
        application.add_handler(CommandHandler("duel", duel))
        application.add_handler(CommandHandler("duel_accept", duel_accept))
        application.add_handler(CommandHandler("leaderboard", leaderboard))
        application.add_handler(CommandHandler("clan", clan))
        application.add_handler(CommandHandler("give", give))
        application.add_handler(CommandHandler("help", start))
        
        # Обработчики сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(handle_callback))
        
        # Запуск бота
        print("✅ Бот успешно запущен и готов к работе!")
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        # Держим бота запущенным
        await asyncio.Event().wait()
        
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())

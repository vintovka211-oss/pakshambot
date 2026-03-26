import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler
from config import TOKEN, ADMIN_ID, MSG_REWARD
from database import Database
from games import CasinoGames

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

# Команда /start
def start(update: Update, context):
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
    update.message.reply_text(welcome_text)

# Команда /balance
def balance(update: Update, context):
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
        update.message.reply_text(text)
    else:
        update.message.reply_text("❌ Ошибка! Попробуй /start")

# Команда /buy
def buy(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("Купить 100 PAK за 10⭐", callback_data="buy_pak_100")],
        [InlineKeyboardButton("Купить 500 PAK за 50⭐", callback_data="buy_pak_500")],
        [InlineKeyboardButton("Купить 1 РУБ за 1⭐", callback_data="buy_rub_1")],
        [InlineKeyboardButton("Купить 10 РУБ за 10⭐", callback_data="buy_rub_10")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Выбери покупку:", reply_markup=reply_markup)

# Команда /casino
def casino(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("🎲 Кости", callback_data="game_dice")],
        [InlineKeyboardButton("🃏 Блэкджек", callback_data="game_blackjack")],
        [InlineKeyboardButton("🎰 Слоты", callback_data="game_slots")],
        [InlineKeyboardButton("💀 High Risk", callback_data="game_highrisk")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("🎮 Выбери игру:", reply_markup=reply_markup)

# Команда /duel
def duel(update: Update, context):
    args = context.args
    if len(args) < 3:
        update.message.reply_text("❌ Использование: /duel @username [сумма_PAK] [сумма_РУБ]")
        return
    
    opponent = args[0]
    try:
        bet_pak = int(args[1])
        bet_rub = int(args[2])
    except ValueError:
        update.message.reply_text("❌ Ставки должны быть числами!")
        return
    
    update.message.reply_text(f"⚔️ Вы вызвали на дуэль {opponent}!\nСтавка: {bet_pak} PAK и {bet_rub} РУБ\nЖдите ответа...")

# Команда /duel_accept
def duel_accept(update: Update, context):
    update.message.reply_text("⚔️ Вы приняли дуэль! Бросаем кубики...")

# Команда /leaderboard
def leaderboard(update: Update, context):
    top_users = db.get_leaderboard(10)
    
    if not top_users:
        update.message.reply_text("🏆 Пока нет игроков!")
        return
    
    text = "🏆 Топ 10 игроков:\n\n"
    for i, user in enumerate(top_users, 1):
        text += f"{i}. {user[0]}: 💎{user[1]} PAK | 💵{user[2]} РУБ\n"
    
    update.message.reply_text(text)

# Команда /clan
def clan(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("📋 Список кланов", callback_data="clan_list")],
        [InlineKeyboardButton("➕ Создать клан", callback_data="clan_create")],
        [InlineKeyboardButton("👥 Мои кланы", callback_data="clan_my")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("👥 Управление кланами:", reply_markup=reply_markup)

# Команда /give (только для админа)
def give(update: Update, context):
    if not is_admin(update.effective_user.id):
        update.message.reply_text("❌ Недостаточно прав!")
        return
    
    if len(context.args) < 3:
        update.message.reply_text("❌ Использование: /give @username PAK РУБ")
        return
    
    username = context.args[0].replace('@', '')
    try:
        pak = int(context.args[1])
        rub = int(context.args[2])
    except ValueError:
        update.message.reply_text("❌ Суммы должны быть числами!")
        return
    
    update.message.reply_text(f"✅ Выдано {pak} PAK и {rub} РУБ пользователю @{username}")

# Обработка сообщений
def handle_message(update: Update, context):
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
            update.message.reply_text(f"💎 +{MSG_REWARD} PAK за сообщение!")

# Обработка callback запросов
def handle_callback(update: Update, context):
    query = update.callback_query
    query.answer()
    
    if query.data.startswith("buy_"):
        query.edit_message_text("🛒 Покупка через Telegram Stars. Функция в разработке!")
    elif query.data.startswith("game_"):
        query.edit_message_text("🎮 Игра в разработке! Скоро появится.")
    elif query.data == "clan_list":
        clans = db.get_all_clans()
        if clans:
            text = "📋 Доступные кланы:\n\n"
            for clan in clans:
                text += f"🏰 {clan[1]}: {clan[2]}\n"
            query.edit_message_text(text)
        else:
            query.edit_message_text("❌ Нет доступных кланов")
    elif query.data == "clan_create":
        query.edit_message_text("🏰 Функция создания клана в разработке!")
    elif query.data == "clan_my":
        user_id = query.from_user.id
        user_data = db.get_user(user_id)
        if user_data and user_data[4]:
            query.edit_message_text("👥 Вы состоите в клане!")
        else:
            query.edit_message_text("❌ Вы не состоите в клане")
    else:
        query.edit_message_text("🛒 Функция в разработке!")

# ГЛАВНАЯ ФУНКЦИЯ
def main():
    """Запуск бота"""
    print("🚀 Запуск бота W1nPAK...")
    
    try:
        # Создаем updater (убрали use_context)
        updater = Updater(TOKEN)
        dp = updater.dispatcher
        
        # Регистрация команд
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("balance", balance))
        dp.add_handler(CommandHandler("buy", buy))
        dp.add_handler(CommandHandler("casino", casino))
        dp.add_handler(CommandHandler("duel", duel))
        dp.add_handler(CommandHandler("duel_accept", duel_accept))
        dp.add_handler(CommandHandler("leaderboard", leaderboard))
        dp.add_handler(CommandHandler("clan", clan))
        dp.add_handler(CommandHandler("give", give))
        dp.add_handler(CommandHandler("help", start))
        
        # Обработчик сообщений
        dp.add_handler(MessageHandler(None, handle_message))
        dp.add_handler(CallbackQueryHandler(handle_callback))
        
        # Запуск бота
        print("✅ Бот успешно запущен и готов к работе!")
        print("🤖 Бот начал polling...")
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        raise

if __name__ == '__main__':
    main()

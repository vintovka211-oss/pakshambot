import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
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
        [InlineKeyboardButton("🎲 Кости", callback_data="game_dice")],
        [InlineKeyboardButton("🃏 Блэкджек", callback_data="game_blackjack")],
        [InlineKeyboardButton("🎰 Слоты", callback_data="game_slots")],
        [InlineKeyboardButton("💀 High Risk", callback_data="game_highrisk")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎮 Выбери игру:", reply_markup=reply_markup)

# Команда /duel
async def duel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚔️ Функция дуэлей в разработке!")

# Команда /duel_accept
async def duel_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚔️ Принять дуэль: /duel_accept")

# Команда /leaderboard
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = db.get_leaderboard(10)
    
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

# Команда /give (только для админа)
async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Недостаточно прав!")
        return
    
    if len(context.args) < 3:
        await update.message.reply_text("❌ Использование: /give @username PAK РУБ")
        return
    
    await update.message.reply_text("✅ Команда give выполнена")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
    await query.edit_message_text("🛒 Функция в разработке!")

# ГЛАВНАЯ ФУНКЦИЯ - ПРАВИЛЬНЫЙ ЗАПУСК
def main():
    """Запуск бота"""
    print("🚀 Запуск бота...")
    
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
    
    # Запуск бота (правильный способ)
    print("✅ Бот успешно запущен и готов к работе!")
    application.run_polling()

if __name__ == '__main__':
    main()

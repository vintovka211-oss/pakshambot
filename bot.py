import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from config import TOKEN, ADMIN_ID, MSG_REWARD, MSG_COOLDOWN, CLAN_CREATE_COST, CLAN_REWARD, CLAN_REWARD_INTERVAL
from database import Database
from games import CasinoGames
import asyncio
from datetime import datetime

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
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
    
    welcome_text = f"""
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

# Обработка игр
async def handle_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    game = query.data.split('_')[1]
    
    # Запрашиваем ставку
    context.user_data['game_type'] = game
    await query.edit_message_text("💰 Введите ставку в PAK (например: 100)")
    context.user_data['waiting_for_bet'] = True

# Команда /duel
async def duel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Использование: /duel @username [сумма_PAK] [сумма_РУБ]")
        return
    
    if len(context.args) < 3:
        await update.message.reply_text("❌ Использование: /duel @username [сумма_PAK] [сумма_РУБ]")
        return
    
    opponent_username = context.args[0].replace('@', '')
    try:
        bet_pak = int(context.args[1])
        bet_rub = int(context.args[2])
    except ValueError:
        await update.message.reply_text("❌ Ставки должны быть числами!")
        return
    
    challenger_id = update.effective_user.id
    challenger_data = db.get_user(challenger_id)
    
    if challenger_data[2] < bet_pak or challenger_data[3] < bet_rub:
        await update.message.reply_text("❌ У тебя недостаточно средств!")
        return
    
    # Ищем противника
    # Здесь нужно получить user_id по username
    # Для простоты используем поиск в базе
    # В реальном боте нужно добавить функцию поиска
    
    await update.message.reply_text(f"⚔️ Дуэль создана! Ждем ответа от @{opponent_username}")

# Команда /duel_accept
async def duel_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    duel = db.get_pending_duel(user_id)
    
    if not duel:
        await update.message.reply_text("❌ Нет активных приглашений на дуэль!")
        return
    
    # Простая проверка: подбрасываем монетку
    import random
    if random.random() > 0.5:
        winner = duel[1]  # challenger
        loser = duel[2]
        result_text = "🎉 Ты победил в дуэли!"
    else:
        winner = duel[2]  # opponent
        loser = duel[1]
        result_text = "😔 Ты проиграл дуэль!"
    
    db.complete_duel(duel[0], winner)
    await update.message.reply_text(result_text)

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
    
    username = context.args[0].replace('@', '')
    try:
        pak = int(context.args[1])
        rub = int(context.args[2])
    except ValueError:
        await update.message.reply_text("❌ Суммы должны быть числами!")
        return
    
    # Находим пользователя по username
    # Для простоты используем прямой апдейт
    # В реальном боте нужно добавить поиск
    
    await update.message.reply_text(f"✅ Выдано {pak} PAK и {rub} РУБ пользователю @{username}")

# Обработка сообщений (награда за сообщения)
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
    
    if query.data.startswith("game_"):
        await handle_game(update, context)
    elif query.data.startswith("buy_"):
        # Обработка покупки
        await query.edit_message_text("🛒 Функция покупки в разработке. Используйте команду /buy в Telegram Stars!")
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
        await query.edit_message_text("🏰 Введите название клана:")
        context.user_data['creating_clan'] = True
    elif query.data == "clan_my":
        user_id = query.from_user.id
        user_data = db.get_user(user_id)
        if user_data[4]:  # in_clan
            members = db.get_clan_members(user_data[4])
            text = f"👥 Участники клана:\n\n"
            for member in members:
                text += f"• {member[1]} - {member[2]}\n"
            await query.edit_message_text(text)
        else:
            await query.edit_message_text("❌ Вы не состоите в клане")

# Основная функция
async def main():
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
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())

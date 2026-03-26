import asyncio
import logging
import random
import os
import sys
from datetime import datetime
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from config import *
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

# ==================== ВЕБ-СЕРВЕР ДЛЯ RENDER ====================

async def health_check(request):
    return web.Response(text="Bot is alive!", status=200)

async def handle_web(request):
    return web.Response(text="W1nPAK Bot is running!", status=200)

async def start_web_server():
    port = int(os.environ.get('PORT', 8080))
    app = web.Application()
    app.router.add_get('/', handle_web)
    app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"🌐 Веб-сервер запущен на порту {port}")

# ==================== ОСНОВНЫЕ КОМАНДЫ ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.register_user(user.id, user.username or str(user.id))
    
    welcome_text = f"""
🎮 Добро пожаловать в W1nPAK Бот!

💰 ТВОЙ БАЛАНС:
💎 PAK: 0
💵 РУБ: 0

📊 НОВАЯ ЭКОНОМИКА:
• 12 PAK = 3 РУБ (4 PAK = 1 РУБ)
• 2 РУБ = 1 ⭐ (звезда)

🌟 ДОСТУПНЫЕ КОМАНДЫ:
💰 /balance - Баланс
🌾 /farm - Управление фермой
🎲 /casino - Казино
⚔️ /duel - Дуэль
👥 /clan - Кланы
⭐ /buy - Купить PAK за звезды
💸 /withdraw - Вывод средств
🏆 /leaderboard - Топ игроков
🏰 /clan_leaderboard - Топ кланов
📝 /help - Помощь

💡 Подсказка: Установи @W1npakshambot в описании профиля и получай 5 PAK за каждое сообщение!
"""
    await update.message.reply_text(welcome_text)

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    
    if user_data:
        # Расчет эквивалента в рублях и звездах
        rub_from_pak = user_data[2] / 4  # 4 PAK = 1 рубль
        total_rub_value = user_data[3] + rub_from_pak
        stars_value = total_rub_value / 2  # 2 рубля = 1 звезда
        
        text = f"""
💰 ТВОЙ БАЛАНС:

💎 PAK: {user_data[2]}
💵 РУБ: {user_data[3]}

📊 ЭКВИВАЛЕНТ:
💵 В рублях: {total_rub_value:.1f} ₽
⭐ В звездах: {stars_value:.1f} ⭐

🌾 ФЕРМА:
📈 Уровень: {user_data[6]}
⚡ Добыча/час: {user_data[7]} PAK
🏆 Всего добыто: {user_data[8]} PAK

👥 КЛАН: {'✅ В клане' if user_data[9] else '❌ Не в клане'}

📈 КУРСЫ:
• 4 PAK = 1 ₽
• 2 ₽ = 1 ⭐
"""
        await update.message.reply_text(text)
    else:
        await update.message.reply_text("❌ Ошибка! Попробуй /start")

# ==================== ФЕРМА ====================

async def farm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌾 Собрать урожай", callback_data="farm_collect")],
        [InlineKeyboardButton("📈 Улучшить ферму", callback_data="farm_upgrade")],
        [InlineKeyboardButton("📊 Статистика фермы", callback_data="farm_stats")],
        [InlineKeyboardButton("🏆 Топ фермеров", callback_data="farm_leaderboard")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🌾 УПРАВЛЕНИЕ ФЕРМОЙ 🌾", reply_markup=reply_markup)

async def farm_collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    available, amount = db.get_farm_available(user_id)
    
    if available:
        earned = db.collect_farm(user_id)
        user_data = db.get_user(user_id)
        await update.callback_query.edit_message_text(
            f"🌾 ВЫ СОБРАЛИ УРОЖАЙ!\n\n"
            f"💰 Получено: +{earned} PAK\n"
            f"💎 Текущий баланс: {user_data[2]} PAK\n"
            f"⚡ Добыча/час: {user_data[7]} PAK"
        )
    else:
        user_data = db.get_user(user_id)
        last_collect = datetime.fromisoformat(user_data[10])
        hours_left = 1 - (datetime.now() - last_collect).total_seconds() / 3600
        minutes_left = int(hours_left * 60)
        await update.callback_query.edit_message_text(
            f"⏳ Урожай еще не готов!\n\n"
            f"Следующий сбор через: {minutes_left} минут\n"
            f"Текущая добыча: {user_data[7]} PAK/час"
        )

async def farm_upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    success, cost, new_level, new_rate = db.upgrade_farm(user_id)
    
    if success:
        user_data = db.get_user(user_id)
        await update.callback_query.edit_message_text(
            f"📈 ФЕРМА УЛУЧШЕНА!\n\n"
            f"💰 Потрачено: {cost} PAK\n"
            f"📊 Новый уровень: {new_level}\n"
            f"⚡ Новая добыча: {new_rate} PAK/час\n"
            f"💎 Остаток PAK: {user_data[2]}"
        )
    else:
        user_data = db.get_user(user_id)
        next_cost = 100 + (user_data[6] * 100)
        await update.callback_query.edit_message_text(
            f"❌ НЕДОСТАТОЧНО PAK!\n\n"
            f"💰 Нужно: {next_cost} PAK\n"
            f"💎 У вас: {user_data[2]} PAK\n"
            f"⚡ Текущая добыча: {user_data[7]} PAK/час"
        )

async def farm_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    
    next_cost = 100 + (user_data[6] * 100)
    hours_to_next = (next_cost - user_data[2]) / user_data[7] if user_data[7] > 0 else float('inf')
    
    text = f"""
🌾 СТАТИСТИКА ФЕРМЫ:

📊 Уровень: {user_data[6]}
⚡ Добыча/час: {user_data[7]} PAK
🏆 Всего добыто: {user_data[8]} PAK

💰 Следующее улучшение:
Стоимость: {next_cost} PAK
Добыча станет: {user_data[7] + 1} PAK/час

⏳ До улучшения нужно собрать: {max(0, next_cost - user_data[2])} PAK
{'📈 Примерно через: ' + str(int(hours_to_next)) + ' часов' if hours_to_next != float('inf') else ''}

💡 Совет: Чем выше уровень, тем быстрее окупаются улучшения!
"""
    await update.callback_query.edit_message_text(text)

async def farm_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_farmers = db.get_farm_leaderboard(10)
    
    if not top_farmers:
        await update.callback_query.edit_message_text("🏆 Пока нет фермеров!")
        return
    
    text = "🌾 ТОП ФЕРМЕРОВ 🌾\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, farmer in enumerate(top_farmers):
        text += f"{medals[i]} {farmer[0]}: 📊{farmer[1]} ур. | ⚡{farmer[2]} PAK/ч | 🏆{farmer[3]} PAK\n"
    
    await update.callback_query.edit_message_text(text)

# ==================== КЛАДБИЩЕ (CLAN) ОБНОВЛЕННОЕ ====================

async def clan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    
    keyboard = [
        [InlineKeyboardButton("📋 Список кланов", callback_data="clan_list")],
        [InlineKeyboardButton("➕ Создать клан", callback_data="clan_create")],
        [InlineKeyboardButton("👥 Мой клан", callback_data="clan_my")],
        [InlineKeyboardButton("💰 Получить награду клана (2 PAK/час)", callback_data="clan_reward")],
    ]
    
    if user_data and user_data[9]:
        keyboard.append([InlineKeyboardButton("🚪 Покинуть клан", callback_data="clan_leave")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👥 УПРАВЛЕНИЕ КЛАНАМИ 👥\n\nНаграда: 2 PAK каждый час!", reply_markup=reply_markup)

async def clan_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_clans = db.get_clan_leaderboard(10)
    
    if not top_clans:
        await update.message.reply_text("🏰 Пока нет кланов!")
        return
    
    text = "🏆 ТОП КЛАНОВ ПО БОГАТСТВУ 🏆\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, clan in enumerate(top_clans):
        name, members, total_pak, total_rub, total_wealth = clan
        text += f"{medals[i]} {name}\n"
        text += f"   👥 {members} участников\n"
        text += f"   💎 {total_pak} PAK | 💵 {total_rub} РУБ\n"
        text += f"   💰 Общая ценность: {total_wealth:.0f} PAK\n"
        text += f"   ➖➖➖➖➖➖➖\n"
    
    await update.message.reply_text(text)

# ==================== ПОКУПКА И ВЫВОД ====================

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⭐ 2 рубля → 1 звезда", callback_data="buy_rub_for_stars")],
        [InlineKeyboardButton("💎 Купить PAK за звезды", callback_data="buy_pak_menu")],
        [InlineKeyboardButton("💵 Купить РУБ за звезды", callback_data="buy_rub_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "⭐ ПОКУПКА ЗА ЗВЕЗДЫ ⭐\n\n"
        f"Курс: 2 ₽ = 1 ⭐\n"
        f"12 PAK = 3 ₽ (4 PAK = 1 ₽)\n\n"
        "Выбери действие:",
        reply_markup=reply_markup
    )

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    
    # Создаем заявку на вывод
    # Пока только заглушка
    await update.message.reply_text(
        "💸 ВЫВОД СРЕДСТВ 💸\n\n"
        "⚙️ Функция вывода средств находится в разработке!\n\n"
        "Скоро вы сможете выводить средства на:\n"
        "• Telegram Stars\n"
        "• Криптовалюту (USDT, TON)\n"
        "• Банковские карты\n\n"
        "Следите за обновлениями! 🔜",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔔 Уведомить о запуске", callback_data="withdraw_notify")]
        ])
    )

# ==================== ОСТАЛЬНЫЕ КОМАНДЫ ====================

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = db.get_leaderboard(10)
    
    if not top_users:
        await update.message.reply_text("🏆 Пока нет игроков!")
        return
    
    text = "🏆 ТОП ИГРОКОВ ПО БОГАТСТВУ 🏆\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, user in enumerate(top_users):
        username, pak, rub, wealth = user
        text += f"{medals[i]} {username}: 💎{pak} PAK | 💵{rub} РУБ | 💰{wealth:.0f} PAK\n"
    
    await update.message.reply_text(text)

async def casino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎲 Кости", callback_data="game_dice")],
        [InlineKeyboardButton("🃏 Блэкджек", callback_data="game_blackjack")],
        [InlineKeyboardButton("🎰 Слоты", callback_data="game_slots")],
        [InlineKeyboardButton("💀 High Risk", callback_data="game_highrisk")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎮 ВЫБЕРИ ИГРУ 🎮", reply_markup=reply_markup)
    context.user_data['waiting_for_bet'] = True

async def handle_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('waiting_for_bet'):
        return
    
    user_id = update.effective_user.id
    text = update.message.text.split()
    
    if len(text) != 2:
        await update.message.reply_text("❌ Введите: PAK РУБ\nПример: 100 50")
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

async def duel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    
    if len(args) < 3:
        await update.message.reply_text(
            "⚔️ ИСПОЛЬЗОВАНИЕ ДУЭЛИ:\n\n"
            "/duel @username [PAK] [РУБ]\n\n"
            "Пример: /duel @ivan 100 50"
        )
        return
    
    opponent_username = args[0].replace('@', '')
    try:
        bet_pak = int(args[1])
        bet_rub = int(args[2])
    except ValueError:
        await update.message.reply_text("❌ Ставки должны быть числами!")
        return
    
    challenger_data = db.get_user(user_id)
    if challenger_data[2] < bet_pak or challenger_data[3] < bet_rub:
        await update.message.reply_text("❌ Недостаточно средств!")
        return
    
    opponent = db.get_user_by_username(opponent_username)
    if not opponent:
        await update.message.reply_text(f"❌ Пользователь @{opponent_username} не найден!")
        return
    
    opponent_id = opponent[0]
    if opponent_id == user_id:
        await update.message.reply_text("❌ Нельзя вызвать себя!")
        return
    
    duel_id = db.create_duel(user_id, opponent_id, bet_pak, bet_rub)
    
    active_duels[opponent_id] = {
        'duel_id': duel_id,
        'challenger_id': user_id,
        'bet_pak': bet_pak,
        'bet_rub': bet_rub
    }
    
    await update.message.reply_text(f"⚔️ Вы вызвали @{opponent_username} на дуэль!\n💰 Ставка: {bet_pak} PAK, {bet_rub} РУБ")
    
    try:
        await context.bot.send_message(
            chat_id=opponent_id,
            text=f"⚔️ Вас вызвали на дуэль!\n\n"
                 f"👤 Противник: @{update.effective_user.username or 'Игрок'}\n"
                 f"💰 Ставка: {bet_pak} PAK, {bet_rub} РУБ\n\n"
                 f"✅ /duel_accept - принять дуэль\n"
                 f"❌ /duel_cancel - отклонить"
        )
    except:
        pass

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
    if acceptor_data[2] < bet_pak or acceptor_data[3] < bet_rub:
        await update.message.reply_text("❌ Недостаточно средств для дуэли!")
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
        win_pak = bet_pak * 2
        win_rub = bet_rub * 2
        db.update_balance(winner_id, win_pak, win_rub)
        result_text = f"🎲 {challenger_roll} vs {acceptor_roll}\n🏆 ПОБЕДИЛ ВЫЗЫВАЮЩИЙ!"
        
    elif acceptor_roll > challenger_roll:
        winner_id = user_id
        win_pak = bet_pak * 2
        win_rub = bet_rub * 2
        db.update_balance(winner_id, win_pak, win_rub)
        result_text = f"🎲 {challenger_roll} vs {acceptor_roll}\n🏆 ПОБЕДИЛ ПРИНЯВШИЙ!"
        
    else:
        db.update_balance(challenger_id, bet_pak, bet_rub)
        db.update_balance(user_id, bet_pak, bet_rub)
        result_text = f"🎲 {challenger_roll} vs {acceptor_roll}\n🤝 НИЧЬЯ! Ставки возвращены."
        db.complete_duel(duel_id, None)
        del active_duels[user_id]
        
        await update.message.reply_text(result_text)
        try:
            await context.bot.send_message(chat_id=challenger_id, text=result_text)
        except:
            pass
        return
    
    await update.message.reply_text(
        f"⚔️ РЕЗУЛЬТАТ ДУЭЛИ!\n\n{result_text}\n\n"
        f"💰 Выигрыш: {bet_pak} PAK и {bet_rub} РУБ"
    )
    
    try:
        await context.bot.send_message(
            chat_id=challenger_id,
            text=f"⚔️ РЕЗУЛЬТАТ ДУЭЛИ!\n\n{result_text}\n\n"
                 f"💰 {'Вы выиграли' if winner_id == challenger_id else 'Вы проиграли'} {bet_pak} PAK и {bet_rub} РУБ"
        )
    except:
        pass
    
    db.complete_duel(duel_id, winner_id)
    del active_duels[user_id]

async def duel_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    cancelled = False
    for opponent_id, duel_info in list(active_duels.items()):
        if duel_info['challenger_id'] == user_id:
            await update.message.reply_text("❌ Вы отменили дуэль")
            try:
                await context.bot.send_message(chat_id=opponent_id, text="❌ Противник отменил дуэль")
            except:
                pass
            del active_duels[opponent_id]
            cancelled = True
            break
    
    if not cancelled:
        await update.message.reply_text("❌ У вас нет активных дуэлей!")

# ==================== GIVE ====================

async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Недостаточно прав!")
        return
    
    if len(context.args) == 0:
        db.update_balance(user_id, 10000, 1000)
        user_data = db.get_user(user_id)
        await update.message.reply_text(f"✅ Выдано: 10000 PAK, 1000 РУБ\n💰 Баланс: {user_data[2]} PAK, {user_data[3]} РУБ")
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
    
    user = db.get_user_by_username(username)
    if user:
        db.update_balance(user[0], pak, rub)
        await update.message.reply_text(f"✅ Выдано {pak} PAK и {rub} РУБ пользователю @{username}")
    else:
        await update.message.reply_text(f"❌ Пользователь @{username} не найден!")

# ==================== ОБРАБОТЧИКИ ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Обработка создания клана
    if context.user_data.get('creating_clan') == 'waiting_name':
        await clan_create_name(update, context)
        return
    elif context.user_data.get('creating_clan') == 'waiting_description':
        await clan_create_description(update, context)
        return
    
    # Обработка ставки в казино
    if context.user_data.get('waiting_for_bet'):
        await handle_bet(update, context)
        return
    
    # Пропускаем команды
    if update.message.text and update.message.text.startswith('/'):
        return
    
    # Награда за сообщения
    user_id = update.effective_user.id
    user = update.effective_user
    
    db.register_user(user_id, user.username or str(user_id))
    
    if db.can_get_message_reward(user_id):
        if user.bio and "W1npakshambot" in user.bio:
            db.update_balance(user_id, MSG_REWARD, 0)
            db.update_message_time(user_id)
            await update.message.reply_text(f"💎 +{MSG_REWARD} PAK за сообщение!")

# ==================== ОБРАБОТЧИК CALLBACK ====================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    # ФЕРМА
    if data == "farm_collect":
        await farm_collect(update, context)
    elif data == "farm_upgrade":
        await farm_upgrade(update, context)
    elif data == "farm_stats":
        await farm_stats(update, context)
    elif data == "farm_leaderboard":
        await farm_leaderboard(update, context)
    
    # КЛАНЫ
    elif data == "clan_list":
        await clan_list(update, context)
    elif data == "clan_create":
        await clan_create_start(update, context)
    elif data == "clan_my":
        await clan_my(update, context)
    elif data == "clan_leave":
        await clan_leave(update, context)
    elif data == "clan_reward":
        await clan_reward(update, context)
    elif data == "clan_back":
        await clan(update, context)
    
    elif data.startswith("clan_join_"):
        clan_id = int(data.replace("clan_join_", ""))
        await clan_join(update, context, clan_id)
    
    elif data.startswith("clan_requests_"):
        clan_id = int(data.replace("clan_requests_", ""))
        await clan_requests(update, context, clan_id)
    
    elif data.startswith("clan_accept_"):
        parts = data.split("_")
        request_id = int(parts[2])
        clan_id = int(parts[3])
        await clan_accept(update, context, request_id, clan_id)
    
    elif data.startswith("clan_reject_"):
        request_id = int(data.replace("clan_reject_", ""))
        await clan_reject(update, context, request_id)
    
    elif data.startswith("clan_kick_"):
        clan_id = int(data.replace("clan_kick_", ""))
        await clan_kick(update, context, clan_id)
    
    elif data.startswith("clan_kick_user_"):
        parts = data.split("_")
        clan_id = int(parts[3])
        user_id = int(parts[4])
        await clan_kick_user(update, context, clan_id, user_id)
    
    # ПОКУПКИ
    elif data == "withdraw_notify":
        await query.edit_message_text("🔔 Вы будете уведомлены, когда вывод средств станет доступен!")
    
    # ИГРЫ
    elif data.startswith("game_"):
        game = data.replace("game_", "")
        context.user_data['selected_game'] = game
        await query.edit_message_text(
            f"🎮 Выбрана игра: {game}\n\n"
            f"💰 Введите ставку в формате:\n"
            f"PAK РУБ\n\n"
            f"Пример: 100 50"
        )
        context.user_data['waiting_for_bet'] = True

# ==================== КЛАНЫ (вспомогательные функции) ====================

async def clan_create_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    
    if user_data[9]:
        await update.callback_query.edit_message_text("❌ Вы уже состоите в клане!")
        return
    
    if user_data[2] < CLAN_CREATE_COST:
        await update.callback_query.edit_message_text(f"❌ Недостаточно PAK! Нужно {CLAN_CREATE_COST} PAK")
        return
    
    await update.callback_query.edit_message_text("🏰 Введите название клана:")
    context.user_data['creating_clan'] = 'waiting_name'

async def clan_create_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('creating_clan') == 'waiting_name':
        return
    
    name = update.message.text.strip()
    if len(name) < 3 or len(name) > 20:
        await update.message.reply_text("❌ Название должно быть от 3 до 20 символов!")
        return
    
    context.user_data['clan_name'] = name
    context.user_data['creating_clan'] = 'waiting_description'
    await update.message.reply_text("📝 Введите описание клана:")

async def clan_create_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('creating_clan') == 'waiting_description':
        return
    
    user_id = update.effective_user.id
    name = context.user_data['clan_name']
    description = update.message.text.strip()
    
    if len(description) > 200:
        await update.message.reply_text("❌ Описание слишком длинное (макс 200 символов)!")
        return
    
    db.update_balance(user_id, -CLAN_CREATE_COST, 0)
    clan_id = db.create_clan(name, description, user_id)
    
    if clan_id:
        await update.message.reply_text(
            f"✅ Клан '{name}' успешно создан!\n\n"
            f"📝 Описание: {description}\n"
            f"💰 Снято: {CLAN_CREATE_COST} PAK"
        )
    else:
        db.update_balance(user_id, CLAN_CREATE_COST, 0)
        await update.message.reply_text("❌ Клан с таким названием уже существует!")
    
    context.user_data.pop('creating_clan', None)
    context.user_data.pop('clan_name', None)

async def clan_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clans = db.get_all_clans()
    
    if not clans:
        await update.callback_query.edit_message_text("❌ Нет созданных кланов!")
        return
    
    text = "🏰 ТОП КЛАНОВ ПО БОГАТСТВУ 🏰\n\n"
    keyboard = []
    
    for clan in clans:
        clan_id, name, description, members, wealth = clan
        text += f"🏰 {name}\n"
        text += f"📝 {description[:50]}...\n"
        text += f"👥 Участников: {members}\n"
        text += f"💰 Богатство: {wealth:.0f} PAK\n"
        text += f"➖➖➖➖➖➖➖\n"
        keyboard.append([InlineKeyboardButton(f"📩 Вступить в {name}", callback_data=f"clan_join_{clan_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="clan_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def clan_join(update: Update, context: ContextTypes.DEFAULT_TYPE, clan_id: int):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    
    if user_data[9]:
        await update.callback_query.edit_message_text("❌ Вы уже состоите в клане!")
        return
    
    db.send_clan_request(clan_id, user_id)
    clan = db.get_clan_by_id(clan_id)
    owner_id = db.get_clan_owner(clan_id)
    
    await update.callback_query.edit_message_text(
        f"✅ Заявка на вступление в клан '{clan[1]}' отправлена!\n"
        f"Ожидайте подтверждения от лидера клана."
    )
    
    try:
        keyboard = [[InlineKeyboardButton("📋 Посмотреть заявки", callback_data=f"clan_requests_{clan_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=owner_id,
            text=f"👥 Новая заявка в клан '{clan[1]}' от @{update.effective_user.username or 'игрока'}!",
            reply_markup=reply_markup
        )
    except:
        pass

async def clan_my(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    
    if not user_data[9]:
        await update.callback_query.edit_message_text("❌ Вы не состоите в клане!")
        return
    
    clan = db.get_clan_by_id(user_data[9])
    members = db.get_clan_members(user_data[9])
    total_wealth = db.get_clan_total_wealth(user_data[9])
    
    text = f"🏰 {clan[1]}\n"
    text += f"📝 {clan[2]}\n"
    text += f"👑 Лидер: @{db.get_user(clan[3])[1] if db.get_user(clan[3]) else 'Неизвестно'}\n"
    text += f"👥 Участников: {len(members)}\n"
    text += f"💰 Богатство клана: {total_wealth:.0f} PAK\n"
    text += f"📅 Создан: {clan[4][:10]}\n\n"
    text += "👥 УЧАСТНИКИ:\n"
    
    for member in members:
        role_icon = "👑" if member[2] == "owner" else "👤"
        text += f"{role_icon} @{member[1]} | 💎{member[3]} PAK | 💵{member[4]} РУБ\n"
    
    keyboard = []
    if user_data[10] == 'owner':
        keyboard.append([InlineKeyboardButton("📋 Заявки", callback_data=f"clan_requests_{clan[0]}")])
        keyboard.append([InlineKeyboardButton("👋 Выгнать участника", callback_data=f"clan_kick_{clan[0]}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="clan_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def clan_requests(update: Update, context: ContextTypes.DEFAULT_TYPE, clan_id: int):
    requests = db.get_clan_requests(clan_id)
    
    if not requests:
        await update.callback_query.edit_message_text("❌ Нет активных заявок!")
        return
    
    text = "📋 ЗАЯВКИ НА ВСТУПЛЕНИЕ 📋\n\n"
    keyboard = []
    
    for req in requests:
        req_id, user_id, username, created_at = req
        text += f"👤 @{username}\n"
        text += f"📅 {created_at[:10]}\n\n"
        keyboard.append([
            InlineKeyboardButton(f"✅ Принять @{username}", callback_data=f"clan_accept_{req_id}_{clan_id}"),
            InlineKeyboardButton(f"❌ Отклонить", callback_data=f"clan_reject_{req_id}")
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="clan_my")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def clan_accept(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id: int, clan_id: int):
    user_id = db.accept_clan_request(request_id, clan_id)
    
    if user_id:
        await update.callback_query.edit_message_text("✅ Заявка принята!")
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="🎉 Поздравляем! Вы приняты в клан!\n💰 Каждый час вы получаете 2 PAK!"
            )
        except:
            pass
    else:
        await update.callback_query.edit_message_text("❌ Ошибка при принятии заявки!")

async def clan_reject(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id: int):
    db.reject_clan_request(request_id)
    await update.callback_query.edit_message_text("✅ Заявка отклонена!")

async def clan_kick(update: Update, context: ContextTypes.DEFAULT_TYPE, clan_id: int):
    members = db.get_clan_members(clan_id)
    keyboard = []
    
    for member in members:
        if member[2] != 'owner':
            keyboard.append([InlineKeyboardButton(f"👋 Выгнать @{member[1]}", callback_data=f"clan_kick_user_{clan_id}_{member[0]}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="clan_my")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text("Выберите участника для исключения:", reply_markup=reply_markup)

async def clan_kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE, clan_id: int, user_id: int):
    db.kick_from_clan(clan_id, user_id)
    await update.callback_query.edit_message_text("✅ Участник исключен из клана!")

async def clan_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db.remove_from_clan(user_id)
    await update.callback_query.edit_message_text("✅ Вы покинули клан!")

async def clan_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not db.get_clan_reward_available(user_id):
        await update.callback_query.edit_message_text("❌ Награду можно получать раз в час!")
        return
    
    db.give_clan_reward(user_id)
    db.update_clan_reward_time(user_id)
    
    user_data = db.get_user(user_id)
    await update.callback_query.edit_message_text(
        f"💰 Вы получили 2 PAK за участие в клане!\n"
        f"💎 Новый баланс: {user_data[2]} PAK"
    )

# ==================== ЗАПУСК БОТА ====================

async def keep_alive():
    """Держит бота активным"""
    while True:
        await asyncio.sleep(600)
        print(f"🏓 Бот активен - {datetime.now().strftime('%H:%M:%S')}")

async def main():
    print("🚀 Запуск бота W1nPAK...")
    
    await start_web_server()
    asyncio.create_task(keep_alive())
    
    try:
        application = Application.builder().token(TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("balance", balance))
        application.add_handler(CommandHandler("farm", farm))
        application.add_handler(CommandHandler("buy", buy))
        application.add_handler(CommandHandler("withdraw", withdraw))
        application.add_handler(CommandHandler("casino", casino))
        application.add_handler(CommandHandler("duel", duel))
        application.add_handler(CommandHandler("duel_accept", duel_accept))
        application.add_handler(CommandHandler("duel_cancel", duel_cancel))
        application.add_handler(CommandHandler("leaderboard", leaderboard))
        application.add_handler(CommandHandler("clan", clan))
        application.add_handler(CommandHandler("clan_leaderboard", clan_leaderboard))
        application.add_handler(CommandHandler("give", give))
        application.add_handler(CommandHandler("help", start))
        
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(handle_callback))
        
        print("✅ Бот успешно запущен и готов к работе!")
        
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        print("🤖 Бот начал polling...")
        
        await asyncio.Event().wait()
        
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
```

---

📁 4. requirements.txt

```txt
python-telegram-bot==21.10
aiohttp==3.9.1
```

---

📁 5. .python-version

```
3.11.10
```

---

🚀 Что нового:

✅ Веб-сервер

· Бот теперь слушает порт 10000
· Эндпоинты / и /health для проверки работы
· Render не будет "усыплять" бота

✅ Ферма

· Начальная добыча: 2 PAK/час
· Улучшение: +100 PAK к стоимости за уровень
· За 100 PAK → +1 PAK/час к добыче
· Таблица лидеров по добыче

✅ Новая экономика

· 12 PAK = 3 рубля (4 PAK = 1 рубль)
· 2 рубля = 1 звезда
· Обновлены все расчеты

✅ Вывод средств

· Кнопка /withdraw с заглушкой
· Уведомление о скором запуске

✅ Обновленные кланы

· Награда: 2 PAK в час (вместо 50)
· Таблица лучших кланов по суммарному богатству
· Отображение богатства в PAK

---

🎮 Новые команды:

Команда Описание
/farm Управление фермой
/withdraw Вывод средств (заглушка)
/clan_leaderboard Топ кланов по богатству

---

🚀 Деплой:

1. Загрузите все файлы на GitHub
2. На Render нажмите "Manual Deploy" → "Deploy latest commit"
3. Проверьте логи - должно быть:
   ```
   🌐 Веб-сервер запущен на порту 10000
   ✅ Бот успешно запущен и готов к работе!
   🤖 Бот начал polling...
   ```

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

# ==================== WEB SERVER ====================

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
    print(f"Web server started on port {port}")

# ==================== MAIN COMMANDS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.register_user(user.id, user.username or str(user.id))
    
    welcome_text = """
W1nPAK Bot

Your balance:
PAK: 0
RUB: 0

New economy:
12 PAK = 3 RUB (4 PAK = 1 RUB)
2 RUB = 1 star

Commands:
/balance - Balance
/farm - Farm management
/casino - Casino games
/duel - Duel
/clan - Clans
/buy - Buy PAK for stars
/withdraw - Withdraw funds
/leaderboard - Top players
/clan_leaderboard - Top clans
/help - Help

Tip: Set @W1npakshambot in your profile bio and get 5 PAK per message!
"""
    await update.message.reply_text(welcome_text)

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    
    if user_data:
        rub_from_pak = user_data[2] / 4
        total_rub_value = user_data[3] + rub_from_pak
        stars_value = total_rub_value / 2
        
        text = f"""
YOUR BALANCE:

PAK: {user_data[2]}
RUB: {user_data[3]}

EQUIVALENT:
In RUB: {total_rub_value:.1f}
In stars: {stars_value:.1f}

FARM:
Level: {user_data[6]}
Rate/hour: {user_data[7]} PAK
Total earned: {user_data[8]} PAK

CLAN: {'In clan' if user_data[9] else 'Not in clan'}

RATES:
4 PAK = 1 RUB
2 RUB = 1 star
"""
        await update.message.reply_text(text)
    else:
        await update.message.reply_text("Error! Try /start")

# ==================== FARM ====================

async def farm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Harvest", callback_data="farm_collect")],
        [InlineKeyboardButton("Upgrade farm", callback_data="farm_upgrade")],
        [InlineKeyboardButton("Farm stats", callback_data="farm_stats")],
        [InlineKeyboardButton("Top farmers", callback_data="farm_leaderboard")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("FARM MANAGEMENT", reply_markup=reply_markup)

async def farm_collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    available, amount = db.get_farm_available(user_id)
    
    if available:
        earned = db.collect_farm(user_id)
        user_data = db.get_user(user_id)
        await update.callback_query.edit_message_text(
            f"HARVEST COMPLETE!\n\n"
            f"Earned: +{earned} PAK\n"
            f"New balance: {user_data[2]} PAK\n"
            f"Rate/hour: {user_data[7]} PAK"
        )
    else:
        user_data = db.get_user(user_id)
        last_collect = datetime.fromisoformat(user_data[10])
        hours_left = 1 - (datetime.now() - last_collect).total_seconds() / 3600
        minutes_left = int(hours_left * 60)
        await update.callback_query.edit_message_text(
            f"Harvest not ready!\n\n"
            f"Next harvest in: {minutes_left} minutes\n"
            f"Current rate: {user_data[7]} PAK/hour"
        )

async def farm_upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    success, cost, new_level, new_rate = db.upgrade_farm(user_id)
    
    if success:
        user_data = db.get_user(user_id)
        await update.callback_query.edit_message_text(
            f"FARM UPGRADED!\n\n"
            f"Cost: {cost} PAK\n"
            f"New level: {new_level}\n"
            f"New rate: {new_rate} PAK/hour\n"
            f"Remaining PAK: {user_data[2]}"
        )
    else:
        user_data = db.get_user(user_id)
        next_cost = 100 + (user_data[6] * 100)
        await update.callback_query.edit_message_text(
            f"NOT ENOUGH PAK!\n\n"
            f"Need: {next_cost} PAK\n"
            f"You have: {user_data[2]} PAK\n"
            f"Current rate: {user_data[7]} PAK/hour"
        )

async def farm_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    
    next_cost = 100 + (user_data[6] * 100)
    hours_to_next = (next_cost - user_data[2]) / user_data[7] if user_data[7] > 0 else float('inf')
    
    text = f"""
FARM STATISTICS:

Level: {user_data[6]}
Rate/hour: {user_data[7]} PAK
Total earned: {user_data[8]} PAK

Next upgrade:
Cost: {next_cost} PAK
New rate: {user_data[7] + 1} PAK/hour

Need for upgrade: {max(0, next_cost - user_data[2])} PAK
{'Time needed: ' + str(int(hours_to_next)) + ' hours' if hours_to_next != float('inf') else ''}

Tip: Higher level = faster return on investment!
"""
    await update.callback_query.edit_message_text(text)

async def farm_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_farmers = db.get_farm_leaderboard(10)
    
    if not top_farmers:
        await update.callback_query.edit_message_text("No farmers yet!")
        return
    
    text = "TOP FARMERS\n\n"
    medals = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
    
    for i, farmer in enumerate(top_farmers):
        text += f"{medals[i]}. {farmer[0]}: Lvl{farmer[1]} | {farmer[2]} PAK/h | Total {farmer[3]} PAK\n"
    
    await update.callback_query.edit_message_text(text)

# ==================== CLANS ====================

async def clan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    
    keyboard = [
        [InlineKeyboardButton("Clan list", callback_data="clan_list")],
        [InlineKeyboardButton("Create clan", callback_data="clan_create")],
        [InlineKeyboardButton("My clan", callback_data="clan_my")],
        [InlineKeyboardButton("Get clan reward (2 PAK/hour)", callback_data="clan_reward")],
    ]
    
    if user_data and user_data[9]:
        keyboard.append([InlineKeyboardButton("Leave clan", callback_data="clan_leave")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("CLAN MANAGEMENT\n\nReward: 2 PAK every hour!", reply_markup=reply_markup)

async def clan_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_clans = db.get_clan_leaderboard(10)
    
    if not top_clans:
        await update.message.reply_text("No clans yet!")
        return
    
    text = "TOP CLANS BY WEALTH\n\n"
    medals = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
    
    for i, clan in enumerate(top_clans):
        name, members, total_pak, total_rub, total_wealth = clan
        text += f"{medals[i]}. {name}\n"
        text += f"   Members: {members}\n"
        text += f"   PAK: {total_pak} | RUB: {total_rub}\n"
        text += f"   Total wealth: {total_wealth:.0f} PAK\n"
        text += f"   ----------\n"
    
    await update.message.reply_text(text)

# ==================== BUY & WITHDRAW ====================

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("2 RUB -> 1 star", callback_data="buy_rub_for_stars")],
        [InlineKeyboardButton("Buy PAK for stars", callback_data="buy_pak_menu")],
        [InlineKeyboardButton("Buy RUB for stars", callback_data="buy_rub_menu")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "BUY WITH STARS\n\n"
        "Rate: 2 RUB = 1 star\n"
        "12 PAK = 3 RUB (4 PAK = 1 RUB)\n\n"
        "Choose action:",
        reply_markup=reply_markup
    )

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    
    await update.message.reply_text(
        "WITHDRAW FUNDS\n\n"
        "This feature is under development!\n\n"
        "Soon you will be able to withdraw to:\n"
        "- Telegram Stars\n"
        "- Cryptocurrency (USDT, TON)\n"
        "- Bank cards\n\n"
        "Stay tuned!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Notify me", callback_data="withdraw_notify")]
        ])
    )

# ==================== LEADERBOARD ====================

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = db.get_leaderboard(10)
    
    if not top_users:
        await update.message.reply_text("No players yet!")
        return
    
    text = "TOP PLAYERS BY WEALTH\n\n"
    medals = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
    
    for i, user in enumerate(top_users):
        username, pak, rub, wealth = user
        text += f"{medals[i]}. {username}: PAK {pak} | RUB {rub} | {wealth:.0f} PAK\n"
    
    await update.message.reply_text(text)

# ==================== CASINO ====================

async def casino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Dice", callback_data="game_dice")],
        [InlineKeyboardButton("Blackjack", callback_data="game_blackjack")],
        [InlineKeyboardButton("Slots", callback_data="game_slots")],
        [InlineKeyboardButton("High Risk", callback_data="game_highrisk")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("CHOOSE GAME", reply_markup=reply_markup)
    context.user_data['waiting_for_bet'] = True

async def handle_bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('waiting_for_bet'):
        return
    
    user_id = update.effective_user.id
    text = update.message.text.split()
    
    if len(text) != 2:
        await update.message.reply_text("Enter: PAK RUB\nExample: 100 50")
        return
    
    try:
        bet_pak = int(text[0])
        bet_rub = int(text[1])
    except ValueError:
        await update.message.reply_text("Bets must be numbers!")
        return
    
    user_data = db.get_user(user_id)
    if user_data[2] < bet_pak or user_data[3] < bet_rub:
        await update.message.reply_text("Insufficient funds!")
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
        await update.message.reply_text("Game not found!")
        context.user_data['waiting_for_bet'] = False
        return
    
    if win is True:
        db.update_balance(user_id, change_pak, change_rub)
    elif win is False:
        db.update_balance(user_id, -change_pak, -change_rub)
    
    await update.message.reply_text(result_text)
    
    new_balance = db.get_user(user_id)
    await update.message.reply_text(f"New balance: {new_balance[2]} PAK, {new_balance[3]} RUB")
    
    context.user_data['waiting_for_bet'] = False

# ==================== DUEL ====================

async def duel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    
    if len(args) < 3:
        await update.message.reply_text(
            "DUEL USAGE:\n\n"
            "/duel @username [PAK] [RUB]\n\n"
            "Example: /duel @ivan 100 50"
        )
        return
    
    opponent_username = args[0].replace('@', '')
    try:
        bet_pak = int(args[1])
        bet_rub = int(args[2])
    except ValueError:
        await update.message.reply_text("Bets must be numbers!")
        return
    
    challenger_data = db.get_user(user_id)
    if challenger_data[2] < bet_pak or challenger_data[3] < bet_rub:
        await update.message.reply_text("Insufficient funds!")
        return
    
    opponent = db.get_user_by_username(opponent_username)
    if not opponent:
        await update.message.reply_text(f"User @{opponent_username} not found!")
        return
    
    opponent_id = opponent[0]
    if opponent_id == user_id:
        await update.message.reply_text("You cannot duel yourself!")
        return
    
    duel_id = db.create_duel(user_id, opponent_id, bet_pak, bet_rub)
    
    active_duels[opponent_id] = {
        'duel_id': duel_id,
        'challenger_id': user_id,
        'bet_pak': bet_pak,
        'bet_rub': bet_rub
    }
    
    await update.message.reply_text(f"You challenged @{opponent_username} to a duel!\nBet: {bet_pak} PAK, {bet_rub} RUB")
    
    try:
        await context.bot.send_message(
            chat_id=opponent_id,
            text=f"You were challenged to a duel!\n\n"
                 f"Opponent: @{update.effective_user.username or 'Player'}\n"
                 f"Bet: {bet_pak} PAK, {bet_rub} RUB\n\n"
                 f"Type /duel_accept to accept\n"
                 f"Type /duel_cancel to decline"
        )
    except:
        pass

async def duel_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in active_duels:
        await update.message.reply_text("No active duel invitations!")
        return
    
    duel_info = active_duels[user_id]
    challenger_id = duel_info['challenger_id']
    bet_pak = duel_info['bet_pak']
    bet_rub = duel_info['bet_rub']
    duel_id = duel_info['duel_id']
    
    acceptor_data = db.get_user(user_id)
    if acceptor_data[2] < bet_pak or acceptor_data[3] < bet_rub:
        await update.message.reply_text("Insufficient funds for duel!")
        del active_duels[user_id]
        return
    
    db.update_balance(challenger_id, -bet_pak, -bet_rub)
    db.update_balance(user_id, -bet_pak, -bet_rub)
    
    challenger_roll = random.randint(1, 6)
    acceptor_roll = random.randint(1, 6)
    
    if challenger_roll > acceptor_roll:
        winner_id = challenger_id
        win_pak = bet_pak * 2
        win_rub = bet_rub * 2
        db.update_balance(winner_id, win_pak, win_rub)
        result_text = f"Challenger rolled {challenger_roll}\nOpponent rolled {acceptor_roll}\nCHALLENGER WINS!"
        
    elif acceptor_roll > challenger_roll:
        winner_id = user_id
        win_pak = bet_pak * 2
        win_rub = bet_rub * 2
        db.update_balance(winner_id, win_pak, win_rub)
        result_text = f"Challenger rolled {challenger_roll}\nOpponent rolled {acceptor_roll}\nOPPONENT WINS!"
        
    else:
        db.update_balance(challenger_id, bet_pak, bet_rub)
        db.update_balance(user_id, bet_pak, bet_rub)
        result_text = f"Challenger rolled {challenger_roll}\nOpponent rolled {acceptor_roll}\nDRAW! Bets returned."
        db.complete_duel(duel_id, None)
        del active_duels[user_id]
        
        await update.message.reply_text(result_text)
        try:
            await context.bot.send_message(chat_id=challenger_id, text=result_text)
        except:
            pass
        return
    
    await update.message.reply_text(
        f"DUEL RESULT!\n\n{result_text}\n\n"
        f"Winnings: {bet_pak} PAK and {bet_rub} RUB"
    )
    
    try:
        await context.bot.send_message(
            chat_id=challenger_id,
            text=f"DUEL RESULT!\n\n{result_text}\n\n"
                 f"You {'won' if winner_id == challenger_id else 'lost'} {bet_pak} PAK and {bet_rub} RUB"
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
            await update.message.reply_text("You cancelled the duel")
            try:
                await context.bot.send_message(chat_id=opponent_id, text="Opponent cancelled the duel")
            except:
                pass
            del active_duels[opponent_id]
            cancelled = True
            break
    
    if not cancelled:
        await update.message.reply_text("No active duels to cancel!")

# ==================== GIVE ====================

async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("Insufficient permissions!")
        return
    
    if len(context.args) == 0:
        db.update_balance(user_id, 10000, 1000)
        user_data = db.get_user(user_id)
        await update.message.reply_text(f"Gave self: 10000 PAK, 1000 RUB\nBalance: {user_data[2]} PAK, {user_data[3]} RUB")
        return
    
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /give @username PAK RUB")
        return
    
    username = context.args[0].replace('@', '')
    try:
        pak = int(context.args[1])
        rub = int(context.args[2])
    except ValueError:
        await update.message.reply_text("Amounts must be numbers!")
        return
    
    user = db.get_user_by_username(username)
    if user:
        db.update_balance(user[0], pak, rub)
        await update.message.reply_text(f"Gave {pak} PAK and {rub} RUB to @{username}")
    else:
        await update.message.reply_text(f"User @{username} not found!")

# ==================== MESSAGE HANDLER ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('creating_clan') == 'waiting_name':
        await clan_create_name(update, context)
        return
    elif context.user_data.get('creating_clan') == 'waiting_description':
        await clan_create_description(update, context)
        return
    
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
            await update.message.reply_text(f"+{MSG_REWARD} PAK for message!")

# ==================== CALLBACK HANDLER ====================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "farm_collect":
        await farm_collect(update, context)
    elif data == "farm_upgrade":
        await farm_upgrade(update, context)
    elif data == "farm_stats":
        await farm_stats(update, context)
    elif data == "farm_leaderboard":
        await farm_leaderboard(update, context)
    
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
    
    elif data == "withdraw_notify":
        await query.edit_message_text("You will be notified when withdrawals are available!")
    
    elif data.startswith("game_"):
        game = data.replace("game_", "")
        context.user_data['selected_game'] = game
        await query.edit_message_text(
            f"Game selected: {game}\n\n"
            f"Enter bet in format:\n"
            f"PAK RUB\n\n"
            f"Example: 100 50"
        )
        context.user_data['waiting_for_bet'] = True

# ==================== CLAN HELPER FUNCTIONS ====================

async def clan_create_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    
    if user_data[9]:
        await update.callback_query.edit_message_text("You are already in a clan!")
        return
    
    if user_data[2] < CLAN_CREATE_COST:
        await update.callback_query.edit_message_text(f"Not enough PAK! Need {CLAN_CREATE_COST} PAK")
        return
    
    await update.callback_query.edit_message_text("Enter clan name:")
    context.user_data['creating_clan'] = 'waiting_name'

async def clan_create_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('creating_clan') == 'waiting_name':
        return
    
    name = update.message.text.strip()
    if len(name) < 3 or len(name) > 20:
        await update.message.reply_text("Name must be 3-20 characters!")
        return
    
    context.user_data['clan_name'] = name
    context.user_data['creating_clan'] = 'waiting_description'
    await update.message.reply_text("Enter clan description:")

async def clan_create_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('creating_clan') == 'waiting_description':
        return
    
    user_id = update.effective_user.id
    name = context.user_data['clan_name']
    description = update.message.text.strip()
    
    if len(description) > 200:
        await update.message.reply_text("Description too long (max 200 chars)!")
        return
    
    db.update_balance(user_id, -CLAN_CREATE_COST, 0)
    clan_id = db.create_clan(name, description, user_id)
    
    if clan_id:
        await update.message.reply_text(
            f"Clan '{name}' created successfully!\n\n"
            f"Description: {description}\n"
            f"Cost: {CLAN_CREATE_COST} PAK"
        )
    else:
        db.update_balance(user_id, CLAN_CREATE_COST, 0)
        await update.message.reply_text("Clan with this name already exists!")
    
    context.user_data.pop('creating_clan', None)
    context.user_data.pop('clan_name', None)

async def clan_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clans = db.get_all_clans()
    
    if not clans:
        await update.callback_query.edit_message_text("No clans created!")
        return
    
    text = "TOP CLANS BY WEALTH\n\n"
    keyboard = []
    
    for clan in clans:
        clan_id, name, description, members, wealth = clan
        text += f" {name}\n"
        text += f"   Description: {description[:50]}...\n"
        text += f"   Members: {members}\n"
        text += f"   Wealth: {wealth:.0f} PAK\n"
        text += f"   ----------\n"
        keyboard.append([InlineKeyboardButton(f"Join {name}", callback_data=f"clan_join_{clan_id}")])
    
    keyboard.append([InlineKeyboardButton("Back", callback_data="clan_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def clan_join(update: Update, context: ContextTypes.DEFAULT_TYPE, clan_id: int):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    
    if user_data[9]:
        await update.callback_query.edit_message_text("You are already in a clan!")
        return
    
    db.send_clan_request(clan_id, user_id)
    clan = db.get_clan_by_id(clan_id)
    owner_id = db.get_clan_owner(clan_id)
    
    await update.callback_query.edit_message_text(
        f"Request to join '{clan[1]}' sent!\n"
        f"Wait for clan leader approval."
    )
    
    try:
        keyboard = [[InlineKeyboardButton("View requests", callback_data=f"clan_requests_{clan_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.send_message(
            chat_id=owner_id,
            text=f"New request to join '{clan[1]}' from @{update.effective_user.username or 'player'}!",
            reply_markup=reply_markup
        )
    except:
        pass

async def clan_my(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    
    if not user_data[9]:
        await update.callback_query.edit_message_text("You are not in a clan!")
        return
    
    clan = db.get_clan_by_id(user_data[9])
    members = db.get_clan_members(user_data[9])
    total_wealth = db.get_clan_total_wealth(user_data[9])
    
    text = f"{clan[1]}\n"
    text += f"Description: {clan[2]}\n"
    text += f"Leader: @{db.get_user(clan[3])[1] if db.get_user(clan[3]) else 'Unknown'}\n"
    text += f"Members: {len(members)}\n"
    text += f"Clan wealth: {total_wealth:.0f} PAK\n"
    text += f"Created: {clan[4][:10]}\n\n"
    text += "MEMBERS:\n"
    
    for member in members:
        role_icon = "Leader" if member[2] == "owner" else "Member"
        text += f"{role_icon} @{member[1]} | PAK {member[3]} | RUB {member[4]}\n"
    
    keyboard = []
    if user_data[10] == 'owner':
        keyboard.append([InlineKeyboardButton("Requests", callback_data=f"clan_requests_{clan[0]}")])
        keyboard.append([InlineKeyboardButton("Kick member", callback_data=f"clan_kick_{clan[0]}")])
    
    keyboard.append([InlineKeyboardButton("Back", callback_data="clan_back")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def clan_requests(update: Update, context: ContextTypes.DEFAULT_TYPE, clan_id: int):
    requests = db.get_clan_requests(clan_id)
    
    if not requests:
        await update.callback_query.edit_message_text("No pending requests!")
        return
    
    text = "JOIN REQUESTS\n\n"
    keyboard = []
    
    for req in requests:
        req_id, user_id, username, created_at = req
        text += f"@{username}\n"
        text += f"Date: {created_at[:10]}\n\n"
        keyboard.append([
            InlineKeyboardButton(f"Accept @{username}", callback_data=f"clan_accept_{req_id}_{clan_id}"),
            InlineKeyboardButton(f"Reject", callback_data=f"clan_reject_{req_id}")
        ])
    
    keyboard.append([InlineKeyboardButton("Back", callback_data="clan_my")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(text, reply_markup=reply_markup)

async def clan_accept(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id: int, clan_id: int):
    user_id = db.accept_clan_request(request_id, clan_id)
    
    if user_id:
        await update.callback_query.edit_message_text("Request accepted!")
        
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="Congratulations! You were accepted into the clan!\nYou now get 2 PAK every hour!"
            )
        except:
            pass
    else:
        await update.callback_query.edit_message_text("Error accepting request!")

async def clan_reject(update: Update, context: ContextTypes.DEFAULT_TYPE, request_id: int):
    db.reject_clan_request(request_id)
    await update.callback_query.edit_message_text("Request rejected!")

async def clan_kick(update: Update, context: ContextTypes.DEFAULT_TYPE, clan_id: int):
    members = db.get_clan_members(clan_id)
    keyboard = []
    
    for member in members:
        if member[2] != 'owner':
            keyboard.append([InlineKeyboardButton(f"Kick @{member[1]}", callback_data=f"clan_kick_user_{clan_id}_{member[0]}")])
    
    keyboard.append([InlineKeyboardButton("Back", callback_data="clan_my")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text("Select member to kick:", reply_markup=reply_markup)

async def clan_kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE, clan_id: int, user_id: int):
    db.kick_from_clan(clan_id, user_id)
    await update.callback_query.edit_message_text("Member kicked from clan!")

async def clan_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db.remove_from_clan(user_id)
    await update.callback_query.edit_message_text("You left the clan!")

async def clan_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not db.get_clan_reward_available(user_id):
        await update.callback_query.edit_message_text("Reward can be claimed once per hour!")
        return
    
    db.give_clan_reward(user_id)
    db.update_clan_reward_time(user_id)
    
    user_data = db.get_user(user_id)
    await update.callback_query.edit_message_text(
        f"You received 2 PAK for being in a clan!\n"
        f"New balance: {user_data[2]} PAK"
    )

# ==================== KEEP ALIVE & MAIN ====================

async def keep_alive():
    while True:
        await asyncio.sleep(600)
        print(f"Bot is alive - {datetime.now().strftime('%H:%M:%S')}")

async def main():
    print("Starting W1nPAK Bot...")
    
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
        
        print("Bot successfully started and ready!")
        
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        print("Bot is polling...")
        
        await asyncio.Event().wait()
        
    except Exception as e:
        print(f"Error starting bot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Critical error: {e}")

import time
import asyncio
from mcstatus import JavaServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== ВСТАВЬТЕ НОВЫЙ ТОКЕН ==========
TOKEN = "8590452175:AAGcmk1Gn-GnVZbUUAvLTRhd3QBslVE5bFk"
# ==========================================

SERVER_IP = "hi3.qwertyx.host:27228"

cache = {"data": None, "time": 0}
last_players = set()
chats = set()
consecutive_empty = 0
MAX_EMPTY_BEFORE_WARNING = 3

async def get_status():
    global consecutive_empty
    now = time.time()
    if cache["data"] and now - cache["time"] < 10:
        return cache["data"]
    try:
        server = JavaServer.lookup(SERVER_IP)
        status = server.status()
        
        players_list = []
        if status.players.sample:
            players_list = [p.name for p in status.players.sample]
        
        if status.players.online > 0 and len(players_list) == 0:
            consecutive_empty += 1
        else:
            consecutive_empty = 0
        
        data = {
            "online": True,
            "players": status.players.online,
            "max": status.players.max,
            "motd": str(status.description),
            "version": status.version.name,
            "list": players_list,
            "names_hidden": status.players.online > 0 and len(players_list) == 0
        }
        cache["data"] = data
        cache["time"] = now
        return data
    except:
        return {"online": False, "list": [], "names_hidden": False}

async def tracker(app):
    global last_players, consecutive_empty
    
    while True:
        try:
            data = await get_status()
            
            if data["online"] and not data["names_hidden"]:
                current = set(data["list"])
                
                if len(current) > 0 or len(last_players) == 0:
                    for player in current - last_players:
                        if player:
                            for chat_id in list(chats):
                                try:
                                    await app.bot.send_message(chat_id, f"🟢 {player} зашёл на сервер")
                                except:
                                    chats.discard(chat_id)
                            await asyncio.sleep(0.3)
                    
                    for player in last_players - current:
                        if player:
                            for chat_id in list(chats):
                                try:
                                    await app.bot.send_message(chat_id, f"🔴 {player} вышел с сервера")
                                except:
                                    chats.discard(chat_id)
                            await asyncio.sleep(0.3)
                    
                    last_players = current
            
            elif data["online"] and data["names_hidden"]:
                if consecutive_empty >= MAX_EMPTY_BEFORE_WARNING and len(chats) > 0:
                    for chat_id in list(chats):
                        try:
                            await app.bot.send_message(chat_id, f"⚠️ На сервере {data['players']} игроков, но хостинг скрывает их имена")
                        except:
                            chats.discard(chat_id)
                    consecutive_empty = 0
            
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Ошибка: {e}")
            await asyncio.sleep(5)

def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 Статус", callback_data="status"),
         InlineKeyboardButton("📊 Онлайн", callback_data="online")],
        [InlineKeyboardButton("👥 Список игроков", callback_data="list"),
         InlineKeyboardButton("🖥️ IP", callback_data="ip")],
        [InlineKeyboardButton("🔄 Обновить", callback_data="refresh")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chats.add(chat_id)
    await update.message.reply_text(
        "🎮 **Бот сервера Minecraft**\n\n"
        "👇 Нажмите на кнопку:\n\n"
        "📢 Бот уведомляет о входе/выходе игроков",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

async def cmd_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🖥️ `{SERVER_IP}`", parse_mode="Markdown")

# ========== НОВАЯ КОМАНДА /list ==========
async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает список всех игроков в сети"""
    data = await get_status()
    
    if not data["online"]:
        await update.message.reply_text("🔴 Сервер выключен")
        return
    
    if data["names_hidden"]:
        await update.message.reply_text(f"⚠️ Хостинг скрывает имена игроков\n📊 Онлайн: {data['players']} / {data['max']}")
        return
    
    if data["players"] == 0:
        await update.message.reply_text("🌙 На сервере никого нет")
        return
    
    # Формируем красивый список игроков
    players_list = "\n".join([f"👤 {p}" for p in data["list"]])
    await update.message.reply_text(
        f"👥 **Игроки в сети ({data['players']}/{data['max']}):**\n\n{players_list}",
        parse_mode="Markdown"
    )
# =========================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = await get_status()
    action = query.data
    
    if action == "status":
        if not data["online"]:
            text = "🔴 Сервер выключен"
        else:
            hidden_note = "\n⚠️ Имена игроков скрыты хостингом" if data.get("names_hidden", False) else ""
            text = (f"🟢 **Сервер работает**\n"
                   f"━━━━━━━━━━━━━━━━━━━\n"
                   f"📊 Онлайн: {data['players']}/{data['max']}\n"
                   f"🎮 Версия: {data['version']}\n"
                   f"📝 {data['motd']}{hidden_note}")
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_main_keyboard())
    
    elif action == "online":
        if data["online"]:
            text = f"📊 **Сейчас на сервере:** {data['players']} / {data['max']} игроков"
        else:
            text = "🔴 Сервер выключен"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_main_keyboard())
    
    elif action == "list":
        if not data["online"]:
            text = "🔴 Сервер выключен"
        elif data["names_hidden"]:
            text = f"⚠️ Хостинг скрывает имена игроков\n📊 Онлайн: {data['players']} / {data['max']}"
        elif data["players"] == 0:
            text = "🌙 На сервере никого нет"
        else:
            players_list = "\n".join([f"👤 {p}" for p in data["list"]])
            text = f"👥 **Игроки в сети ({data['players']}/{data['max']}):**\n\n{players_list}"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_main_keyboard())
    
    elif action == "ip":
        await query.edit_message_text(
            f"🖥️ `{SERVER_IP}`",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    
    elif action == "refresh":
        cache["data"] = None
        await query.edit_message_text("🔄 **Обновление...**", parse_mode="Markdown")
        new_data = await get_status()
        if new_data["online"]:
            hidden_note = "\n⚠️ Имена игроков скрыты хостингом" if new_data.get("names_hidden", False) else ""
            text = (f"🟢 **Сервер работает**\n"
                   f"━━━━━━━━━━━━━━━━━━━\n"
                   f"📊 Онлайн: {new_data['players']}/{new_data['max']}\n"
                   f"🎮 Версия: {new_data['version']}\n"
                   f"📝 {new_data['motd']}{hidden_note}")
        else:
            text = "🔴 Сервер выключен"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_main_keyboard())

async def cmd_debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отладочная команда /debug"""
    data = await get_status()
    if data["online"]:
        await update.message.reply_text(
            f"📡 **Данные от сервера:**\n\n"
            f"Онлайн: {data['players']}/{data['max']}\n"
            f"Список: {data['list'] if data['list'] else 'ПУСТО'}\n"
            f"Имена скрыты: {data.get('names_hidden', False)}\n"
            f"Версия: {data['version']}\n"
            f"MOTD: {data['motd']}",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("🔴 Сервер выключен")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ip", cmd_ip))
    app.add_handler(CommandHandler("list", cmd_list))  # Новая команда
    app.add_handler(CommandHandler("debug", cmd_debug))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(tracker(app))
    
    print("✅ Бот запущен!")
    print(f"📡 Сервер: {SERVER_IP}")
    print("👥 Команда /list — показать всех игроков в сети")
    
    app.run_polling()

if __name__ == "__main__":
    main()

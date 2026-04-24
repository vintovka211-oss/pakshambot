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

async def get_status():
    now = time.time()
    if cache["data"] and now - cache["time"] < 10:
        return cache["data"]
    try:
        server = JavaServer.lookup(SERVER_IP)
        status = server.status()
        ping = server.ping()
        data = {
            "online": True,
            "players": status.players.online,
            "max": status.players.max,
            "ping": int(ping),
            "motd": str(status.description),
            "version": status.version.name,
            "list": [p.name for p in status.players.sample] if status.players.sample else []
        }
        cache["data"] = data
        cache["time"] = now
        return data
    except:
        return {"online": False, "list": []}

async def tracker(app):
    global last_players
    while True:
        try:
            data = await get_status()
            if data["online"]:
                current = set(data["list"])
                for p in current - last_players:
                    for c in list(chats):
                        try:
                            await app.bot.send_message(c, f"🟢 **{p}** зашёл на сервер", parse_mode="Markdown")
                        except:
                            chats.discard(c)
                for p in last_players - current:
                    for c in list(chats):
                        try:
                            await app.bot.send_message(c, f"🔴 **{p}** вышел с сервера", parse_mode="Markdown")
                        except:
                            chats.discard(c)
                last_players = current
            await asyncio.sleep(5)
        except:
            await asyncio.sleep(5)

def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 Статус", callback_data="status"),
         InlineKeyboardButton("📊 Онлайн", callback_data="online")],
        [InlineKeyboardButton("📡 Пинг", callback_data="ping"),
         InlineKeyboardButton("🖥️ IP", callback_data="ip")],
        [InlineKeyboardButton("🔄 Обновить", callback_data="refresh")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chats.add(update.effective_chat.id)
    await update.message.reply_text(
        "🎮 **Бот сервера Minecraft**\n\n👇 Нажмите на кнопку:",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

# ⭐ ГЛАВНОЕ — КОМАНДА /ip ВЫВОДИТ ТОЛЬКО IP
async def cmd_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🖥️ `{SERVER_IP}`", parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = await get_status()
    action = query.data
    
    if action == "status":
        if not data["online"]:
            text = "🔴 Сервер выключен"
        else:
            ping = data["ping"]
            if ping < 50: ping_emoji = "🟢"
            elif ping < 100: ping_emoji = "🟡"
            elif ping < 150: ping_emoji = "🟠"
            else: ping_emoji = "🔴"
            text = (f"🟢 **Сервер работает**\n"
                   f"━━━━━━━━━━━━━━━━━━━\n"
                   f"📊 Онлайн: {data['players']}/{data['max']}\n"
                   f"📡 Пинг: {data['ping']} мс {ping_emoji}\n"
                   f"🎮 Версия: {data['version']}\n"
                   f"📝 {data['motd']}")
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_main_keyboard())
    
    elif action == "online":
        if data["online"]:
            text = f"📊 **Сейчас на сервере:** {data['players']} / {data['max']} игроков"
        else:
            text = "🔴 Сервер выключен"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_main_keyboard())
    
    elif action == "ping":
        if data["online"]:
            text = f"📡 **Пинг до сервера:** {data['ping']} мс"
        else:
            text = "🔴 Сервер выключен"
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
            ping = new_data["ping"]
            if ping < 50: ping_emoji = "🟢"
            elif ping < 100: ping_emoji = "🟡"
            elif ping < 150: ping_emoji = "🟠"
            else: ping_emoji = "🔴"
            text = (f"🟢 **Сервер работает**\n"
                   f"━━━━━━━━━━━━━━━━━━━\n"
                   f"📊 Онлайн: {new_data['players']}/{new_data['max']}\n"
                   f"📡 Пинг: {new_data['ping']} мс {ping_emoji}\n"
                   f"🎮 Версия: {new_data['version']}\n"
                   f"📝 {new_data['motd']}")
        else:
            text = "🔴 Сервер выключен"
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=get_main_keyboard())

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ip", cmd_ip))  # <--- Команда /ip
    app.add_handler(CallbackQueryHandler(button_handler))
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(tracker(app))
    
    print("✅ Бот запущен!")
    print(f"📡 Сервер: {SERVER_IP}")
    
    app.run_polling()

if __name__ == "__main__":
    main()

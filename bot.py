import os
import time
import asyncio
from mcstatus import JavaServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== НАСТРОЙКИ ==========
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8590452175:AAHXgI4NGGfBAxzvnnjW0ZM4_MixECdB8FQ")
JAVA_IP = os.environ.get("JAVA_IP", "hi3.qwertyx.host:27228")
BEDROCK_IP = os.environ.get("BEDROCK_IP", "hi3.qwertyx.host:27562")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 8493522297))
# ===============================

cache = {"data": None, "time": 0, "uptime_start": None}
chats = set()
last_command_time = {}
RATE_LIMIT = 3  # секунды между командами от одного пользователя

def format_uptime(seconds):
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    if days > 0:
        return f"{days}д {hours}ч {minutes}м"
    elif hours > 0:
        return f"{hours}ч {minutes}м"
    else:
        return f"{minutes}м"

def check_rate_limit(user_id):
    now = time.time()
    if user_id in last_command_time:
        if now - last_command_time[user_id] < RATE_LIMIT:
            return False
    last_command_time[user_id] = now
    return True

async def get_status():
    now = time.time()
    if cache["data"] and now - cache["time"] < 30:  # 30 секунд кэш
        return cache["data"]
    try:
        server = JavaServer.lookup(JAVA_IP)
        status = await server.async_status()
        players = [p.name for p in status.players.sample] if status.players.sample else []
        
        java_players = [p for p in players if not p.startswith(".")]
        bedrock_players = [p for p in players if p.startswith(".")]
        
        data = {
            "online": True,
            "players": status.players.online,
            "max": status.players.max,
            "motd": str(status.description),
            "version": status.version.name,
            "list": players,
            "java_list": java_players,
            "bedrock_list": bedrock_players,
        }
        cache["data"] = data
        cache["time"] = now
        if cache["uptime_start"] is None and data["online"]:
            cache["uptime_start"] = now
        return data
    except:
        return {"online": False, "list": [], "java_list": [], "bedrock_list": []}

def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 Статус", callback_data="status")],
        [InlineKeyboardButton("👥 Список игроков", callback_data="list"),
         InlineKeyboardButton("📱 Bedrock IP", callback_data="bedrock_ip")],
        [InlineKeyboardButton("📜 Правила", callback_data="rules"),
         InlineKeyboardButton("⏱ Uptime", callback_data="uptime")],
    ])

async def start(update, context):
    if not check_rate_limit(update.effective_user.id):
        await update.message.reply_text("⏳ Подожди 3 секунды перед следующей командой!")
        return
    chats.add(update.effective_chat.id)
    await update.message.reply_text(
        "🎮 HazeSMP\n"
        "🔥 PvP-сервер без приватов\n"
        "👇 Выбери действие:",
        reply_markup=get_keyboard()
    )

async def cmd_ip(update, context):
    if not check_rate_limit(update.effective_user.id):
        await update.message.reply_text("⏳ Подожди 3 секунды!")
        return
    await update.message.reply_text(f"💻 Java: {JAVA_IP} (1.21.11+)\n📱 Bedrock: {BEDROCK_IP} (1.21.130+)")

async def cmd_list(update, context):
    if not check_rate_limit(update.effective_user.id):
        await update.message.reply_text("⏳ Подожди 3 секунды!")
        return
    data = await get_status()
    if not data["online"]:
        await update.message.reply_text("🔴 Сервер выключен")
    elif data["players"] == 0:
        await update.message.reply_text("🌙 Никого нет")
    else:
        java = ', '.join(data["java_list"]) if data["java_list"] else "нет"
        bedrock = ', '.join(data["bedrock_list"]) if data["bedrock_list"] else "нет"
        await update.message.reply_text(f"👥 {data['players']}/{data['max']}\n💻 {java}\n📱 {bedrock}")

async def cmd_rules(update, context):
    if not check_rate_limit(update.effective_user.id):
        await update.message.reply_text("⏳ Подожди 3 секунды!")
        return
    await update.message.reply_text("📜 ПРАВИЛА\n🚫 Не строй неприличное\n🚫 Не оскорбляй\n⚔️ ПВП, грифинг, воровство разрешены")

async def cmd_uptime(update, context):
    if not check_rate_limit(update.effective_user.id):
        await update.message.reply_text("⏳ Подожди 3 секунды!")
        return
    if cache["uptime_start"]:
        uptime = time.time() - cache["uptime_start"]
        await update.message.reply_text(f"⏱ {format_uptime(uptime)}")
    else:
        await update.message.reply_text("🔴 Сервер выключен")

async def cmd_status(update, context):
    if not check_rate_limit(update.effective_user.id):
        await update.message.reply_text("⏳ Подожди 3 секунды!")
        return
    data = await get_status()
    if not data["online"]:
        await update.message.reply_text("🔴 Сервер выключен")
    else:
        await update.message.reply_text(f"🟢 HazeSMP\n👥 {data['players']}/{data['max']}\n🎮 {data['version']}")

async def cmd_report(update, context):
    if not check_rate_limit(update.effective_user.id):
        await update.message.reply_text("⏳ Подожди 3 секунды!")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ /report <игрок> <причина>\nПример: /report Steve Читер")
        return
    
    player = args[0]
    reason = ' '.join(args[1:])
    reporter = update.effective_user.first_name
    
    await context.bot.send_message(
        ADMIN_ID,
        f"📢 НОВАЯ ЖАЛОБА!\n\n👤 Игрок: {player}\n📝 Причина: {reason}\n📞 Пожаловался: {reporter}"
    )
    await update.message.reply_text(f"✅ Жалоба на {player} отправлена!")

async def button_handler(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    
    if not check_rate_limit(user_id):
        await query.answer("⏳ Подожди 3 секунды!", show_alert=True)
        return
    
    await query.answer()
    data = await get_status()

    if query.data == "status":
        if not data["online"]:
            text = "🔴 Сервер выключен"
        else:
            text = f"🟢 HazeSMP\n👥 {data['players']}/{data['max']}"
        await query.edit_message_text(text, reply_markup=get_keyboard())

    elif query.data == "list":
        if not data["online"]:
            text = "🔴 Сервер выключен"
        elif data["players"] == 0:
            text = "🌙 Никого нет"
        else:
            java = ', '.join(data["java_list"]) if data["java_list"] else "нет"
            bedrock = ', '.join(data["bedrock_list"]) if data["bedrock_list"] else "нет"
            text = f"👥 {data['players']}/{data['max']}\n💻 {java}\n📱 {bedrock}"
        await query.edit_message_text(text, reply_markup=get_keyboard())

    elif query.data == "bedrock_ip":
        text = f"📱 Bedrock Edition\n{BEDROCK_IP}\n✅ Версия: 1.21.130+"
        await query.edit_message_text(text, reply_markup=get_keyboard())

    elif query.data == "rules":
        text = "📜 НЕЛЬЗЯ:\n🚫 Неприличные постройки\n🚫 Оскорбления\n✅ ПВП, грифинг, воровство"
        await query.edit_message_text(text, reply_markup=get_keyboard())

    elif query.data == "uptime":
        if cache["uptime_start"]:
            uptime = time.time() - cache["uptime_start"]
            text = f"⏱ {format_uptime(uptime)}"
        else:
            text = "🔴 Сервер выключен"
        await query.edit_message_text(text, reply_markup=get_keyboard())

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ip", cmd_ip))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("rules", cmd_rules))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("uptime", cmd_uptime))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ Бот HazeSMP запущен!")
    print(f"💻 Java: {JAVA_IP}")
    print(f"📱 Bedrock: {BEDROCK_IP}")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    async def cleanup():
        app = Application.builder().token(TOKEN).build()
        await app.bot.delete_webhook(drop_pending_updates=True)
        await app.bot.close()
    asyncio.run(cleanup())
    main()

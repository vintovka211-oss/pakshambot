import time
import asyncio
from mcstatus import JavaServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== НАСТРОЙКИ ==========
TOKEN = "8590452175:AAF0Ij8fBfK6EZ3XFresIoJDsXZCpN2EAC4"
JAVA_IP = "hi3.qwertyx.host:27228"
BEDROCK_IP = "hi3.qwertyx.host:27562"
ADMIN_ID = 8493522297
# ===============================

cache = {"data": None, "time": 0, "uptime_start": None}
chats = set()
last_command_time = {}
RATE_LIMIT = 2

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
    if cache["data"] and now - cache["time"] < 30:
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
            "version": status.version.name,
            "java_list": java_players,
            "bedrock_list": bedrock_players,
        }
        cache["data"] = data
        cache["time"] = now
        if cache["uptime_start"] is None:
            cache["uptime_start"] = now
        return data
    except:
        return {"online": False, "java_list": [], "bedrock_list": []}

def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 Статус", callback_data="status"),
         InlineKeyboardButton("👥 Список", callback_data="list")],
        [InlineKeyboardButton("💻 Java IP", callback_data="java_ip"),
         InlineKeyboardButton("📱 Bedrock IP", callback_data="bedrock_ip")],
        [InlineKeyboardButton("📜 Правила", callback_data="rules"),
         InlineKeyboardButton("⏱ Uptime", callback_data="uptime"),
         InlineKeyboardButton("📢 Жалоба", callback_data="report")],
    ])

async def start(update, context):
    chats.add(update.effective_chat.id)
    await update.message.reply_text(
        "🎮 HazeSMP\n🔥 PvP-сервер без приватов\n👇 Выбери действие:",
        reply_markup=get_keyboard()
    )

async def cmd_java_ip(update, context):
    await update.message.reply_text(f"💻 Java IP: {JAVA_IP}\n✅ Версия 1.21.11+")

async def cmd_bedrock_ip(update, context):
    await update.message.reply_text(f"📱 Bedrock IP: {BEDROCK_IP}\n✅ Версия 1.21.130+")

async def cmd_ip(update, context):
    await update.message.reply_text(
        f"💻 Java: {JAVA_IP} (1.21.11+)\n📱 Bedrock: {BEDROCK_IP} (1.21.130+)"
    )

async def cmd_list(update, context):
    data = await get_status()
    if not data["online"]:
        await update.message.reply_text("🔴 Сервер выключен")
    elif len(data["java_list"]) == 0 and len(data["bedrock_list"]) == 0:
        await update.message.reply_text("🌙 На сервере никого нет")
    else:
        java = ', '.join(data["java_list"]) if data["java_list"] else "нет"
        bedrock = ', '.join(data["bedrock_list"]) if data["bedrock_list"] else "нет"
        await update.message.reply_text(
            f"👥 {len(data['java_list']) + len(data['bedrock_list'])}/{data['max']}\n\n"
            f"💻 Java: {java}\n"
            f"📱 Bedrock: {bedrock}"
        )

async def cmd_rules(update, context):
    await update.message.reply_text(
        "📜 ПРАВИЛА HazeSMP\n\n"
        "🚫 Не строить неприличные постройки\n"
        "🚫 Не оскорблять родню игроков\n"
        "⚔️ Разрешены: ПВП, грифинг, воровство\n\n"
        "✅ Нарушители получают бан!"
    )

async def cmd_uptime(update, context):
    if cache["uptime_start"]:
        uptime = time.time() - cache["uptime_start"]
        await update.message.reply_text(f"⏱ Сервер работает: {format_uptime(uptime)}")
    else:
        await update.message.reply_text("🔴 Сервер выключен")

async def cmd_status(update, context):
    data = await get_status()
    if not data["online"]:
        await update.message.reply_text("🔴 Сервер выключен")
    else:
        await update.message.reply_text(
            f"🟢 HazeSMP\n"
            f"👥 Онлайн: {len(data['java_list']) + len(data['bedrock_list'])}/{data['max']}\n"
            f"🎮 Версия: {data['version']}"
        )

async def cmd_online(update, context):
    data = await get_status()
    if data["online"]:
        await update.message.reply_text(f"📊 Онлайн: {len(data['java_list']) + len(data['bedrock_list'])}/{data['max']}")
    else:
        await update.message.reply_text("🔴 Сервер выключен")

async def cmd_report(update, context):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "❌ /report <игрок> <причина>\n"
            "Пример: /report Steve Читер"
        )
        return
    
    player = args[0]
    reason = ' '.join(args[1:])
    reporter = update.effective_user.first_name
    
    await context.bot.send_message(
        ADMIN_ID,
        f"📢 НОВАЯ ЖАЛОБА!\n\n"
        f"👤 Игрок: {player}\n"
        f"📝 Причина: {reason}\n"
        f"📞 Пожаловался: {reporter}\n"
        f"🆔 ID: {update.effective_user.id}"
    )
    await update.message.reply_text(f"✅ Жалоба на {player} отправлена администрации!")

async def button_handler(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    
    if not check_rate_limit(user_id):
        await query.answer("⏳ Подожди 2 секунды!", show_alert=True)
        return
    
    await query.answer()
    data = await get_status()

    if query.data == "status":
        if not data["online"]:
            text = "🔴 Сервер выключен"
        else:
            text = f"🟢 HazeSMP\n👥 {len(data['java_list']) + len(data['bedrock_list'])}/{data['max']}\n🎮 {data['version']}"
        await query.edit_message_text(text, reply_markup=get_keyboard())

    elif query.data == "list":
        if not data["online"]:
            text = "🔴 Сервер выключен"
        elif len(data["java_list"]) == 0 and len(data["bedrock_list"]) == 0:
            text = "🌙 Никого нет"
        else:
            java = ', '.join(data["java_list"]) if data["java_list"] else "нет"
            bedrock = ', '.join(data["bedrock_list"]) if data["bedrock_list"] else "нет"
            text = f"👥 {len(data['java_list']) + len(data['bedrock_list'])}/{data['max']}\n\n💻 {java}\n📱 {bedrock}"
        await query.edit_message_text(text, reply_markup=get_keyboard())

    elif query.data == "java_ip":
        await query.edit_message_text(f"💻 Java IP: {JAVA_IP}\n✅ 1.21.11+", reply_markup=get_keyboard())

    elif query.data == "bedrock_ip":
        await query.edit_message_text(f"📱 Bedrock IP: {BEDROCK_IP}\n✅ 1.21.130+", reply_markup=get_keyboard())

    elif query.data == "rules":
        await query.edit_message_text(
            "📜 ПРАВИЛА\n\n🚫 Неприличные постройки\n🚫 Оскорбления\n✅ ПВП, грифинг, воровство",
            reply_markup=get_keyboard()
        )

    elif query.data == "uptime":
        if cache["uptime_start"]:
            uptime = time.time() - cache["uptime_start"]
            text = f"⏱ {format_uptime(uptime)}"
        else:
            text = "🔴 Сервер выключен"
        await query.edit_message_text(text, reply_markup=get_keyboard())

    elif query.data == "report":
        await query.edit_message_text(
            "📢 ЖАЛОБА\n\nКоманда: /report <игрок> <причина>\nПример: /report Steve Читер",
            reply_markup=get_keyboard()
        )

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ip", cmd_ip))
    app.add_handler(CommandHandler("java_ip", cmd_java_ip))
    app.add_handler(CommandHandler("bedrock_ip", cmd_bedrock_ip))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("rules", cmd_rules))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("online", cmd_online))
    app.add_handler(CommandHandler("uptime", cmd_uptime))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("✅ Бот HazeSMP запущен!")
    print(f"💻 Java: {JAVA_IP}")
    print(f"📱 Bedrock: {BEDROCK_IP}")
    
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

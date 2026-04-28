import time
import asyncio
from mcstatus import JavaServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ========== НАСТРОЙКИ ==========
TOKEN = "8590452175:AAHXgI4NGGfBAxzvnnjW0ZM4_MixECdB8FQ"
JAVA_IP = "hi3.qwertyx.host:27228"
BEDROCK_IP = "hi3.qwertyx.host:27562"
ADMIN_ID = 8493522297
# ===============================

cache = {"data": None, "time": 0, "uptime_start": None}
chats = set()

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

async def get_status():
    now = time.time()
    if cache["data"] and now - cache["time"] < 10:
        return cache["data"]
    try:
        server = JavaServer.lookup(JAVA_IP)
        status = await server.async_status()
        players = [p.name for p in status.players.sample] if status.players.sample else []
        data = {
            "online": True,
            "players": status.players.online,
            "max": status.players.max,
            "motd": str(status.description),
            "version": status.version.name,
            "list": players,
        }
        cache["data"] = data
        cache["time"] = now
        if cache["uptime_start"] is None:
            cache["uptime_start"] = now
        return data
    except:
        return {"online": False, "list": []}

def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 Статус", callback_data="status"),
         InlineKeyboardButton("📊 Онлайн", callback_data="online")],
        [InlineKeyboardButton("👥 Список игроков", callback_data="list"),
         InlineKeyboardButton("💻 Java IP", callback_data="java_ip"),
         InlineKeyboardButton("📱 Bedrock IP", callback_data="bedrock_ip")],
        [InlineKeyboardButton("📜 Правила", callback_data="rules"),
         InlineKeyboardButton("🔄 Обновить", callback_data="refresh")]
    ])

async def start(update, context):
    chats.add(update.effective_chat.id)
    await update.message.reply_text(
        "🎮 **HazeSMP**\n"
        "🔥 PvP-сервер без приватов\n"
        "👇 Выбери действие:",
        reply_markup=get_keyboard(),
        parse_mode="Markdown"
    )

async def cmd_ip(update, context):
    await update.message.reply_text(
        "💻 **Java Edition**\n"
        f"`{JAVA_IP}`\n"
        "📌 Версия: **1.21.11** и выше\n\n"
        "📱 **Bedrock Edition**\n"
        f"`{BEDROCK_IP}`\n"
        "📌 Версия: **1.21.130** и выше\n\n"
        "🌍 Бери любой порт, играй с друзьями!",
        parse_mode="Markdown"
    )

async def cmd_java_ip(update, context):
    await update.message.reply_text(
        "💻 **Java Edition**\n"
        f"`{JAVA_IP}`\n"
        "✅ Версия: **1.21.11** и выше\n"
        "🎮 Заходи на ПК!",
        parse_mode="Markdown"
    )

async def cmd_bedrock_ip(update, context):
    await update.message.reply_text(
        "📱 **Bedrock Edition**\n"
        f"`{BEDROCK_IP}`\n"
        "✅ Версия: **1.21.130** и выше\n"
        "📲 Играй с телефона или планшета!",
        parse_mode="Markdown"
    )

async def cmd_list(update, context):
    data = await get_status()
    if not data["online"]:
        await update.message.reply_text("🔴 Сервер выключен")
    elif data["players"] == 0:
        await update.message.reply_text("🌙 На сервере никого нет...")
    else:
        await update.message.reply_text(f"👥 **Игроки онлайн:**\n{', '.join(data['list'])}", parse_mode="Markdown")

async def cmd_rules(update, context):
    await update.message.reply_text(
        "📜 **Правила HazeSMP**\n\n"
        "🚫 Не строить неприличные постройки\n"
        "🚫 Не оскорблять и не задевать родню игроков\n"
        "⚔️ Разрешены: ПВП, грифинг, воровство\n\n"
        "✅ Нарушители получают бан!",
        parse_mode="Markdown"
    )

async def cmd_uptime(update, context):
    if cache["uptime_start"]:
        uptime = time.time() - cache["uptime_start"]
        await update.message.reply_text(f"⏱ **Сервер работает:** {format_uptime(uptime)}", parse_mode="Markdown")
    else:
        await update.message.reply_text("🔴 Сервер выключен")

async def cmd_myid(update, context):
    await update.message.reply_text(f"🆔 Твой Telegram ID: `{update.effective_user.id}`", parse_mode="Markdown")

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    data = await get_status()

    if query.data == "status":
        if not data["online"]:
            text = "🔴 Сервер выключен"
        else:
            text = (f"🟢 **HazeSMP работает**\n"
                    f"📊 Онлайн: **{data['players']}/{data['max']}**\n"
                    f"🎮 Версия: `{data['version']}`\n"
                    f"📝 {data['motd']}")
        await query.edit_message_text(text, reply_markup=get_keyboard(), parse_mode="Markdown")

    elif query.data == "online":
        text = f"📊 **Онлайн:** {data['players']}/{data['max']}" if data["online"] else "🔴 Сервер выключен"
        await query.edit_message_text(text, reply_markup=get_keyboard(), parse_mode="Markdown")

    elif query.data == "list":
        if not data["online"]:
            text = "🔴 Сервер выключен"
        elif data["players"] == 0:
            text = "🌙 Никого нет"
        else:
            text = f"👥 **Список игроков:**\n{', '.join(data['list'])}"
        await query.edit_message_text(text, reply_markup=get_keyboard(), parse_mode="Markdown")

    elif query.data == "java_ip":
        text = (f"💻 **Java Edition**\n"
                f"`{JAVA_IP}`\n"
                "✅ Версия: **1.21.11** и выше")
        await query.edit_message_text(text, reply_markup=get_keyboard(), parse_mode="Markdown")

    elif query.data == "bedrock_ip":
        text = (f"📱 **Bedrock Edition**\n"
                f"`{BEDROCK_IP}`\n"
                "✅ Версия: **1.21.130** и выше")
        await query.edit_message_text(text, reply_markup=get_keyboard(), parse_mode="Markdown")

    elif query.data == "rules":
        await query.edit_message_text(
            "📜 **Правила HazeSMP**\n\n"
            "🚫 Не строить неприличные постройки\n"
            "🚫 Не оскорблять и не задевать родню\n"
            "⚔️ Разрешены: ПВП, грифинг, воровство\n\n"
            "✅ Нарушители получают бан!",
            reply_markup=get_keyboard(),
            parse_mode="Markdown"
        )

    elif query.data == "refresh":
        cache["data"] = None
        await query.edit_message_text("🔄 Обновление...", reply_markup=get_keyboard())
        new_data = await get_status()
        if new_data["online"]:
            text = f"🟢 Сервер работает\n📊 Онлайн: {new_data['players']}/{new_data['max']}"
        else:
            text = "🔴 Сервер выключен"
        await query.edit_message_text(text, reply_markup=get_keyboard())

async def cmd_status(update, context):
    data = await get_status()
    if not data["online"]:
        await update.message.reply_text("🔴 Сервер выключен")
    else:
        await update.message.reply_text(f"🟢 **HazeSMP**\n📊 Онлайн: {data['players']}/{data['max']}\n🎮 Версия: {data['version']}\n📝 {data['motd']}", parse_mode="Markdown")

async def cmd_online(update, context):
    data = await get_status()
    if data["online"]:
        await update.message.reply_text(f"📊 **Онлайн:** {data['players']}/{data['max']}", parse_mode="Markdown")
    else:
        await update.message.reply_text("🔴 Сервер выключен")

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
    app.add_handler(CommandHandler("myid", cmd_myid))

    app.add_handler(CallbackQueryHandler(button_handler))

    print("✅ Бот HazeSMP запущен!")
    print(f"💻 Java: {JAVA_IP}")
    print(f"📱 Bedrock: {BEDROCK_IP}")
    app.run_polling()

if __name__ == "__main__":
    main()

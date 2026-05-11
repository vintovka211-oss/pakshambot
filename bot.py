import os
import time
import asyncio
import socket
from mcstatus import JavaServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.environ.get("TELEGRAM_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", 8493522297))

JAVA_HOST = "hi3.qwertyx.host"
JAVA_PORT = 27228
BEDROCK_IP = f"{JAVA_HOST}:29098"
MAP_URL = f"http://{JAVA_HOST}:27100"

cache = {"data": None, "time": 0}

async def delete_after(context, chat_id, message_id, seconds=30):
    await asyncio.sleep(seconds)
    try:
        await context.bot.delete_message(chat_id, message_id)
    except:
        pass

def resolve_host(host):
    try:
        return socket.gethostbyname(host)
    except:
        return host

async def get_status():
    now = time.time()
    if cache["data"] and now - cache["time"] < 10:
        return cache["data"]
    try:
        # Простой сокет-тест: проверяем, открыт ли порт
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(JAVA_HOST, JAVA_PORT),
            timeout=5
        )
        writer.close()
        await writer.wait_closed()
        
        # Если порт открыт — сервер онлайн
        cache["data"] = {
            "online": True,
            "players": "?",
            "max": "?",
            "java_list": [],
            "bedrock_list": [],
        }
        cache["time"] = now
        return cache["data"]
    except:
        return {"online": False, "java_list": [], "bedrock_list": []}

def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Bedrock IP", callback_data="bedrock_ip"),
         InlineKeyboardButton("💻 Java IP", callback_data="java_ip")],
        [InlineKeyboardButton("🗺️ Карта", callback_data="map"),
         InlineKeyboardButton("👥 Онлайн", callback_data="list")],
        [InlineKeyboardButton("📢 Жалоба", callback_data="report")]
    ])

async def start(update, context):
    msg = await update.message.reply_text(
        "🎮 **HazeRage**\n👇 Выбери действие:",
        reply_markup=get_keyboard(),
        parse_mode="Markdown"
    )
    asyncio.create_task(delete_after(context, msg.chat_id, msg.message_id))

async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    data = await get_status()

    if query.data == "java_ip":
        text = f"💻 **Java**\n`{JAVA_HOST}:{JAVA_PORT}`\n✅ 1.21.11+"
        await query.edit_message_text(text, parse_mode="Markdown")
        msg = await query.message.reply_text("⬅️ Назад", reply_markup=get_keyboard())
        asyncio.create_task(delete_after(context, msg.chat_id, msg.message_id))

    elif query.data == "bedrock_ip":
        text = f"📱 **Bedrock**\n`{BEDROCK_IP}`\n✅ 1.21.130+"
        await query.edit_message_text(text, parse_mode="Markdown")
        msg = await query.message.reply_text("⬅️ Назад", reply_markup=get_keyboard())
        asyncio.create_task(delete_after(context, msg.chat_id, msg.message_id))

    elif query.data == "map":
        text = f"🗺️ **Карта**\n{MAP_URL}"
        await query.edit_message_text(text, parse_mode="Markdown")
        msg = await query.message.reply_text("⬅️ Назад", reply_markup=get_keyboard())
        asyncio.create_task(delete_after(context, msg.chat_id, msg.message_id))

    elif query.data == "list":
        if not data["online"]:
            text = "🔴 Сервер выключен"
        elif data["players"] == 0:
            text = "🌙 Никого нет"
        else:
            java = ', '.join(data["java_list"]) if data["java_list"] else "—"
            bedrock = ', '.join(data["bedrock_list"]) if data["bedrock_list"] else "—"
            text = f"👥 **Онлайн:** {data['players']}/{data['max']}\n\n💻 Java: {java}\n📱 Bedrock: {bedrock}"
        await query.edit_message_text(text, parse_mode="Markdown")
        msg = await query.message.reply_text("⬅️ Назад", reply_markup=get_keyboard())
        asyncio.create_task(delete_after(context, msg.chat_id, msg.message_id))

    elif query.data == "report":
        msg = await query.edit_message_text(
            "📢 **Жалоба**\n\n`/report <игрок> <причина>`\nПример: `/report Steve`",
            parse_mode="Markdown"
        )
        asyncio.create_task(delete_after(context, msg.chat_id, msg.message_id, 20))

async def cmd_report(update, context):
    args = context.args
    if len(args) < 2:
        msg = await update.message.reply_text("❌ /report <игрок> <причина>")
        asyncio.create_task(delete_after(context, msg.chat_id, msg.message_id, 10))
        return
    player = args[0]
    reason = ' '.join(args[1:])
    reporter = update.effective_user.first_name
    await context.bot.send_message(
        ADMIN_ID,
        f"📢 **ЖАЛОБА**\n👤 {player}\n📝 {reason}\n📞 {reporter}"
    )
    msg = await update.message.reply_text(f"✅ Жалоба на {player} отправлена")
    asyncio.create_task(delete_after(context, msg.chat_id, msg.message_id, 10))

def main():
    if not TOKEN:
        print("❌ Нет токена! Добавь переменную TELEGRAM_TOKEN")
        return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("✅ Бот HazeRage запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

import time
import asyncio
from mcstatus import JavaServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMemberUpdated
from telegram.constants import ChatMemberStatus
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ChatMemberHandler, ContextTypes

# ========== НАСТРОЙКИ ==========
TOKEN = "8590452175:AAF0Ij8fBfK6EZ3XFresIoJDsXZCpN2EAC4"
JAVA_IP = "hi3.qwertyx.host:27228"
BEDROCK_IP = "hi3.qwertyx.host:29098"
MAP_URL = "http://hi3.qwertyx.host:27100"
ADMIN_ID = 8493522297
# ===============================

cache = {"data": None, "time": 0}

async def delete_after(context, chat_id, message_id, seconds=30):
    await asyncio.sleep(seconds)
    try:
        await context.bot.delete_message(chat_id, message_id)
    except:
        pass

async def get_status():
    now = time.time()
    if cache["data"] and now - cache["time"] < 10:
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
            "list": players,
            "java_list": java_players,
            "bedrock_list": bedrock_players,
        }
        cache["data"] = data
        cache["time"] = now
        return data
    except:
        return {"online": False, "list": [], "java_list": [], "bedrock_list": []}

def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Bedrock IP", callback_data="bedrock_ip"),
         InlineKeyboardButton("💻 Java IP", callback_data="java_ip")],
        [InlineKeyboardButton("🗺️ Карта", callback_data="map"),
         InlineKeyboardButton("👥 Список игроков", callback_data="list")],
        [InlineKeyboardButton("📢 Жалоба", callback_data="report")]
    ])

# ========== ПРИВЕТСТВИЕ НОВОГО УЧАСТНИКА ==========
async def welcome_new_member(update: ChatMemberUpdated, context: ContextTypes.DEFAULT_TYPE):
    if update.new_chat_member.status == ChatMemberStatus.MEMBER and update.old_chat_member.status != ChatMemberStatus.MEMBER:
        user = update.new_chat_member.user
        
        try:
            with open("welcome.png", "rb") as photo:
                await context.bot.send_photo(
                    chat_id=update.chat.id,
                    photo=photo,
                    caption=f"🎉 **Добро пожаловать, {user.first_name}!**\n\n"
                            f"🔥 **HazeRage** — PvP-сервер без приватов\n"
                            f"💻 Java / 📱 Bedrock\n\n"
                            f"⬇️ **Нажми /start, чтобы начать!**",
                    parse_mode="Markdown"
                )
        except FileNotFoundError:
            await context.bot.send_message(
                chat_id=update.chat.id,
                text=f"🎉 **Добро пожаловать, {user.first_name}!**\n\n"
                     f"🔥 **HazeRage** — PvP-сервер без приватов\n"
                     f"💻 Java / 📱 Bedrock\n\n"
                     f"⬇️ **Нажми /start, чтобы начать!**",
                parse_mode="Markdown"
            )

# ========== СТАРТ ==========
async def start(update, context):
    msg = await update.message.reply_text(
        "🎮 **HazeRage**\n"
        "👇 Выбери действие:",
        reply_markup=get_keyboard(),
        parse_mode="Markdown"
    )
    asyncio.create_task(delete_after(context, msg.chat_id, msg.message_id))

# ========== КНОПКИ ==========
async def button_handler(update, context):
    query = update.callback_query
    await query.answer()
    data = await get_status()

    if query.data == "java_ip":
        text = f"💻 **Java Edition**\n`{JAVA_IP}`\n✅ Версия: 1.21.11+"
        await query.edit_message_text(text, parse_mode="Markdown")
        msg = await query.message.reply_text("⬅️ Вернись в меню", reply_markup=get_keyboard())
        asyncio.create_task(delete_after(context, msg.chat_id, msg.message_id))
        
    elif query.data == "bedrock_ip":
        text = f"📱 **Bedrock Edition**\n`{BEDROCK_IP}`\n✅ Версия: 1.21.130+"
        await query.edit_message_text(text, parse_mode="Markdown")
        msg = await query.message.reply_text("⬅️ Вернись в меню", reply_markup=get_keyboard())
        asyncio.create_task(delete_after(context, msg.chat_id, msg.message_id))
        
    elif query.data == "map":
        text = f"🗺️ **Карта HazeRage**\n\n{MAP_URL}"
        await query.edit_message_text(text, parse_mode="Markdown")
        msg = await query.message.reply_text("⬅️ Вернись в меню", reply_markup=get_keyboard())
        asyncio.create_task(delete_after(context, msg.chat_id, msg.message_id))
        
    elif query.data == "list":
        if not data["online"]:
            text = "🔴 Сервер выключен"
        elif data["players"] == 0:
            text = "🌙 Никого нет"
        else:
            java = ', '.join(data["java_list"]) if data["java_list"] else "никого"
            bedrock = ', '.join(data["bedrock_list"]) if data["bedrock_list"] else "никого"
            text = f"👥 **Игроки онлайн:** {data['players']}/{data['max']}\n\n💻 Java: {java}\n📱 Bedrock: {bedrock}"
        await query.edit_message_text(text, parse_mode="Markdown")
        msg = await query.message.reply_text("⬅️ Вернись в меню", reply_markup=get_keyboard())
        asyncio.create_task(delete_after(context, msg.chat_id, msg.message_id))
        
    elif query.data == "report":
        msg = await query.edit_message_text(
            "📢 **Отправить жалобу**\n\n"
            "Напиши в чат:\n`/report <игрок> <причина>`\n\n"
            "Пример: `/report Steve Читер`",
            parse_mode="Markdown"
        )
        asyncio.create_task(delete_after(context, msg.chat_id, msg.message_id, 20))

# ========== ЖАЛОБЫ ==========
async def cmd_report(update, context):
    args = context.args
    if len(args) < 2:
        msg = await update.message.reply_text(
            "❌ /report <игрок> <причина>\nПример: /report Steve Читер"
        )
        asyncio.create_task(delete_after(context, msg.chat_id, msg.message_id, 10))
        return
    
    player = args[0]
    reason = ' '.join(args[1:])
    reporter = update.effective_user.first_name
    
    await context.bot.send_message(
        ADMIN_ID,
        f"📢 **НОВАЯ ЖАЛОБА**\n\n"
        f"👤 Игрок: {player}\n"
        f"📝 Причина: {reason}\n"
        f"📞 От: {reporter}\n"
        f"🆔 ID: {update.effective_user.id}"
    )
    msg = await update.message.reply_text(f"✅ Жалоба на {player} отправлена!")
    asyncio.create_task(delete_after(context, msg.chat_id, msg.message_id, 10))

# ========== АДМИН КОМАНДЫ ==========
async def cmd_broadcast(update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Нет прав")
        return
    message = ' '.join(context.args)
    if not message:
        await update.message.reply_text("❌ /broadcast <текст>")
        return
    for member in await context.bot.get_chat_administrators(update.effective_chat.id):
        try:
            await context.bot.send_message(member.user.id, f"📢 {message}")
        except:
            pass
    await update.message.reply_text("✅ Рассылка отправлена")

# ========== MAIN ==========
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(ChatMemberHandler(welcome_new_member, ChatMemberHandler.CHAT_MEMBER))

    print("✅ Бот HazeRage запущен!")
    print(f"💻 Java: {JAVA_IP}")
    print(f"📱 Bedrock: {BEDROCK_IP}")
    print(f"🗺️ Карта: {MAP_URL}")

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

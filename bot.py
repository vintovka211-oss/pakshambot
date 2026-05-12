import os
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Токен из переменной окружения
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    print("❌ Ошибка: переменная окружения TELEGRAM_TOKEN не найдена!")
    sys.exit(1)

# Настройки сервера
JAVA_IP = "hi3.qwertyx.host:27228"
BEDROCK_IP = "hi3.qwertyx.host:29098"
MAP_URL = "http://hi3.qwertyx.host:27100"

# Куда отправлять жалобы
ADMIN_ID = 8493522297

def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Онлайн", callback_data="online"),
         InlineKeyboardButton("📢 Жалоба", callback_data="report")]
    ])

async def start(update: Update, context):
    await update.message.reply_text(
        f"🔥 **HazeRage** — анархия, PvP, без приватов\n\n"
        f"💻 **Java Edition**\n`{JAVA_IP}`\n_Версия: 1.21.11+_\n\n"
        f"📱 **Bedrock Edition**\n`{BEDROCK_IP}`\n_Версия: 1.21.130+_\n\n"
        f"🗺️ **Карта:**\n{MAP_URL}\n\n"
        f"👇 Выбери действие:",
        reply_markup=get_keyboard(),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == "online":
        await query.edit_message_text(
            f"💻 **Java Edition:** `{JAVA_IP}`\n"
            f"📱 **Bedrock Edition:** `{BEDROCK_IP}`\n"
            f"🗺️ **Карта:** {MAP_URL}\n\n"
            f"🟢 Сервер работает, заходи!",
            reply_markup=get_keyboard(),
            parse_mode="Markdown"
        )
    
    elif query.data == "report":
        await query.edit_message_text(
            "📢 **Пожаловаться на игрока**\n\n"
            "Напиши в ответном сообщении:\n"
            "`/report <ник> <причина>`\n\n"
            "Пример: `/report Steve Читер`",
            reply_markup=get_keyboard(),
            parse_mode="Markdown"
        )

async def cmd_report(update: Update, context):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ /report <ник> <причина>")
        return
    player = args[0]
    reason = ' '.join(args[1:])
    await context.bot.send_message(
        ADMIN_ID,
        f"📢 **Жалоба на {player}**\n📝 Причина: {reason}\n👤 От: {update.effective_user.first_name}"
    )
    await update.message.reply_text(f"✅ Жалоба на **{player}** отправлена администрации!", parse_mode="Markdown")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("report", cmd_report))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("✅ Бот HazeRage запущен!")
    print(f"💻 Java: {JAVA_IP}")
    print(f"📱 Bedrock: {BEDROCK_IP}")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

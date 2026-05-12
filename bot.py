import os
import sys
import time
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Токен из переменной окружения
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    print("❌ Токен не найден! Добавь переменную TELEGRAM_TOKEN")
    sys.exit(1)

# Настройки сервера
JAVA_IP = "hi3.qwertyx.host:27228"
BEDROCK_IP = "hi3.qwertyx.host:29098"
MAP_URL = "http://hi3.qwertyx.host:27100"
ADMIN_ID = 8493522297

# Кеш для онлайна
online_cache = {"online": 0, "timestamp": 0}

# ========== КОМАНДЫ ==========

async def start(update: Update, context):
    """Приветствие с IP и картой"""
    await update.message.reply_text(
        f"🔥 HazeRage — анархия, PvP, без приватов\n\n"
        f"💻 Java Edition: {JAVA_IP}\n"
        f"📱 Bedrock Edition: {BEDROCK_IP}\n"
        f"🗺️ Карта: {MAP_URL}\n\n"
        f"Команды:\n"
        f"/online — показывает онлайн\n"
        f"/report <ник> <причина> — жалоба"
    )

async def online(update: Update, context):
    """Показывает онлайн сервера"""
    now = time.time()
    
    # Обновляем кеш раз в 30 секунд
    if now - online_cache["timestamp"] > 30:
        try:
            r = requests.get(f"https://api.mcsrvstat.us/2/{JAVA_IP}", timeout=5)
            data = r.json()
            online_cache["online"] = data.get("players", {}).get("online", 0)
            online_cache["timestamp"] = now
        except:
            pass
    
    await update.message.reply_text(f"📊 Онлайн: {online_cache['online']}")

async def report(update: Update, context):
    """Отправляет жалобу админу"""
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ Использование: /report <ник> <причина>\nПример: /report Steve Читер")
        return
    
    player = args[0]
    reason = ' '.join(args[1:])
    sender = update.effective_user.first_name
    
    await context.bot.send_message(
        ADMIN_ID,
        f"📢 ЖАЛОБА!\n\n👤 Игрок: {player}\n📝 Причина: {reason}\n📞 От: {sender}"
    )
    await update.message.reply_text(f"✅ Жалоба на {player} отправлена!")

# ========== ЗАПУСК ==========

def main():
    app = Application.builder().token(TOKEN).build()
    
    # Регистрируем команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("online", online))
    app.add_handler(CommandHandler("report", report))
    
    print("✅ Бот HazeRage запущен!")
    print(f"💻 Java: {JAVA_IP}")
    print(f"📱 Bedrock: {BEDROCK_IP}")
    
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

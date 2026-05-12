import os
import sys
import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler

# Берем токен из переменной окружения
TOKEN = os.environ.get("TELEGRAM_TOKEN")

if not TOKEN:
    print("❌ Ошибка: переменная окружения TELEGRAM_TOKEN не найдена!")
    print("👉 Добавь её в настройках Pterodactyl (Variables)")
    sys.exit(1)

async def start(update: Update, context):
    await update.message.reply_text("✅ Бот работает!")

async def ping(update: Update, context):
    await update.message.reply_text("🏓 Pong!")

def main():
    print("✅ Бот HazeRage запущен!")
    print(f"📡 Токен получен из переменной окружения")
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))
    
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

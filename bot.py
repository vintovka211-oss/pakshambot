import os
import logging
import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ===== НАСТРОЙКИ =====
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise ValueError("Переменная TOKEN не установлена!")

# ВАШ TELEGRAM ID (только вы можете активировать подписку)
ADMIN_ID = 8493522297

# ВАШ НОМЕР ТЕЛЕФОНА ДЛЯ ОПЛАТЫ
PHONE_NUMBER = "+7 927 668-55-12"

# ===== БАЗА ДАННЫХ =====
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        income INTEGER DEFAULT 0,
        income_from_individuals INTEGER DEFAULT 0,
        income_from_legal INTEGER DEFAULT 0,
        subscription_until TEXT,
        tax_rate INTEGER DEFAULT 4
    )
''')
conn.commit()

# ===== ЛОГИРОВАНИЕ =====
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ===== КОМАНДА /start =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "NoUsername"
    
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
    conn.commit()
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить доход", callback_data="add_income")],
        [InlineKeyboardButton("📊 Мой налог", callback_data="my_tax")],
        [InlineKeyboardButton("⚙️ Ставка налога", callback_data="tax_rate")],
        [InlineKeyboardButton("💎 Подписка 199 ₽/мес", callback_data="subscription")]
    ]
    await update.message.reply_text(
        "🤖 *Налоговый помощник для самозанятых 2026*\n\n"
        "Я считаю налог 4% или 6% от вашего дохода, учитываю вычет 10 000 ₽ и контролирую лимит 2.4 млн ₽.\n\n"
        "🔓 *Бесплатно:* ручной ввод суммы, базовый расчёт\n"
        "💎 *Подписка 199 ₽/мес:* история доходов + напоминалки + контроль лимита\n\n"
        "⚙️ Сначала выберите ставку налога (4% — с физлиц, 6% — с юрлиц)",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ===== ВЫБОР СТАВКИ НАЛОГА =====
async def tax_rate_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🏠 4% (с физических лиц)", callback_data="set_rate_4")],
        [InlineKeyboardButton("🏢 6% (с юридических лиц)", callback_data="set_rate_6")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
    ]
    
    await query.edit_message_text(
        "⚙️ *Выберите ставку налога:*\n\n"
        "• 4% — если получаете доход от физических лиц\n"
        "• 6% — если получаете доход от юридических лиц\n\n"
        "⚠️ *Важно:* при получении доходов от разных типов клиентов, налог считается по каждой ставке отдельно.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def set_rate_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    cursor.execute('UPDATE users SET tax_rate = 4 WHERE user_id = ?', (user_id,))
    conn.commit()
    
    keyboard = [[InlineKeyboardButton("🔙 В меню", callback_data="back_to_menu")]]
    await query.edit_message_text(
        "✅ Установлена ставка *4%* (с физических лиц)\n\n"
        "Теперь вы можете добавлять доходы.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def set_rate_6(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    cursor.execute('UPDATE users SET tax_rate = 6 WHERE user_id = ?', (user_id,))
    conn.commit()
    
    keyboard = [[InlineKeyboardButton("🔙 В меню", callback_data="back_to_menu")]]
    await query.edit_message_text(
        "✅ Установлена ставка *6%* (с юридических лиц)\n\n"
        "Теперь вы можете добавлять доходы.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ===== ДОБАВЛЕНИЕ ДОХОДА =====
async def add_income_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("👤 От физического лица (4%)", callback_data="income_individual")],
        [InlineKeyboardButton("🏢 От юридического лица (6%)", callback_data="income_legal")],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
    ]
    
    await query.edit_message_text(
        "➕ *Выберите тип дохода:*\n\n"
        "• От физического лица — ставка 4%\n"
        "• От юридического лица — ставка 6%",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def income_individual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['income_type'] = 'individual'
    await query.edit_message_text("Введите сумму дохода от физического лица (например: 15000):")

async def income_legal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['income_type'] = 'legal'
    await query.edit_message_text("Введите сумму дохода от юридического лица (например: 15000):")

async def handle_income_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('income_type'):
        try:
            amount = int(update.message.text.replace(' ', ''))
            user_id = update.effective_user.id
            income_type = context.user_data['income_type']
            
            if income_type == 'individual':
                cursor.execute('UPDATE users SET income = income + ?, income_from_individuals = income_from_individuals + ? WHERE user_id = ?', (amount, amount, user_id))
            else:
                cursor.execute('UPDATE users SET income = income + ?, income_from_legal = income_from_legal + ? WHERE user_id = ?', (amount, amount, user_id))
            
            conn.commit()
            await update.message.reply_text(f"✅ Добавлено {amount} ₽")
            context.user_data['income_type'] = None
            
            # Показать обновлённый налог
            await my_tax_auto(update, context)
            
        except:
            await update.message.reply_text("❌ Ошибка. Введите число без букв.")
            context.user_data['income_type'] = None

async def my_tax_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute('SELECT income_from_individuals, income_from_legal, subscription_until FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    income_ind = result[0] or 0
    income_leg = result[1] or 0
    subscription_until = result[2]
    
    has_subscription = subscription_until and datetime.strptime(subscription_until, '%Y-%m-%d') > datetime.now()
    
    tax_ind = int(income_ind * 0.04)
    tax_leg = int(income_leg * 0.06)
    total_tax = tax_ind + tax_leg
    total_income = income_ind + income_leg
    
    # Налоговый вычет 10 000 ₽
    DEDUCTION = 10000
    if total_tax > DEDUCTION:
        total_tax_after_deduction = total_tax - DEDUCTION
        deduction_text = f"🎁 Вычет 10 000 ₽ применён. Экономия: 10 000 ₽"
    else:
        total_tax_after_deduction = 0
        deduction_text = f"🎁 Вычет 10 000 ₽ полностью обнулил налог"
    
    # Проверка лимита 2.4 млн ₽
    LIMIT = 2_400_000
    if total_income > LIMIT and has_subscription:
        await update.message.reply_text(
            f"⚠️ *КРИТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ!*\n\n"
            f"Ваш доход ({total_income:,} ₽) превысил лимит самозанятого (2.4 млн ₽).\n\n"
            f"С превышения налог считается по ставке 13% как НДФЛ.\n"
            f"Рекомендуем обратиться к бухгалтеру или рассмотреть открытие ИП.\n\n"
            f"📞 *Нужна консультация?* Напишите /help",
            parse_mode="Markdown"
        )
        return
    
    if has_subscription:
        await update.message.reply_text(
            f"📊 *Ваш налог за месяц:*\n\n"
            f"👤 С физлиц (4%): {income_ind:,} ₽ → *{tax_ind:,} ₽*\n"
            f"🏢 С юрлиц (6%): {income_leg:,} ₽ → *{tax_leg:,} ₽*\n"
            f"📈 Всего доход: {total_income:,} ₽\n"
            f"💰 Итого налог: *{total_tax:,} ₽*\n"
            f"{deduction_text}\n"
            f"💵 К оплате: *{total_tax_after_deduction:,} ₽*\n\n"
            f"🗓 Заплатить до 25 числа\n"
            f"📊 Лимит: {total_income:,} / {LIMIT:,} ₽",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"📊 *Ваш налог за месяц:*\n\n"
            f"👤 С физлиц (4%): {income_ind:,} ₽ → {tax_ind:,} ₽\n"
            f"🏢 С юрлиц (6%): {income_leg:,} ₽ → {tax_leg:,} ₽\n"
            f"💰 Всего: *{total_tax:,} ₽*\n\n"
            f"💎 *Купите подписку за 199 ₽*, чтобы:\n"
            f"• Получать напоминалки об оплате\n"
            f"• Видеть учёт вычета и контроль лимита\n"
            f"• Сохранять историю доходов\n\n"
            f"Нажмите «Подписка» в главном меню",
            parse_mode="Markdown"
        )

# ===== МОЙ НАЛОГ (из меню) =====
async def my_tax(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await my_tax_auto(update, context)
    
    keyboard = [[InlineKeyboardButton("🔙 В меню", callback_data="back_to_menu")]]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

# ===== ПОДПИСКА =====
async def subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
    ]
    
    await query.edit_message_text(
        f"💎 *Подписка 199 ₽/мес*\n\n"
        f"Что даёт:\n"
        f"✅ Полный расчёт налога с учётом вычета 10 000 ₽\n"
        f"✅ Контроль лимита 2.4 млн ₽ (предупреждение о превышении)\n"
        f"✅ Напоминалки об оплате до 25 числа\n"
        f"✅ История всех доходов за месяц\n\n"
        f"🔐 *Как оплатить:*\n"
        f"1️⃣ Переведите 199 ₽ по номеру телефона:\n"
        f"`{PHONE_NUMBER}`\n\n"
        f"2️⃣ После оплаты пришлите скриншот чека сюда\n"
        f"3️⃣ Я активирую подписку вручную\n\n"
        f"✅ Подписка будет активна 30 дней\n\n"
        f"⏱ Обычно активирую в течение часа в рабочее время",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ===== АКТИВАЦИЯ ПОДПИСКИ (ТОЛЬКО ДЛЯ АДМИНА) =====
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет прав для этой команды.\n\nЕсли вы оплатили подписку, отправьте чек сюда — я активирую вручную.")
        return
    
    args = context.args
    if not args:
        await update.message.reply_text(
            "ℹ️ *Как активировать подписку:*\n\n"
            "1. Узнайте ID пользователя (он виден в переписке или через @userinfobot)\n"
            "2. Напишите: `/confirm 123456789`\n\n"
            "Где 123456789 — ID пользователя",
            parse_mode="Markdown"
        )
        return
    
    try:
        target_user_id = int(args[0])
        until = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        cursor.execute('UPDATE users SET subscription_until = ? WHERE user_id = ?', (until, target_user_id))
        conn.commit()
        await update.message.reply_text(f"✅ Подписка активирована для пользователя `{target_user_id}` на 30 дней!", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}\nУбедитесь, что ID правильный.")

# ===== КНОПКА НАЗАД =====
async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить доход", callback_data="add_income")],
        [InlineKeyboardButton("📊 Мой налог", callback_data="my_tax")],
        [InlineKeyboardButton("⚙️ Ставка налога", callback_data="tax_rate")],
        [InlineKeyboardButton("💎 Подписка 199 ₽/мес", callback_data="subscription")]
    ]
    
    await query.edit_message_text(
        "🤖 *Налоговый помощник для самозанятых 2026*\n\n"
        "Выберите действие:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ===== ЗАПУСК БОТА =====
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm))
    app.add_handler(CallbackQueryHandler(tax_rate_menu, pattern="tax_rate"))
    app.add_handler(CallbackQueryHandler(set_rate_4, pattern="set_rate_4"))
    app.add_handler(CallbackQueryHandler(set_rate_6, pattern="set_rate_6"))
    app.add_handler(CallbackQueryHandler(add_income_callback, pattern="add_income"))
    app.add_handler(CallbackQueryHandler(income_individual, pattern="income_individual"))
    app.add_handler(CallbackQueryHandler(income_legal, pattern="income_legal"))
    app.add_handler(CallbackQueryHandler(my_tax, pattern="my_tax"))
    app.add_handler(CallbackQueryHandler(subscription, pattern="subscription"))
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern="back_to_menu"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_income_text))
    
    print("✅ Бот запущен и работает...")
    app.run_polling()

if __name__ == "__main__":
    main()

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

ADMIN_ID = 8493522297
PHONE_NUMBER = "+7 927 668-55-12"

# ===== БАЗА ДАННЫХ =====
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

# Создание таблиц
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        income INTEGER DEFAULT 0,
        income_from_individuals INTEGER DEFAULT 0,
        income_from_legal INTEGER DEFAULT 0,
        subscription_until TEXT,
        tax_rate INTEGER DEFAULT 4,
        last_month_income INTEGER DEFAULT 0,
        incomes_history TEXT DEFAULT ''
    )
''')
conn.commit()

# ===== КОНСТАНТЫ =====
LIMIT = 2_400_000
DEDUCTION = 10_000

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
def has_subscription(user_id):
    cursor.execute('SELECT subscription_until FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    return result and result[0] and datetime.strptime(result[0], '%Y-%m-%d') > datetime.now()

def save_income_history(user_id, amount, income_type):
    cursor.execute('SELECT incomes_history FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    history = result[0] if result[0] else ""
    new_entry = f"{datetime.now().strftime('%Y-%m-%d')}:{amount}:{income_type}|"
    cursor.execute('UPDATE users SET incomes_history = ? WHERE user_id = ?', (history + new_entry, user_id))
    conn.commit()

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
        [InlineKeyboardButton("💎 Premium 199 ₽/мес", callback_data="subscription")]
    ]
    await update.message.reply_text(
        "🤖 *Налоговый помощник для самозанятых 2026*\n\n"
        "Я считаю налог 4% или 6%, учитываю вычет 10 000 ₽ и контролирую лимит 2.4 млн ₽.\n\n"
        "🔓 *Бесплатно:* базовый расчёт\n"
        "💎 *Premium 199 ₽/мес:* полная аналитика + отчёты + прогнозы\n\n"
        "⚙️ Начните с выбора ставки налога",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ===== ВЫБОР СТАВКИ =====
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
        "• 4% — доходы от физических лиц\n"
        "• 6% — доходы от юридических лиц",
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
        "✅ Установлена ставка *4%* (с физических лиц)",
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
        "✅ Установлена ставка *6%* (с юридических лиц)",
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
        "➕ *Выберите тип дохода:*",
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

# ===== ОБРАБОТКА ВВОДА СУММЫ =====
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
            
            save_income_history(user_id, amount, income_type)
            conn.commit()
            await update.message.reply_text(f"✅ Добавлено {amount:,} ₽")
            context.user_data['income_type'] = None
            await my_tax_auto(update, context)
            
        except:
            await update.message.reply_text("❌ Ошибка. Введите число без букв.")
            context.user_data['income_type'] = None

# ===== РАСЧЁТ НАЛОГА =====
async def my_tax_auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute('SELECT income_from_individuals, income_from_legal, subscription_until, last_month_income, incomes_history FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    income_ind = result[0] or 0
    income_leg = result[1] or 0
    sub_until = result[2]
    last_month = result[3] or 0
    history = result[4] or ""
    
    is_premium = sub_until and datetime.strptime(sub_until, '%Y-%m-%d') > datetime.now()
    
    total_income = income_ind + income_leg
    tax_ind = int(income_ind * 0.04)
    tax_leg = int(income_leg * 0.06)
    total_tax = tax_ind + tax_leg
    
    # Налоговый вычет
    if total_tax > DEDUCTION:
        total_tax_after = total_tax - DEDUCTION
        deduction_text = f"🎁 Вычет {DEDUCTION:,} ₽ применён"
    else:
        total_tax_after = 0
        deduction_text = f"🎁 Вычет полностью обнулил налог"
    
    # Сравнение с прошлым месяцем
    change = total_income - last_month
    trend = "📈 +" if change > 0 else "📉 "
    
    # Прогноз на следующий месяц (простой: +10% если рост)
    if last_month > 0:
        growth_rate = (total_income - last_month) / last_month
        forecast = int(total_income * (1 + growth_rate))
    else:
        forecast = int(total_income * 1.1)
    
    # Проверка лимита
    limit_warning = ""
    if total_income > LIMIT:
        limit_warning = f"\n⚠️ *ПРЕВЫШЕНИЕ ЛИМИТА!* {total_income:,} / {LIMIT:,} ₽"
    
    if is_premium:
        # Чек-лист для Premium
        checklist = """
📋 *Чек-лист самозанятого:*
✅ Зарегистрирован в ФНС
✅ Выдаю чеки через «Мой налог»
✅ Плачу налог до 25 числа
✅ Не превысил лимит 2.4 млн ₽
✅ Использовал вычет 10 000 ₽
"""
        
        await update.message.reply_text(
            f"📊 *Ваш налог за месяц*\n\n"
            f"👤 С физлиц (4%): {income_ind:,} ₽ → *{tax_ind:,} ₽*\n"
            f"🏢 С юрлиц (6%): {income_leg:,} ₽ → *{tax_leg:,} ₽*\n"
            f"📈 Всего доход: {total_income:,} ₽\n"
            f"💰 Налог до вычета: {total_tax:,} ₽\n"
            f"{deduction_text}\n"
            f"💵 *К оплате: {total_tax_after:,} ₽*\n\n"
            f"📉 *Динамика:* {trend}{abs(change):,} ₽ к прошлому месяцу\n"
            f"🔮 *Прогноз на след. месяц:* {forecast:,} ₽\n"
            f"🗓 Заплатить до 25 числа\n"
            f"📊 Лимит: {total_income:,} / {LIMIT:,} ₽{limit_warning}\n"
            f"{checklist}\n"
            f"📎 /report — скачать годовой отчёт",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"📊 *Ваш налог за месяц*\n\n"
            f"👤 С физлиц: {income_ind:,} ₽ → {tax_ind:,} ₽\n"
            f"🏢 С юрлиц: {income_leg:,} ₽ → {tax_leg:,} ₽\n"
            f"💰 *Итого: {total_tax:,} ₽*\n\n"
            f"💎 *Premium 199 ₽/мес* — получите:\n"
            f"• Учёт вычета {DEDUCTION:,} ₽\n"
            f"• Динамику и прогноз\n"
            f"• Чек-лист самозанятого\n"
            f"• Годовой отчёт\n"
            f"• Напоминалки\n\n"
            f"Нажмите «Premium» в меню",
            parse_mode="Markdown"
        )

# ===== МОЙ НАЛОГ (из меню) =====
async def my_tax(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await my_tax_auto(update, context)
    
    keyboard = [[InlineKeyboardButton("🔙 В меню", callback_data="back_to_menu")]]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))

# ===== ГОДОВОЙ ОТЧЁТ (только Premium) =====
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not has_subscription(user_id):
        await update.message.reply_text("❌ Годовой отчёт доступен только по Premium подписке. Нажмите «Premium» в меню.")
        return
    
    cursor.execute('SELECT income_from_individuals, income_from_legal, incomes_history FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    income_ind = result[0] or 0
    income_leg = result[1] or 0
    history = result[2] or ""
    
    total_income = income_ind + income_leg
    total_tax = int(income_ind * 0.04 + income_leg * 0.06)
    
    report_text = f"""
📄 *ГОДОВОЙ ОТЧЕТ ДЛЯ ФНС*
━━━━━━━━━━━━━━━━━━━━━

📊 *Доходы за год:*
• От физических лиц: {income_ind:,} ₽
• От юридических лиц: {income_leg:,} ₽
• Всего доходов: {total_income:,} ₽

💰 *Налог:*
• Ставка 4%: {int(income_ind * 0.04):,} ₽
• Ставка 6%: {int(income_leg * 0.06):,} ₽
• Итого налог: {total_tax:,} ₽

🎁 *Налоговый вычет:* {DEDUCTION:,} ₽
💵 *К оплате после вычета:* {max(0, total_tax - DEDUCTION):,} ₽

✅ *Статус:* Лимит {'НЕ превышен' if total_income <= LIMIT else 'ПРЕВЫШЕН'}

━━━━━━━━━━━━━━━━━━━━━
📅 Отчёт сгенерирован: {datetime.now().strftime('%d.%m.%Y')}
    """
    
    await update.message.reply_text(report_text, parse_mode="Markdown")

# ===== ПОДПИСКА PREMIUM =====
async def subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]]
    
    await query.edit_message_text(
        f"💎 *Premium Подписка — 199 ₽/мес*\n\n"
        f"🔥 *Что вы получаете:*\n\n"
        f"📊 *Полная налоговая аналитика*\n"
        f"• Расчёт с учётом вычета {DEDUCTION:,} ₽\n"
        f"• Контроль лимита {LIMIT:,} ₽\n"
        f"• Прогноз налога на следующий месяц\n"
        f"• Сравнение с прошлым месяцем\n\n"
        f"⏰ *Умные напоминалки*\n"
        f"• За 3 дня до срока оплаты\n"
        f"• Ежемесячный отчёт\n\n"
        f"📎 *Экспорт документов*\n"
        f"• Годовой отчёт для ФНС (/report)\n"
        f"• Чек-лист самозанятого\n\n"
        f"💡 *Советы по экономии*\n"
        f"• Персональные рекомендации\n\n"
        f"🔐 *Как оплатить:*\n"
        f"Переведите 199 ₽ на номер:\n`{PHONE_NUMBER}`\n\n"
        f"После оплаты пришлите чек сюда и напишите /confirm",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ===== АКТИВАЦИЯ ПОДПИСКИ (ТОЛЬКО АДМИН) =====
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ У вас нет прав. Если оплатили — пришлите чек сюда.")
        return
    
    args = context.args
    if not args:
        await update.message.reply_text(
            "ℹ️ *Активация подписки:*\n/confirm 123456789\n\nГде 123456789 — ID пользователя",
            parse_mode="Markdown"
        )
        return
    
    try:
        target_user_id = int(args[0])
        until = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        cursor.execute('UPDATE users SET subscription_until = ? WHERE user_id = ?', (until, target_user_id))
        
        # Сохраняем текущий доход как "прошлый месяц" для будущего сравнения
        cursor.execute('SELECT income FROM users WHERE user_id = ?', (target_user_id,))
        current_income = cursor.fetchone()[0] or 0
        cursor.execute('UPDATE users SET last_month_income = ? WHERE user_id = ?', (current_income, target_user_id))
        
        conn.commit()
        await update.message.reply_text(f"✅ Premium активирован для `{target_user_id}` на 30 дней!", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

# ===== КНОПКА НАЗАД =====
async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить доход", callback_data="add_income")],
        [InlineKeyboardButton("📊 Мой налог", callback_data="my_tax")],
        [InlineKeyboardButton("⚙️ Ставка налога", callback_data="tax_rate")],
        [InlineKeyboardButton("💎 Premium 199 ₽/мес", callback_data="subscription")]
    ]
    
    await query.edit_message_text(
        "🤖 *Налоговый помощник для самозанятых 2026*\n\n"
        "Выберите действие:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ===== ЗАПУСК =====
def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("confirm", confirm))
    app.add_handler(CommandHandler("report", report))
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
    
    print("✅ Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()

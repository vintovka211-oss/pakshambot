            chat_id=opponent_id,
            text=f"⚔️ Вас вызвали на дуэль!\n\n"
                 f"👤 Противник: @{update.effective_user.username or 'Игрок'}\n"
                 f"💰 Ставка: {bet_pak} PAK, {bet_rub} РУБ\n\n"
                 f"✅ /duel_accept - принять дуэль\n"
                 f"❌ /duel_cancel - отклонить"
        )
    except:
        pass

async def duel_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in active_duels:
        await update.message.reply_text("❌ У вас нет активных приглашений на дуэль!")
        return
    
    duel_info = active_duels[user_id]
    challenger_id = duel_info['challenger_id']
    bet_pak = duel_info['bet_pak']
    bet_rub = duel_info['bet_rub']
    duel_id = duel_info['duel_id']
    
    acceptor_data = db.get_user(user_id)
    if acceptor_data[2] < bet_pak or acceptor_data[3] < bet_rub:
        await update.message.reply_text("❌ Недостаточно средств для дуэли!")
        del active_duels[user_id]
        return
    
    # Снимаем ставки
    db.update_balance(challenger_id, -bet_pak, -bet_rub)
    db.update_balance(user_id, -bet_pak, -bet_rub)
    
    # Бросаем кубики
    challenger_roll = random.randint(1, 6)
    acceptor_roll = random.randint(1, 6)
    
    if challenger_roll > acceptor_roll:
        winner_id = challenger_id
        win_pak = bet_pak * 2
        win_rub = bet_rub * 2
        db.update_balance(winner_id, win_pak, win_rub)
        result_text = f"🎲 {challenger_roll} vs {acceptor_roll}\n🏆 ПОБЕДИЛ ВЫЗЫВАЮЩИЙ!"
        
    elif acceptor_roll > challenger_roll:
        winner_id = user_id
        win_pak = bet_pak * 2
        win_rub = bet_rub * 2
        db.update_balance(winner_id, win_pak, win_rub)
        result_text = f"🎲 {challenger_roll} vs {acceptor_roll}\n🏆 ПОБЕДИЛ ПРИНЯВШИЙ!"
        
    else:
        db.update_balance(challenger_id, bet_pak, bet_rub)
        db.update_balance(user_id, bet_pak, bet_rub)
        result_text = f"🎲 {challenger_roll} vs {acceptor_roll}\n🤝 НИЧЬЯ! Ставки возвращены."
        db.complete_duel(duel_id, None)
        del active_duels[user_id]
        
        await update.message.reply_text(result_text)
        try:
            await context.bot.send_message(chat_id=challenger_id, text=result_text)
        except:
            pass
        return
    
    await update.message.reply_text(
        f"⚔️ РЕЗУЛЬТАТ ДУЭЛИ!\n\n{result_text}\n\n"
        f"💰 Выигрыш: {bet_pak} PAK и {bet_rub} РУБ"
    )
    
    try:
        await context.bot.send_message(
            chat_id=challenger_id,
            text=f"⚔️ РЕЗУЛЬТАТ ДУЭЛИ!\n\n{result_text}\n\n"
                 f"💰 {'Вы выиграли' if winner_id == challenger_id else 'Вы проиграли'} {bet_pak} PAK и {bet_rub} РУБ"
        )
    except:
        pass
    
    db.complete_duel(duel_id, winner_id)
    del active_duels[user_id]

async def duel_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    cancelled = False
    for opponent_id, duel_info in list(active_duels.items()):
        if duel_info['challenger_id'] == user_id:
            await update.message.reply_text("❌ Вы отменили дуэль")
            try:
                await context.bot.send_message(chat_id=opponent_id, text="❌ Противник отменил дуэль")
            except:
                pass
            del active_duels[opponent_id]
            cancelled = True
            break
    
    if not cancelled:
        await update.message.reply_text("❌ У вас нет активных дуэлей!")

# ==================== ОСТАЛЬНЫЕ КОМАНДЫ ====================

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = db.get_leaderboard(10)
    
    if not top_users:
        await update.message.reply_text("🏆 Пока нет игроков!")
        return
    
    text = "🏆 ТОП 10 ИГРОКОВ 🏆\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    
    for i, user in enumerate(top_users):
        text += f"{medals[i]} {user[0]}: 💎{user[1]} PAK | 💵{user[2]} РУБ\n"
    
    await update.message.reply_text(text)

async def give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Недостаточно прав!")
        return
    
    if len(context.args) == 0:
        db.update_balance(user_id, 10000, 1000)
        user_data = db.get_user(user_id)
        await update.message.reply_text(f"✅ Выдано: 10000 PAK, 1000 РУБ\n💰 Баланс: {user_data[2]} PAK, {user_data[3]} РУБ")
        return
    
    if len(context.args) < 3:
        await update.message.reply_text("❌ Использование: /give @username PAK РУБ")
        return
    
    username = context.args[0].replace('@', '')
    try:
        pak = int(context.args[1])
        rub = int(context.args[2])
    except ValueError:
        await update.message.reply_text("❌ Суммы должны быть числами!")
        return
    
    user = db.get_user_by_username(username)
    if user:
        db.update_balance(user[0], pak, rub)
        await update.message.reply_text(f"✅ Выдано {pak} PAK и {rub} РУБ пользователю @{username}")
    else:
        await update.message.reply_text(f"❌ Пользователь @{username} не найден!")

# ==================== ОБРАБОТЧИКИ СООБЩЕНИЙ ====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Обработка создания клана
    if context.user_data.get('creating_clan') == 'waiting_name':
        await clan_create_name(update, context)
        return
    elif context.user_data.get('creating_clan') == 'waiting_description':
        await clan_create_description(update, context)
        return
    
    # Обработка ставки в казино
    if context.user_data.get('waiting_for_bet'):
        await handle_bet(update, context)
        return
    
    # Пропускаем команды
    if update.message.text and update.message.text.startswith('/'):
        return
    
    # Награда за сообщения
    user_id = update.effective_user.id
    user = update.effective_user
    
    db.register_user(user_id, user.username or str(user_id))
    
    if db.can_get_message_reward(user_id):
        if user.bio and "W1npakshambot" in user.bio:
            db.update_balance(user_id, MSG_REWARD, 0)
            db.update_message_time(user_id)
            await update.message.reply_text(f"💎 +{MSG_REWARD} PAK за сообщение!")

# ==================== ОБРАБОТЧИК CALLBACK ====================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    # ========== ПОКУПКА ЗА ЗВЕЗДЫ ==========
    if data.startswith("buy_stars_"):
        stars = int(data.replace("buy_stars_", ""))
        if stars == 10:
            await handle_star_purchase(update, context, 10, 100, 0)
        elif stars == 50:
            await handle_star_purchase(update, context, 50, 500, 0)
        elif stars == 100:
            await handle_star_purchase(update, context, 100, 1200, 0)
        elif stars == 500:
            await handle_star_purchase(update, context, 500, 6500, 0)
    
    elif data.startswith("buy_rub_"):
        stars = int(data.replace("buy_rub_", ""))
        if stars == 1:
            await handle_star_purchase(update, context, 1, 0, 1)
        elif stars == 10:
            await handle_star_purchase(update, context, 10, 0, 10)
        elif stars == 50:
            await handle_star_purchase(update, context, 50, 0, 55)
        elif stars == 100:
            await handle_star_purchase(update, context, 100, 0, 115)
    
    elif data.startswith("confirm_stars_"):
        parts = data.split("_")
        stars = int(parts[2])
        pak = int(parts[3])
        rub = int(parts[4])
        
        user_id = query.from_user.id
        db.update_balance(user_id, pak, rub)
        db.add_star_purchase(user_id, stars, pak, rub)
        
        await query.edit_message_text(
            f"✅ Покупка успешно завершена!\n\n"
            f"⭐ Потрачено звезд: {stars}\n"
            f"💰 Получено: +{pak} PAK, +{rub} РУБ"
        )
    
    elif data == "cancel_purchase":
        await query.edit_message_text("❌ Покупка отменена")
    
    # ========== КЛАНЫ ==========
    elif data == "clan_list":
        await clan_list(update, context)
    elif data == "clan_create":
        await clan_create_start(update, context)
    elif data == "clan_my":
        await clan_my(update, context)
    elif data == "clan_leave":
        await clan_leave(update, context)
    elif data == "clan_reward":
        await clan_reward(update, context)
    elif data == "clan_back":
        await clan(update, context)
    
    elif data.startswith("clan_join_"):
        clan_id = int(data.replace("clan_join_", ""))
        await clan_join(update, context, clan_id)
    
    elif data.startswith("clan_requests_"):
        clan_id = int(data.replace("clan_requests_", ""))
        await clan_requests(update, context, clan_id)
    
    elif data.startswith("clan_accept_"):
        parts = data.split("_")
        request_id = int(parts[2])
        clan_id = int(parts[3])
        await clan_accept(update, context, request_id, clan_id)
    
    elif data.startswith("clan_reject_"):
        request_id = int(data.replace("clan_reject_", ""))
        await clan_reject(update, context, request_id)
    
    elif data.startswith("clan_kick_"):
        clan_id = int(data.replace("clan_kick_", ""))
        await clan_kick(update, context, clan_id)
    
    elif data.startswith("clan_kick_user_"):
        parts = data.split("_")
        clan_id = int(parts[3])
        user_id = int(parts[4])
        await clan_kick_user(update, context, clan_id, user_id)
    
    # ========== ИГРЫ ==========
    elif data.startswith("game_"):
        game = data.replace("game_", "")
        context.user_data['selected_game'] = game
        await query.edit_message_text(
            f"🎮 Выбрана игра: {game}\n\n"
            f"💰 Введите ставку в формате:\n"
            f"PAK РУБ\n\n"
            f"Пример: 100 50"
        )
        context.user_data['waiting_for_bet'] = True

# ==================== ЗАПУСК БОТА ====================

async def main():
    """Запуск бота с защитой от дублирования"""
    
    # Проверяем, не запущен ли уже бот
    pid_file = "bot.pid"
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                old_pid = f.read().strip()
            if old_pid:
                try:
                    os.kill(int(old_pid), 0)
                    print(f"❌ Бот уже запущен с PID: {old_pid}")
                    sys.exit(1)
                except (ProcessLookupError, ValueError):
                    print("✅ Старый PID неактивен, запускаем...")
        except Exception as e:
            print(f"⚠️ Ошибка проверки PID: {e}")
    
    # Сохраняем текущий PID
    try:
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
        print(f"📝 Сохранен PID: {os.getpid()}")
    except Exception as e:
        print(f"⚠️ Не удалось сохранить PID: {e}")
    
    print("🚀 Запуск бота W1nPAK...")
    
    try:
        application = Application.builder().token(TOKEN).build()
        
        # Регистрация команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("balance", balance))
        application.add_handler(CommandHandler("buy", buy))
        application.add_handler(CommandHandler("casino", casino))
        application.add_handler(CommandHandler("duel", duel))
        application.add_handler(CommandHandler("duel_accept", duel_accept))
        application.add_handler(CommandHandler("duel_cancel", duel_cancel))
        application.add_handler(CommandHandler("leaderboard", leaderboard))
        application.add_handler(CommandHandler("clan", clan))
        application.add_handler(CommandHandler("give", give))
        application.add_handler(CommandHandler("help", start))
        
        # Обработчики сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CallbackQueryHandler(handle_callback))
        
        print("✅ Бот успешно запущен и готов к работе!")
        
        # Запуск бота
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        print("🤖 Бот начал polling...")
        
        # Держим бота запущенным
        await asyncio.Event().wait()
        
    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Удаляем PID файл при завершении
        try:
            if os.path.exists(pid_file):
                os.remove(pid_file)
                print("🧹 PID файл удален")
        except:
            pass

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

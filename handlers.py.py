    # РУЛЕТКА
    elif data == "game_roulette":
        await callback.message.answer("🎡 Введите сумму и цвет (🔴/⚫/🟢), например: 100 🔴")
        await state.update_data(game="roulette")
        await state.set_state(GameStates.waiting_bet)
    
    # БЛЭКДЖЕК
    elif data == "game_blackjack":
        await callback.message.answer("🃏 Введите сумму ставки:")
        await state.update_data(game="blackjack")
        await state.set_state(GameStates.waiting_bet)
    
    # МИНЫ
    elif data == "game_mines":
        await callback.message.answer("💣 Введите сумму ставки:")
        await state.update_data(game="mines")
        await state.set_state(GameStates.waiting_bet)
    
    # КОЛЕСО ФОРТУНЫ
    elif data == "game_wheel":
        await callback.message.answer("🎡 Введите сумму ставки:")
        await state.update_data(game="wheel")
        await state.set_state(GameStates.waiting_bet)
    
    # ОРЁЛ/РЕШКА
    elif data == "game_coin":
        await callback.message.answer("🪙 Введите сумму и выбор (орел/решка), например: 100 орел")
        await state.update_data(game="coin")
        await state.set_state(GameStates.waiting_bet)
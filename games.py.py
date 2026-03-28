import random
from config import GAME_COMMISSION
from database import get_user, update_user, add_transaction

async def play_slots(user_id, bet):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    symbols = ["🍒", "🍋", "🍊", "🍉", "⭐", "💎", "7️⃣"]
    result = [random.choice(symbols) for _ in range(3)]
    
    win = 0
    if result[0] == result[1] == result[2]:
        if result[0] == "7️⃣":
            win = bet * 10
        elif result[0] == "💎":
            win = bet * 5
        elif result[0] == "⭐":
            win = bet * 3
        else:
            win = bet * 2
    elif result[0] == result[1] or result[1] == result[2] or result[0] == result[2]:
        win = bet // 2
    
    commission = int(bet * GAME_COMMISSION / 100)
    actual_bet = bet - commission
    
    await update_user(user_id, 
        pac_balance=user["pac_balance"] - actual_bet + win,
        total_games=user["total_games"] + 1,
        turnover=user["turnover"] + actual_bet
    )
    await add_transaction(user_id, "game", -actual_bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "game_win", win, "Выигрыш")
    
    if win > 0:
        return win, f"🎰 {result[0]} | {result[1]} | {result[2]}\n🎉 Вы выиграли {win} PAC!"
    else:
        return 0, f"🎰 {result[0]} | {result[1]} | {result[2]}\n😔 Вы проиграли {actual_bet} PAC."

async def play_dice(user_id, bet, choice=None):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    dice = random.randint(1, 6)
    win = 0
    if choice and 1 <= choice <= 6:
        if dice == choice:
            win = bet * 5
    elif choice in ["even", "odd"]:
        if (choice == "even" and dice % 2 == 0) or (choice == "odd" and dice % 2 == 1):
            win = bet * 2
    
    commission = int(bet * GAME_COMMISSION / 100)
    actual_bet = bet - commission
    
    await update_user(user_id, 
        pac_balance=user["pac_balance"] - actual_bet + win,
        total_games=user["total_games"] + 1,
        turnover=user["turnover"] + actual_bet
    )
    await add_transaction(user_id, "game", -actual_bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "game_win", win, "Выигрыш")
    
    if win > 0:
        return win, f"🎲 Выпало: {dice}\n🎉 Вы выиграли {win} PAC!"
    else:
        return 0, f"🎲 Выпало: {dice}\n😔 Вы проиграли {actual_bet} PAC."

async def play_roulette(user_id, bet, color):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    colors = ["🔴", "⚫", "🟢"]
    result = random.choice(colors)
    
    win = 0
    if result == color:
        if color == "🟢":
            win = bet * 14
        else:
            win = bet * 2
    
    commission = int(bet * GAME_COMMISSION / 100)
    actual_bet = bet - commission
    
    await update_user(user_id, 
        pac_balance=user["pac_balance"] - actual_bet + win,
        total_games=user["total_games"] + 1,
        turnover=user["turnover"] + actual_bet
    )
    await add_transaction(user_id, "game", -actual_bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "game_win", win, "Выигрыш")
    
    if win > 0:
        return win, f"🎡 Выпало: {result}\n🎉 Вы выиграли {win} PAC!"
    else:
        return 0, f"🎡 Выпало: {result}\n😔 Вы проиграли {actual_bet} PAC."

async def play_blackjack(user_id, bet):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    cards = [2,3,4,5,6,7,8,9,10,10,10,10,11]
    player = [random.choice(cards), random.choice(cards)]
    dealer = [random.choice(cards), random.choice(cards)]
    
    while sum(player) < 17:
        player.append(random.choice(cards))
    while sum(dealer) < 17:
        dealer.append(random.choice(cards))
    
    player_sum = sum(player)
    dealer_sum = sum(dealer)
    
    win = 0
    if player_sum > 21:
        result_text = "Перебор! Вы проиграли"
    elif dealer_sum > 21 or player_sum > dealer_sum:
        win = bet * 2
        result_text = "Вы выиграли!"
    elif player_sum == dealer_sum:
        win = bet
        result_text = "Ничья!"
    else:
        result_text = "Дилер выиграл!"
    
    commission = int(bet * GAME_COMMISSION / 100)
    actual_bet = bet - commission
    
    await update_user(user_id, 
        pac_balance=user["pac_balance"] - actual_bet + win,
        total_games=user["total_games"] + 1,
        turnover=user["turnover"] + actual_bet
    )
    await add_transaction(user_id, "game", -actual_bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "game_win", win, "Выигрыш")
    
    return win, f"🃏 **Блэкджек**\n\nВаши карты: {player} = {player_sum}\nКарты дилера: {dealer} = {dealer_sum}\n\n{result_text}"

async def play_mines(user_id, bet):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    mines = random.sample(range(25), 5)
    click = random.randint(0, 24)
    
    win = bet * 2 if click not in mines else 0
    
    commission = int(bet * GAME_COMMISSION / 100)
    actual_bet = bet - commission
    
    await update_user(user_id, 
        pac_balance=user["pac_balance"] - actual_bet + win,
        total_games=user["total_games"] + 1,
        turnover=user["turnover"] + actual_bet
    )
    await add_transaction(user_id, "game", -actual_bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "game_win", win, "Выигрыш")
    
    if win > 0:
        return win, f"💣 **Мины**\n\n🎉 Вы не наступили на мину! +{win} PAC!"
    else:
        return 0, f"💣 **Мины**\n\n💥 Вы наступили на мину! -{actual_bet} PAC."

async def play_wheel(user_id, bet):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    segments = [1, 2, 3, 5, 10, 20, 50, 0, 0, 0]
    result = random.choice(segments)
    win = bet * result
    
    commission = int(bet * GAME_COMMISSION / 100)
    actual_bet = bet - commission
    
    await update_user(user_id, 
        pac_balance=user["pac_balance"] - actual_bet + win,
        total_games=user["total_games"] + 1,
        turnover=user["turnover"] + actual_bet
    )
    await add_transaction(user_id, "game", -actual_bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "game_win", win, "Выигрыш")
    
    if win > 0:
        return win, f"🎡 **Колесо Фортуны**\n\nМножитель x{result}!\n🎉 Вы выиграли {win} PAC!"
    else:
        return 0, f"🎡 **Колесо Фортуны**\n\nВыпал 0!\n😔 Вы проиграли {actual_bet} PAC."

async def play_coin(user_id, bet, choice):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    result = random.choice(["орел", "решка"])
    win = bet * 2 if choice == result else 0
    
    commission = int(bet * GAME_COMMISSION / 100)
    actual_bet = bet - commission
    
    await update_user(user_id, 
        pac_balance=user["pac_balance"] - actual_bet + win,
        total_games=user["total_games"] + 1,
        turnover=user["turnover"] + actual_bet
    )
    await add_transaction(user_id, "game", -actual_bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "game_win", win, "Выигрыш")
    
    if win > 0:
        return win, f"🪙 **Орёл/Решка**\n\nВыпал: {result}\n🎉 Вы угадали! +{win} PAC!"
    else:
        return 0, f"🪙 **Орёл/Решка**\n\nВыпал: {result}\n😔 Вы не угадали. -{actual_bet} PAC."
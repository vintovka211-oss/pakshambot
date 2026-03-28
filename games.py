import random
from config import GAME_COMMISSION
from database import get_user, update_user, add_transaction

# ==================== СЛОТЫ (ШАНС ВЫИГРЫША ~15%) ====================
async def play_slots(user_id, bet):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    symbols = ["🍒", "🍋", "🍊", "🍉", "⭐", "💎", "7️⃣"]
    result = [random.choice(symbols) for _ in range(3)]
    
    win = 0
    # Джекпот (7️⃣7️⃣7️⃣) - шанс ~0.3%
    if result[0] == "7️⃣" and result[1] == "7️⃣" and result[2] == "7️⃣":
        win = bet * 5  # x5
    # Три одинаковых символа (кроме 7) - шанс ~0.6%
    elif result[0] == result[1] == result[2]:
        if result[0] == "💎":
            win = bet * 3
        elif result[0] == "⭐":
            win = bet * 2
        else:
            win = bet * 1
    # Два одинаковых - шанс ~15%
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


# ==================== КУБИК (УГАДАТЬ ЧИСЛО 1-6, ШАНС 16.6%) ====================
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
            win = bet * 3  # x3 вместо x5
    elif choice in ["even", "odd"]:
        if (choice == "even" and dice % 2 == 0) or (choice == "odd" and dice % 2 == 1):
            win = bet * 1.5  # x1.5 вместо x2
    
    commission = int(bet * GAME_COMMISSION / 100)
    actual_bet = bet - commission
    win = int(win)
    
    await update_user(user_id, 
        pac_balance=user["pac_balance"] - actual_bet + win,
        total_games=user["total_games"] + 1,
        turnover=user["turnover"] + actual_bet
    )
    await add_transaction(user_id, "game", -actual_bet, f"Ставка {bet}")
    if win > 0:
        await add_transaction(user_id, "game_win", win, "Выигрыш")
    
    if win > 0:
        return win, f"🎲 Выпало: {dice}\n🎉 Вы угадали! +{win} PAC!"
    else:
        return 0, f"🎲 Выпало: {dice}\n😔 Вы проиграли {actual_bet} PAC."


# ==================== РУЛЕТКА (ШАНС 33% на красное/черное, 2.7% на зеро) ====================
async def play_roulette(user_id, bet, color):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    colors = ["🔴", "⚫", "🟢"]
    # Зеро (🟢) выпадает редко
    result = random.choices(colors, weights=[48, 48, 4])[0]
    
    win = 0
    if result == color:
        if color == "🟢":
            win = bet * 10  # x10 за зеро
        else:
            win = bet * 1.5  # x1.5 за цвет
    
    win = int(win)
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


# ==================== БЛЭКДЖЕК (21) - КАЗИНО ВСЕГДА В ПЛЮСЕ ====================
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
    
    player_sum = min(sum(player), 21) if sum(player) > 21 else sum(player)
    dealer_sum = min(sum(dealer), 21) if sum(dealer) > 21 else sum(dealer)
    
    win = 0
    if player_sum > 21:
        result_text = "Перебор! Вы проиграли"
    elif dealer_sum > 21:
        win = bet * 1.5
        result_text = "Дилер перебрал! Вы выиграли!"
    elif player_sum > dealer_sum:
        win = bet * 1.5
        result_text = "Вы выиграли!"
    elif player_sum == dealer_sum:
        win = bet
        result_text = "Ничья! Ставка возвращена"
    else:
        result_text = "Дилер выиграл!"
    
    win = int(win)
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


# ==================== МИНЫ (ШАНС ВЫИГРЫША 80%) НО ВЫИГРЫШ МАЛЕНЬКИЙ ====================
async def play_mines(user_id, bet):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    mines = random.sample(range(25), 5)
    click = random.randint(0, 24)
    
    # 80% шанс не наступить на мину
    if click not in mines:
        win = bet * 1.2  # +20% прибыли
    else:
        win = 0
    
    win = int(win)
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


# ==================== КОЛЕСО ФОРТУНЫ (МАКСИМУМ 3Х) ====================
async def play_wheel(user_id, bet):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    # Множители: 0 (проигрыш) выпадает часто
    segments = [0, 0, 0, 0, 0, 0, 1, 1, 1, 2, 2, 3]  # 6 нулей, 3 единицы, 2 двойки, 1 тройка
    result = random.choice(segments)
    win = bet * result
    
    win = int(win)
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


# ==================== ОРЁЛ/РЕШКА (50/50, НО С КОМИССИЕЙ) ====================
async def play_coin(user_id, bet, choice):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["pac_balance"] < bet:
        return 0, "❌ Недостаточно PAC!"
    
    result = random.choice(["орел", "решка"])
    
    commission = int(bet * GAME_COMMISSION / 100)
    actual_bet = bet - commission
    
    if choice == result:
        win = bet * 1.8  # x1.8 вместо x2 (10% комиссия)
    else:
        win = 0
    
    win = int(win)
    
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

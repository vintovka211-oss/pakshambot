import random
from config import CURRENCY, GAME_COMMISSION
from database import get_user, update_user, add_transaction, add_income

# ==================== СЛОТЫ ====================
async def play_slots(user_id, bet):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["balance"] < bet:
        return 0, "❌ Недостаточно средств!"
    
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
    
    await update_user(user_id, balance=user["balance"] - actual_bet + win, total_games=user["total_games"] + 1, turnover=user["turnover"] + actual_bet)
    await add_transaction(user_id, "game_bet", -actual_bet, "Ставка в слотах")
    if win > 0:
        await add_transaction(user_id, "game_win", win, "Выигрыш в слотах")
    await add_income("game_commission", commission, user_id)
    
    if win > 0:
        return win, f"🎰 {result[0]} | {result[1]} | {result[2]}\n🎉 Вы выиграли {win}{CURRENCY}!"
    else:
        return 0, f"🎰 {result[0]} | {result[1]} | {result[2]}\n😔 Вы проиграли {actual_bet}{CURRENCY}."

# ==================== КУБИК ====================
async def play_dice(user_id, bet, choice=None):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["balance"] < bet:
        return 0, "❌ Недостаточно средств!"
    
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
    
    await update_user(user_id, balance=user["balance"] - actual_bet + win, total_games=user["total_games"] + 1, turnover=user["turnover"] + actual_bet)
    await add_transaction(user_id, "game_bet", -actual_bet, "Ставка в кубик")
    if win > 0:
        await add_transaction(user_id, "game_win", win, "Выигрыш в кубик")
    await add_income("game_commission", commission, user_id)
    
    if win > 0:
        return win, f"🎲 Выпало: {dice}\n🎉 Вы выиграли {win}{CURRENCY}!"
    else:
        return 0, f"🎲 Выпало: {dice}\n😔 Вы проиграли {actual_bet}{CURRENCY}."

# ==================== РУЛЕТКА ====================
async def play_roulette(user_id, bet, color):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["balance"] < bet:
        return 0, "❌ Недостаточно средств!"
    
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
    
    await update_user(user_id, balance=user["balance"] - actual_bet + win, total_games=user["total_games"] + 1, turnover=user["turnover"] + actual_bet)
    await add_transaction(user_id, "game_bet", -actual_bet, "Ставка в рулетку")
    if win > 0:
        await add_transaction(user_id, "game_win", win, "Выигрыш в рулетку")
    await add_income("game_commission", commission, user_id)
    
    if win > 0:
        return win, f"🎡 Выпало: {result}\n🎉 Вы выиграли {win}{CURRENCY}!"
    else:
        return 0, f"🎡 Выпало: {result}\n😔 Вы проиграли {actual_bet}{CURRENCY}."

# ==================== БЛЭКДЖЕК (21) ====================
async def play_blackjack(user_id, bet):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["balance"] < bet:
        return 0, "❌ Недостаточно средств!"
    
    def deal_card():
        cards = [2,3,4,5,6,7,8,9,10,10,10,10,11]
        return random.choice(cards)
    
    player = [deal_card(), deal_card()]
    dealer = [deal_card(), deal_card()]
    
    while sum(player) < 21 and sum(player) < 17:
        player.append(deal_card())
    
    while sum(dealer) < 17:
        dealer.append(deal_card())
    
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
        result_text = "Ничья! Ставка возвращена"
    else:
        result_text = "Дилер выиграл!"
    
    commission = int(bet * GAME_COMMISSION / 100)
    actual_bet = bet - commission if win != bet else 0
    
    await update_user(user_id, balance=user["balance"] - actual_bet + win, total_games=user["total_games"] + 1, turnover=user["turnover"] + actual_bet)
    await add_transaction(user_id, "game_bet", -actual_bet, "Ставка в блэкджек")
    if win > 0:
        await add_transaction(user_id, "game_win", win, "Выигрыш в блэкджек")
    await add_income("game_commission", commission, user_id)
    
    return win, f"🃏 **Блэкджек**\n\nВаши карты: {player} = {player_sum}\nКарты дилера: {dealer} = {dealer_sum}\n\n{result_text}"

# ==================== МИНЫ ====================
async def play_mines(user_id, bet):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["balance"] < bet:
        return 0, "❌ Недостаточно средств!"
    
    board = [["⬜" for _ in range(5)] for _ in range(5)]
    mines = random.sample(range(25), 5)
    
    win = bet * 2
    result_text = "🎮 Игра Мины\n\nВы нажали на мину! Проигрыш."
    
    commission = int(bet * GAME_COMMISSION / 100)
    actual_bet = bet - commission
    
    await update_user(user_id, balance=user["balance"] - actual_bet, total_games=user["total_games"] + 1, turnover=user["turnover"] + actual_bet)
    await add_transaction(user_id, "game_bet", -actual_bet, "Ставка в мины")
    await add_income("game_commission", commission, user_id)
    
    return 0, f"💣 **Мины**\n\n{result_text}"

# ==================== КОЛЕСО ФОРТУНЫ ====================
async def play_wheel(user_id, bet):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["balance"] < bet:
        return 0, "❌ Недостаточно средств!"
    
    segments = [1, 2, 5, 10, 20, 50, 100, 0, 0, 0]
    result = random.choice(segments)
    win = bet * result
    
    commission = int(bet * GAME_COMMISSION / 100)
    actual_bet = bet - commission
    
    await update_user(user_id, balance=user["balance"] - actual_bet + win, total_games=user["total_games"] + 1, turnover=user["turnover"] + actual_bet)
    await add_transaction(user_id, "game_bet", -actual_bet, "Ставка в колесо фортуны")
    if win > 0:
        await add_transaction(user_id, "game_win", win, "Выигрыш в колесо фортуны")
    await add_income("game_commission", commission, user_id)
    
    if win > 0:
        return win, f"🎡 **Колесо фортуны**\n\nВыпал множитель x{result}!\n🎉 Вы выиграли {win}{CURRENCY}!"
    else:
        return 0, f"🎡 **Колесо фортуны**\n\nВыпал 0!\n😔 Вы проиграли {actual_bet}{CURRENCY}."

# ==================== ОРЁЛ/РЕШКА ====================
async def play_coin(user_id, bet, choice):
    user = await get_user(user_id)
    if bet <= 0:
        return 0, "❌ Ставка должна быть больше 0!"
    if user["balance"] < bet:
        return 0, "❌ Недостаточно средств!"
    
    result = random.choice(["орел", "решка"])
    win = bet * 2 if choice == result else 0
    
    commission = int(bet * GAME_COMMISSION / 100)
    actual_bet = bet - commission
    
    await update_user(user_id, balance=user["balance"] - actual_bet + win, total_games=user["total_games"] + 1, turnover=user["turnover"] + actual_bet)
    await add_transaction(user_id, "game_bet", -actual_bet, "Ставка в орёл/решка")
    if win > 0:
        await add_transaction(user_id, "game_win", win, "Выигрыш в орёл/решка")
    await add_income("game_commission", commission, user_id)
    
    if win > 0:
        return win, f"🪙 **Орёл/Решка**\n\nВыпал: {result}\n🎉 Вы угадали! +{win}{CURRENCY}!"
    else:
        return 0, f"🪙 **Орёл/Решка**\n\nВыпал: {result}\n😔 Вы не угадали. -{actual_bet}{CURRENCY}."

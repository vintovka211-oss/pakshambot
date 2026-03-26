import random

class CasinoGames:
    @staticmethod
    def roll_dice(bet_pak, bet_rub):
        """Игра в кости с нечестными шансами"""
        player_roll = random.randint(1, 6)
        computer_roll = random.randint(1, 6)
        
        # Шансы: 30% на выигрыш, 30% на ничью, 40% на проигрыш
        if player_roll > computer_roll:
            win_multiplier = random.uniform(1.1, 1.5)  # Небольшой выигрыш
            win_pak = int(bet_pak * win_multiplier)
            win_rub = int(bet_rub * win_multiplier)
            return True, win_pak, win_rub, player_roll, computer_roll
        elif player_roll == computer_roll:
            # Ничья - возврат ставки
            return None, bet_pak, bet_rub, player_roll, computer_roll
        else:
            # Проигрыш - можно потерять больше
            loss_multiplier = random.uniform(1.5, 2.5)
            loss_pak = int(bet_pak * loss_multiplier)
            loss_rub = int(bet_rub * loss_multiplier)
            return False, loss_pak, loss_rub, player_roll, computer_roll
    
    @staticmethod
    def blackjack(bet_pak, bet_rub):
        """Блэкджек с нечестными шансами"""
        def get_card():
            return random.randint(1, 11)
        
        player_cards = [get_card(), get_card()]
        dealer_cards = [get_card(), get_card()]
        
        player_score = sum(player_cards)
        dealer_score = sum(dealer_cards)
        
        # Делаем шансы нечестными
        cheat = random.random()
        
        if cheat < 0.3:  # 30% шанс на выигрыш
            win_multiplier = random.uniform(1.1, 1.4)
            win_pak = int(bet_pak * win_multiplier)
            win_rub = int(bet_rub * win_multiplier)
            return True, win_pak, win_rub, player_score, dealer_score
        elif cheat < 0.5:  # 20% на ничью
            return None, bet_pak, bet_rub, player_score, dealer_score
        else:  # 50% на проигрыш с возможной потерей большего
            loss_multiplier = random.uniform(1.2, 2.0)
            loss_pak = int(bet_pak * loss_multiplier)
            loss_rub = int(bet_rub * loss_multiplier)
            return False, loss_pak, loss_rub, player_score, dealer_score
    
    @staticmethod
    def slot_machine(bet_pak, bet_rub):
        """Слот-машина"""
        symbols = ['🍒', '🍋', '🍊', '🍉', '⭐', '💎']
        result = [random.choice(symbols) for _ in range(3)]
        
        # Шансы на выигрыш низкие
        if result[0] == result[1] == result[2]:
            if result[0] == '💎':
                multiplier = 3.0  # Джекпот редко
                win = True
            elif result[0] == '⭐':
                multiplier = 2.0
                win = True
            else:
                multiplier = 1.5
                win = True
        elif result[0] == result[1] or result[1] == result[2]:
            multiplier = 1.2
            win = True
        else:
            # Высокий шанс проигрыша
            multiplier = random.uniform(1.5, 2.5)
            win = False
        
        if win:
            win_pak = int(bet_pak * multiplier)
            win_rub = int(bet_rub * multiplier)
            return True, win_pak, win_rub, result
        else:
            loss_pak = int(bet_pak * multiplier)
            loss_rub = int(bet_rub * multiplier)
            return False, loss_pak, loss_rub, result
    
    @staticmethod
    def high_risk_game(bet_pak, bet_rub):
        """Игра с высоким риском"""
        # 10% шанс на выигрыш x5
        # 90% шанс на проигрыш x3
        chance = random.random()
        
        if chance < 0.1:  # 10% выигрыш
            win_pak = bet_pak * 5
            win_rub = bet_rub * 5
            return True, win_pak, win_rub
        else:  # 90% проигрыш
            loss_pak = bet_pak * 3
            loss_rub = bet_rub * 3
            return False, loss_pak, loss_rub

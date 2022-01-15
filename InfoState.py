from dataclasses import dataclass
from typing import List, Sequence, Tuple

RANKS = '23456789TJQKA'
SUITS = 'cdhs'

@dataclass(frozen=True)
class PlayerInfo: 
    spent: int
    stack: int
    active: bool

@dataclass(frozen=True)
class ActionInfo: 
    player: int
    action: int
    def __str__(self) -> str:
        if self.player == -1:
            return "Dealer: " + card_num_to_str(self.action)
        player_str = "Player: " + str(self.player)
        if self.action == 0:
            return player_str + "Fold"
        if self.action == 1:
            return player_str + "Call"
        return player_str + "Raise to " + str(self.action)

@dataclass(frozen=True)
class Observation: 
    my_hand: Tuple[str]
    my_index: int
    board_cards: Tuple[str]
    player_infos: Tuple[PlayerInfo]
    history: Tuple[ActionInfo]
    small_blind: int
    big_blind: int
    legal_actions: Tuple[int]

    def get_player_count(self):
        return len(self.player_infos)

    def get_active_player_count(self):
        return len(p for p in self.player_infos if p.active)

    def get_betting_round(self):
        deal_count = len(h for h in self.history if h.player == -1)
        return 0 if deal_count == 0 else deal_count-2

    def get_max_spent(self):
        return max(map(lambda p: p.spent, self.player_infos))

    def get_asked_amount(self):
        return self.get_max_spent()
    
    def can_raise(self):
        return any(a for a in self.legal_actions if a > 1)
    
    def get_min_raise(self):
        return min(a for a in self.legal_actions if a > 1) if self.can_raise() else 0

    def get_max_raise(self):
        return max(a for a in self.legal_actions if a > 1) if self.can_raise() else 0

    def action_to_str(self, action_num: int, player_idx: int = None):
        if player_idx is None:
            player_idx = self.my_index
        return str(ActionInfo(player_idx, action_num))

class InfoState: 
    player_hands: List[Tuple[str]]
    board_cards: List[str]
    player_infos: List[PlayerInfo]
    history: List[ActionInfo]
    small_blind: int
    big_blind: int

    def __init__(self, history: List[int], stacks: List[int], blinds: List[int]):
        cards1 = map(card_num_to_str, [history[i] for i in range(0,len(history),2)])
        cards2 = map(card_num_to_str, [history[i] for i in range(1,len(history),2)])
        self.player_hands = [hand for hand in zip(cards1, cards2)]
        self.player_infos = [PlayerInfo(blind, stack-blind, True) for blind, stack in zip(blinds, stacks)]
        self.board_cards = []
        self.history = []
        self.small_blind = blinds[0]
        self.big_blind = blinds[1]

    def update_info_state_action(self, player_idx: int, action: int):
        player_info = self.player_infos[player_idx]
        if action > 1:
            r = action - player_info.spent
            self.player_infos[player_idx] = PlayerInfo(action, player_info.stack - r, player_info.active)
        elif action == 1:
            max_spent = max(map(lambda p: p.spent, self.player_infos))
            c = max_spent - player_info.spent
            self.player_infos[player_idx] = PlayerInfo(max_spent, player_info.stack - c, player_info.active)
        else:
            self.player_infos[player_idx] = PlayerInfo(player_info.spent, player_info.stack, False)
        self.history.append(ActionInfo(player_idx, action))


    def update_info_state_draw(self, card_num = int):
        cards_str = card_num_to_str(card_num)
        self.board_cards.append(cards_str)
        self.history.append(ActionInfo(-1,card_num))
            
    def to_observation(self, player_idx: int, legal_actions: List[int]):
        return Observation(self.player_hands[player_idx], 
                        player_idx, 
                        tuple(self.board_cards), 
                        tuple(self.player_infos), 
                        tuple(self.history),
                        self.small_blind,
                        self.big_blind,
                        tuple(legal_actions))

def amount_to_call(player_infos: Sequence[PlayerInfo], player_idx: int):
    max_spent = max(map(lambda p: p.spent, player_infos))
    return max_spent - player_infos[player_idx].spent

def card_num_to_str(card_num: int):
    rank_num = int(card_num / 4)
    suit_num = card_num % 4
    return RANKS[rank_num] + SUITS[suit_num]
import random

class Bot(object):

    def ask_for_crib_throw(self, has_crib, scores=None):
        raise NotImplementedError

    def notify_starter_card(self, card):
        self.hand.add_starter_card(card)

    def notify_new_hand(self, hand):
        self.hand = hand


class RandomBot(Bot):

    def ask_for_crib_throw(self, has_crib, scores=None):
        return self.hand.throw_cards(*random.sample(self.hand.cards, 2))



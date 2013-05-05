import random
import cribbage

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


class HumanBot(Bot):

    def ask_for_crib_throw(self, has_crib, scores=None):
        print "The score is: %s" % scores
        print "It is your crib: %s" % has_crib

        print "Your hand is: %s" % self.hand.prompt
        print "Select card to throw:"
        def print_prompt(cards, selected_idxs):
            for i, card in enumerate(cards):
                print i+1, card.colored_print, '<-' if (i+1) in selected_idxs else ''

        print_prompt(self.hand.cards, [])
        card_idx1 = int(raw_input())

        print_prompt(self.hand.cards, [card_idx1])
        card_idx2 = int(raw_input())

        return self.hand.throw_cards(self.hand.cards[card_idx1 - 1], self.hand.cards[card_idx2 - 1])

    def notify_starter_card(self, card):
        super(HumanBot, self).notify_starter_card(card)
        print "Your hand is: %s" % self.hand.prompt
        print "You will receive %s points" % cribbage.Scorer.score(self.hand)


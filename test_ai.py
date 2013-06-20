import random
import cribbage

class Bot(object):

    def ask_for_crib_throw(self, has_crib, scores=None):
        raise NotImplementedError

    def notify_starter_card(self, card):
        self.hand.add_starter_card(card)

    def notify_new_hand(self, hand):
        self.hand = hand

    def ask_for_next_peg_card(self, cards_in_pegging_round, all_cards_pegged):
        raise NotImplementedError


class RandomBot(Bot):

    def ask_for_crib_throw(self, has_crib, scores=None):
        return self.hand.throw_cards(*random.sample(self.hand.cards, 2))

    def ask_for_next_peg_card(self, cards_in_pegging_round, all_cards_pegged):
        current_sum = cribbage.sum_cards_for_pegging(cards_in_pegging_round)
        cards_not_played = set(self.hand.cards) - set(all_cards_pegged)
        cards_can_play = [card for card in cards_not_played if cribbage.VALUES[card.rank] < (31 - current_sum)]
        if not cards_can_play:
            return None
        return random.choice(cards_can_play)

class OneSixBot(Bot):

    def ask_for_crib_throw(self, has_crib, scores=None):
        if has_crib:
            return self.hand.throw_cards(self.hand.cards[0], self.hand.cards[1])
        else:
            return self.hand.throw_cards(self.hand.cards[0], self.hand.cards[5])

    def ask_for_next_peg_card(self, cards_in_pegging_round, all_cards_pegged):
        current_sum = cribbage.sum_cards_for_pegging(cards_in_pegging_round)
        cards_not_played = set(self.hand.cards) - set(all_cards_pegged)
        cards_can_play = [card for card in cards_not_played if cribbage.VALUES[card.rank] < (31 - current_sum)]
        if not cards_can_play:
            return None
        return sorted(cards_can_play)[-1]


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


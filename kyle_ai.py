import itertools
import logging
logging.basicConfig(filename='kyle_ai.log', filemode='w', level=logging.INFO)
import random

import cribbage
from test_ai import Bot

class KyleBotV1(Bot):

    seen_cards = set()

    def _score_from_hand(self, hand, card_set, has_crib):
        return cribbage.Scorer.score(hand, has_crib=has_crib)['score']

    def _score_from_crib(self, cards_to_throw, starter_card, card_set, has_crib):
        return 0

    def notify_new_hand(self, hand):
        super(KyleBotV1, self).notify_new_hand(hand)
        self.seen_cards = set()

    def ask_for_crib_throw(self, has_crib, scores=None):
        assert self.hand
        card_set = set(cribbage.Deck.all_cards())
        hand_set = set(self.hand.all_cards)
        other_cards = card_set - hand_set

        best_hand = None
        best_score = 0
        for possible_hand in itertools.combinations(hand_set, 4):
            hand = cribbage.Hand(list(possible_hand))
            cards_to_throw = list(hand_set - set(possible_hand))
            total_score = 0
            for starter_card in card_set:
                hand.add_starter_card(starter_card)
                total_score += self._score_from_hand(hand, card_set, has_crib)
                total_score += self._score_from_crib(cards_to_throw, starter_card, card_set, has_crib)

            if total_score > best_score:
                best_score = total_score
                best_hand = possible_hand
        normalized_score = float(best_score) / float(len(card_set))
        cards_to_throw = list(hand_set - set(best_hand))
        assert len(cards_to_throw) == 2

        logging.info("Full hand: %s, %s %s", self.hand.prompt, has_crib, scores)
        logging.info("Keeping: %s", ' '.join([card.colored_print for card in best_hand]))
        logging.info("Throwing: %s", ' '.join([card.colored_print for card in cards_to_throw]))
        logging.info("Expected points: %s", normalized_score)

        return cards_to_throw[0], cards_to_throw[1]

class KyleBotV2(KyleBotV1):
    def _score_from_crib(self, cards_to_throw, starter_card, card_set, has_crib):
        total_card_set = card_set - set(cards_to_throw) - set([starter_card])
        for other_cribs in itertools.combinations(card_set, 2):
            pass



if __name__ == '__main__':
    me = KyleBotV1()
    me.ask_for_crib_throw(True)

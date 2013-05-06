import itertools
import logging
import heapq
import random
logging.basicConfig(filename='kyle_ai.log', filemode='w', level=logging.INFO)

import cribbage
from test_ai import Bot

class KyleBotV1(Bot):

    seen_cards = set()

    def _score_from_hand(self, hand, card_set, has_crib):
        return cribbage.Scorer.score(hand, has_crib=has_crib)['score']

    def _score_from_crib(self, cards_to_throw, starter_card, card_set, has_crib):
        return 0

    def _eval_scores(self, hand_score, crib_score):
        return hand_score + crib_score

    def notify_new_hand(self, hand):
        super(KyleBotV1, self).notify_new_hand(hand)
        self.seen_cards = set()

    def _get_best_hand(self, has_crib, scores):
        assert self.hand
        card_set = set(cribbage.Deck.all_cards())
        hand_set = set(self.hand.all_cards)
        other_cards = card_set - hand_set

        best_hand = None
        best_score = -1000
        for possible_hand in itertools.combinations(hand_set, 4):
            hand = cribbage.Hand(list(possible_hand))
            cards_to_throw = list(hand_set - set(possible_hand))
            total_score = 0
            hand_score = 0
            crib_score = 0
            for starter_card in other_cards:
                hand.add_starter_card(starter_card)
                hand_score += self._score_from_hand(hand, other_cards, has_crib)
                crib_score += self._score_from_crib(cards_to_throw, starter_card, other_cards - set([starter_card]), has_crib)

            total_score = self._eval_scores(hand_score, crib_score)
            if total_score > best_score:
                best_score = total_score
                best_hand = possible_hand
        normalized_score = float(best_score) / float(len(other_cards))
        return best_hand, normalized_score

    def ask_for_crib_throw(self, has_crib, scores=None):
        assert self.hand
        best_hand, best_score = self._get_best_hand(has_crib, scores)
        card_set = set(cribbage.Deck.all_cards())

        cards_to_throw = list(set(self.hand.cards) - set(best_hand))
        assert len(cards_to_throw) == 2

        logging.info("\nPLAYER %s", type(self))
        logging.info("Full hand: %s, %s %s", self.hand.prompt, has_crib, scores)
        logging.info("Keeping: %s", ' '.join([card.colored_print for card in best_hand]))
        logging.info("Throwing: %s", ' '.join([card.colored_print for card in cards_to_throw]))
        logging.info("Expected points: %s", best_score)

        return self.hand.throw_cards(cards_to_throw[0], cards_to_throw[1])

class KyleBotV2(KyleBotV1):
    NUM_SAMPLES = 100
    def _score_from_crib(self, cards_to_throw, starter_card, other_cards, has_crib):
        crib_score = 0
        num_other_cribs = 0
        for sample_num in xrange(self.NUM_SAMPLES):
            other_cribs = random.sample(other_cards, 2)
            new_hand = cribbage.Hand(list(cards_to_throw) + list(other_cribs))
            new_hand.add_starter_card(starter_card)
            crib_score += cribbage.Scorer.score(new_hand, is_crib=True)['score']
            num_other_cribs += 1
        expected_crib_score = float(crib_score) / float(num_other_cribs)
        if not has_crib:
            return -1 * expected_crib_score
        return expected_crib_score

class KyleBotV3(KyleBotV1):

    def _score_from_crib(self, cards_to_throw, starter_card, other_cards, has_crib):
        crib_score = 0
        num_other_cribs = 0
        for other_cribs in itertools.combinations(other_cards, 2):
            new_hand = cribbage.Hand(list(cards_to_throw) + list(other_cribs))
            new_hand.add_starter_card(starter_card)
            crib_score += cribbage.Scorer.score(new_hand, is_crib=True)['score']
            num_other_cribs += 1
        expected_crib_score = float(crib_score) / float(num_other_cribs)
        if not has_crib:
            return -1 * expected_crib_score
        return expected_crib_score

    def _get_best_hand(self, has_crib, scores):
        assert self.hand
        card_set = set(cribbage.Deck.all_cards())
        hand_set = set(self.hand.all_cards)
        other_cards = card_set - hand_set

        hands_and_scores = []
        for possible_hand in itertools.combinations(hand_set, 4):
            hand = cribbage.Hand(list(possible_hand))
            total_score = 0
            hand_score = 0
            crib_score = 0
            for starter_card in other_cards:
                hand.add_starter_card(starter_card)
                hand_score += self._score_from_hand(hand, other_cards, has_crib)

            heapq.heappush(hands_and_scores, (-1 * hand_score, possible_hand))

        best_hand = None
        best_score = -1000
        for _ in xrange(3):
            negative_hand_score, possible_hand = heapq.heappop(hands_and_scores)
            crib_score = 0
            hand = cribbage.Hand(list(possible_hand))
            cards_to_throw = list(hand_set - set(possible_hand))
            for starter_card in other_cards:
                crib_score += self._score_from_crib(cards_to_throw, starter_card, other_cards - set([starter_card]), has_crib)
            total_score = self._eval_scores(-1 * negative_hand_score, crib_score)

            if total_score > best_score:
                best_score = total_score
                best_hand = possible_hand
        normalized_score = float(best_score) / float(len(other_cards))
        return best_hand, normalized_score

if __name__ == '__main__':
    me = KyleBotV1()
    me.ask_for_crib_throw(True)

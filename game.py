import argparse
import logging
import random
import time

import cribbage
import kyle_ai
import test_ai

GAME_OVER_POINTS = 121
MAX_TIME_FOR_PLAY = 15

class GameRunner(object):

    def __init__(self, bot1, bot2):
        self.bots = [bot1, bot2]
        self.bot1 = bot1
        self.bot2 = bot2
        self.forfeits = [False, False]

    def player_index(self, bot):
        if bot is self.bot1:
            return 0
        elif bot is self.bot2:
            return 1

    def _game_over(self):
        return self.scores[0] >= GAME_OVER_POINTS or self.scores[1] >= GAME_OVER_POINTS or any(self.forfeits)

    def _time_play(self, player_index, run_func, *run_args, **run_kwargs):
        start_time = time.time()
        ret_val = run_func(*run_args, **run_kwargs)
        end_time = time.time()
        if end_time - start_time > MAX_TIME_FOR_PLAY:
            self.forfeits[player_index] = True
        return ret_val

    def do_pegging(self, player_one_has_crib):
        player_idx_to_start = 0
        if player_one_has_crib:
            player_idx_to_start = 1

        all_cards_pegged = set()
        cards_in_pegging_round = []
        gos = [False, False]
        while len(all_cards_pegged) < 8 and not self._game_over():
            peg_card = self.bots[player_idx_to_start].ask_for_next_peg_card(
                list(cards_in_pegging_round),
                list(all_cards_pegged),
            )
            if peg_card is None:
                gos[player_idx_to_start] = True
                if sum(gos) == 2:
                    gos = [False, False]
                    cards_in_pegging_round = []
                    self.scores[player_idx_to_start] += 1
                player_idx_to_start ^= 1
                continue

            # TODO: Check if cheating
            all_cards_pegged.add(peg_card)
            cards_in_pegging_round.append(peg_card)
            # TODO: Score card
            pegging_sum = cribbage.sum_cards_for_pegging(cards_in_pegging_round)
            assert pegging_sum <= 31
            if pegging_sum == 31:
                gos = [False, False]
                cards_in_pegging_round = []
                self.scores[player_idx_to_start] += 2
            player_idx_to_start ^= 1

    def _run_round(self, player_one_has_crib):
        cards = cribbage.Deck.draw(13)
        hand1_cards = sorted(cards[0:6])
        hand2_cards = sorted(cards[6:12])
        starter_card = cards[-1]

        hand1 = cribbage.Hand(list(hand1_cards))
        hand2 = cribbage.Hand(list(hand2_cards))

        self.bot1.notify_new_hand(hand1)
        self.bot2.notify_new_hand(hand2)

        bot1_crib_throw = self._time_play(
            0,
            self.bot1.ask_for_crib_throw,
            player_one_has_crib,
            self.scores,
        )
        if not set(self.bot1.hand.cards).issubset(hand1_cards) or len(self.bot1.hand.cards) != 4:
            self.forfeits[0] = True
        if self._game_over():
            self.scores[0] = -1
            return

        bot2_crib_throw = self._time_play(
            1,
            self.bot2.ask_for_crib_throw,
            not player_one_has_crib,
            list(reversed(self.scores)),
        )
        if not set(self.bot2.hand.cards).issubset(hand2_cards) or len(self.bot2.hand.cards) != 4:
            self.forfeits[1] = True
        if self._game_over():
            self.scores[1] = -1
            return

        crib_cards = bot1_crib_throw + bot2_crib_throw

        self.bot1.notify_starter_card(starter_card)
        self.bot2.notify_starter_card(starter_card)

        self.do_pegging(player_one_has_crib)
        if self._game_over():
            return

        count_order = [0, 1]
        if player_one_has_crib:
            count_order.reverse()
        for player_idx in count_order:
            self.scores[player_idx] += cribbage.Scorer.score(
                self.bots[player_idx].hand,
                has_crib=bool(player_one_has_crib ^ player_idx),
            )['score']
            if self._game_over():
                return

        crib = cribbage.Hand(crib_cards)
        crib.add_starter_card(starter_card)

        self.scores[count_order[-1]] += cribbage.Scorer.score(crib, is_crib=True)['score']

    def run_game(self):
        self.scores = [0, 0]
        player_one_has_crib = bool(random.choice([0, 1]))

        while not self._game_over():
            self._run_round(player_one_has_crib)
            player_one_has_crib = bool(not player_one_has_crib)

        return self.scores


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run some cribbage AIs.')
    parser.add_argument('--num_games', default=1, required=False, type=int, help='Number of games to run')
    args = parser.parse_args()
    game_scores = []
    players = [
        test_ai.RandomBot,
        test_ai.OneSixBot,
    ]
    for i in xrange(args.num_games / 2):
        random_state = random.getstate()
        runner = GameRunner(*[player() for player in players])
        game_scores.append(runner.run_game())
        print i, game_scores[-1]

        random.setstate(random_state)
        runner = GameRunner(*list(reversed([player() for player in players])))
        game_scores.append(list(reversed(runner.run_game())))
        print i, game_scores[-1]


    num_player_one_wins = sum(score[0] > score[1] for score in game_scores)
    print "Player 1:", num_player_one_wins
    print "Player 2:", args.num_games - num_player_one_wins


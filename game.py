import random
import cribbage

GAME_OVER_POINTS = 121

class GameRunner(object):

    def __init__(self, bot1, bot2):
        self.bots = [bot1, bot2]
        self.bot1 = bot1
        self.bot2 = bot2

    def player_index(self, bot):
        if bot is self.bot1:
            return 0
        elif bot is self.bot2:
            return 1

    def _game_over(self):
        return self.scores[0] > GAME_OVER_POINTS or self.scores[1] > GAME_OVER_POINTS

    def _run_round(self, player_one_has_crib):
        cards = cribbage.Deck.draw(13)
        hand1_cards = sorted(cards[0:6])
        hand2_cards = sorted(cards[6:12])
        starter_card = cards[-1]

        hand1 = cribbage.Hand(list(hand1_cards))
        hand2 = cribbage.Hand(list(hand2_cards))

        self.bot1.notify_new_hand(hand1)
        self.bot2.notify_new_hand(hand2)

        crib_cards = list(
            self.bot1.ask_for_crib_throw(player_one_has_crib, self.scores)
            + self.bot2.ask_for_crib_throw(not player_one_has_crib, reversed(self.scores))
        )

        self.bot1.notify_starter_card(starter_card)
        self.bot2.notify_starter_card(starter_card)

        # TODO: peg

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

        print self.scores


if __name__ == '__main__':
    import test_ai
    runner = GameRunner(test_ai.HumanBot(), test_ai.RandomBot())
    runner.run_game()


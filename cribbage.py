# -*- coding: utf-8 -*-
from __future__ import unicode_literals

""" Presents the user with cribbage hands for scoring practice.
FORKED FROM hrichards, many thanks :)

Program Goals:

    * have a quick, easy to program system for training on scoring, my weakest
        cribbage skill
    * collect data for each hand I see so that I can analyze such data later

Pedagogical Goals:

    * practice unicode
    * practice using the nose testing framework
"""


import itertools
import collections
import math
import os
import random
import string
import sys
import time
import types

HAND_LENGTH = 5

SPADES = 'spades'
HEARTS = 'hearts'
DIAMONDS = 'diamonds'
CLUBS = 'clubs'

RED_SUITS = [HEARTS, DIAMONDS]
BLACK_SUITS = [SPADES, CLUBS]

# TODO: try to get rid of the u'' bits
SUITS = {
        SPADES:   u'♠',
        HEARTS:   u'♥',
        DIAMONDS: u'♦',
        CLUBS:    u'♣',
        }

KING = 13
QUEEN = 12
JACK = 11
ACE = 1

RANKS = {
        KING: u'K',
        QUEEN: u'Q',
        JACK: u'J',
        10: u'T',
        9: u'9',
        8: u'8',
        7: u'7',
        6: u'6',
        5: u'5',
        4: u'4',
        3: u'3',
        2: u'2',
        ACE: u'A',
        }

VALUES = {
        KING: 10,
        QUEEN: 10,
        JACK: 10,
        10: 10,
        9: 9,
        8: 8,
        7: 7,
        6: 6,
        5: 5,
        4: 4,
        3: 3,
        2: 2,
        ACE: 1,
        }

# ANSI escape sequences for "red" and "cancel color"
RED_ESCAPE_OPEN = u'\x1b[31m'
RED_ESCAPE_CLOSE = u'\x1b[0m'


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.izip(a, b)

def ranged_powerset(iterable, range_):
    for i in xrange(range_[0], range_[1] + 1):
        for x in itertools.combinations(iterable, i):
            yield x

class Card(object):
    """ One of the 52 standard playing cards.

    Cards know their suit, rank, and how to be displayed.
    """
    def __init__(self, rank, suit):
        """
        """
        if rank not in RANKS.keys() or suit not in SUITS.keys():
            raise ValueError("No such card.")

        self.rank = rank
        self.suit = suit

    def __hash__(self):
        return hash(self.plaintext_print)

    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit

    def __cmp__(self, other):
        rank_cmp = self.rank - other.rank
        if rank_cmp:
            return rank_cmp
        if self.suit < other.suit:
            return -1
        elif self.suit > other.suit:
            return 1
        else:
            return 0

    @property
    def colored_print(self):
        """ Print a color version of the hand, suitable for CLI
        """
        if self.suit in RED_SUITS:
            escaped_template = RED_ESCAPE_OPEN + "%s%s" + RED_ESCAPE_CLOSE
            return escaped_template % (RANKS[self.rank], SUITS[self.suit])
        else:
            return "%s%s" % (RANKS[self.rank], SUITS[self.suit])

    @property
    def plaintext_print(self):
        """ Print a plaintext version of the hand, suitable for logging
        """
        return "%s %s" % (RANKS[self.rank], self.suit)

    def __str__(self):
        return colored_print()

    def __repr__(self):
        return self.plaintext_print


class Deck(object):

    # XXX: Ghetto memoization
    _all_cards = None

    @classmethod
    def all_cards(cls):
        if cls._all_cards is not None:
            return cls._all_cards
        full_deck = list(itertools.product(RANKS.keys(), SUITS.keys()))
        hand_as_cards = [Card(card[0], card[1]) for card in
                full_deck]
        cls._all_cards = hand_as_cards
        return hand_as_cards

    @classmethod
    def draw(cls, num_cards):
        """
        """
        if num_cards < 0 or num_cards > 52:
            raise ValueError
        else:
            return random.sample(cls.all_cards(), num_cards)


class Hand(object):
    """ A collection of five cards that the user is meant to score.
    """
    def __init__(self, cards, starter_card=None, is_crib=False, has_crib=False):
        """ Get a random hand of five cards.
        """
        self.cards = list(cards)
        self.starter_card = starter_card

    @property
    def prompt(self):
        """ Print the cards in this deal using unicode card glyphs
        """
        color_cards = [card.colored_print for card in self.all_cards]
        return ' '.join(color_cards)

    @property
    def record(self):
        """ Print the cards in this deal using plaintext
        """
        plaintext_cards = [card.plaintext_print for card in self.all_cards]
        return ' '.join(color_cards)

    @property
    def all_cards(self):
        if self.starter_card is not None:
            return self.cards + [self.starter_card]
        else:
            return self.cards

    def add_starter_card(self, card):
        self.starter_card = card

    def throw_cards(self, *cards):
        for card in cards:
            self.cards.remove(card)
        return cards


class Scorer(object):

    @classmethod
    def has_run(cls, hand):
        # Assume sorted hand
        for i in xrange(len(hand) - 2):
            cards = hand[i:i+3]
            if Scorer.is_run(cards):
                return True
        return False

    @classmethod
    def is_run(cls, hand):
        # Assume sorted hand
        if len(hand) < 3:
            return False
        ranks = [card.rank for card in hand]

        for i in xrange(len(ranks) - 1):
            if ranks[i + 1] - ranks[i] != 1:
                return False

        return True

    @classmethod
    def flush_points(cls, hand):
        if len(hand) < 4:
            return 0

        suit_counter = collections.Counter([card.suit for card in hand])
        if any(val for val in suit_counter.values() if val > 3):
            return max(val for val in suit_counter.values())
        return 0

    @classmethod
    def has_pairs(cls, hand):
        # Assume sorted hand
        for card, next_card in pairwise(hand):
            if card.rank == next_card.rank:
                return True
        return False

    @classmethod
    def score(cls, hand, has_crib=False, is_crib=False):
        """ Score the hand in this Deal

        The following patterns are searched for:

        Pairs - 2 for 2, 6 for 3 of a kind, 12 for 4 of a kind
        Fifteens - Any combinations totalling 15 exactly - 2pts each
        Runs - consecutive cards of any suit - 3 for 3, 4 for 4, etc.
        Flush - 4 for 4 in the hand, 5 for 5
        Nobs - J of same suit as starter
        """

        all_cards = sorted(hand.all_cards)

        pairs = []
        if Scorer.has_pairs(all_cards):
            counts = collections.Counter([card.rank for card in all_cards])
            pairs = [2 * sum(xrange(1, val)) for val in counts.values() if val > 1]

        fifteens = [2 for combo in ranged_powerset(all_cards, [2, 5]) if
                sum([VALUES[card.rank] for card in combo]) == 15]

        runs = []
        if Scorer.has_run(all_cards):
            prev_len = 0
            for run in reversed(list(ranged_powerset(all_cards, [3, 5]))):
                run_len = len(run)
                if runs and run_len != prev_len:
                    break
                prev_len = run_len
                if Scorer.is_run(run):
                    runs.append(run_len)

        flush_points = Scorer.flush_points(all_cards)
        if flush_points != 5 and is_crib:
            # Crib flushes must be all 5
            flush_points = 0

        nobs = []
        heels = []
        if hand.starter_card is not None:
            heels = [2 if hand.starter_card.rank == JACK and has_crib else 0]

            if not heels:
                nobs = [1 for card in cards if card.rank == JACK and card.suit ==
                    hand.starter_card.suit]

                assert sum(nobs) in [0, 1]

        score = sum(pairs + fifteens + runs + nobs + heels) + flush_points

        score_dict = dict(
            score=score,
            pairs=sum(pairs),
            fifteens=sum(fifteens),
            runs=sum(runs),
            flushes=flush_points,
            nobs=sum(nobs),
            heels=sum(heels),
        )

        return score_dict

if __name__ == '__main__':
    cards = Deck.all_cards()
    test_hand1 = Hand([cards[0], cards[1], cards[2], cards[5], cards[9]])
    print test_hand1.prompt
    print Scorer.score(test_hand1)
    for _ in xrange(10):
        hand = Hand(Deck.draw(5))
        print hand.prompt
        print Scorer.score(hand)


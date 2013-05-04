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

    @classmethod
    def all_cards(cls):
        full_deck = list(itertools.product(RANKS.keys(), SUITS.keys()))
        hand_as_cards = [Card(card[0], card[1]) for card in
                full_deck]
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
        self.cards = cards
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
    def is_run(cls, hand):
        if len(hand) < 3:
            return False
        ranks = [card.rank for card in hand]

        ranks.sort()

        for i in range(len(ranks) - 1):
            if ranks[i + 1] - ranks[i] != 1:
                return False

        return True

    @classmethod
    def is_flush(cls, hand):
        if len(hand) < 4:
            return False

        suits = [card.suit for card in hand]

        num_suits = len(set(suits))
        return num_suits == 1

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

        combos_dict = {}
        for i in xrange(2, len(hand.all_cards) + 1):
            combos_dict[i] = list(itertools.combinations(hand.all_cards, i))

        pairs = [2 for pair in combos_dict[2] if pair[0].rank == pair[1].rank]

        all_combos = itertools.chain.from_iterable(combos_dict.values())
        fifteens = [2 for combo in itertools.chain.from_iterable(combos_dict.values()) if
                sum([VALUES[card.rank] for card in combo]) == 15]

        runs = []
        for length in sorted(combos_dict.keys(), reverse=True):
            if any(Scorer.is_run(cards) for cards in combos_dict[length]):
                runs.append(length)
                break

        flushes = []
        for length in sorted(combos_dict.keys(), reverse=True):
            if any(Scorer.is_flush(cards) for cards in combos_dict[length]):
                if is_crib and length != 5:
                    # Crib flushes must be all 5
                    continue
                flushes.append(length)
                break

        nobs = []
        heels = []
        if hand.starter_card is not None:
            heels = [2 if hand.starter_card.rank == JACK and has_crib else 0]

            if not heels:
                nobs = [1 for card in cards if card.rank == JACK and card.suit ==
                    hand.starter_card.suit]

                assert sum(nobs) in [0, 1]

        score = sum(pairs + fifteens + runs + flushes + nobs)

        score_dict = dict(
            score=score,
            pairs=sum(pairs),
            fifteens=sum(fifteens),
            runs=sum(runs),
            flushes=sum(flushes),
            nobs=sum(nobs),
        )

        return score_dict

if __name__ == '__main__':
    for _ in xrange(10):
        hand = Hand(Deck.draw(5))
        print hand.prompt
        print Scorer.score(hand)


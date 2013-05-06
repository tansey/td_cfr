import sys
import os
sys.path.insert(0,os.path.realpath('../cfr/'))
from pokertrees import *
from pokerstrategy import *
from environment import *
import random
import math
from itertools import combinations
from itertools import permutations
from itertools import product
from collections import Counter

class ExplicitModelingAgent(Agent):
    def __init__(self, rules, seat, default_strategy, baseline, initial_prior_strength=5):
        Agent.__init__(self, rules, seat)
        self.opponent_seat = -1 * seat + 1
        self.priors = { infoset: [x * initial_prior_strength for x in probs] for infoset,probs in baseline.policy.items() }
        self.opponent_model = Strategy(self.opponent_seat)
        self.opponent_model.policy = { infoset: probs for infoset,probs in baseline.policy.items() }
        self.strategy = Strategy(seat)
        self.strategy.policy = { infoset: probs for infoset,probs in default_strategy.policy.items() }
        self.winnings = 0

    def episode_starting(self):
        self.trajectory = []

    def set_holecards(self, hc):
        self.holecards = hc

    def episode_over(self, state):
        """
        If the opponent revealed their cards, use it to update our explicit model, calculate
        a best response to the explicit model, and store it as our new strategy.
        """
        if state.players_in.count(True) == 2:
            # Showdown. Update our priors on the explicit model of the opponent.
            hc = state.holecards[self.opponent_seat]
            for observation in self.trajectory:
                infoset = self.rules.infoset_format(observation[0], hc, observation[1], observation[2])
                self.priors[infoset][observation[3]] += 1
        else:
            # Somebody folded. No showdown, so marginalize out the hidden opponent holecards.
            for hc,hc_prob in self.possible_opponent_holecards().items():
                infoset = self.rules.infoset_format(observation[0], hc, observation[1], observation[2])
                self.priors[infoset][observation[3]] += hc_prob
        # Use Thompson sampling to create a new explicit opponent model
        self.sample_explicit_model()
        # Calculate a best response to our new opponent model and use it as our strategy
        self.update_strategy()

    def possible_opponent_holecards(self):
        deck = [x for x in self.rules.deck if x not in state.holecards[self.seat]]
        x = Counter(combinations(deck, len(state.holecards[self.opponent_seat])))
        d = float(sum(x.values()))
        return zip(x.keys(),[y / d for y in x.values()])

    def set_infoset(self, infoset):
        self.infoset = infoset

    def get_action(self):
        return self.strategy.sample_action(self.infoset)

    def observe_action(self, player, board, bet_history, action):
        if player == self.opponent_seat:
            self.trajectory.append((player, board, bet_history, action))

    def observe_reward(self, r):
        self.winnings += r

    def sample_dirichlet(self, prior):
        sample = [0,0,0]
        for i in range(len(sample)):
            if prior[i] == 0:
                continue
            else:
                sample[i] = random.gammavariate(prior[i],1)
        sample = [v/sum(sample) for v in sample]
        return sample

    def sample_explicit_model(self):
        self.opponent_model.policy = { infoset: self.sample_dirichlet(prior) for infoset,prior in self.priors.items() }

    def update_strategy(self):
        strategies = [None, None]
        strategies[self.seat] = self.strategy
        strategies[self.opponent_seat] = self.opponent_model
        profile = StrategyProfile(self.rules, strategies)
        self.strategy = profile.best_response()[0].strategies[self.seat]
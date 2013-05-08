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

class ImplicitModelingAgent(Agent):
    def __init__(self, rules, seat, default_strategy, baseline, portfolio):
        Agent.__init__(self, rules, seat)
        self.opponent_seat = -1 * seat + 1
        self.baseline = baseline
        self.portfolio = portfolio
        self.opponent_model = Strategy(self.opponent_seat)
        self.opponent_model.policy = { infoset: probs for infoset,probs in self.baseline.policy.items() }
        self.strategy = Strategy(seat)
        self.strategy.policy = { infoset: probs for infoset,probs in default_strategy.policy.items() }
        self.observation_probs = [1 for model in portfolio]
        self.winnings = 0

    def episode_starting(self):
        self.trajectory = []

    def set_holecards(self, hc):
        self.holecards = hc

    def episode_over(self, state):
        """
        If the opponent revealed their cards, calculate the exact trajectory probability, otherwise
        marginalize over all possible holecards. Then update our implicit models, sample one, calculate 
        a best response, and store it as our new strategy.
        """
        if state.players_in.count(True) == 2:
            # Showdown
            #trajectory_logprobs = [math.log(x) for x in self.trajectory_probs(state.holecards[self.opponent_seat], 1)]
            trajprobs = self.trajectory_probs(state.holecards[self.opponent_seat], 1)
        else:
            # Somebody folded. No showdown, so marginalize out the hidden opponent holecards.
            trajprobs = [0 for model in self.portfolio]
            for hc,hc_prob in self.possible_opponent_holecards(state):
                probs = self.trajectory_probs(hc, hc_prob)
                for i,p in enumerate(probs):
                    trajprobs[i] += p
            #trajectory_logprobs = [math.log(x) for x in trajectory_logprobs]
        # We're only interested in pseudo-likelihood, so store the logprobs to prevent buffer underflows
        for i,prob in enumerate(trajprobs):
                self.observation_probs[i] *= prob
        # Use importance sampling (Thompson's response) to choose a model for our opponent
        implicit_model = self.sample_portfolio_model()
        print self.observation_probs
        # Use the implicit model as the opponent model (Bayes' Bluff)
        self.opponent_model = implicit_model
        self.update_strategy()


    def trajectory_probs(self, hc, hc_prob):
        """
        Calculates the probability of each of the portfolio models generating the trajectory given a certain
        holecard and some probability of having that holecard.
        """
        trajprobs = [hc_prob for model in self.portfolio]
        for observation in self.trajectory:
            infoset = self.rules.infoset_format(observation[0], hc, observation[1], observation[2])
            for model in range(len(self.portfolio)):
                trajprobs[model] *= self.portfolio[model].probs(infoset)[observation[3]]
        return trajprobs

    def possible_opponent_holecards(self, state):
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

    def sample_portfolio_model(self):
        total = sum(self.observation_probs)
        self.observation_probs = [x / total for x in self.observation_probs]
        r = random.random()
        cur = 0
        for i,w in enumerate(self.observation_probs):
            cur += w
            if w > 0 and cur > r:
                print 'Choosing model {0}'.format(i)
                return self.portfolio[i]
        raise Exception('Invalid distribution')

    def update_strategy(self):
        strategies = [None, None]
        strategies[self.seat] = self.strategy
        strategies[self.opponent_seat] = self.opponent_model
        profile = StrategyProfile(self.rules, strategies)
        self.strategy = profile.best_response()[0].strategies[self.seat]
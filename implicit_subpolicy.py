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

class ImplicitSubpolicyModelingAgent(Agent):
    def __init__(self, rules, seat, default_strategy, baseline, portfolio):
        Agent.__init__(self, rules, seat)
        self.opponent_seat = -1 * seat + 1
        self.baseline = baseline
        self.portfolio = portfolio
        self.preflop_portfolio = [{ infoset: probs for infoset,probs in model.policy.items() if infoset.count('/') == 1 } for model in portfolio]
        self.flop_portfolio = [{ infoset: probs for infoset,probs in model.policy.items() if infoset.count('/') == 2 } for model in portfolio]
        self.implicit_preflop = self.preflop_portfolio[0]
        self.implicit_flop = self.flop_portfolio[0]
        print [len(x) for x in self.preflop_portfolio]
        print [len(x) for x in self.flop_portfolio]
        self.opponent_model = Strategy(self.opponent_seat)
        self.opponent_model.policy = { infoset: probs for infoset,probs in self.baseline.policy.items() }
        self.strategy = Strategy(seat)
        self.strategy.policy = { infoset: probs for infoset,probs in default_strategy.policy.items() }
        self.preflop_observation_probs = [1 for model in self.preflop_portfolio]
        self.flop_observation_probs = [1 for model in self.flop_portfolio]
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
        preflop_trajectory = [observation for observation in self.trajectory if observation[2].count('/') == 1]
        flop_trajectory = [observation for observation in self.trajectory if observation[2].count('/') == 2]
        if state.players_in.count(True) == 2:
            # Showdown
            # Calculate preflop trajectory probability for every preflop subpolicy
            preflop_trajprobs = self.trajectory_probs(state.holecards[self.opponent_seat], 1, self.preflop_portfolio, preflop_trajectory)
            # Update the total probability of each subpolicy
            for i,prob in enumerate(preflop_trajprobs):
                self.preflop_observation_probs[i] *= prob
            # Importance sampling to choose a preflop subpolicy
            preflop_subpolicy_idx = self.importance_sampling(self.preflop_observation_probs)
            self.implicit_preflop = self.preflop_portfolio[preflop_subpolicy_idx]
            if len(flop_trajectory) > 0:
                # Marginalize out preflop subpolicies
                reachprob = sum([preflop_trajprobs[i] * self.preflop_observation_probs[i] for i in range(len(preflop_trajprobs))]) / sum(self.preflop_observation_probs)
                # Calculate flop trajectory probability for every flop subpolicy
                flop_trajprobs = self.trajectory_probs(state.holecards[self.opponent_seat], reachprob, self.flop_portfolio, flop_trajectory)
                # Update the total probability, independent of preflop probabilities
                for i,prob in enumerate(flop_trajprobs):
                    self.flop_observation_probs[i] *= prob
                # Importance sampling to choose a flop subpolicy, given we used a certain preflop model
                flop_subpolicy_idx = self.importance_sampling([x * preflop_trajprobs[preflop_subpolicy_idx] for x in self.flop_observation_probs])
                self.implicit_flop = self.flop_portfolio[flop_subpolicy_idx]
        else:
            # Somebody folded. No showdown, so marginalize out the hidden opponent holecards.
            preflop_trajprobs = [{} for model in self.preflop_portfolio]
            for hc,hc_prob in self.possible_opponent_holecards().items():
                probs = self.trajectory_probs(hc, hc_prob, self.preflop_portfolio, preflop_trajectory)
                for i,p in enumerate(probs):
                    preflop_trajprobs[i][hc] = p
            # Update the total probability of each subpolicy
            for i,p in enumerate(preflop_trajprobs):
                self.preflop_observation_probs[i] *= sum(p.values())
            # Importance sampling to choose a preflop subpolicy
            preflop_subpolicy_idx = self.importance_sampling(self.preflop_observation_probs)
            self.implicit_preflop = self.preflop_portfolio[preflop_subpolicy_idx]
            if len(flop_trajectory) > 0:
                hc_probs = {hc: 0 for hc in self.possible_opponent_holecards()}
                # Marginalize out preflop subpolicies
                for i,preflop_model in enumerate(preflop_trajprobs):
                    for hc,hc_prob in preflop_model.iteritems():
                        hc_probs[hc] += self.preflop_observation_probs[i] * hc_prob / sum(self.preflop_observation_probs)
                # Calculate flop trajectory probability for every flop subpolicy, given we are marginalizing out holecards
                flop_trajprobs = [[] for model in self.flop_portfolio]
                for hc,hc_prob in hc_probs.items():
                    probs = self.trajectory_probs(hc, hc_prob, self.flop_portfolio, flop_trajectory)
                # Update the total probability of each subpolicy
                for i,p in enumerate(flop_trajprobs):
                    self.flop_observation_probs[i] *= sum(p)
                # Importance sampling to choose a flop subpolicy, given we marginalized out our preflop model
                flop_subpolicy_idx = self.importance_sampling(self.flop_observation_probs)
                self.implicit_flop = self.flop_portfolio[flop_subpolicy_idx]
        # Use the implicit model as the opponent model (Bayes' Bluff)
        self.merge_subpolicies()
        self.update_strategy()


    def trajectory_probs(self, hc, hc_prob, portfolio, trajectory):
        """
        Calculates the probability of each of the portfolio models generating the trajectory given a certain
        holecard and some probability of having that holecard.
        """
        trajprobs = [hc_prob for model in portfolio]
        for observation in trajectory:
            infoset = self.rules.infoset_format(observation[0], hc, observation[1], observation[2])
            for model in range(len(portfolio)):
                trajprobs[model] *= portfolio[model][infoset][observation[3]]
        return trajprobs

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

    def importance_sampling(self, probs):
        total = sum(probs)
        probs = [x / total for x in probs]
        r = random.random()
        cur = 0
        for i,w in enumerate(probs):
            cur += w
            if w > 0 and cur > r:
                #print 'Choosing model {0}'.format(i)
                return i
        raise Exception('Invalid distribution')

    def merge_subpolicies(self):
        for infoset in self.opponent_model.policy:
            if infoset in self.implicit_preflop:
                self.opponent_model.policy[infoset] = self.implicit_preflop[infoset]
            elif infoset in self.implicit_flop:
                self.opponent_model.policy[infoset] = self.implicit_flop[infoset]
            else:
                raise Exception("Not in here: {0}".format(infoset))

    def update_strategy(self):
        strategies = [None, None]
        strategies[self.seat] = self.strategy
        strategies[self.opponent_seat] = self.opponent_model
        profile = StrategyProfile(self.rules, strategies)
        self.strategy = profile.best_response()[0].strategies[self.seat]
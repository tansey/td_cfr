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

class SubpolicyBootstrappingAgent(Agent):
    def __init__(self, rules, seat, default_strategy, baseline, portfolio, initial_prior_strength=5, min_subpolicy_deviation=0.05, max_subpolicy_range=0.25, min_subpolicy_size=3):
        Agent.__init__(self, rules, seat)
        self.opponent_seat = -1 * seat + 1
        self.baseline = baseline
        self.portfolio = portfolio
        self.min_subpolicy_deviation = min_subpolicy_deviation
        self.max_subpolicy_range = max_subpolicy_range
        self.min_subpolicy_size = min_subpolicy_size
        self.infer_subpolicies()
        self.priors = { infoset: [x * initial_prior_strength for x in probs] for infoset,probs in self.baseline.policy.items() }
        self.opponent_model = Strategy(self.opponent_seat)
        self.opponent_model.policy = { infoset: probs for infoset,probs in self.baseline.policy.items() }
        self.strategy = Strategy(seat)
        self.strategy.policy = { infoset: probs for infoset,probs in default_strategy.policy.items() }
        self.observation_probs = [1 for model in portfolio]
        self.winnings = 0

    def infer_subpolicies(self):
        self.subpolicies = []
        for model in self.portfolio:
            # Calculate how much the model deviates from the baseline strategy at each point
            model_dev = {}
            for infoset in model.policy:
                model_probs = model.probs(infoset)
                baseline_probs = self.baseline.probs(infoset)
                deviation = [model_probs[i] / baseline_probs[i] - 1 if baseline_probs[i] > 0 else model_probs[i] for i in range(3)]
                # Filter out cases where the opponent plays close to the NE
                if self.L2_distance(deviation, [0,0,0]) > self.min_subpolicy_deviation:
                    model_dev[infoset] = deviation
            # Cluster the infosets based on L2 distance
            found = 0
            while len(model_dev) > 0:
                next_centroid = None
                next_subpolicy = None
                for infoset,deviation in model_dev.items():
                    if next_subpolicy is None:
                        #print deviation
                        next_centroid = deviation
                        next_subpolicy = [infoset]
                        model_dev.pop(infoset)
                    elif self.L2_distance(deviation, next_centroid) < self.max_subpolicy_range:
                        #print '\t{0}'.format(deviation)
                        next_subpolicy.append(infoset)
                        model_dev.pop(infoset)
                subpolicy = { infoset: probs for infoset,probs in model.policy.items() if infoset in next_subpolicy }
                if len(subpolicy) > self.min_subpolicy_size:
                    self.subpolicies.append(subpolicy)
                    found += 1
            print 'Found {0} subpolicies, with lengths {1}'.format(found, [len(x) for x in self.subpolicies[-found:]])
        #sys.exit()

    def L2_distance(self, p1, p2):
        return math.sqrt(sum([(p1[i] - p2[i])**2 for i in range(len(p1))]))

    def episode_starting(self):
        self.trajectory = []

    def set_holecards(self, hc):
        self.holecards = hc

    def episode_over(self, state):
        """
        If the opponent revealed their cards, calculate the exact subset trajectory probabilities, otherwise
        marginalize over all possible holecards. Then update our implicit models, sample one, use it to
        generate samples for our explicit model, calculate a best response to the explicit model, and
        store it as our new strategy.
        """
        if state.players_in.count(True) == 2:
            # Showdown
            #trajectory_logprobs = [math.log(x) for x in self.trajectory_probs(state.holecards[self.opponent_seat], 1)]
            trajprobs = self.trajectory_probs(state.holecards[self.opponent_seat], 1)
        else:
            # Somebody folded. No showdown, so marginalize out the hidden opponent holecards.
            trajprobs = [1 for model in self.portfolio]
            for hc,hc_prob in self.possible_opponent_holecards().items():
                probs = self.trajectory_probs(hc, hc_prob)
                for i,p in enumerate(probs):
                    trajprobs[i] += p
            #trajectory_logprobs = [math.log(x) for x in trajectory_logprobs]
        # We're only interested in pseudo-likelihood, so store the logprobs to prevent buffer underflows
        for i,prob in enumerate(trajprobs):
                self.observation_probs[i] *= prob
        # Use importance sampling (Thompson's response) to choose a model for our opponent
        implicit_model = self.sample_portfolio_model()
        # Update our priors on the explicit model of the opponent
        self.bootstrap_explicit_model(implicit_model)
        # Use Thompson sampling to create a new explicit opponent model
        self.sample_explicit_model()
        # Calculate a best response to our new opponent model and use it as our strategy
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

    def sample_dirichlet(self, prior):
        sample = [0,0,0]
        for i in range(len(sample)):
            if prior[i] == 0:
                continue
            else:
                sample[i] = random.gammavariate(prior[i],1)
        sample = [v/sum(sample) for v in sample]
        return sample

    def bootstrap_explicit_model(self, portfolio_model):
        for infoset in self.opponent_model.policy:
            prior = self.priors[infoset]
            portfolio_probs = portfolio_model.probs(infoset)
            for i in range(3):
                prior[i] += portfolio_probs[i]

    def sample_explicit_model(self):
        self.opponent_model.policy = { infoset: self.sample_dirichlet(prior) for infoset,prior in self.priors.items() }

    def update_strategy(self):
        strategies = [None, None]
        strategies[self.seat] = self.strategy
        strategies[self.opponent_seat] = self.opponent_model
        profile = StrategyProfile(self.rules, strategies)
        self.strategy = profile.best_response()[0].strategies[self.seat]